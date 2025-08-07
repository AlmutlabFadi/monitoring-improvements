#!/usr/bin/env python3
"""Test Android APK generation with advanced features"""

import sys
sys.path.append('.')
from ULTIMATE_ANDROID_GENERATOR import UltimateAndroidGenerator

def test_android_generation():
    print('📱 Testing Android APK generation with advanced features...')
    
    try:
        generator = UltimateAndroidGenerator()
        result = generator.generate_complete_android_app()
        
        print(f'📱 APK Generation Result: {result["status"]}')
        
        if result['status'] == 'success':
            print(f'✅ APK Path: {result["apk_path"]}')
            print(f'📁 Project Directory: {result["project_dir"]}')
            print('🔧 Advanced Features Included:')
            for feature, enabled in result['features'].items():
                status = '✅' if enabled else '❌'
                print(f'   {status} {feature}')
            
            print('\n🎯 Installation Methods:')
            for method, available in result['installation_methods'].items():
                status = '✅' if available else '❌'
                print(f'   {status} {method}')
                
            return True
        else:
            print(f'❌ Generation failed: {result["message"]}')
            return False
            
    except Exception as e:
        print(f'❌ Android generation test failed: {e}')
        return False

if __name__ == "__main__":
    success = test_android_generation()
    print(f'✅ Android generation test: {"PASSED" if success else "FAILED"}')
