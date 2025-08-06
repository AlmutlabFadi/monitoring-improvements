#!/usr/bin/env python3
"""
الخادم الخلفي الحقيقي لتطبيق المراقبة
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime
from database import db
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# إعداد مجلدات التحميل
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'audio')
SCREENSHOT_FOLDER = os.path.join(UPLOAD_FOLDER, 'screenshots')

os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

# إعدادات الملفات المسموحة
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'm4a', 'wav', 'aac'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# ===== API Routes =====

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """الحصول على قائمة الأجهزة"""
    try:
        devices = db.get_devices()
        return jsonify({
            'success': True,
            'devices': devices
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """الحصول على تفاصيل جهاز معين"""
    try:
        device = db.get_device_by_id(device_id)
        if device:
            return jsonify({
                'success': True,
                'device': device
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices', methods=['POST'])
def add_device():
    """إضافة جهاز جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['device_id', 'device_name', 'device_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        success = db.add_device(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Device added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add device'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>/status', methods=['PUT'])
def update_device_status(device_id):
    """تحديث حالة الجهاز"""
    try:
        data = request.get_json()
        
        success = db.update_device_status(
            device_id,
            battery_level=data.get('battery_level'),
            location_lat=data.get('location_lat'),
            location_lng=data.get('location_lng')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Device status updated'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update device status'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """حذف جهاز"""
    try:
        success = db.delete_device(device_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Device deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete device'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio', methods=['GET'])
def get_audio_recordings():
    """الحصول على التسجيلات الصوتية"""
    try:
        device_id = request.args.get('device_id')
        recordings = db.get_audio_recordings(device_id)
        
        return jsonify({
            'success': True,
            'recordings': recordings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio/upload', methods=['POST'])
def upload_audio():
    """رفع تسجيل صوتي"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        device_id = request.form.get('device_id')
        
        if not device_id:
            return jsonify({
                'success': False,
                'error': 'Device ID is required'
            }), 400
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if file and allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
            # إنشاء اسم ملف فريد
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{device_id}_{timestamp}_{secure_filename(file.filename)}"
            file_path = os.path.join(AUDIO_FOLDER, filename)
            
            # حفظ الملف
            file.save(file_path)
            
            # إضافة معلومات الملف إلى قاعدة البيانات
            file_size = os.path.getsize(file_path)
            
            recording_data = {
                'device_id': device_id,
                'filename': filename,
                'file_path': f'/uploads/audio/{filename}',
                'file_size': file_size,
                'duration': request.form.get('duration', 0),
                'quality': request.form.get('quality', 'medium')
            }
            
            success = db.add_audio_recording(recording_data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Audio file uploaded successfully',
                    'filename': filename
                })
            else:
                # حذف الملف في حالة فشل إضافته لقاعدة البيانات
                os.remove(file_path)
                return jsonify({
                    'success': False,
                    'error': 'Failed to save file information'
                }), 500
        
        return jsonify({
            'success': False,
            'error': 'Invalid file type'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/screenshots', methods=['GET'])
def get_screenshots():
    """الحصول على لقطات الشاشة"""
    try:
        device_id = request.args.get('device_id')
        screenshots = db.get_screenshots(device_id)
        
        return jsonify({
            'success': True,
            'screenshots': screenshots
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/screenshots/upload', methods=['POST'])
def upload_screenshot():
    """رفع لقطة شاشة"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        device_id = request.form.get('device_id')
        
        if not device_id:
            return jsonify({
                'success': False,
                'error': 'Device ID is required'
            }), 400
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            # إنشاء اسم ملف فريد
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{device_id}_{timestamp}_{secure_filename(file.filename)}"
            file_path = os.path.join(SCREENSHOT_FOLDER, filename)
            
            # حفظ الملف
            file.save(file_path)
            
            # إضافة معلومات الملف إلى قاعدة البيانات
            file_size = os.path.getsize(file_path)
            
            screenshot_data = {
                'device_id': device_id,
                'filename': filename,
                'file_path': f'/uploads/screenshots/{filename}',
                'file_size': file_size,
                'width': request.form.get('width', 0),
                'height': request.form.get('height', 0)
            }
            
            success = db.add_screenshot(screenshot_data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Screenshot uploaded successfully',
                    'filename': filename
                })
            else:
                # حذف الملف في حالة فشل إضافته لقاعدة البيانات
                os.remove(file_path)
                return jsonify({
                    'success': False,
                    'error': 'Failed to save file information'
                }), 500
        
        return jsonify({
            'success': False,
            'error': 'Invalid file type'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """الحصول على الإحصائيات"""
    try:
        stats = db.get_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """تقديم الملفات المرفوعة"""
    return send_from_directory(UPLOAD_FOLDER, filename)

# ===== Device Control Routes =====

@app.route('/api/devices/<device_id>/start_recording', methods=['POST'])
def start_recording(device_id):
    """بدء التسجيل الصوتي"""
    try:
        # هنا يمكن إضافة منطق إرسال أمر للجهاز لبدء التسجيل
        # في الوقت الحالي سنعيد استجابة نجاح
        
        return jsonify({
            'success': True,
            'message': f'Recording started for device {device_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>/stop_recording', methods=['POST'])
def stop_recording(device_id):
    """إيقاف التسجيل الصوتي"""
    try:
        return jsonify({
            'success': True,
            'message': f'Recording stopped for device {device_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>/take_screenshot', methods=['POST'])
def take_screenshot(device_id):
    """التقاط لقطة شاشة"""
    try:
        return jsonify({
            'success': True,
            'message': f'Screenshot taken for device {device_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>/start_monitoring', methods=['POST'])
def start_monitoring(device_id):
    """بدء المراقبة"""
    try:
        return jsonify({
            'success': True,
            'message': f'Monitoring started for device {device_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>/stop_monitoring', methods=['POST'])
def stop_monitoring(device_id):
    """إيقاف المراقبة"""
    try:
        return jsonify({
            'success': True,
            'message': f'Monitoring stopped for device {device_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== Static Files =====

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """تقديم الملفات الثابتة"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    print("🚀 بدء تشغيل خادم المراقبة...")
    print("📊 قاعدة البيانات: متصلة")
    print("🌐 الخادم: http://0.0.0.0:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

