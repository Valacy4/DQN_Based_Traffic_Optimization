import numpy as np
from abc import ABC, abstractmethod
from collections import defaultdict

class TrafficController(ABC):
    def __init__(self, tls_ids):
        self.tls_ids = tls_ids
        self.phase_times = defaultdict(lambda: {'current': 0, 'last_switch': 0})
        self.metrics = {
            'total_waiting_time': 0,
            'total_vehicles_passed': 0,
            'emergency_vehicles': 0,
            'regular_vehicles': 0,
            'queue_lengths': defaultdict(list),
            'emergency_vehicle_list': []
        }
        self.emergency_vehicles_tracked = set()
        
    @abstractmethod
    def decide_phase(self, tls_id):
        pass
    
    def get_lane_data(self, tls_id):
        """Get comprehensive lane data for traffic light"""
        import traci
        controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
        
        queue_lengths = {}
        waiting_times = {}
        occupancy = {}
        
        for lane in set(controlled_lanes):
            try:
                queue_lengths[lane] = traci.lane.getLastStepHaltingNumber(lane)
                waiting_times[lane] = traci.lane.getWaitingTime(lane)
                occupancy[lane] = traci.lane.getLastStepOccupancy(lane)
            except Exception as e:
                queue_lengths[lane] = 0
                waiting_times[lane] = 0
                occupancy[lane] = 0
        
        return queue_lengths, waiting_times, occupancy
    
    def get_emergency_vehicles(self, tls_id):
        """Get emergency vehicles near traffic light"""
        import traci
        controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
        emergency_veh = []
        
        for lane in set(controlled_lanes):
            try:
                vehicles = traci.lane.getLastStepVehicleIDs(lane)
                for veh in vehicles:
                    try:
                        vtype = traci.vehicle.getTypeID(veh)
                        if vtype in ['ambulance', 'police', 'firetruck']:
                            vehicle_info = {
                                'vehicle_id': veh,
                                'vehicle_type': vtype,
                                'lane': lane,
                                'position': traci.vehicle.getLanePosition(veh),
                                'speed': traci.vehicle.getSpeed(veh),
                                'waiting_time': traci.vehicle.getWaitingTime(veh)
                            }
                            emergency_veh.append((veh, lane, vehicle_info))
                            self.emergency_vehicles_tracked.add(veh)
                    except:
                        continue
            except:
                continue
        
        return emergency_veh
    
    def set_phase(self, tls_id, phase_index):
        """Set traffic light phase"""
        import traci
        try:
            current_phase = traci.trafficlight.getPhase(tls_id)
            if current_phase != phase_index:
                traci.trafficlight.setPhase(tls_id, phase_index)
                self.phase_times[tls_id]['last_switch'] = traci.simulation.getTime()
            self.phase_times[tls_id]['current'] = phase_index
        except Exception as e:
            print(f"Error setting phase for {tls_id}: {e}")
    
    def get_phase_duration(self, tls_id):
        """Get duration of current phase"""
        import traci
        try:
            current_time = traci.simulation.getTime()
            last_switch = self.phase_times[tls_id]['last_switch']
            return current_time - last_switch
        except:
            return 0
    
    def update_metrics(self):
        """Update traffic metrics"""
        import traci
        try:
            all_vehicles = traci.vehicle.getIDList()
            total_wait = 0
            emergency_count = 0
            regular_count = 0
            emergency_vehicle_list = []
            
            for veh in all_vehicles:
                try:
                    wait_time = traci.vehicle.getWaitingTime(veh)
                    total_wait += wait_time
                    
                    vtype = traci.vehicle.getTypeID(veh)
                    if vtype in ['ambulance', 'police', 'firetruck']:
                        emergency_count += 1
                        
                        try:
                            emergency_info = {
                                'vehicle_id': veh,
                                'vehicle_type': vtype,
                                'current_lane': traci.vehicle.getLaneID(veh),
                                'position': traci.vehicle.getPosition(veh),
                                'speed': traci.vehicle.getSpeed(veh),
                                'waiting_time': wait_time,
                                'has_priority': wait_time < 5
                            }
                            emergency_vehicle_list.append(emergency_info)
                        except:
                            pass
                    else:
                        regular_count += 1
                        
                except:
                    continue
            
            self.metrics['total_waiting_time'] = total_wait
            self.metrics['emergency_vehicles'] = emergency_count
            self.metrics['regular_vehicles'] = regular_count
            self.metrics['emergency_vehicle_list'] = emergency_vehicle_list
            
            try:
                arrived = traci.simulation.getArrivedNumber()
                self.metrics['total_vehicles_passed'] = arrived
            except:
                pass
            
            queue_data = {}
            for tls_id in self.tls_ids:
                try:
                    queue_lengths, _, _ = self.get_lane_data(tls_id)
                    queue_data.update(queue_lengths)
                except:
                    pass
            
            self.metrics['queue_lengths'] = queue_data
            
            return self.metrics
            
        except Exception as e:
            print(f"Error updating metrics: {e}")
            return self.metrics
