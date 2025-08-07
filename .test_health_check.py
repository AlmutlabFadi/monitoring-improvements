#!/usr/bin/env python3
"""Test health check endpoint"""

import sys
sys.path.append('.')
from ULTIMATE_MONITORING_SYSTEM import UltimateMonitoringCore
import time
import requests
import threading

def test_health_check():
    print('🚀 Starting backend server...')
    core = UltimateMonitoringCore()

    def run_server():
        core.run()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(3)

    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        print(f'✅ Health check response: {response.status_code}')
        print(f'📊 Response: {response.json()}')
        return True
    except Exception as e:
        print(f'❌ Health check failed: {e}')
        return False

if __name__ == "__main__":
    success = test_health_check()
    print(f'✅ Health check test: {"PASSED" if success else "FAILED"}')
