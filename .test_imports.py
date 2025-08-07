#!/usr/bin/env python3
"""Test all ULTIMATE module imports"""

modules = [
    'ULTIMATE_ANDROID_GENERATOR',
    'ULTIMATE_CENTRAL_DASHBOARD', 
    'ULTIMATE_INSTALLATION_METHODS',
    'ULTIMATE_IOS_COMPONENTS',
    'ULTIMATE_MONITORING_SYSTEM',
    'ULTIMATE_MULTIPLATFORM_DESKTOP',
    'ULTIMATE_STEALTH_SYSTEM',
    'ULTIMATE_SYSTEM_INTEGRATOR',
    'ULTIMATE_TELEGRAM_BOT'
]

success = 0
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
        success += 1
    except Exception as e:
        print(f'❌ {module}: {e}')

print(f'📊 {success}/9 modules ready')
