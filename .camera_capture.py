#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام التقاط الصور من الكاميرا المتقدم
Advanced Camera Capture System
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
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io

# إعداد نظام السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CameraCapture:
    """فئة لتمثيل التقاط صورة من الكاميرا"""
    capture_id: str
    device_id: str
    camera_type: str  # 'front', 'back'
    capture_time: str
    file_path: str
    file_size: int
    resolution: str  # مثل "1920x1080"
    trigger_type: str  # 'manual', 'automatic', 'app_open', 'unlock', 'scheduled'
    trigger_app: str
    location_data: Dict  # إحداثيات GPS
    is_encrypted: bool
    thumbnail_path: str
    metadata: Dict

class CameraCaptureDatabase:
    """مدير قاعدة بيانات التقاط الصور"""
    
    def __init__(self, db_path: str = "camera_capture.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول التقاط الصور
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camera_captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capture_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                camera_type TEXT NOT NULL,
                capture_time DATETIME NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                resolution TEXT,
                trigger_type TEXT DEFAULT 'manual',
                trigger_app TEXT,
                location_data TEXT,
                is_encrypted BOOLEAN DEFAULT 0,
                thumbnail_path TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول إعدادات الكاميرا
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camera_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                auto_capture_enabled BOOLEAN DEFAULT 0,
                front_camera_enabled BOOLEAN DEFAULT 1,
                back_camera_enabled BOOLEAN DEFAULT 1,
                capture_on_unlock BOOLEAN DEFAULT 1,
                capture_on_app_open BOOLEAN DEFAULT 1,
                capture_interval_minutes INTEGER DEFAULT 60,
                image_quality INTEGER DEFAULT 85,
                resolution_front TEXT DEFAULT '1280x720',
                resolution_back TEXT DEFAULT '1920x1080',
                save_location BOOLEAN DEFAULT 1,
                encryption_enabled BOOLEAN DEFAULT 1,
                auto_upload BOOLEAN DEFAULT 1,
                delete_after_upload BOOLEAN DEFAULT 0,
                storage_limit_mb INTEGER DEFAULT 1000,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول جدولة التقاط الصور
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capture_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                schedule_name TEXT NOT NULL,
                camera_type TEXT DEFAULT 'both',
                start_time TIME,
                end_time TIME,
                interval_minutes INTEGER DEFAULT 30,
                days_of_week TEXT DEFAULT '1,2,3,4,5,6,7',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول التطبيقات المراقبة للتقاط الصور
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_apps_camera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                app_package TEXT NOT NULL,
                app_name TEXT,
                auto_capture BOOLEAN DEFAULT 1,
                camera_type TEXT DEFAULT 'front',
                capture_delay_seconds INTEGER DEFAULT 2,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, app_package)
            )
        ''')
        
        # جدول إحصائيات التقاط الصور
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capture_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                date DATE NOT NULL,
                total_captures INTEGER DEFAULT 0,
                front_camera_captures INTEGER DEFAULT 0,
                back_camera_captures INTEGER DEFAULT 0,
                automatic_captures INTEGER DEFAULT 0,
                manual_captures INTEGER DEFAULT 0,
                storage_used_mb REAL DEFAULT 0,
                upload_success INTEGER DEFAULT 0,
                upload_failed INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_capture(self, capture: CameraCapture):
        """إدراج التقاط صورة جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO camera_captures 
            (capture_id, device_id, camera_type, capture_time, file_path, file_size,
             resolution, trigger_type, trigger_app, location_data, is_encrypted, 
             thumbnail_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            capture.capture_id, capture.device_id, capture.camera_type, capture.capture_time,
            capture.file_path, capture.file_size, capture.resolution, capture.trigger_type,
            capture.trigger_app, json.dumps(capture.location_data, ensure_ascii=False),
            capture.is_encrypted, capture.thumbnail_path, 
            json.dumps(capture.metadata, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def get_captures(self, device_id: str = None, limit: int = 100) -> List[Dict]:
        """استرجاع التقاط الصور"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('''
                SELECT * FROM camera_captures 
                WHERE device_id = ? 
                ORDER BY capture_time DESC 
                LIMIT ?
            ''', (device_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM camera_captures 
                ORDER BY capture_time DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results

class CameraController:
    """تحكم في الكاميرا والتقاط الصور"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.is_capturing = False
        self.capture_lock = threading.Lock()
    
    def capture_photo(self, camera_type: str = 'front', quality: int = 85, 
                     resolution: str = None) -> Optional[str]:
        """التقاط صورة من الكاميرا"""
        with self.capture_lock:
            try:
                # تحديد الدقة الافتراضية
                if not resolution:
                    resolution = '1280x720' if camera_type == 'front' else '1920x1080'
                
                # إنشاء مسار الملف
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"camera_{camera_type}_{timestamp}.jpg"
                captures_dir = f"camera_captures/{self.device_id}"
                os.makedirs(captures_dir, exist_ok=True)
                file_path = os.path.join(captures_dir, filename)
                
                # التقاط الصورة (محاكاة)
                image = self._simulate_camera_capture(camera_type, resolution, quality)
                
                if image:
                    # حفظ الصورة
                    image.save(file_path, 'JPEG', quality=quality)
                    logger.info(f"تم التقاط صورة من الكاميرا {camera_type}: {file_path}")
                    return file_path
                
                return None
                
            except Exception as e:
                logger.error(f"خطأ في التقاط الصورة: {e}")
                return None
    
    def _simulate_camera_capture(self, camera_type: str, resolution: str, quality: int) -> Optional[Image.Image]:
        """محاكاة التقاط صورة من الكاميرا"""
        try:
            # تحليل الدقة
            width, height = map(int, resolution.split('x'))
            
            # إنشاء صورة وهمية
            if camera_type == 'front':
                # كاميرا أمامية - خلفية فاتحة مع وجه وهمي
                image = Image.new('RGB', (width, height), color='lightblue')
                draw = ImageDraw.Draw(image)
                
                # رسم وجه وهمي
                face_size = min(width, height) // 3
                face_x = (width - face_size) // 2
                face_y = (height - face_size) // 2
                
                # الوجه
                draw.ellipse([face_x, face_y, face_x + face_size, face_y + face_size], 
                           fill='peachpuff', outline='black', width=2)
                
                # العيون
                eye_size = face_size // 8
                left_eye_x = face_x + face_size // 3
                right_eye_x = face_x + 2 * face_size // 3
                eye_y = face_y + face_size // 3
                
                draw.ellipse([left_eye_x - eye_size, eye_y - eye_size, 
                            left_eye_x + eye_size, eye_y + eye_size], fill='black')
                draw.ellipse([right_eye_x - eye_size, eye_y - eye_size, 
                            right_eye_x + eye_size, eye_y + eye_size], fill='black')
                
                # الفم
                mouth_y = face_y + 2 * face_size // 3
                draw.arc([face_x + face_size // 4, mouth_y - face_size // 8,
                         face_x + 3 * face_size // 4, mouth_y + face_size // 8],
                        start=0, end=180, fill='red', width=3)
                
            else:
                # كاميرا خلفية - منظر عام
                image = Image.new('RGB', (width, height), color='skyblue')
                draw = ImageDraw.Draw(image)
                
                # رسم منظر طبيعي بسيط
                # الأرض
                ground_y = height * 2 // 3
                draw.rectangle([0, ground_y, width, height], fill='green')
                
                # الشمس
                sun_size = min(width, height) // 10
                draw.ellipse([width - sun_size * 2, sun_size, 
                            width - sun_size, sun_size * 2], fill='yellow')
                
                # الغيوم
                cloud_y = height // 4
                for i in range(3):
                    cloud_x = i * width // 3 + width // 6
                    draw.ellipse([cloud_x - 50, cloud_y - 20, 
                                cloud_x + 50, cloud_y + 20], fill='white')
            
            # إضافة معلومات الالتقاط
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw.text((10, 10), f"{camera_type.upper()} Camera", fill='white', font=font)
            draw.text((10, 40), timestamp, fill='white', font=font)
            draw.text((10, 70), f"Resolution: {resolution}", fill='white', font=font)
            
            return image
            
        except Exception as e:
            logger.error(f"خطأ في محاكاة التقاط الصورة: {e}")
            return None
    
    def create_thumbnail(self, image_path: str, thumbnail_path: str, size: Tuple[int, int] = (200, 200)) -> bool:
        """إنشاء صورة مصغرة"""
        try:
            with Image.open(image_path) as image:
                # إنشاء صورة مصغرة مع الحفاظ على النسبة
                image.thumbnail(size, Image.Resampling.LANCZOS)
                image.save(thumbnail_path, 'JPEG', quality=80)
                return True
        except Exception as e:
            logger.error(f"خطأ في إنشاء الصورة المصغرة: {e}")
            return False
    
    def enhance_image(self, image_path: str, enhanced_path: str) -> bool:
        """تحسين جودة الصورة"""
        try:
            with Image.open(image_path) as image:
                # تحسين السطوع والتباين
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(1.1)  # زيادة السطوع بنسبة 10%
                
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.2)  # زيادة التباين بنسبة 20%
                
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.1)  # زيادة الحدة بنسبة 10%
                
                # حفظ الصورة المحسنة
                image.save(enhanced_path, 'JPEG', quality=95)
                return True
        except Exception as e:
            logger.error(f"خطأ في تحسين الصورة: {e}")
            return False

class AppMonitorCamera:
    """مراقب التطبيقات للتقاط الصور التلقائي"""
    
    def __init__(self, device_id: str, db: CameraCaptureDatabase, camera_controller: CameraController):
        self.device_id = device_id
        self.db = db
        self.camera_controller = camera_controller
        self.is_monitoring = False
        self.monitor_thread = None
        self.monitored_apps = self._load_monitored_apps()
        self.current_app = ""
    
    def _load_monitored_apps(self) -> Dict[str, Dict]:
        """تحميل قائمة التطبيقات المراقبة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT app_package, app_name, auto_capture, camera_type, capture_delay_seconds 
            FROM monitored_apps_camera 
            WHERE device_id = ? AND is_active = 1
        ''', (self.device_id,))
        
        apps = {}
        for row in cursor.fetchall():
            package_name, app_name, auto_capture, camera_type, delay = row
            apps[package_name] = {
                'name': app_name,
                'auto_capture': bool(auto_capture),
                'camera_type': camera_type,
                'delay': delay
            }
        
        conn.close()
        return apps
    
    def start_monitoring(self):
        """بدء مراقبة التطبيقات"""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("بدء مراقبة التطبيقات للتقاط الصور التلقائي")
    
    def stop_monitoring(self):
        """إيقاف مراقبة التطبيقات"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("تم إيقاف مراقبة التطبيقات للكاميرا")
    
    def _monitor_worker(self):
        """عامل مراقبة التطبيقات"""
        while self.is_monitoring:
            try:
                # الحصول على التطبيق النشط حالياً
                current_app = self._get_current_app()
                
                # فحص إذا تغير التطبيق
                if current_app != self.current_app and current_app in self.monitored_apps:
                    self._handle_app_open(current_app)
                    self.current_app = current_app
                
                time.sleep(3)  # فحص كل 3 ثوانٍ
                
            except Exception as e:
                logger.error(f"خطأ في مراقبة التطبيقات للكاميرا: {e}")
                time.sleep(10)
    
    def _get_current_app(self) -> str:
        """الحصول على التطبيق النشط حالياً"""
        # محاكاة تغيير التطبيقات
        import random
        apps = list(self.monitored_apps.keys()) + ['com.android.launcher', 'com.android.settings']
        
        if random.random() < 0.1:  # 10% احتمال تغيير التطبيق
            return random.choice(apps)
        
        return self.current_app
    
    def _handle_app_open(self, app_package: str):
        """معالجة فتح تطبيق مراقب"""
        app_info = self.monitored_apps[app_package]
        
        if app_info['auto_capture']:
            logger.info(f"تم فتح تطبيق مراقب: {app_info['name']}")
            
            # انتظار قبل التقاط الصورة
            time.sleep(app_info['delay'])
            
            # التقاط صورة
            self._capture_for_app(app_package, app_info)
    
    def _capture_for_app(self, app_package: str, app_info: Dict):
        """التقاط صورة لتطبيق محدد"""
        try:
            file_path = self.camera_controller.capture_photo(
                camera_type=app_info['camera_type'],
                quality=85
            )
            
            if file_path:
                logger.info(f"تم التقاط صورة تلقائية لتطبيق {app_info['name']}")
                return file_path
            
        except Exception as e:
            logger.error(f"خطأ في التقاط صورة للتطبيق {app_package}: {e}")
        
        return None

class ScheduledCapture:
    """نظام التقاط الصور المجدول"""
    
    def __init__(self, device_id: str, db: CameraCaptureDatabase, camera_controller: CameraController):
        self.device_id = device_id
        self.db = db
        self.camera_controller = camera_controller
        self.is_running = False
        self.scheduler_thread = None
        self.schedules = self._load_schedules()
    
    def _load_schedules(self) -> List[Dict]:
        """تحميل جداول التقاط الصور"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT schedule_name, camera_type, start_time, end_time, 
                   interval_minutes, days_of_week 
            FROM capture_schedules 
            WHERE device_id = ? AND is_active = 1
        ''', (self.device_id,))
        
        schedules = []
        for row in cursor.fetchall():
            schedules.append({
                'name': row[0],
                'camera_type': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'interval_minutes': row[4],
                'days_of_week': [int(d) for d in row[5].split(',')]
            })
        
        conn.close()
        return schedules
    
    def start_scheduler(self):
        """بدء جدولة التقاط الصور"""
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_worker)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        logger.info("بدء جدولة التقاط الصور")
    
    def stop_scheduler(self):
        """إيقاف جدولة التقاط الصور"""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        logger.info("تم إيقاف جدولة التقاط الصور")
    
    def _scheduler_worker(self):
        """عامل الجدولة"""
        while self.is_running:
            try:
                current_time = datetime.now()
                current_weekday = current_time.weekday() + 1  # 1=Monday, 7=Sunday
                current_time_str = current_time.strftime("%H:%M")
                
                for schedule in self.schedules:
                    if self._should_capture_now(schedule, current_weekday, current_time_str):
                        self._execute_scheduled_capture(schedule)
                
                time.sleep(60)  # فحص كل دقيقة
                
            except Exception as e:
                logger.error(f"خطأ في جدولة التقاط الصور: {e}")
                time.sleep(300)  # انتظار 5 دقائق عند حدوث خطأ
    
    def _should_capture_now(self, schedule: Dict, current_weekday: int, current_time: str) -> bool:
        """تحديد ما إذا كان يجب التقاط صورة الآن"""
        # فحص اليوم
        if current_weekday not in schedule['days_of_week']:
            return False
        
        # فحص الوقت
        if schedule['start_time'] <= current_time <= schedule['end_time']:
            # فحص الفترة الزمنية
            # هنا يمكن إضافة منطق أكثر تعقيداً للفترات
            return True
        
        return False
    
    def _execute_scheduled_capture(self, schedule: Dict):
        """تنفيذ التقاط مجدول"""
        try:
            camera_types = ['front', 'back'] if schedule['camera_type'] == 'both' else [schedule['camera_type']]
            
            for camera_type in camera_types:
                file_path = self.camera_controller.capture_photo(camera_type=camera_type)
                if file_path:
                    logger.info(f"تم تنفيذ التقاط مجدول: {schedule['name']} - {camera_type}")
                
        except Exception as e:
            logger.error(f"خطأ في تنفيذ التقاط مجدول: {e}")

class CameraCaptureCore:
    """النواة الأساسية لنظام التقاط الصور"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.db = CameraCaptureDatabase()
        self.camera_controller = CameraController(device_id)
        self.app_monitor = AppMonitorCamera(device_id, self.db, self.camera_controller)
        self.scheduler = ScheduledCapture(device_id, self.db, self.camera_controller)
        
        # تحميل إعدادات الجهاز
        self.settings = self._load_device_settings()
        
        # بدء المراقبة التلقائية إذا كانت مفعلة
        if self.settings.get('auto_capture_enabled', False):
            self.start_monitoring()
    
    def _load_device_settings(self) -> Dict:
        """تحميل إعدادات الجهاز"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM camera_settings WHERE device_id = ?', (self.device_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [description[0] for description in cursor.description]
            settings = dict(zip(columns, result))
        else:
            # إنشاء إعدادات افتراضية
            settings = {
                'device_id': self.device_id,
                'auto_capture_enabled': False,
                'front_camera_enabled': True,
                'back_camera_enabled': True,
                'capture_on_unlock': True,
                'capture_on_app_open': True,
                'capture_interval_minutes': 60,
                'image_quality': 85,
                'resolution_front': '1280x720',
                'resolution_back': '1920x1080',
                'save_location': True,
                'encryption_enabled': True,
                'auto_upload': True,
                'delete_after_upload': False,
                'storage_limit_mb': 1000
            }
            
            cursor.execute('''
                INSERT INTO camera_settings 
                (device_id, auto_capture_enabled, front_camera_enabled, back_camera_enabled,
                 capture_on_unlock, capture_on_app_open, capture_interval_minutes, image_quality,
                 resolution_front, resolution_back, save_location, encryption_enabled,
                 auto_upload, delete_after_upload, storage_limit_mb)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                settings['device_id'], settings['auto_capture_enabled'], settings['front_camera_enabled'],
                settings['back_camera_enabled'], settings['capture_on_unlock'], settings['capture_on_app_open'],
                settings['capture_interval_minutes'], settings['image_quality'], settings['resolution_front'],
                settings['resolution_back'], settings['save_location'], settings['encryption_enabled'],
                settings['auto_upload'], settings['delete_after_upload'], settings['storage_limit_mb']
            ))
            conn.commit()
        
        conn.close()
        return settings
    
    def start_monitoring(self):
        """بدء المراقبة التلقائية"""
        if self.settings.get('capture_on_app_open', True):
            self.app_monitor.start_monitoring()
        
        self.scheduler.start_scheduler()
        logger.info("تم بدء مراقبة الكاميرا التلقائية")
    
    def stop_monitoring(self):
        """إيقاف المراقبة التلقائية"""
        self.app_monitor.stop_monitoring()
        self.scheduler.stop_scheduler()
        logger.info("تم إيقاف مراقبة الكاميرا التلقائية")
    
    def capture_photo_manual(self, camera_type: str = 'front', trigger_app: str = '') -> Optional[str]:
        """التقاط صورة يدوي"""
        if not self.settings.get(f'{camera_type}_camera_enabled', True):
            logger.warning(f"الكاميرا {camera_type} غير مفعلة")
            return None
        
        # تحديد الدقة والجودة
        resolution = self.settings.get(f'resolution_{camera_type}', '1280x720')
        quality = self.settings.get('image_quality', 85)
        
        # التقاط الصورة
        file_path = self.camera_controller.capture_photo(camera_type, quality, resolution)
        
        if file_path:
            # إنشاء سجل التقاط
            capture = self._create_capture_record(file_path, camera_type, 'manual', trigger_app)
            
            # حفظ في قاعدة البيانات
            self.db.insert_capture(capture)
            
            # معالجة إضافية
            self._post_process_capture(capture)
            
            return capture.capture_id
        
        return None
    
    def _create_capture_record(self, file_path: str, camera_type: str, trigger_type: str, trigger_app: str) -> CameraCapture:
        """إنشاء سجل التقاط صورة"""
        capture_id = self._generate_capture_id()
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # الحصول على الموقع الجغرافي (محاكاة)
        location_data = {}
        if self.settings.get('save_location', True):
            location_data = self._get_current_location()
        
        capture = CameraCapture(
            capture_id=capture_id,
            device_id=self.device_id,
            camera_type=camera_type,
            capture_time=datetime.now().isoformat(),
            file_path=file_path,
            file_size=file_size,
            resolution=self.settings.get(f'resolution_{camera_type}', '1280x720'),
            trigger_type=trigger_type,
            trigger_app=trigger_app,
            location_data=location_data,
            is_encrypted=self.settings.get('encryption_enabled', True),
            thumbnail_path="",
            metadata={}
        )
        
        return capture
    
    def _generate_capture_id(self) -> str:
        """توليد معرف فريد للالتقاط"""
        timestamp = str(int(time.time()))
        device_hash = hashlib.md5(self.device_id.encode()).hexdigest()[:8]
        return f"capture_{device_hash}_{timestamp}"
    
    def _get_current_location(self) -> Dict:
        """الحصول على الموقع الجغرافي الحالي (محاكاة)"""
        # في التطبيق الحقيقي، سيتم استخدام GPS
        import random
        return {
            'latitude': round(random.uniform(20.0, 30.0), 6),
            'longitude': round(random.uniform(40.0, 50.0), 6),
            'accuracy': random.randint(5, 20),
            'timestamp': datetime.now().isoformat()
        }
    
    def _post_process_capture(self, capture: CameraCapture):
        """معالجة إضافية بعد التقاط الصورة"""
        try:
            # إنشاء صورة مصغرة
            thumbnail_path = capture.file_path.replace('.jpg', '_thumb.jpg')
            if self.camera_controller.create_thumbnail(capture.file_path, thumbnail_path):
                capture.thumbnail_path = thumbnail_path
            
            # تشفير الصورة إذا كان مفعلاً
            if capture.is_encrypted:
                encrypted_path = self._encrypt_image(capture.file_path)
                if encrypted_path:
                    os.remove(capture.file_path)  # حذف الصورة غير المشفرة
                    capture.file_path = encrypted_path
                    capture.file_size = os.path.getsize(encrypted_path)
            
            # تحديث الإحصائيات
            self._update_daily_statistics(capture.camera_type, capture.trigger_type)
            
            # رفع إلى السحابة إذا كان مفعلاً
            if self.settings.get('auto_upload', True):
                self._upload_image(capture.file_path)
            
        except Exception as e:
            logger.error(f"خطأ في المعالجة الإضافية: {e}")
    
    def _encrypt_image(self, file_path: str) -> Optional[str]:
        """تشفير ملف الصورة"""
        try:
            # قراءة الملف
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # تشفير البيانات (تشفير بسيط باستخدام base64)
            encrypted_data = base64.b64encode(data)
            
            # حفظ الملف المشفر
            encrypted_path = file_path + '.enc'
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            return encrypted_path
        except Exception as e:
            logger.error(f"خطأ في تشفير الصورة: {e}")
            return None
    
    def _update_daily_statistics(self, camera_type: str, trigger_type: str):
        """تحديث الإحصائيات اليومية"""
        today = datetime.now().date().isoformat()
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # الحصول على الإحصائيات الحالية
        cursor.execute('''
            SELECT total_captures, front_camera_captures, back_camera_captures,
                   automatic_captures, manual_captures, storage_used_mb
            FROM capture_statistics 
            WHERE device_id = ? AND date = ?
        ''', (self.device_id, today))
        
        result = cursor.fetchone()
        
        if result:
            total, front, back, automatic, manual, storage = result
            new_total = total + 1
            new_front = front + (1 if camera_type == 'front' else 0)
            new_back = back + (1 if camera_type == 'back' else 0)
            new_automatic = automatic + (1 if trigger_type == 'automatic' else 0)
            new_manual = manual + (1 if trigger_type == 'manual' else 0)
            
            cursor.execute('''
                UPDATE capture_statistics 
                SET total_captures = ?, front_camera_captures = ?, back_camera_captures = ?,
                    automatic_captures = ?, manual_captures = ?
                WHERE device_id = ? AND date = ?
            ''', (new_total, new_front, new_back, new_automatic, new_manual, self.device_id, today))
        else:
            cursor.execute('''
                INSERT INTO capture_statistics 
                (device_id, date, total_captures, front_camera_captures, back_camera_captures,
                 automatic_captures, manual_captures)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.device_id, today, 1,
                1 if camera_type == 'front' else 0,
                1 if camera_type == 'back' else 0,
                1 if trigger_type == 'automatic' else 0,
                1 if trigger_type == 'manual' else 0
            ))
        
        conn.commit()
        conn.close()
    
    def _upload_image(self, file_path: str):
        """رفع الصورة إلى السحابة"""
        # محاكاة رفع الصورة
        logger.info(f"رفع الصورة إلى السحابة: {file_path}")
        time.sleep(1)  # محاكاة وقت الرفع

class CameraCaptureAPI:
    """واجهة برمجة التطبيقات لنظام التقاط الصور"""
    
    def __init__(self, device_id: str):
        self.capture_system = CameraCaptureCore(device_id)
    
    def capture_photo(self, camera_type: str = 'front', trigger_app: str = '') -> Dict:
        """التقاط صورة"""
        capture_id = self.capture_system.capture_photo_manual(camera_type, trigger_app)
        return {
            "status": "success" if capture_id else "failed",
            "capture_id": capture_id,
            "message": "تم التقاط الصورة بنجاح" if capture_id else "فشل في التقاط الصورة"
        }
    
    def start_auto_capture(self) -> Dict:
        """بدء التقاط الصور التلقائي"""
        self.capture_system.start_monitoring()
        return {"status": "started", "message": "تم بدء التقاط الصور التلقائي"}
    
    def stop_auto_capture(self) -> Dict:
        """إيقاف التقاط الصور التلقائي"""
        self.capture_system.stop_monitoring()
        return {"status": "stopped", "message": "تم إيقاف التقاط الصور التلقائي"}
    
    def get_captures(self, limit: int = 50) -> List[Dict]:
        """الحصول على قائمة الصور الملتقطة"""
        return self.capture_system.db.get_captures(self.capture_system.device_id, limit)
    
    def get_statistics(self) -> Dict:
        """الحصول على إحصائيات التقاط الصور"""
        conn = sqlite3.connect(self.capture_system.db.db_path)
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute('SELECT COUNT(*) FROM camera_captures WHERE device_id = ?', (self.capture_system.device_id,))
        total_captures = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM camera_captures WHERE device_id = ? AND camera_type = "front"', (self.capture_system.device_id,))
        front_captures = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM camera_captures WHERE device_id = ? AND camera_type = "back"', (self.capture_system.device_id,))
        back_captures = cursor.fetchone()[0]
        
        # إحصائيات اليوم
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM camera_captures 
            WHERE device_id = ? AND DATE(capture_time) = ?
        ''', (self.capture_system.device_id, today))
        today_captures = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_captures': total_captures,
            'front_camera_captures': front_captures,
            'back_camera_captures': back_captures,
            'today_captures': today_captures,
            'settings': self.capture_system.settings,
            'auto_monitoring_active': self.capture_system.app_monitor.is_monitoring
        }

# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مثيل من نظام التقاط الصور
    device_id = "test_device_001"
    camera_api = CameraCaptureAPI(device_id)
    
    # التقاط صورة من الكاميرا الأمامية
    print("التقاط صورة من الكاميرا الأمامية...")
    result = camera_api.capture_photo('front', 'manual_test')
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # التقاط صورة من الكاميرا الخلفية
    print("التقاط صورة من الكاميرا الخلفية...")
    result = camera_api.capture_photo('back', 'manual_test')
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # بدء التقاط التلقائي
    print("بدء التقاط الصور التلقائي...")
    result = camera_api.start_auto_capture()
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # انتظار قليل
    time.sleep(5)
    
    # الحصول على الإحصائيات
    stats = camera_api.get_statistics()
    print(f"الإحصائيات: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # إيقاف التقاط التلقائي
    result = camera_api.stop_auto_capture()
    print(f"إيقاف التلقائي: {json.dumps(result, ensure_ascii=False, indent=2)}")

