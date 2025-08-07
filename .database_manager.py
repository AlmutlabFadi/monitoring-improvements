#!/usr/bin/env python3
"""
مدير قاعدة البيانات المحسن
Enhanced Database Manager
"""

import sqlite3
import json
import os
import shutil
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import secrets
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class AdvancedDatabaseManager:
    """مدير قاعدة البيانات المتقدم"""
    
    def __init__(self, db_path='monitoring.db', backup_dir='backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self._lock = threading.Lock()
        
        # إنشاء مجلد النسخ الاحتياطية
        os.makedirs(backup_dir, exist_ok=True)
        
        # تهيئة قاعدة البيانات
        self.init_database()
        
        # بدء مهمة النسخ الاحتياطي التلقائي
        self.start_auto_backup()
    
    def _get_or_create_encryption_key(self):
        """الحصول على مفتاح التشفير أو إنشاؤه"""
        key_file = 'encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_data(self, data: str) -> str:
        """تشفير البيانات"""
        if not data:
            return data
        
        try:
            encrypted = self.cipher_suite.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """فك تشفير البيانات"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decrypted = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return encrypted_data
    
    def init_database(self):
        """تهيئة قاعدة البيانات مع الجداول المحسنة"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # تفعيل المفاتيح الخارجية
            cursor.execute('PRAGMA foreign_keys = ON')
            
            # جدول المستخدمين المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE,
                    full_name TEXT,
                    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
                    permissions TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    two_factor_secret TEXT
                )
            ''')
            
            # جدول جلسات المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # جدول الأجهزة المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    device_name TEXT,
                    device_type TEXT,
                    os_info TEXT,
                    hardware_info TEXT,
                    network_info TEXT,
                    location_info TEXT,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'maintenance')),
                    battery_level INTEGER,
                    storage_info TEXT,
                    installed_apps TEXT,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # جدول التسجيلات الصوتية المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    duration INTEGER,
                    file_size INTEGER,
                    quality TEXT,
                    format TEXT,
                    is_encrypted BOOLEAN DEFAULT 0,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transcription TEXT,
                    tags TEXT,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
                )
            ''')
            
            # جدول لقطات الشاشة المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    file_size INTEGER,
                    resolution TEXT,
                    format TEXT,
                    is_encrypted BOOLEAN DEFAULT 0,
                    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    tags TEXT,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
                )
            ''')
            
            # جدول الرسائل النصية المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sms_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    sender TEXT,
                    recipient TEXT,
                    message_body TEXT,
                    message_body_encrypted TEXT,
                    timestamp TIMESTAMP,
                    message_type TEXT DEFAULT 'received' CHECK (message_type IN ('sent', 'received', 'draft')),
                    read_status BOOLEAN DEFAULT 0,
                    thread_id TEXT,
                    contact_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
                )
            ''')
            
            # جدول المكالمات المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS call_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    phone_number TEXT,
                    contact_name TEXT,
                    call_type TEXT CHECK (call_type IN ('incoming', 'outgoing', 'missed')),
                    duration INTEGER,
                    timestamp TIMESTAMP,
                    location TEXT,
                    recording_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
                )
            ''')
            
            # جدول المواقع المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    accuracy REAL,
                    altitude REAL,
                    speed REAL,
                    bearing REAL,
                    address TEXT,
                    location_source TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
                )
            ''')
            
            # جدول الأنشطة المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    description TEXT,
                    data TEXT,
                    data_encrypted TEXT,
                    severity TEXT DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT 0,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
                )
            ''')
            
            # جدول الإعدادات المحسن
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    value_type TEXT DEFAULT 'string' CHECK (value_type IN ('string', 'integer', 'boolean', 'json')),
                    description TEXT,
                    is_encrypted BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, key)
                )
            ''')
            
            # جدول سجل النظام
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                    message TEXT NOT NULL,
                    module TEXT,
                    function TEXT,
                    line_number INTEGER,
                    user_id INTEGER,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # جدول النسخ الاحتياطية
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_name TEXT NOT NULL,
                    backup_path TEXT NOT NULL,
                    backup_size INTEGER,
                    backup_type TEXT DEFAULT 'full' CHECK (backup_type IN ('full', 'incremental')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed' CHECK (status IN ('in_progress', 'completed', 'failed'))
                )
            ''')
            
            # جدول الإشعارات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT DEFAULT 'info' CHECK (type IN ('info', 'warning', 'error', 'success')),
                    read_status BOOLEAN DEFAULT 0,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # إنشاء الفهارس لتحسين الأداء
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_devices_device_id ON devices(device_id)',
                'CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status)',
                'CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen)',
                'CREATE INDEX IF NOT EXISTS idx_audio_device_id ON audio_recordings(device_id)',
                'CREATE INDEX IF NOT EXISTS idx_audio_recorded_at ON audio_recordings(recorded_at)',
                'CREATE INDEX IF NOT EXISTS idx_screenshots_device_id ON screenshots(device_id)',
                'CREATE INDEX IF NOT EXISTS idx_screenshots_captured_at ON screenshots(captured_at)',
                'CREATE INDEX IF NOT EXISTS idx_sms_device_id ON sms_messages(device_id)',
                'CREATE INDEX IF NOT EXISTS idx_sms_timestamp ON sms_messages(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_calls_device_id ON call_logs(device_id)',
                'CREATE INDEX IF NOT EXISTS idx_calls_timestamp ON call_logs(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_locations_device_id ON locations(device_id)',
                'CREATE INDEX IF NOT EXISTS idx_locations_timestamp ON locations(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_activities_device_id ON activities(device_id)',
                'CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(activity_type)',
                'CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level)',
                'CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_notifications_read_status ON notifications(read_status)'
            ]
            
            for index in indexes:
                cursor.execute(index)
            
            # إنشاء مستخدم افتراضي إذا لم يوجد
            cursor.execute('SELECT COUNT(*) FROM users')
            if cursor.fetchone()[0] == 0:
                from werkzeug.security import generate_password_hash
                default_password = generate_password_hash('admin123')
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, full_name, role, permissions)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('admin', default_password, 'admin@monitoring.local', 'System Administrator', 
                      'admin', json.dumps({'all': True})))
            
            # إدراج الإعدادات الافتراضية
            default_settings = [
                ('system', 'app_name', 'تطبيق المراقبة والتسجيل', 'string', 'اسم التطبيق'),
                ('system', 'app_version', '1.0.0', 'string', 'إصدار التطبيق'),
                ('system', 'max_file_size', '104857600', 'integer', 'الحد الأقصى لحجم الملف (بايت)'),
                ('system', 'backup_interval', '24', 'integer', 'فترة النسخ الاحتياطي (ساعات)'),
                ('system', 'log_retention_days', '30', 'integer', 'مدة الاحتفاظ بالسجلات (أيام)'),
                ('security', 'session_timeout', '3600', 'integer', 'انتهاء صلاحية الجلسة (ثواني)'),
                ('security', 'max_login_attempts', '5', 'integer', 'الحد الأقصى لمحاولات تسجيل الدخول'),
                ('security', 'lockout_duration', '900', 'integer', 'مدة القفل (ثواني)'),
                ('security', 'password_min_length', '8', 'integer', 'الحد الأدنى لطول كلمة المرور'),
                ('notifications', 'email_enabled', 'false', 'boolean', 'تفعيل إشعارات البريد الإلكتروني'),
                ('notifications', 'push_enabled', 'true', 'boolean', 'تفعيل الإشعارات الفورية'),
                ('monitoring', 'auto_screenshot', 'false', 'boolean', 'لقطات الشاشة التلقائية'),
                ('monitoring', 'screenshot_interval', '300', 'integer', 'فترة لقطات الشاشة (ثواني)'),
                ('monitoring', 'location_tracking', 'true', 'boolean', 'تتبع الموقع'),
                ('monitoring', 'location_interval', '600', 'integer', 'فترة تحديث الموقع (ثواني)')
            ]
            
            for category, key, value, value_type, description in default_settings:
                cursor.execute('''
                    INSERT OR IGNORE INTO settings (category, key, value, value_type, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (category, key, value, value_type, description))
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
    
    def get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """تنفيذ استعلام وإرجاع النتائج"""
        with self._lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                result = cursor.fetchall()
                conn.commit()
                
                return [dict(row) for row in result]
            
            except Exception as e:
                conn.rollback()
                logger.error(f"Query execution error: {e}")
                raise
            finally:
                conn.close()
    
    def execute_insert(self, query: str, params: Tuple) -> int:
        """تنفيذ إدراج وإرجاع ID الجديد"""
        with self._lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute(query, params)
                last_id = cursor.lastrowid
                conn.commit()
                
                return last_id
            
            except Exception as e:
                conn.rollback()
                logger.error(f"Insert execution error: {e}")
                raise
            finally:
                conn.close()
    
    def execute_transaction(self, queries: List[Tuple[str, Tuple]]) -> bool:
        """تنفيذ عدة استعلامات في معاملة واحدة"""
        with self._lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                for query, params in queries:
                    cursor.execute(query, params)
                
                conn.commit()
                return True
            
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction execution error: {e}")
                return False
            finally:
                conn.close()
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """إنشاء نسخة احتياطية"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # نسخ قاعدة البيانات
            shutil.copy2(self.db_path, backup_path)
            
            # حفظ معلومات النسخة الاحتياطية
            backup_size = os.path.getsize(backup_path)
            self.execute_insert(
                '''INSERT INTO backups (backup_name, backup_path, backup_size, backup_type)
                   VALUES (?, ?, ?, ?)''',
                (backup_name, backup_path, backup_size, 'full')
            )
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> bool:
        """استعادة نسخة احتياطية"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # إنشاء نسخة احتياطية من الحالة الحالية
            current_backup = self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            
            # استعادة النسخة الاحتياطية
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"Database restored from backup: {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            # الحصول على النسخ الاحتياطية القديمة
            old_backups = self.execute_query(
                'SELECT * FROM backups WHERE created_at < ?',
                (cutoff_date.isoformat(),)
            )
            
            for backup in old_backups:
                # حذف الملف
                if os.path.exists(backup['backup_path']):
                    os.remove(backup['backup_path'])
                
                # حذف السجل
                self.execute_query(
                    'DELETE FROM backups WHERE id = ?',
                    (backup['id'],)
                )
            
            logger.info(f"Cleaned up {len(old_backups)} old backups")
        
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def start_auto_backup(self):
        """بدء النسخ الاحتياطي التلقائي"""
        def backup_worker():
            while True:
                try:
                    # الحصول على فترة النسخ الاحتياطي من الإعدادات
                    settings = self.execute_query(
                        "SELECT value FROM settings WHERE category = 'system' AND key = 'backup_interval'"
                    )
                    
                    interval_hours = 24  # افتراضي
                    if settings:
                        interval_hours = int(settings[0]['value'])
                    
                    # انتظار الفترة المحددة
                    time.sleep(interval_hours * 3600)
                    
                    # إنشاء نسخة احتياطية
                    self.create_backup()
                    
                    # تنظيف النسخ القديمة
                    self.cleanup_old_backups()
                
                except Exception as e:
                    logger.error(f"Auto backup error: {e}")
                    time.sleep(3600)  # انتظار ساعة في حالة الخطأ
        
        backup_thread = threading.Thread(target=backup_worker, daemon=True)
        backup_thread.start()
        logger.info("Auto backup started")
    
    def log_system_event(self, level: str, message: str, module: str = None, 
                        function: str = None, user_id: int = None, ip_address: str = None):
        """تسجيل حدث في سجل النظام"""
        try:
            self.execute_insert(
                '''INSERT INTO system_logs 
                   (level, message, module, function, user_id, ip_address)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (level, message, module, function, user_id, ip_address)
            )
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
    
    def get_database_stats(self) -> Dict:
        """الحصول على إحصائيات قاعدة البيانات"""
        try:
            stats = {}
            
            # حجم قاعدة البيانات
            stats['database_size'] = os.path.getsize(self.db_path)
            
            # عدد الجداول والسجلات
            tables = [
                'users', 'devices', 'audio_recordings', 'screenshots',
                'sms_messages', 'call_logs', 'locations', 'activities',
                'settings', 'system_logs', 'notifications'
            ]
            
            for table in tables:
                count = self.execute_query(f'SELECT COUNT(*) as count FROM {table}')[0]['count']
                stats[f'{table}_count'] = count
            
            # آخر نسخة احتياطية
            last_backup = self.execute_query(
                'SELECT * FROM backups ORDER BY created_at DESC LIMIT 1'
            )
            
            if last_backup:
                stats['last_backup'] = last_backup[0]['created_at']
            
            return stats
        
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def optimize_database(self):
        """تحسين قاعدة البيانات"""
        try:
            with self._lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # تحليل الجداول
                cursor.execute('ANALYZE')
                
                # ضغط قاعدة البيانات
                cursor.execute('VACUUM')
                
                conn.commit()
                conn.close()
            
            logger.info("Database optimization completed")
        
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
    
    def close(self):
        """إغلاق مدير قاعدة البيانات"""
        logger.info("Database manager closed")

