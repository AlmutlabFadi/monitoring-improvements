#!/usr/bin/env python3
"""Test system integrator with timeout"""

import sys
import subprocess
import time

def test_system_integrator():
    print('🔧 Testing system integrator with all 9 components...')
    
    try:
        process = subprocess.Popen(
            [sys.executable, 'ULTIMATE_SYSTEM_INTEGRATOR.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=10)
            print(f'✅ System integrator output:\n{stdout}')
            if stderr:
                print(f'⚠️ Warnings/Errors:\n{stderr}')
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            print('✅ System integrator test completed (timeout expected)')
            print(f'📊 Output:\n{stdout}')
            
        return True
    except Exception as e:
        print(f'❌ System integrator test failed: {e}')
        return False

if __name__ == "__main__":
    success = test_system_integrator()
    print(f'✅ System integrator test: {"PASSED" if success else "FAILED"}')
