from config.traffic_controller import TrafficController

class RuleBasedController(TrafficController):
    def __init__(self, tls_ids, max_starvation_time=40):
        super().__init__(tls_ids)
        self.max_starvation_time = max_starvation_time
        self.lane_wait_times = {}
        self.emergency_override_active = {}
        self.emergency_phase_start_time = {}
        self.min_emergency_phase_duration = 15
        
    def decide_phase(self, tls_id):
        """Rule-based decision making with emergency vehicle priority"""
        import traci
        try:
            emergency_vehicles = self.get_emergency_vehicles(tls_id)
            if emergency_vehicles:
                self.emergency_override_active[tls_id] = True
                target_phase = self._handle_emergency(tls_id, emergency_vehicles)
                
                current_time = traci.simulation.getTime()
                current_phase = traci.trafficlight.getPhase(tls_id)
                
                if current_phase != target_phase:
                    traci.trafficlight.setPhase(tls_id, target_phase)
                    self.emergency_phase_start_time[tls_id] = current_time
                    print(f"⚡ EMERGENCY PHASE SWITCH: {tls_id} → Phase {target_phase}")
                
                if tls_id in self.emergency_phase_start_time:
                    elapsed = current_time - self.emergency_phase_start_time[tls_id]
                    if elapsed < self.min_emergency_phase_duration:
                        remaining = self.min_emergency_phase_duration - elapsed
                        traci.trafficlight.setPhaseDuration(tls_id, max(remaining, 10))
                    
                return target_phase
            else:
                if self.emergency_override_active.get(tls_id, False):
                    self.emergency_override_active[tls_id] = False
                    if tls_id in self.emergency_phase_start_time:
                        del self.emergency_phase_start_time[tls_id]
            
            queue_lengths, waiting_times, occupancy = self.get_lane_data(tls_id)
            
            for lane in waiting_times:
                if lane not in self.lane_wait_times:
                    self.lane_wait_times[lane] = 0
                self.lane_wait_times[lane] = waiting_times[lane]
            
            starving_lanes = [lane for lane, wait in self.lane_wait_times.items() 
                             if wait > self.max_starvation_time]
            
            if starving_lanes:
                target_lane = max(starving_lanes, key=lambda l: self.lane_wait_times[l])
                return self._get_phase_for_lane(tls_id, target_lane)
            
            if queue_lengths:
                lane_scores = {}
                for lane, queue in queue_lengths.items():
                    wait_time = waiting_times.get(lane, 0)
                    lane_scores[lane] = queue * 1.0 + wait_time * 0.1
                
                if lane_scores:
                    max_score_lane = max(lane_scores.items(), key=lambda x: x[1])
                    if max_score_lane[1] > 0:
                        return self._get_phase_for_lane(tls_id, max_score_lane[0])
            
            return traci.trafficlight.getPhase(tls_id)
            
        except Exception as e:
            print(f"Error in rule-based decision for {tls_id}: {e}")
            return 0
    
    def _handle_emergency(self, tls_id, emergency_vehicles):
        """Handle emergency vehicle priority"""
        import traci
        try:
            priority_order = {'ambulance': 3, 'firetruck': 3, 'police': 2}
            
            best_vehicle = None
            best_priority = 0
            
            for veh_id, lane, veh_info in emergency_vehicles:
                veh_type = veh_info['vehicle_type']
                priority = priority_order.get(veh_type, 1)
                
                waiting_time = veh_info.get('waiting_time', 0)
                waiting_factor = min(waiting_time / 30.0, 2.0)
                
                position = veh_info.get('position', 0)
                distance_factor = max(0, 1 - position / 500)
                
                total_priority = priority + distance_factor + waiting_factor
                
                if total_priority > best_priority:
                    best_priority = total_priority
                    best_vehicle = (veh_id, lane, veh_info)
            
            if best_vehicle:
                emergency_lane = best_vehicle[1]
                veh_type = best_vehicle[2]['vehicle_type']
                veh_id = best_vehicle[0]
                
                print(f"🚨 EMERGENCY: {veh_type.upper()} {veh_id} on {emergency_lane}")
                
                target_phase = self._get_phase_for_lane(tls_id, emergency_lane)
                return target_phase
            
            return traci.trafficlight.getPhase(tls_id)
            
        except Exception as e:
            print(f"Error handling emergency for {tls_id}: {e}")
            return 0
    
    def _get_phase_for_lane(self, tls_id, lane):
        """Get the optimal phase for a specific lane"""
        import traci
        try:
            controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
            logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
            
            for phase_idx, phase in enumerate(logic.phases):
                state = phase.state
                for i, lane_id in enumerate(controlled_lanes):
                    if lane_id == lane and i < len(state):
                        if state[i] in ['G', 'g']:
                            return phase_idx
            
            for phase_idx, phase in enumerate(logic.phases):
                state = phase.state
                for i, lane_id in enumerate(controlled_lanes):
                    if lane_id == lane and i < len(state):
                        if state[i] not in ['r', 'R']:
                            return phase_idx
            
            return 0
            
        except Exception as e:
            print(f"Error getting phase for lane {lane}: {e}")
            return 0
