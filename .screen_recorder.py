#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام تسجيل الشاشة المتقدم
Advanced Screen Recording System
"""

import os
import json
import time
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
import base64
from dataclasses import dataclass, asdict
import logging
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io

# إعداد نظام السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScreenRecording:
    """فئة لتمثيل تسجيل شاشة"""
    recording_id: str
    device_id: str
    start_time: str
    end_time: str
    duration: int  # بالثواني
    file_path: str
    file_size: int  # بالبايت
    resolution: str  # مثل "1920x1080"
    fps: int  # إطارات في الثانية
    quality: str  # 'high', 'medium', 'low'
    trigger_type: str  # 'manual', 'scheduled', 'app_based', 'automatic'
    trigger_app: str  # التطبيق الذي تسبب في التسجيل
    is_encrypted: bool
    thumbnail_path: str
    metadata: Dict

class ScreenRecorderDatabase:
    """مدير قاعدة بيانات تسجيل الشاشة"""
    
    def __init__(self, db_path: str = "screen_recorder.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول تسجيلات الشاشة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screen_recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                duration INTEGER DEFAULT 0,
                file_path TEXT,
                file_size INTEGER DEFAULT 0,
                resolution TEXT,
                fps INTEGER DEFAULT 30,
                quality TEXT DEFAULT 'medium',
                trigger_type TEXT DEFAULT 'manual',
                trigger_app TEXT,
                is_encrypted BOOLEAN DEFAULT 0,
                thumbnail_path TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول جدولة التسجيل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recording_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                schedule_name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_apps TEXT,
                start_time TIME,
                end_time TIME,
                days_of_week TEXT,
                duration_minutes INTEGER DEFAULT 60,
                quality TEXT DEFAULT 'medium',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول إعدادات التسجيل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recording_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                auto_record BOOLEAN DEFAULT 0,
                default_quality TEXT DEFAULT 'medium',
                default_fps INTEGER DEFAULT 30,
                max_duration INTEGER DEFAULT 3600,
                storage_limit_mb INTEGER DEFAULT 5000,
                auto_upload BOOLEAN DEFAULT 1,
                encryption_enabled BOOLEAN DEFAULT 1,
                delete_after_upload BOOLEAN DEFAULT 0,
                record_audio BOOLEAN DEFAULT 1,
                show_cursor BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول التطبيقات المراقبة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                app_name TEXT NOT NULL,
                package_name TEXT,
                auto_record BOOLEAN DEFAULT 1,
                record_duration INTEGER DEFAULT 300,
                quality TEXT DEFAULT 'medium',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, package_name)
            )
        ''')
        
        # جدول إحصائيات التسجيل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recording_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                date DATE NOT NULL,
                total_recordings INTEGER DEFAULT 0,
                total_duration INTEGER DEFAULT 0,
                storage_used_mb REAL DEFAULT 0,
                upload_success INTEGER DEFAULT 0,
                upload_failed INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_recording(self, recording: ScreenRecording):
        """إدراج تسجيل شاشة جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO screen_recordings 
            (recording_id, device_id, start_time, end_time, duration, file_path, file_size,
             resolution, fps, quality, trigger_type, trigger_app, is_encrypted, thumbnail_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            recording.recording_id, recording.device_id, recording.start_time, recording.end_time,
            recording.duration, recording.file_path, recording.file_size, recording.resolution,
            recording.fps, recording.quality, recording.trigger_type, recording.trigger_app,
            recording.is_encrypted, recording.thumbnail_path, json.dumps(recording.metadata, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def get_recordings(self, device_id: str = None, limit: int = 100) -> List[Dict]:
        """استرجاع تسجيلات الشاشة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('''
                SELECT * FROM screen_recordings 
                WHERE device_id = ? 
                ORDER BY start_time DESC 
                LIMIT ?
            ''', (device_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM screen_recordings 
                ORDER BY start_time DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results

class ScreenCapture:
    """نظام التقاط الشاشة"""
    
    def __init__(self):
        self.is_capturing = False
        self.capture_thread = None
        self.frames = []
        self.frame_rate = 30
        self.quality = 'medium'
    
    def start_capture(self, output_path: str, duration: int = None, quality: str = 'medium'):
        """بدء التقاط الشاشة"""
        self.is_capturing = True
        self.frames = []
        self.quality = quality
        
        # تحديد معدل الإطارات حسب الجودة
        if quality == 'high':
            self.frame_rate = 60
        elif quality == 'medium':
            self.frame_rate = 30
        else:  # low
            self.frame_rate = 15
        
        # بدء خيط التقاط الشاشة
        self.capture_thread = threading.Thread(
            target=self._capture_worker, 
            args=(output_path, duration)
        )
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        logger.info(f"بدء تسجيل الشاشة: {output_path}")
    
    def stop_capture(self):
        """إيقاف التقاط الشاشة"""
        self.is_capturing = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=10)
        logger.info("تم إيقاف تسجيل الشاشة")
    
    def _capture_worker(self, output_path: str, duration: int = None):
        """عامل التقاط الشاشة"""
        start_time = time.time()
        frame_interval = 1.0 / self.frame_rate
        
        try:
            while self.is_capturing:
                # فحص المدة القصوى
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # التقاط إطار من الشاشة
                frame = self._capture_screen()
                if frame:
                    self.frames.append(frame)
                
                time.sleep(frame_interval)
            
            # حفظ الفيديو
            if self.frames:
                self._save_video(output_path)
                
        except Exception as e:
            logger.error(f"خطأ في تسجيل الشاشة: {e}")
    
    def _capture_screen(self) -> Optional[Image.Image]:
        """التقاط لقطة شاشة واحدة"""
        try:
            # في التطبيق الحقيقي، سيتم استخدام مكتبة مثل PIL أو pyautogui
            # هنا نقوم بإنشاء صورة وهمية للمحاكاة
            width, height = 1920, 1080
            
            # إنشاء صورة وهمية
            image = Image.new('RGB', (width, height), color='lightblue')
            draw = ImageDraw.Draw(image)
            
            # إضافة نص يوضح الوقت الحالي
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            draw.text((50, 50), f"Screen Recording - {timestamp}", fill='black', font=font)
            draw.text((50, 100), "Simulated Screen Content", fill='darkblue', font=font)
            
            # إضافة بعض الأشكال للمحاكاة
            draw.rectangle([100, 200, 400, 400], outline='red', width=3)
            draw.ellipse([500, 200, 800, 400], outline='green', width=3)
            
            return image
            
        except Exception as e:
            logger.error(f"خطأ في التقاط الشاشة: {e}")
            return None
    
    def _save_video(self, output_path: str):
        """حفظ الإطارات كفيديو"""
        try:
            if not self.frames:
                return
            
            # في التطبيق الحقيقي، سيتم استخدام مكتبة مثل opencv أو ffmpeg
            # هنا نقوم بحفظ الإطار الأول كصورة للمحاكاة
            first_frame = self.frames[0]
            
            # تحويل إلى تنسيق مناسب للحفظ
            if output_path.endswith('.mp4'):
                # محاكاة حفظ فيديو
                temp_image_path = output_path.replace('.mp4', '_frame.png')
                first_frame.save(temp_image_path, 'PNG')
                
                # محاكاة تحويل إلى فيديو باستخدام ffmpeg
                self._convert_to_video(temp_image_path, output_path)
                
                # حذف الصورة المؤقتة
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
            else:
                # حفظ كصورة
                first_frame.save(output_path)
            
            logger.info(f"تم حفظ التسجيل: {output_path}")
            
        except Exception as e:
            logger.error(f"خطأ في حفظ الفيديو: {e}")
    
    def _convert_to_video(self, image_path: str, video_path: str):
        """تحويل الصور إلى فيديو باستخدام ffmpeg (محاكاة)"""
        try:
            # في التطبيق الحقيقي، سيتم استخدام ffmpeg لتحويل الإطارات إلى فيديو
            # هنا نقوم بإنشاء ملف فيديو وهمي
            with open(video_path, 'wb') as f:
                # كتابة بيانات وهمية للفيديو
                f.write(b'FAKE_VIDEO_DATA_FOR_SIMULATION')
                f.write(f"Created at {datetime.now()}".encode())
            
            logger.info(f"تم إنشاء ملف الفيديو: {video_path}")
            
        except Exception as e:
            logger.error(f"خطأ في تحويل الفيديو: {e}")
    
    def create_thumbnail(self, video_path: str, thumbnail_path: str) -> bool:
        """إنشاء صورة مصغرة للفيديو"""
        try:
            if self.frames:
                # استخدام الإطار الأول كصورة مصغرة
                thumbnail = self.frames[0].copy()
                thumbnail.thumbnail((320, 240), Image.Resampling.LANCZOS)
                thumbnail.save(thumbnail_path, 'JPEG', quality=85)
                return True
            else:
                # إنشاء صورة مصغرة افتراضية
                thumbnail = Image.new('RGB', (320, 240), color='gray')
                draw = ImageDraw.Draw(thumbnail)
                draw.text((50, 100), "Video Thumbnail", fill='white')
                thumbnail.save(thumbnail_path, 'JPEG', quality=85)
                return True
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء الصورة المصغرة: {e}")
            return False

class AppMonitor:
    """مراقب التطبيقات للتسجيل التلقائي"""
    
    def __init__(self, device_id: str, db: ScreenRecorderDatabase):
        self.device_id = device_id
        self.db = db
        self.is_monitoring = False
        self.monitor_thread = None
        self.current_app = ""
        self.monitored_apps = self._load_monitored_apps()
    
    def _load_monitored_apps(self) -> Dict[str, Dict]:
        """تحميل قائمة التطبيقات المراقبة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT package_name, app_name, auto_record, record_duration, quality 
            FROM monitored_apps 
            WHERE device_id = ? AND is_active = 1
        ''', (self.device_id,))
        
        apps = {}
        for row in cursor.fetchall():
            package_name, app_name, auto_record, duration, quality = row
            apps[package_name] = {
                'name': app_name,
                'auto_record': bool(auto_record),
                'duration': duration,
                'quality': quality
            }
        
        conn.close()
        return apps
    
    def start_monitoring(self):
        """بدء مراقبة التطبيقات"""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("بدء مراقبة التطبيقات للتسجيل التلقائي")
    
    def stop_monitoring(self):
        """إيقاف مراقبة التطبيقات"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("تم إيقاف مراقبة التطبيقات")
    
    def _monitor_worker(self):
        """عامل مراقبة التطبيقات"""
        while self.is_monitoring:
            try:
                # الحصول على التطبيق النشط حالياً
                current_app = self._get_current_app()
                
                # فحص إذا تغير التطبيق
                if current_app != self.current_app:
                    self._handle_app_change(self.current_app, current_app)
                    self.current_app = current_app
                
                time.sleep(2)  # فحص كل ثانيتين
                
            except Exception as e:
                logger.error(f"خطأ في مراقبة التطبيقات: {e}")
                time.sleep(5)
    
    def _get_current_app(self) -> str:
        """الحصول على التطبيق النشط حالياً"""
        # في التطبيق الحقيقي، سيتم استخدام APIs النظام للحصول على التطبيق النشط
        # هنا نقوم بمحاكاة تغيير التطبيقات
        import random
        apps = ['com.whatsapp', 'com.instagram.android', 'com.facebook.katana', 
                'com.android.chrome', 'com.google.android.gm', 'com.spotify.music']
        
        # محاكاة تغيير التطبيق أحياناً
        if random.random() < 0.1:  # 10% احتمال تغيير التطبيق
            return random.choice(apps)
        
        return self.current_app
    
    def _handle_app_change(self, old_app: str, new_app: str):
        """معالجة تغيير التطبيق"""
        if new_app in self.monitored_apps and self.monitored_apps[new_app]['auto_record']:
            logger.info(f"تم اكتشاف تطبيق مراقب: {new_app}")
            # إشعار نظام التسجيل لبدء التسجيل
            self._trigger_recording(new_app)
    
    def _trigger_recording(self, app_package: str):
        """تشغيل التسجيل للتطبيق المحدد"""
        app_info = self.monitored_apps[app_package]
        logger.info(f"بدء تسجيل تلقائي للتطبيق: {app_info['name']}")
        
        # في التطبيق الحقيقي، سيتم استدعاء نظام التسجيل
        # هنا نقوم بتسجيل الحدث فقط
        
    def add_monitored_app(self, package_name: str, app_name: str, auto_record: bool = True, 
                         duration: int = 300, quality: str = 'medium'):
        """إضافة تطبيق للمراقبة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO monitored_apps 
            (device_id, app_name, package_name, auto_record, record_duration, quality)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.device_id, app_name, package_name, auto_record, duration, quality))
        
        conn.commit()
        conn.close()
        
        # تحديث القائمة في الذاكرة
        self.monitored_apps[package_name] = {
            'name': app_name,
            'auto_record': auto_record,
            'duration': duration,
            'quality': quality
        }

class ScreenRecorderCore:
    """النواة الأساسية لنظام تسجيل الشاشة"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.db = ScreenRecorderDatabase()
        self.screen_capture = ScreenCapture()
        self.app_monitor = AppMonitor(device_id, self.db)
        self.current_recording = None
        self.is_recording = False
        
        # إعدادات التسجيل
        self.recordings_dir = f"screen_recordings/{device_id}"
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # تحميل إعدادات الجهاز
        self.settings = self._load_device_settings()
        
        # بدء مراقبة التطبيقات إذا كانت مفعلة
        if self.settings.get('auto_record', False):
            self.app_monitor.start_monitoring()
    
    def _load_device_settings(self) -> Dict:
        """تحميل إعدادات الجهاز"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM recording_settings WHERE device_id = ?', (self.device_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [description[0] for description in cursor.description]
            settings = dict(zip(columns, result))
        else:
            # إنشاء إعدادات افتراضية
            settings = {
                'device_id': self.device_id,
                'auto_record': False,
                'default_quality': 'medium',
                'default_fps': 30,
                'max_duration': 3600,
                'storage_limit_mb': 5000,
                'auto_upload': True,
                'encryption_enabled': True,
                'delete_after_upload': False,
                'record_audio': True,
                'show_cursor': True
            }
            
            cursor.execute('''
                INSERT INTO recording_settings 
                (device_id, auto_record, default_quality, default_fps, max_duration,
                 storage_limit_mb, auto_upload, encryption_enabled, delete_after_upload,
                 record_audio, show_cursor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                settings['device_id'], settings['auto_record'], settings['default_quality'],
                settings['default_fps'], settings['max_duration'], settings['storage_limit_mb'],
                settings['auto_upload'], settings['encryption_enabled'], settings['delete_after_upload'],
                settings['record_audio'], settings['show_cursor']
            ))
            conn.commit()
        
        conn.close()
        return settings
    
    def start_recording(self, trigger_type: str = 'manual', trigger_app: str = '', 
                       duration: int = None, quality: str = None) -> str:
        """بدء تسجيل الشاشة"""
        if self.is_recording:
            logger.warning("التسجيل قيد التشغيل بالفعل")
            return None
        
        # إنشاء معرف فريد للتسجيل
        recording_id = self._generate_recording_id()
        
        # تحديد الجودة
        if not quality:
            quality = self.settings['default_quality']
        
        # تحديد المدة القصوى
        if not duration:
            duration = self.settings['max_duration']
        
        # إنشاء مسار الملف
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{recording_id}_{timestamp}.mp4"
        file_path = os.path.join(self.recordings_dir, filename)
        
        # إنشاء سجل التسجيل
        self.current_recording = ScreenRecording(
            recording_id=recording_id,
            device_id=self.device_id,
            start_time=datetime.now().isoformat(),
            end_time="",
            duration=0,
            file_path=file_path,
            file_size=0,
            resolution="1920x1080",  # سيتم تحديثها لاحقاً
            fps=self.settings['default_fps'],
            quality=quality,
            trigger_type=trigger_type,
            trigger_app=trigger_app,
            is_encrypted=self.settings['encryption_enabled'],
            thumbnail_path="",
            metadata={}
        )
        
        # بدء التسجيل
        self.is_recording = True
        self.screen_capture.start_capture(file_path, duration, quality)
        
        logger.info(f"بدء تسجيل الشاشة: {recording_id}")
        return recording_id
    
    def stop_recording(self) -> Optional[ScreenRecording]:
        """إيقاف تسجيل الشاشة"""
        if not self.is_recording or not self.current_recording:
            return None
        
        # إيقاف التسجيل
        self.is_recording = False
        self.screen_capture.stop_capture()
        
        # تحديث معلومات التسجيل
        self.current_recording.end_time = datetime.now().isoformat()
        self.current_recording.duration = self._calculate_duration()
        
        # فحص وجود الملف وحساب حجمه
        if os.path.exists(self.current_recording.file_path):
            self.current_recording.file_size = os.path.getsize(self.current_recording.file_path)
        
        # إنشاء صورة مصغرة
        thumbnail_path = self.current_recording.file_path.replace('.mp4', '_thumb.jpg')
        if self.screen_capture.create_thumbnail(self.current_recording.file_path, thumbnail_path):
            self.current_recording.thumbnail_path = thumbnail_path
        
        # تشفير الملف إذا كان مفعلاً
        if self.current_recording.is_encrypted:
            encrypted_path = self._encrypt_recording(self.current_recording.file_path)
            if encrypted_path:
                os.remove(self.current_recording.file_path)  # حذف الملف غير المشفر
                self.current_recording.file_path = encrypted_path
                self.current_recording.file_size = os.path.getsize(encrypted_path)
        
        # حفظ في قاعدة البيانات
        self.db.insert_recording(self.current_recording)
        
        # تحديث الإحصائيات
        self._update_daily_stats()
        
        logger.info(f"تم حفظ تسجيل الشاشة: {self.current_recording.recording_id}")
        
        # رفع التسجيل إلى السحابة إذا كان مفعلاً
        if self.settings['auto_upload']:
            self._upload_recording(self.current_recording.file_path)
        
        completed_recording = self.current_recording
        self.current_recording = None
        return completed_recording
    
    def _generate_recording_id(self) -> str:
        """توليد معرف فريد للتسجيل"""
        timestamp = str(int(time.time()))
        device_hash = hashlib.md5(self.device_id.encode()).hexdigest()[:8]
        return f"screen_{device_hash}_{timestamp}"
    
    def _calculate_duration(self) -> int:
        """حساب مدة التسجيل بالثواني"""
        if not self.current_recording or not self.current_recording.start_time:
            return 0
        
        start = datetime.fromisoformat(self.current_recording.start_time)
        end = datetime.now()
        duration = (end - start).total_seconds()
        return int(duration)
    
    def _encrypt_recording(self, file_path: str) -> Optional[str]:
        """تشفير ملف التسجيل"""
        try:
            # قراءة الملف
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # تشفير البيانات (تشفير بسيط باستخدام base64 - في التطبيق الحقيقي استخدم AES)
            encrypted_data = base64.b64encode(data)
            
            # حفظ الملف المشفر
            encrypted_path = file_path + '.enc'
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            return encrypted_path
        except Exception as e:
            logger.error(f"خطأ في تشفير الملف: {e}")
            return None
    
    def _update_daily_stats(self):
        """تحديث الإحصائيات اليومية"""
        today = datetime.now().date().isoformat()
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # الحصول على الإحصائيات الحالية
        cursor.execute('''
            SELECT total_recordings, total_duration, storage_used_mb 
            FROM recording_stats 
            WHERE device_id = ? AND date = ?
        ''', (self.device_id, today))
        
        result = cursor.fetchone()
        
        if result:
            total_recordings, total_duration, storage_used = result
            new_total_recordings = total_recordings + 1
            new_total_duration = total_duration + self.current_recording.duration
            new_storage_used = storage_used + (self.current_recording.file_size / (1024 * 1024))
            
            cursor.execute('''
                UPDATE recording_stats 
                SET total_recordings = ?, total_duration = ?, storage_used_mb = ?
                WHERE device_id = ? AND date = ?
            ''', (new_total_recordings, new_total_duration, new_storage_used, self.device_id, today))
        else:
            cursor.execute('''
                INSERT INTO recording_stats 
                (device_id, date, total_recordings, total_duration, storage_used_mb)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.device_id, today, 1, self.current_recording.duration,
                self.current_recording.file_size / (1024 * 1024)
            ))
        
        conn.commit()
        conn.close()
    
    def _upload_recording(self, file_path: str):
        """رفع التسجيل إلى السحابة"""
        # في التطبيق الحقيقي، سيتم رفع الملف إلى خدمة سحابية
        logger.info(f"رفع تسجيل الشاشة إلى السحابة: {file_path}")
        
        # محاكاة عملية الرفع
        time.sleep(2)
        
        # تحديث إحصائيات الرفع
        today = datetime.now().date().isoformat()
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE recording_stats 
            SET upload_success = upload_success + 1
            WHERE device_id = ? AND date = ?
        ''', (self.device_id, today))
        
        conn.commit()
        conn.close()

class ScreenRecorderAPI:
    """واجهة برمجة التطبيقات لنظام تسجيل الشاشة"""
    
    def __init__(self, device_id: str):
        self.recorder = ScreenRecorderCore(device_id)
    
    def start_recording(self, trigger_type: str = 'manual', trigger_app: str = '', 
                       duration: int = None, quality: str = None) -> Dict:
        """بدء تسجيل الشاشة"""
        recording_id = self.recorder.start_recording(trigger_type, trigger_app, duration, quality)
        return {
            "status": "started" if recording_id else "failed",
            "recording_id": recording_id,
            "message": "تم بدء تسجيل الشاشة" if recording_id else "فشل في بدء التسجيل"
        }
    
    def stop_recording(self) -> Dict:
        """إيقاف تسجيل الشاشة"""
        completed_recording = self.recorder.stop_recording()
        return {
            "status": "completed" if completed_recording else "no_active_recording",
            "recording": asdict(completed_recording) if completed_recording else None,
            "message": "تم حفظ التسجيل" if completed_recording else "لا يوجد تسجيل نشط"
        }
    
    def get_recordings(self, limit: int = 50) -> List[Dict]:
        """الحصول على قائمة التسجيلات"""
        return self.recorder.db.get_recordings(self.recorder.device_id, limit)
    
    def get_recording_stats(self) -> Dict:
        """إحصائيات التسجيل"""
        conn = sqlite3.connect(self.recorder.db.db_path)
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute('SELECT COUNT(*) FROM screen_recordings WHERE device_id = ?', (self.recorder.device_id,))
        total_recordings = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(duration) FROM screen_recordings WHERE device_id = ?', (self.recorder.device_id,))
        total_duration = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(file_size) FROM screen_recordings WHERE device_id = ?', (self.recorder.device_id,))
        total_size = cursor.fetchone()[0] or 0
        
        # إحصائيات اليوم
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM screen_recordings 
            WHERE device_id = ? AND DATE(start_time) = ?
        ''', (self.recorder.device_id, today))
        today_recordings = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_recordings': total_recordings,
            'total_duration_seconds': total_duration,
            'total_size_bytes': total_size,
            'today_recordings': today_recordings,
            'storage_usage_mb': total_size / (1024 * 1024) if total_size else 0,
            'settings': self.recorder.settings,
            'is_recording': self.recorder.is_recording,
            'current_recording': asdict(self.recorder.current_recording) if self.recorder.current_recording else None
        }
    
    def add_monitored_app(self, package_name: str, app_name: str, auto_record: bool = True, 
                         duration: int = 300, quality: str = 'medium') -> Dict:
        """إضافة تطبيق للمراقبة"""
        self.recorder.app_monitor.add_monitored_app(package_name, app_name, auto_record, duration, quality)
        return {
            "status": "added",
            "message": f"تم إضافة {app_name} للمراقبة"
        }

# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مثيل من نظام تسجيل الشاشة
    device_id = "test_device_001"
    screen_recorder_api = ScreenRecorderAPI(device_id)
    
    # بدء تسجيل الشاشة
    print("بدء تسجيل الشاشة...")
    result = screen_recorder_api.start_recording('manual', '', 10, 'medium')
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # محاكاة مدة التسجيل
    time.sleep(12)
    
    # إيقاف التسجيل
    print("إيقاف التسجيل...")
    result = screen_recorder_api.stop_recording()
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # الحصول على الإحصائيات
    stats = screen_recorder_api.get_recording_stats()
    print(f"الإحصائيات: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # إضافة تطبيق للمراقبة
    result = screen_recorder_api.add_monitored_app('com.whatsapp', 'WhatsApp', True, 300, 'high')
    print(f"إضافة تطبيق: {json.dumps(result, ensure_ascii=False, indent=2)}")

