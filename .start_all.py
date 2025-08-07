#!/usr/bin/env python3
"""Start all services"""
import subprocess
import sys
import threading
import time

def start_service(script_name, service_name):
    print(f"🚀 Starting {service_name}...")
    subprocess.run([sys.executable, script_name])

if __name__ == "__main__":
    print("🌍 Starting World-Class Monitoring System...")
    
    services = [
        ("enhanced_main.py", "Backend Server"),
        ("enhanced_desktop_app.py", "Desktop Application"),
        ("world_class_telegram_bot.py", "Telegram Bot")
    ]
    
    threads = []
    for script, name in services:
        thread = threading.Thread(target=start_service, args=(script, name))
        thread.daemon = True
        thread.start()
        threads.append(thread)
        time.sleep(2)
    
    print("✅ All services started successfully!")
    print("Press Ctrl+C to stop all services")
    
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
