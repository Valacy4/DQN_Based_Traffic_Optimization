#!/usr/bin/env python3
import subprocess
import threading
import time
import os
import sys
import signal
import argparse

class ApplicationLauncher:
    def __init__(self):
        self.dashboard_process = None
        self.simulation_process = None
        self.running = True
        
    def start_dashboard(self):
        """Start the Streamlit dashboard"""
        print("🖥️  Starting dashboard...")
        try:
            os.makedirs('.streamlit', exist_ok=True)
            
            self.dashboard_process = subprocess.Popen([
                'streamlit', 'run', 'dashboard/app.py',
                '--server.port', '5000',
                '--server.address', '0.0.0.0',
                '--server.headless', 'true'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(3)
            
            if self.dashboard_process.poll() is None:
                print("✅ Dashboard started on http://localhost:5000")
            else:
                print("❌ Dashboard failed to start")
                
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
    
    def start_simulation(self, mode='rule', gui=True):
        """Start the traffic simulation"""
        print(f"🚦 Starting simulation (mode: {mode}, gui: {gui})...")
        try:
            cmd = ['python3', 'run.py', '--mode', mode]
            if not gui:
                cmd.append('--no-gui')
            
            self.simulation_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(5)
            
            if self.simulation_process.poll() is None:
                print("✅ Simulation started")
            else:
                print("❌ Simulation failed to start")
                
        except Exception as e:
            print(f"❌ Error starting simulation: {e}")
    
    def monitor_processes(self):
        """Monitor processes"""
        while self.running:
            try:
                if self.dashboard_process and self.dashboard_process.poll() is not None:
                    print("⚠️  Dashboard ended, restarting...")
                    self.start_dashboard()
                
                if self.simulation_process and self.simulation_process.poll() is not None:
                    print("ℹ️  Simulation ended")
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)
    
    def stop_processes(self):
        """Stop all processes"""
        print("\n🛑 Stopping...")
        self.running = False
        
        if self.simulation_process:
            try:
                self.simulation_process.terminate()
                self.simulation_process.wait(timeout=10)
                print("✅ Simulation stopped")
            except:
                try:
                    self.simulation_process.kill()
                except:
                    pass
        
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=10)
                print("✅ Dashboard stopped")
            except:
                try:
                    self.dashboard_process.kill()
                except:
                    pass
    
    def run(self, mode='rule', gui=True, auto_start_sim=False):
        """Run application"""
        
        def signal_handler(signum, frame):
            print(f"\n📡 Received signal {signum}")
            self.stop_processes()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("🚀 Traffic Signal Control System")
        print("=" * 60)
        print(f"Mode: {mode.upper()}, GUI: {gui}, Auto-start: {auto_start_sim}")
        print("=" * 60)
        
        try:
            self.start_dashboard()
            
            if auto_start_sim:
                time.sleep(2)
                self.start_simulation(mode=mode, gui=gui)
            
            print("\n📊 Dashboard: http://localhost:5000")
            print("🛑 Press Ctrl+C to stop")
            
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()
            
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Interrupted")
        finally:
            self.stop_processes()

def main():
    parser = argparse.ArgumentParser(description='Traffic Signal Control Application')
    parser.add_argument('--mode', choices=['rule', 'rl'], default='rule')
    parser.add_argument('--gui', action='store_true', default=True)
    parser.add_argument('--no-gui', action='store_true')
    parser.add_argument('--auto-start', action='store_true')
    
    args = parser.parse_args()
    
    gui = not args.no_gui if args.no_gui else args.gui
    
    launcher = ApplicationLauncher()
    launcher.run(mode=args.mode, gui=gui, auto_start_sim=args.auto_start)

if __name__ == "__main__":
    main()
