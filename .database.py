#!/usr/bin/env python3
"""
قاعدة البيانات الحقيقية لتطبيق المراقبة
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class MonitoringDatabase:
    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء قاعدة البيانات والجداول"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول الأجهزة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                os_version TEXT,
                app_version TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                battery_level INTEGER DEFAULT 0,
                location_lat REAL,
                location_lng REAL,
                settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول التسجيلات الصوتية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                duration INTEGER,
                quality TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                width INTEGER,
                height INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول الأنشطة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                app_name TEXT,
                window_title TEXT,
                duration INTEGER,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول الرسائل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                sender TEXT,
                recipient TEXT,
                content TEXT,
                app_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # جدول المكالمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                call_type TEXT NOT NULL,
                phone_number TEXT,
                contact_name TEXT,
                duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        
        conn.commit()
        conn.close()
        
        # إدراج بيانات افتراضية للاختبار
        self.insert_sample_data()
    
    def insert_sample_data(self):
        """إدراج بيانات عينة للاختبار"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # التحقق من وجود بيانات
        cursor.execute("SELECT COUNT(*) FROM devices")
        if cursor.fetchone()[0] == 0:
            # إدراج أجهزة عينة
            sample_devices = [
                ('DEV001', 'Samsung Galaxy A52', 'Android', '12.0', '1.0.0', 85, 24.7136, 46.6753),
                ('DEV002', 'iPhone 12 Pro', 'iOS', '15.6', '1.0.0', 92, 24.7136, 46.6753),
                ('DEV003', 'Google Pixel 6', 'Android', '13.0', '1.0.0', 67, 24.7136, 46.6753)
            ]
            
            for device in sample_devices:
                cursor.execute('''
                    INSERT INTO devices (device_id, device_name, device_type, os_version, 
                                       app_version, battery_level, location_lat, location_lng)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', device)
            
            # إدراج تسجيلات صوتية عينة
            sample_recordings = [
                ('DEV001', 'recording_20240115_143000.m4a', '/uploads/audio/recording_20240115_143000.m4a', 1024000, 120),
                ('DEV002', 'recording_20240115_142900.m4a', '/uploads/audio/recording_20240115_142900.m4a', 1536000, 180),
                ('DEV003', 'recording_20240115_142800.m4a', '/uploads/audio/recording_20240115_142800.m4a', 2048000, 240)
            ]
            
            for recording in sample_recordings:
                cursor.execute('''
                    INSERT INTO audio_recordings (device_id, filename, file_path, file_size, duration)
                    VALUES (?, ?, ?, ?, ?)
                ''', recording)
            
            # إدراج لقطات شاشة عينة
            sample_screenshots = [
                ('DEV001', 'screenshot_20240115_143001.png', '/uploads/screenshots/screenshot_20240115_143001.png', 512000, 1080, 1920),
                ('DEV001', 'screenshot_20240115_143002.png', '/uploads/screenshots/screenshot_20240115_143002.png', 487000, 1080, 1920),
                ('DEV002', 'screenshot_20240115_143003.png', '/uploads/screenshots/screenshot_20240115_143003.png', 623000, 1170, 2532),
                ('DEV003', 'screenshot_20240115_143004.png', '/uploads/screenshots/screenshot_20240115_143004.png', 591000, 1080, 2400)
            ]
            
            for screenshot in sample_screenshots:
                cursor.execute('''
                    INSERT INTO screenshots (device_id, filename, file_path, file_size, width, height)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', screenshot)
        
        conn.commit()
        conn.close()
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """الحصول على قائمة الأجهزة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT device_id, device_name, device_type, os_version, last_seen, 
                   is_active, battery_level, location_lat, location_lng
            FROM devices 
            ORDER BY last_seen DESC
        ''')
        
        devices = []
        for row in cursor.fetchall():
            devices.append({
                'device_id': row[0],
                'device_name': row[1],
                'device_type': row[2],
                'os_version': row[3],
                'last_seen': row[4],
                'is_active': bool(row[5]),
                'battery_level': row[6],
                'location_lat': row[7],
                'location_lng': row[8]
            })
        
        conn.close()
        return devices
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على جهاز بواسطة المعرف"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM devices WHERE device_id = ?
        ''', (device_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'device_id': row[1],
                'device_name': row[2],
                'device_type': row[3],
                'os_version': row[4],
                'app_version': row[5],
                'last_seen': row[6],
                'is_active': bool(row[7]),
                'battery_level': row[8],
                'location_lat': row[9],
                'location_lng': row[10],
                'settings': json.loads(row[11] or '{}'),
                'created_at': row[12]
            }
        return None
    
    def add_device(self, device_data: Dict[str, Any]) -> bool:
        """إضافة جهاز جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO devices (device_id, device_name, device_type, os_version, 
                                   app_version, battery_level, location_lat, location_lng, settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                device_data.get('device_id'),
                device_data.get('device_name'),
                device_data.get('device_type'),
                device_data.get('os_version'),
                device_data.get('app_version'),
                device_data.get('battery_level', 0),
                device_data.get('location_lat'),
                device_data.get('location_lng'),
                json.dumps(device_data.get('settings', {}))
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Error adding device: {e}")
            return False
    
    def update_device_status(self, device_id: str, battery_level: int = None, 
                           location_lat: float = None, location_lng: float = None) -> bool:
        """تحديث حالة الجهاز"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if battery_level is not None:
                updates.append("battery_level = ?")
                params.append(battery_level)
            
            if location_lat is not None:
                updates.append("location_lat = ?")
                params.append(location_lat)
            
            if location_lng is not None:
                updates.append("location_lng = ?")
                params.append(location_lng)
            
            updates.append("last_seen = CURRENT_TIMESTAMP")
            updates.append("is_active = 1")
            
            params.append(device_id)
            
            cursor.execute(f'''
                UPDATE devices 
                SET {", ".join(updates)}
                WHERE device_id = ?
            ''', params)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Error updating device status: {e}")
            return False
    
    def get_audio_recordings(self, device_id: str = None) -> List[Dict[str, Any]]:
        """الحصول على التسجيلات الصوتية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('''
                SELECT ar.*, d.device_name 
                FROM audio_recordings ar
                JOIN devices d ON ar.device_id = d.device_id
                WHERE ar.device_id = ?
                ORDER BY ar.created_at DESC
            ''', (device_id,))
        else:
            cursor.execute('''
                SELECT ar.*, d.device_name 
                FROM audio_recordings ar
                JOIN devices d ON ar.device_id = d.device_id
                ORDER BY ar.created_at DESC
            ''')
        
        recordings = []
        for row in cursor.fetchall():
            recordings.append({
                'id': row[0],
                'device_id': row[1],
                'filename': row[2],
                'file_path': row[3],
                'file_size': row[4],
                'duration': row[5],
                'quality': row[6],
                'created_at': row[7],
                'device_name': row[8]
            })
        
        conn.close()
        return recordings
    
    def add_audio_recording(self, recording_data: Dict[str, Any]) -> bool:
        """إضافة تسجيل صوتي"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO audio_recordings (device_id, filename, file_path, 
                                            file_size, duration, quality)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                recording_data.get('device_id'),
                recording_data.get('filename'),
                recording_data.get('file_path'),
                recording_data.get('file_size'),
                recording_data.get('duration'),
                recording_data.get('quality', 'medium')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Error adding audio recording: {e}")
            return False
    
    def get_screenshots(self, device_id: str = None) -> List[Dict[str, Any]]:
        """الحصول على لقطات الشاشة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('''
                SELECT s.*, d.device_name 
                FROM screenshots s
                JOIN devices d ON s.device_id = d.device_id
                WHERE s.device_id = ?
                ORDER BY s.created_at DESC
            ''', (device_id,))
        else:
            cursor.execute('''
                SELECT s.*, d.device_name 
                FROM screenshots s
                JOIN devices d ON s.device_id = d.device_id
                ORDER BY s.created_at DESC
            ''')
        
        screenshots = []
        for row in cursor.fetchall():
            screenshots.append({
                'id': row[0],
                'device_id': row[1],
                'filename': row[2],
                'file_path': row[3],
                'file_size': row[4],
                'width': row[5],
                'height': row[6],
                'created_at': row[7],
                'device_name': row[8]
            })
        
        conn.close()
        return screenshots
    
    def add_screenshot(self, screenshot_data: Dict[str, Any]) -> bool:
        """إضافة لقطة شاشة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO screenshots (device_id, filename, file_path, 
                                       file_size, width, height)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                screenshot_data.get('device_id'),
                screenshot_data.get('filename'),
                screenshot_data.get('file_path'),
                screenshot_data.get('file_size'),
                screenshot_data.get('width'),
                screenshot_data.get('height')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Error adding screenshot: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على الإحصائيات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # عدد الأجهزة النشطة
        cursor.execute("SELECT COUNT(*) FROM devices WHERE is_active = 1")
        active_devices = cursor.fetchone()[0]
        
        # عدد التسجيلات الصوتية
        cursor.execute("SELECT COUNT(*) FROM audio_recordings")
        audio_recordings = cursor.fetchone()[0]
        
        # عدد لقطات الشاشة
        cursor.execute("SELECT COUNT(*) FROM screenshots")
        screenshots = cursor.fetchone()[0]
        
        # حجم التخزين المستخدم
        cursor.execute("SELECT SUM(file_size) FROM audio_recordings")
        audio_size = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(file_size) FROM screenshots")
        screenshot_size = cursor.fetchone()[0] or 0
        
        total_storage_bytes = audio_size + screenshot_size
        total_storage_mb = round(total_storage_bytes / (1024 * 1024), 2)
        
        conn.close()
        
        return {
            'active_devices': active_devices,
            'audio_recordings': audio_recordings,
            'screenshots': screenshots,
            'total_storage_mb': total_storage_mb
        }
    
    def delete_device(self, device_id: str) -> bool:
        """حذف جهاز"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # حذف البيانات المرتبطة أولاً
            cursor.execute("DELETE FROM audio_recordings WHERE device_id = ?", (device_id,))
            cursor.execute("DELETE FROM screenshots WHERE device_id = ?", (device_id,))
            cursor.execute("DELETE FROM activities WHERE device_id = ?", (device_id,))
            cursor.execute("DELETE FROM messages WHERE device_id = ?", (device_id,))
            cursor.execute("DELETE FROM calls WHERE device_id = ?", (device_id,))
            
            # حذف الجهاز
            cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Error deleting device: {e}")
            return False

# إنشاء مثيل قاعدة البيانات
db = MonitoringDatabase()

