#!/usr/bin/env python3
"""
World-Class Startup Manager for Advanced Monitoring System
مدير بدء التشغيل عالمي المستوى لنظام المراقبة المتقدم
"""

import os
import sys
import time
import subprocess
import threading
import signal
import psutil
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorldClassStartupManager:
    """Professional startup manager for all system components"""
    
    def __init__(self):
        self.processes = {}
        self.running = True
        self.startup_order = [
            {
                'name': 'Backend Server',
                'script': 'world_class_backend_enhanced.py',
                'port': 5000,
                'critical': True,
                'startup_delay': 2
            },
            {
                'name': 'Web Dashboard',
                'script': 'world_class_web_server.py',
                'port': 8080,
                'critical': False,
                'startup_delay': 2
            },
            {
                'name': 'Telegram Bot',
                'script': 'world_class_telegram_bot_professional.py',
                'port': None,
                'critical': False,
                'startup_delay': 1
            }
        ]
    
    def print_banner(self):
        """Print professional startup banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    🌍 WORLD-CLASS ADVANCED MONITORING SYSTEM                                ║
║    نظام المراقبة المتقدم عالمي المستوى                                      ║
║                                                                              ║
║    🚀 Professional System Startup Manager                                   ║
║    🛡️ Military-Grade Security & Monitoring                                  ║
║    📊 AI-Powered Analytics Platform                                         ║
║    🌐 Global Infrastructure Management                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"⏰ Startup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def check_dependencies(self):
        """Check if all dependencies are available"""
        print("🔍 Checking system dependencies...")
        
        required_modules = [
            ('flask', 'flask'), 
            ('requests', 'requests'), 
            ('psutil', 'psutil'), 
            ('cryptography', 'cryptography'),
            ('python-telegram-bot', 'telegram'), 
            ('aiohttp', 'aiohttp'), 
            ('matplotlib', 'matplotlib')
        ]
        
        missing_modules = []
        for display_name, import_name in required_modules:
            try:
                __import__(import_name)
                print(f"   ✅ {display_name}")
            except ImportError:
                missing_modules.append(display_name)
                print(f"   ❌ {display_name}")
        
        if missing_modules:
            print(f"\n❌ Missing dependencies: {', '.join(missing_modules)}")
            print("Run: pip install -r requirements_unified.txt")
            return False
        
        print("✅ All dependencies satisfied")
        return True
    
    def check_environment(self):
        """Check environment configuration"""
        print("⚙️ Checking environment configuration...")
        
        if not os.path.exists('.env'):
            print("⚠️ .env file not found, using defaults")
            return True
        
        required_vars = ['API_URL', 'JWT_SECRET']
        missing_vars = []
        
        with open('.env', 'r') as f:
            env_content = f.read()
            for var in required_vars:
                if var not in env_content:
                    missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("✅ Environment configuration OK")
        
        return True
    
    def start_component(self, component):
        """Start a system component"""
        name = component['name']
        script = component['script']
        
        if not os.path.exists(script):
            print(f"❌ {name}: Script {script} not found")
            return False
        
        print(f"🚀 Starting {name}...")
        
        try:
            process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.processes[name] = {
                'process': process,
                'script': script,
                'port': component.get('port'),
                'critical': component.get('critical', False),
                'start_time': datetime.now()
            }
            
            time.sleep(component.get('startup_delay', 1))
            
            if process.poll() is None:
                print(f"   ✅ {name} started successfully (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"   ❌ {name} failed to start")
                if stderr:
                    print(f"   Error: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"   ❌ {name} startup error: {str(e)}")
            return False
    
    def check_component_health(self, name, component):
        """Check if a component is healthy"""
        process = component['process']
        port = component.get('port')
        
        if process.poll() is not None:
            return False
        
        if port:
            try:
                import requests
                response = requests.get(f"http://localhost:{port}/api/system/health", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        return True
    
    def monitor_components(self):
        """Monitor all components and restart if needed"""
        while self.running:
            time.sleep(10)  # Check every 10 seconds
            
            for name, component in self.processes.items():
                if not self.check_component_health(name, component):
                    if component['critical']:
                        print(f"🚨 Critical component {name} is down! Restarting...")
                        self.restart_component(name)
                    else:
                        print(f"⚠️ Component {name} is down")
    
    def restart_component(self, name):
        """Restart a failed component"""
        if name in self.processes:
            component = self.processes[name]
            
            try:
                component['process'].terminate()
                component['process'].wait(timeout=5)
            except:
                try:
                    component['process'].kill()
                except:
                    pass
            
            for comp_config in self.startup_order:
                if comp_config['name'] == name:
                    self.start_component(comp_config)
                    break
    
    def shutdown_all(self):
        """Gracefully shutdown all components"""
        print("\n🛑 Shutting down all components...")
        self.running = False
        
        for name, component in self.processes.items():
            print(f"   Stopping {name}...")
            try:
                component['process'].terminate()
                component['process'].wait(timeout=10)
                print(f"   ✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"   🔥 Force killing {name}...")
                component['process'].kill()
            except Exception as e:
                print(f"   ❌ Error stopping {name}: {str(e)}")
        
        print("✅ All components stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n📡 Received signal {signum}")
        self.shutdown_all()
        sys.exit(0)
    
    def show_status(self):
        """Show status of all components"""
        print("\n📊 System Status:")
        print("-" * 50)
        
        for name, component in self.processes.items():
            status = "🟢 Running" if self.check_component_health(name, component) else "🔴 Down"
            uptime = datetime.now() - component['start_time']
            print(f"{name:20} | {status:12} | Uptime: {str(uptime).split('.')[0]}")
        
        print("-" * 50)
    
    def run(self):
        """Run the startup manager"""
        self.print_banner()
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        if not self.check_dependencies():
            sys.exit(1)
        
        if not self.check_environment():
            sys.exit(1)
        
        print("\n🚀 Starting all system components...")
        print("=" * 50)
        
        failed_components = []
        for component in self.startup_order:
            if not self.start_component(component):
                failed_components.append(component['name'])
                if component.get('critical', False):
                    print(f"\n❌ Critical component {component['name']} failed to start!")
                    print("System startup aborted.")
                    sys.exit(1)
        
        if failed_components:
            print(f"\n⚠️ Some non-critical components failed: {', '.join(failed_components)}")
        
        print("\n✅ System startup completed!")
        print("=" * 50)
        
        monitor_thread = threading.Thread(target=self.monitor_components, daemon=True)
        monitor_thread.start()
        
        try:
            print("\n🎯 System is running. Press Ctrl+C to stop.")
            print("Commands: 'status' - show status, 'quit' - shutdown")
            
            while self.running:
                try:
                    cmd = input("\n> ").strip().lower()
                    if cmd == 'status':
                        self.show_status()
                    elif cmd in ['quit', 'exit', 'stop']:
                        break
                    elif cmd == 'help':
                        print("Available commands: status, quit, help")
                    elif cmd:
                        print("Unknown command. Type 'help' for available commands.")
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
        
        finally:
            self.shutdown_all()

if __name__ == "__main__":
    manager = WorldClassStartupManager()
    manager.run()
