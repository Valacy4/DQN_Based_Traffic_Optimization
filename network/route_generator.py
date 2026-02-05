import random
import xml.etree.ElementTree as ET
import numpy as np

class RouteGenerator:
    def __init__(self, net_file):
        self.net_file = net_file
        self.edge_ids = self._extract_edge_ids()
        self.sumolib_net = None
        self.emergency_spawn_probability = 0.08
        self.spawnable_edges = self._get_spawnable_edges()
        self.boundary_edges = self._get_boundary_edges()
        
    def _extract_edge_ids(self):
        """Extract edge IDs from network file"""
        tree = ET.parse(self.net_file)
        root = tree.getroot()
        edges = [edge.get('id') for edge in root.findall('edge') 
                if ':' not in edge.get('id')]
        return edges
    
    def _get_boundary_edges(self):
        """Get edges at network boundaries (corner nodes for proper vehicle exit)"""
        try:
            tree = ET.parse(self.net_file)
            root = tree.getroot()
            
            boundary_nodes = {'n0_0', 'n0_3', 'n3_0', 'n3_3'}
            
            boundary_edges = []
            for edge in root.findall('edge'):
                edge_id = edge.get('id')
                if ':' in edge_id:
                    continue
                
                to_node = edge.get('to')
                if to_node in boundary_nodes:
                    boundary_edges.append(edge_id)
            
            return boundary_edges if boundary_edges else self.edge_ids
            
        except Exception as e:
            print(f"Warning: Could not identify boundary edges: {e}")
            return self.edge_ids
    
    def _get_spawnable_edges(self):
        """Get edges that are NOT at 4-way intersections (safe for spawning)"""
        try:
            tree = ET.parse(self.net_file)
            root = tree.getroot()
            
            node_connections = {}
            for edge in root.findall('edge'):
                edge_id = edge.get('id')
                if ':' in edge_id:
                    continue
                
                from_node = edge.get('from')
                to_node = edge.get('to')
                
                if from_node not in node_connections:
                    node_connections[from_node] = {'incoming': 0, 'outgoing': 0}
                if to_node not in node_connections:
                    node_connections[to_node] = {'incoming': 0, 'outgoing': 0}
                
                node_connections[from_node]['outgoing'] += 1
                node_connections[to_node]['incoming'] += 1
            
            four_way_nodes = set()
            for node_id, counts in node_connections.items():
                total = counts['incoming'] + counts['outgoing']
                if total >= 8:
                    four_way_nodes.add(node_id)
            
            spawnable = []
            for edge in root.findall('edge'):
                edge_id = edge.get('id')
                if ':' in edge_id:
                    continue
                
                from_node = edge.get('from')
                if from_node not in four_way_nodes:
                    spawnable.append(edge_id)
            
            return spawnable if spawnable else self.edge_ids
            
        except Exception as e:
            print(f"Warning: Could not filter 4-way intersections: {e}")
            return self.edge_ids
    
    def _get_sumolib_net(self):
        """Get sumolib network object"""
        if self.sumolib_net is None:
            try:
                import sumolib
                self.sumolib_net = sumolib.net.readNet(self.net_file)
            except ImportError:
                return None
        return self.sumolib_net
    
    def generate_routes(self, output_file, num_vehicles=100, emergency_ratio=0.08):
        """Generate route file with emergency vehicles, sorted by departure time"""
        routes = ET.Element('routes', xmlns__xsi="http://www.w3.org/2001/XMLSchema-instance",
                           xsi__noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd")
        
        emergency_count = 0
        vehicles_data = []
        
        for i in range(num_vehicles):
            if random.random() < emergency_ratio:
                vtype = random.choice(['ambulance', 'police', 'firetruck'])
                emergency_count += 1
            else:
                vtype = random.choice(['car', 'car', 'car', 'bike', 'motorcycle'])
            
            edge_list, actual_vtype = self.generate_dynamic_route(vtype)
            
            if len(edge_list) >= 2:
                depart_time = i * random.uniform(1.5, 3.0)
                vehicles_data.append({
                    'id': f'veh_{i}',
                    'type': actual_vtype,
                    'depart': depart_time,
                    'edges': edge_list
                })
        
        vehicles_data.sort(key=lambda x: x['depart'])
        
        for veh_data in vehicles_data:
            vehicle = ET.SubElement(routes, 'vehicle')
            vehicle.set('id', veh_data['id'])
            vehicle.set('type', veh_data['type'])
            vehicle.set('depart', f'{veh_data["depart"]:.1f}')
            vehicle.set('departLane', 'best')
            vehicle.set('departSpeed', 'max')
            
            if veh_data['type'] in ['ambulance', 'police', 'firetruck']:
                vehicle.set('departPos', 'random')
                vehicle.set('arrivalPos', 'max')
                vehicle.set('speedFactor', '1.2')
            
            route = ET.SubElement(vehicle, 'route')
            route.set('edges', ' '.join(veh_data['edges']))
        
        tree = ET.ElementTree(routes)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        print(f"Routes generated: {output_file}")
        print(f"Emergency vehicles: {emergency_count}/{num_vehicles}")
        return output_file
    
    def generate_dynamic_route(self, vtype, min_edges=5, max_edges=10):
        """Generate dynamic route ensuring vehicles exit at network boundaries with proper connectivity"""
        if random.random() < self.emergency_spawn_probability:
            emergency_types = ['ambulance', 'police', 'firetruck']
            if vtype in emergency_types:
                actual_vtype = vtype
            else:
                actual_vtype = random.choice(emergency_types)
        else:
            actual_vtype = vtype
        
        start_edge = random.choice(self.spawnable_edges)
        route = [start_edge]
        
        if actual_vtype in ['ambulance', 'police', 'firetruck']:
            num_edges = random.randint(max_edges, max_edges + 3)
        else:
            num_edges = random.randint(min_edges, max_edges)
        
        current_edge_id = start_edge
        net = self._get_sumolib_net()
        
        if net is None:
            return route, actual_vtype
        
        for step in range(num_edges - 1):
            try:
                current_edge = net.getEdge(current_edge_id)
                outgoing = list(current_edge.getOutgoing())
                
                if not outgoing:
                    break
                
                if len(route) > 1:
                    prev_edge_id = route[-2]
                    outgoing = [e for e in outgoing if e.getID() != prev_edge_id]
                
                if not outgoing:
                    outgoing = list(current_edge.getOutgoing())
                
                if not outgoing:
                    break
                
                if step >= num_edges - 3:
                    boundary_options = [e for e in outgoing if e.getID() in self.boundary_edges]
                    if boundary_options:
                        next_edge = random.choice(boundary_options)
                        route.append(next_edge.getID())
                        break
                    else:
                        next_edge = random.choice(outgoing)
                elif actual_vtype in ['ambulance', 'police', 'firetruck']:
                    weights = []
                    for edge in outgoing:
                        try:
                            lanes = edge.getLaneNumber()
                            priority = edge.getPriority()
                            weight = lanes * priority
                            weights.append(weight)
                        except:
                            weights.append(1)
                    
                    if weights and max(weights) > 0:
                        weights = np.array(weights)
                        weights = weights / weights.sum()
                        next_edge = np.random.choice(outgoing, p=weights)
                    else:
                        next_edge = random.choice(outgoing)
                else:
                    next_edge = random.choice(outgoing)
                
                next_edge_id = next_edge.getID()
                
                if next_edge_id not in route:
                    route.append(next_edge_id)
                    current_edge_id = next_edge_id
                    
                    if next_edge_id in self.boundary_edges and step >= min_edges - 1:
                        break
                else:
                    break
            except Exception as e:
                print(f"Route generation error at step {step}: {e}")
                break
        
        if len(route) >= 2 and route[-1] not in self.boundary_edges:
            try:
                for _ in range(5):
                    current_edge = net.getEdge(route[-1])
                    outgoing = list(current_edge.getOutgoing())
                    
                    boundary_options = [e for e in outgoing if e.getID() in self.boundary_edges]
                    if boundary_options:
                        route.append(random.choice(boundary_options).getID())
                        break
                    elif outgoing:
                        filtered = [e for e in outgoing if e.getID() not in route[-3:]]
                        if filtered:
                            next_edge = random.choice(filtered)
                        else:
                            next_edge = random.choice(outgoing)
                        route.append(next_edge.getID())
                    else:
                        break
            except:
                pass
        
        if len(route) < 2:
            route = [random.choice(self.spawnable_edges), random.choice(self.spawnable_edges)]
        
        return route, actual_vtype
    
    def generate_continuous_traffic(self, vehicle_rate=50):
        """Generate single vehicle for continuous spawning"""
        emergency_prob = 0.08 if vehicle_rate > 30 else 0.05
        
        if random.random() < emergency_prob:
            vtype = random.choice(['ambulance', 'police', 'firetruck'])
        else:
            vtype = random.choices(
                ['car', 'bike', 'motorcycle'], 
                weights=[0.75, 0.15, 0.1]
            )[0]
        
        edge_list, actual_vtype = self.generate_dynamic_route(vtype)
        
        return edge_list, actual_vtype
