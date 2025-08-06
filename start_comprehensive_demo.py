#!/usr/bin/env python3
"""
🎬 بدء العرض التوضيحي الشامل
Start Comprehensive Demonstration
"""

import os
import sys
import subprocess
import time

def main():
    """بدء العرض التوضيحي الشامل"""
    print("🌍 Starting Ultimate Global Monitoring System Demonstration")
    print("=" * 60)
    
    os.chdir('/home/ubuntu/repos/monitoring-improvements')
    
    print("📦 Installing required packages...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask-socketio', 'qrcode[pil]', 'opencv-python', 'pillow'], 
                      check=True, capture_output=True)
        print("✅ Packages installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Package installation warning: {e}")
    
    print("🧹 Cleaning up existing processes...")
    ports_to_clean = [5000, 8080, 9000, 3000]
    for port in ports_to_clean:
        try:
            subprocess.run(['pkill', '-f', f':{port}'], capture_output=True)
        except:
            pass
    
    time.sleep(2)
    
    print("🚀 Starting comprehensive demonstration...")
    try:
        subprocess.run([sys.executable, 'comprehensive_demo_launcher.py'])
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        
        print("🔄 Starting fallback mode...")
        try:
            subprocess.run([sys.executable, 'ultimate_web_simulator.py'])
        except Exception as fallback_error:
            print(f"❌ Fallback error: {fallback_error}")

if __name__ == '__main__':
    main()
