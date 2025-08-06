#!/usr/bin/env python3
"""
🚀 مشغل العرض التوضيحي الشامل
Comprehensive Demo Launcher
"""

import subprocess
import threading
import time
import os
import sys

class ComprehensiveDemoLauncher:
    """مشغل العرض التوضيحي الشامل"""
    
    def __init__(self):
        self.processes = []
        self.running = False
    
    def start_all_services(self):
        """بدء جميع الخدمات"""
        print("🚀 Starting Comprehensive Monitoring Demonstration...")
        
        os.makedirs('static', exist_ok=True)
        os.makedirs('static/videos', exist_ok=True)
        
        print("📱 Generating installation demos...")
        try:
            from installation_demo import InstallationDemo
            demo = InstallationDemo()
            demos = demo.generate_all_demos()
            print(f"✅ Generated demos: {list(demos.keys())}")
        except Exception as e:
            print(f"⚠️ Installation demo generation failed: {e}")
        
        print("🎥 Generating video demonstrations...")
        try:
            from video_demo_system import VideoDemoSystem
            video_system = VideoDemoSystem()
            video_system.create_monitoring_demo()
            print("✅ Video demonstrations ready")
        except Exception as e:
            print(f"⚠️ Video demo generation failed: {e}")
        
        print("🌐 Starting Ultimate Web Simulator...")
        simulator_process = subprocess.Popen([
            sys.executable, 'ultimate_web_simulator.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(('Ultimate Web Simulator', simulator_process))
        
        print("🔧 Starting existing monitoring system...")
        try:
            monitoring_process = subprocess.Popen([
                sys.executable, '.ULTIMATE_MONITORING_SYSTEM.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('Monitoring System', monitoring_process))
        except Exception as e:
            print(f"⚠️ Monitoring system start failed: {e}")
        
        print("🌍 Starting existing web server...")
        try:
            web_process = subprocess.Popen([
                sys.executable, '.world_class_web_server.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('Web Server', web_process))
        except Exception as e:
            print(f"⚠️ Web server start failed: {e}")
        
        print("📊 Starting central dashboard...")
        try:
            dashboard_process = subprocess.Popen([
                sys.executable, '.ULTIMATE_CENTRAL_DASHBOARD.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('Central Dashboard', dashboard_process))
        except Exception as e:
            print(f"⚠️ Central dashboard start failed: {e}")
        
        self.running = True
        
        time.sleep(5)
        
        print("\n🎉 All services started successfully!")
        print("\n📋 Access URLs:")
        print("🌐 Main Comprehensive Dashboard: http://localhost:9000")
        print("🎮 Device Simulators: http://localhost:9000/simulators")
        print("📱 Installation Demos: http://localhost:9000/installation-demos")
        print("📊 Existing Dashboard: http://localhost:5000")
        print("🌍 Web Server: http://localhost:8080")
        print("🏢 Central Dashboard: http://localhost:3000")
        
        return True
    
    def monitor_services(self):
        """مراقبة الخدمات"""
        while self.running:
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"⚠️ Service {name} stopped unexpectedly")
            time.sleep(10)
    
    def stop_all_services(self):
        """إيقاف جميع الخدمات"""
        print("🛑 Stopping all services...")
        self.running = False
        
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Stopped {name}")
            except Exception as e:
                print(f"⚠️ Error stopping {name}: {e}")
                try:
                    process.kill()
                except:
                    pass
        
        self.processes.clear()
        print("🎉 All services stopped")
    
    def run_demo(self):
        """تشغيل العرض التوضيحي"""
        try:
            if self.start_all_services():
                monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
                monitor_thread.start()
                
                print("\n🎯 Demo is running! Press Ctrl+C to stop...")
                
                while True:
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping demo...")
            self.stop_all_services()
        except Exception as e:
            print(f"❌ Demo error: {e}")
            self.stop_all_services()

if __name__ == '__main__':
    launcher = ComprehensiveDemoLauncher()
    launcher.run_demo()
