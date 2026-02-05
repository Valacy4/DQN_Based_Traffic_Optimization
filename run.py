import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path

def setup_sumo_environment():
    """Simplified SUMO environment setup without OpenGL library manipulation"""
    sumo_home = None
    
    try:
        result = subprocess.run(['which', 'sumo'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            sumo_path = result.stdout.strip()
            if '.pythonlibs' in sumo_path or 'site-packages' in sumo_path:
                import site
                site_packages = site.getsitepackages()[0]
                sumo_package_path = os.path.join(site_packages, 'sumo')
                if os.path.exists(sumo_package_path):
                    sumo_home = sumo_package_path
                    print(f"✓ SUMO_HOME set from eclipse-sumo package: {sumo_home}")
            else:
                base_path = str(Path(sumo_path).parent.parent)
                for possible_sumo_home in [base_path, os.path.join(base_path, 'share', 'sumo'), '/usr/share/sumo']:
                    tools_path = os.path.join(possible_sumo_home, 'tools')
                    if os.path.exists(tools_path):
                        sumo_home = possible_sumo_home
                        print(f"✓ SUMO_HOME set from system SUMO: {sumo_home}")
                        break
            
            if sumo_home:
                os.environ['SUMO_HOME'] = sumo_home
    except Exception as e:
        print(f"Warning during SUMO detection: {e}")
    
    if not sumo_home:
        try:
            import site
            site_packages = site.getsitepackages()[0]
            sumo_package_path = os.path.join(site_packages, 'sumo')
            if os.path.exists(sumo_package_path):
                sumo_home = sumo_package_path
                os.environ['SUMO_HOME'] = sumo_home
                print(f"✓ SUMO_HOME set from eclipse-sumo package: {sumo_home}")
            else:
                print("✗ Error: SUMO not found. Please install SUMO or eclipse-sumo package.")
                sys.exit(1)
        except Exception as e:
            print(f"✗ Error: SUMO not found: {e}")
            sys.exit(1)
    
    if sumo_home:
        tools_path = os.path.join(sumo_home, 'tools')
        if os.path.exists(tools_path) and tools_path not in sys.path:
            sys.path.insert(0, tools_path)
            print(f"✓ Added SUMO tools to path: {tools_path}")
    
    try:
        import traci
        import sumolib
        print("✓ TraCI and sumolib imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Error importing SUMO modules: {e}")
        print(f"  SUMO_HOME: {sumo_home}")
        print(f"  sys.path: {sys.path[:3]}")
        sys.exit(1)

from network.generate_network import generate_3x3_grid
from network.vehicle_types import create_vehicle_types
from network.route_generator import RouteGenerator
from network.urban_elements import create_urban_elements, create_3d_gui_settings
from config.rule_based_controller import RuleBasedController

class TrafficSimulation:
    def __init__(self, mode='rule', gui=True):
        self.mode = mode
        self.gui = gui
        self.network_dir = 'network'
        self.config_file = os.path.join(self.network_dir, 'simulation.sumocfg')
        self.controller = None
        self.vehicle_counter = 0
        self.last_spawn_time = 0
        self.spawn_interval = 2.0
        
        os.makedirs('dashboard', exist_ok=True)
        os.makedirs('models', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        with open('dashboard/control_mode.txt', 'w') as f:
            f.write('RL-based' if mode == 'rl' else 'Rule-based')
    
    def generate_config_files(self):
        """Generate all SUMO configuration files"""
        print("\n🔧 Generating SUMO network...")
        net_file = generate_3x3_grid()
        
        print("🚗 Creating vehicle types...")
        vtypes_file = create_vehicle_types()
        
        print("🌳 Creating urban elements...")
        create_urban_elements(self.network_dir)
        
        print("🎨 Creating 3D GUI settings...")
        create_3d_gui_settings(self.network_dir)
        
        print("🛣️  Generating initial routes...")
        rg = RouteGenerator(net_file)
        routes_file = rg.generate_routes(
            os.path.join(self.network_dir, 'routes.rou.xml'),
            num_vehicles=100,
            emergency_ratio=0.08
        )
        
        self.route_generator = rg
        
        import xml.etree.ElementTree as ET
        config = ET.Element('configuration')
        
        input_elem = ET.SubElement(config, 'input')
        net_elem = ET.SubElement(input_elem, 'net-file')
        net_elem.set('value', 'grid.net.xml')
        route_elem = ET.SubElement(input_elem, 'route-files')
        route_elem.set('value', 'routes.rou.xml')
        add_elem = ET.SubElement(input_elem, 'additional-files')
        add_elem.set('value', 'vtypes.add.xml,buildings.poly.xml,pois.add.xml')
        
        time_elem = ET.SubElement(config, 'time')
        begin_elem = ET.SubElement(time_elem, 'begin')
        begin_elem.set('value', '0')
        
        gui_settings = ET.SubElement(config, 'gui_only')
        gui_settings_file = ET.SubElement(gui_settings, 'gui-settings-file')
        gui_settings_file.set('value', 'gui-settings.xml')
        
        processing = ET.SubElement(config, 'processing')
        collision_action = ET.SubElement(processing, 'collision.action')
        collision_action.set('value', 'warn')
        rerouting = ET.SubElement(processing, 'device.rerouting.probability')
        rerouting.set('value', '0.1')
        tls_settings = ET.SubElement(processing, 'tls.all-off')
        tls_settings.set('value', 'false')
        
        tree = ET.ElementTree(config)
        tree.write(self.config_file, encoding='utf-8', xml_declaration=True)
        
        self._validate_network_files()
        
        print(f"✓ Configuration created: {self.config_file}")
        return self.config_file
    
    def _validate_network_files(self):
        """Validate all required network files exist"""
        required_files = [
            self.config_file,
            os.path.join(self.network_dir, 'grid.net.xml'),
            os.path.join(self.network_dir, 'routes.rou.xml'),
            os.path.join(self.network_dir, 'vtypes.add.xml'),
            os.path.join(self.network_dir, 'gui-settings.xml'),
            os.path.join(self.network_dir, 'buildings.poly.xml'),
            os.path.join(self.network_dir, 'pois.add.xml')
        ]
        
        print("\n📋 Validating network files:")
        all_valid = True
        for file_path in required_files:
            exists = os.path.exists(file_path)
            status = "✓" if exists else "✗"
            print(f"  {status} {file_path}")
            if not exists:
                all_valid = False
        
        if all_valid:
            print("✓ All network files validated successfully\n")
        else:
            raise FileNotFoundError("Some required network files are missing")
    
    def start_sumo(self):
        """Start SUMO with proper settings"""
        import traci
        
        sumo_binary = 'sumo-gui' if self.gui else 'sumo'
        error_log = 'logs/sumo_error.log'
        
        sumo_cmd = [
            sumo_binary,
            '-c', self.config_file,
            '--start',
            '--quit-on-end',
            '--step-length', '0.08',
            '--collision.action', 'warn',
            '--time-to-teleport', '300',
            '--pedestrian.model', 'striping',
            '--lateral-resolution', '0.8',
            '--log', error_log,
            '--error-log', error_log,
            '--message-log', error_log,
            '--no-warnings', 'false',
            '--gui-settings-file', os.path.join(self.network_dir, 'gui-settings.xml')
        ]
        
        print(f"🚀 Starting SUMO with command: {' '.join(sumo_cmd)}")
        print(f"📝 Logs will be written to: {error_log}")
        
        try:
            traci.start(sumo_cmd)
            print("✓ SUMO started successfully")
            print(f"  Traffic lights found: {len(traci.trafficlight.getIDList())}")
        except Exception as e:
            print(f"\n✗ Error starting SUMO: {e}")
            if os.path.exists(error_log):
                print(f"\n📄 Last 20 lines of {error_log}:")
                with open(error_log, 'r') as f:
                    lines = f.readlines()
                    print(''.join(lines[-20:]))
            raise
    
    def initialize_controller(self):
        """Initialize traffic controller"""
        import traci
        tls_ids = traci.trafficlight.getIDList()
        print(f"🚦 Found {len(tls_ids)} traffic lights: {tls_ids}")
        
        if self.mode == 'rl':
            try:
                from config.dqn_agent import DQNAgent
                self.controller = DQNAgent(tls_ids)
                model_path = 'models/dqn_model.pth'
                if os.path.exists(model_path):
                    self.controller.load_model(model_path)
                    print("✓ Loaded existing DQN model")
            except Exception as e:
                print(f"✗ Warning: Could not load DQN agent ({e}), falling back to rule-based controller")
                self.controller = RuleBasedController(tls_ids)
                self.mode = 'rule'
        else:
            self.controller = RuleBasedController(tls_ids)
        
        print(f"✓ Initialized {self.mode} controller")
    
    def spawn_vehicle(self):
        """Spawn vehicles continuously"""
        import traci
        current_time = traci.simulation.getTime()
        
        if current_time - self.last_spawn_time < self.spawn_interval:
            return
        
        try:
            edge_ids, vtype = self.route_generator.generate_continuous_traffic(vehicle_rate=50)
            
            veh_id = f'dyn_veh_{self.vehicle_counter}'
            self.vehicle_counter += 1
            
            if vtype in ['ambulance', 'police', 'firetruck']:
                print(f"🚨 Spawning emergency vehicle: {vtype} {veh_id}")
                traci.vehicle.add(veh_id, '', typeID=vtype, departLane='first', 
                                departSpeed='max', departPos='base')
            else:
                traci.vehicle.add(veh_id, '', typeID=vtype, departLane='best', 
                                departSpeed='max')
            
            traci.vehicle.setRoute(veh_id, edge_ids)
            self.last_spawn_time = current_time
            
        except Exception as e:
            print(f"Error spawning vehicle: {e}")
    
    def update_metrics(self):
        """Update traffic metrics - WITHOUT throughput"""
        metrics = self.controller.update_metrics()
        
        total_vehicles = len(metrics.get('emergency_vehicle_list', [])) + metrics.get('regular_vehicles', 0)
        avg_wait = metrics.get('total_waiting_time', 0) / max(total_vehicles, 1)
        
        dashboard_metrics = {
            'avg_waiting_time': avg_wait,
            'total_vehicles': total_vehicles,
            'emergency_vehicles': metrics.get('emergency_vehicles', 0),
            'regular_vehicles': metrics.get('regular_vehicles', 0),
            'queue_lengths': dict(metrics.get('queue_lengths', {})),
            'emergency_vehicle_list': metrics.get('emergency_vehicle_list', [])
        }
        
        with open('dashboard/metrics.json', 'w') as f:
            json.dump(dashboard_metrics, f)
    
    def save_training_stats(self):
        """Save training statistics for RL mode"""
        if self.mode == 'rl' and hasattr(self.controller, 'training_stats'):
            with open('dashboard/training_stats.json', 'w') as f:
                json.dump(self.controller.training_stats, f)
    
    def run(self):
        """Main simulation loop"""
        import traci
        
        print("=" * 60)
        print("🚦 Traffic Signal Control System")
        print("=" * 60)
        
        self.generate_config_files()
        self.start_sumo()
        self.initialize_controller()
        
        print("\n▶️  Starting simulation loop...")
        step = 0
        
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                
                self.spawn_vehicle()
                
                for tls_id in self.controller.tls_ids:
                    new_phase = self.controller.decide_phase(tls_id)
                    self.controller.set_phase(tls_id, new_phase)
                
                if step % 10 == 0:
                    self.update_metrics()
                
                if self.mode == 'rl' and step % 50 == 0:
                    if hasattr(self.controller, 'replay'):
                        loss = self.controller.replay(batch_size=32)
                        if loss is not None:
                            print(f"Step {step}: Training loss = {loss:.4f}")
                    
                    if hasattr(self.controller, 'update_throughput'):
                        self.controller.update_throughput()
                    
                    self.save_training_stats()
                
                step += 1
                
        except KeyboardInterrupt:
            print("\n⏹️  Simulation interrupted by user")
        except Exception as e:
            print(f"\n✗ Error during simulation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.mode == 'rl' and hasattr(self.controller, 'save_model'):
                model_path = 'models/dqn_model.pth'
                self.controller.save_model(model_path)
                print(f"✓ Model saved to {model_path}")
            
            print("\n🏁 Simulation ended")
            print(f"  Total steps: {step}")
            
            try:
                traci.close()
            except:
                pass

def main():
    setup_sumo_environment()
    
    parser = argparse.ArgumentParser(description='Traffic Signal Control Simulation')
    parser.add_argument('--mode', choices=['rule', 'rl'], default='rule',
                       help='Control mode: rule-based or RL-based')
    parser.add_argument('--gui', action='store_true', default=False,
                       help='Enable SUMO GUI')
    parser.add_argument('--no-gui', action='store_true', default=False,
                       help='Disable SUMO GUI (headless mode)')
    
    args = parser.parse_args()
    
    gui = not args.no_gui if args.no_gui else args.gui
    
    sim = TrafficSimulation(mode=args.mode, gui=gui)
    sim.run()

if __name__ == "__main__":
    main()
