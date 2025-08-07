#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام Geo-Fencing والتنبيهات الذكية المتقدم
Advanced Geo-Fencing and Smart Alerts System
"""

import os
import json
import time
import sqlite3
import threading
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import hashlib
from dataclasses import dataclass, asdict
import logging
from enum import Enum

# إعداد نظام السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertType(Enum):
    """أنواع التنبيهات"""
    LOCATION_ENTER = "location_enter"
    LOCATION_EXIT = "location_exit"
    SPEED_LIMIT = "speed_limit"
    BATTERY_LOW = "battery_low"
    APP_USAGE = "app_usage"
    KEYWORD_DETECTED = "keyword_detected"
    DEVICE_OFFLINE = "device_offline"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    EMERGENCY = "emergency"
    CUSTOM = "custom"

class AlertPriority(Enum):
    """أولويات التنبيهات"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class GeoFence:
    """فئة لتمثيل منطقة جغرافية محددة"""
    fence_id: str
    device_id: str
    name: str
    description: str
    center_lat: float
    center_lng: float
    radius_meters: float
    fence_type: str  # 'safe_zone', 'restricted_zone', 'work_zone', 'home_zone'
    is_active: bool
    entry_alert: bool
    exit_alert: bool
    created_at: str
    metadata: Dict

@dataclass
class LocationPoint:
    """فئة لتمثيل نقطة موقع جغرافي"""
    location_id: str
    device_id: str
    latitude: float
    longitude: float
    accuracy: float
    altitude: float
    speed: float
    bearing: float
    timestamp: str
    address: str
    is_inside_fence: bool
    fence_ids: List[str]
    metadata: Dict

@dataclass
class SmartAlert:
    """فئة لتمثيل تنبيه ذكي"""
    alert_id: str
    device_id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    timestamp: str
    is_read: bool
    is_resolved: bool
    trigger_data: Dict
    actions_taken: List[str]
    metadata: Dict

class GeoFencingDatabase:
    """مدير قاعدة بيانات نظام Geo-Fencing"""
    
    def __init__(self, db_path: str = "geo_fencing.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول المناطق الجغرافية (Geo-Fences)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS geo_fences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fence_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                center_lat REAL NOT NULL,
                center_lng REAL NOT NULL,
                radius_meters REAL NOT NULL,
                fence_type TEXT DEFAULT 'safe_zone',
                is_active BOOLEAN DEFAULT 1,
                entry_alert BOOLEAN DEFAULT 1,
                exit_alert BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                INDEX(device_id),
                INDEX(fence_type)
            )
        ''')
        
        # جدول نقاط المواقع الجغرافية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL DEFAULT 0,
                altitude REAL DEFAULT 0,
                speed REAL DEFAULT 0,
                bearing REAL DEFAULT 0,
                timestamp DATETIME NOT NULL,
                address TEXT,
                is_inside_fence BOOLEAN DEFAULT 0,
                fence_ids TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX(device_id),
                INDEX(timestamp)
            )
        ''')
        
        # جدول التنبيهات الذكية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                title TEXT NOT NULL,
                message TEXT,
                timestamp DATETIME NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                is_resolved BOOLEAN DEFAULT 0,
                trigger_data TEXT,
                actions_taken TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX(device_id),
                INDEX(alert_type),
                INDEX(priority),
                INDEX(is_read)
            )
        ''')
        
        # جدول قواعد التنبيهات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                conditions TEXT NOT NULL,
                actions TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                priority TEXT DEFAULT 'medium',
                cooldown_minutes INTEGER DEFAULT 5,
                last_triggered DATETIME,
                trigger_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX(device_id),
                INDEX(rule_type),
                INDEX(is_active)
            )
        ''')
        
        # جدول إعدادات التنبيهات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                email_notifications BOOLEAN DEFAULT 1,
                sms_notifications BOOLEAN DEFAULT 1,
                push_notifications BOOLEAN DEFAULT 1,
                telegram_notifications BOOLEAN DEFAULT 1,
                email_address TEXT,
                phone_number TEXT,
                telegram_chat_id TEXT,
                notification_hours_start TIME DEFAULT '08:00',
                notification_hours_end TIME DEFAULT '22:00',
                weekend_notifications BOOLEAN DEFAULT 1,
                emergency_override BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول سجل الأنشطة الجغرافية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS geo_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                fence_id TEXT,
                activity_type TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                location_data TEXT,
                duration_minutes INTEGER DEFAULT 0,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX(device_id),
                INDEX(fence_id),
                INDEX(activity_type),
                INDEX(timestamp)
            )
        ''')
        
        # جدول إحصائيات المواقع
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                date DATE NOT NULL,
                total_locations INTEGER DEFAULT 0,
                distance_traveled_km REAL DEFAULT 0,
                max_speed_kmh REAL DEFAULT 0,
                time_in_safe_zones_minutes INTEGER DEFAULT 0,
                time_in_restricted_zones_minutes INTEGER DEFAULT 0,
                fence_violations INTEGER DEFAULT 0,
                alerts_generated INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_geo_fence(self, fence: GeoFence):
        """إدراج منطقة جغرافية جديدة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO geo_fences 
            (fence_id, device_id, name, description, center_lat, center_lng, radius_meters,
             fence_type, is_active, entry_alert, exit_alert, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fence.fence_id, fence.device_id, fence.name, fence.description,
            fence.center_lat, fence.center_lng, fence.radius_meters,
            fence.fence_type, fence.is_active, fence.entry_alert, fence.exit_alert,
            json.dumps(fence.metadata, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def insert_location_point(self, location: LocationPoint):
        """إدراج نقطة موقع جديدة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO location_points 
            (location_id, device_id, latitude, longitude, accuracy, altitude, speed, bearing,
             timestamp, address, is_inside_fence, fence_ids, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            location.location_id, location.device_id, location.latitude, location.longitude,
            location.accuracy, location.altitude, location.speed, location.bearing,
            location.timestamp, location.address, location.is_inside_fence,
            json.dumps(location.fence_ids), json.dumps(location.metadata, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def insert_alert(self, alert: SmartAlert):
        """إدراج تنبيه ذكي جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO smart_alerts 
            (alert_id, device_id, alert_type, priority, title, message, timestamp,
             is_read, is_resolved, trigger_data, actions_taken, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert.alert_id, alert.device_id, alert.alert_type.value, alert.priority.value,
            alert.title, alert.message, alert.timestamp, alert.is_read, alert.is_resolved,
            json.dumps(alert.trigger_data, ensure_ascii=False),
            json.dumps(alert.actions_taken, ensure_ascii=False),
            json.dumps(alert.metadata, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def get_geo_fences(self, device_id: str = None) -> List[Dict]:
        """استرجاع المناطق الجغرافية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('SELECT * FROM geo_fences WHERE device_id = ? AND is_active = 1', (device_id,))
        else:
            cursor.execute('SELECT * FROM geo_fences WHERE is_active = 1')
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_alerts(self, device_id: str = None, limit: int = 100) -> List[Dict]:
        """استرجاع التنبيهات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('''
                SELECT * FROM smart_alerts 
                WHERE device_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (device_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM smart_alerts 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results

class GeoCalculator:
    """حاسبة العمليات الجغرافية"""
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """حساب المسافة بين نقطتين جغرافيتين بالمتر"""
        # استخدام صيغة Haversine
        R = 6371000  # نصف قطر الأرض بالمتر
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) * math.sin(delta_lng / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    @staticmethod
    def is_point_in_circle(point_lat: float, point_lng: float, 
                          center_lat: float, center_lng: float, radius: float) -> bool:
        """فحص ما إذا كانت النقطة داخل دائرة محددة"""
        distance = GeoCalculator.calculate_distance(point_lat, point_lng, center_lat, center_lng)
        return distance <= radius
    
    @staticmethod
    def calculate_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """حساب الاتجاه بين نقطتين"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lng = math.radians(lng2 - lng1)
        
        y = math.sin(delta_lng) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng))
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    @staticmethod
    def calculate_speed(distance: float, time_seconds: float) -> float:
        """حساب السرعة بالكيلومتر/ساعة"""
        if time_seconds <= 0:
            return 0
        
        speed_ms = distance / time_seconds  # متر/ثانية
        speed_kmh = speed_ms * 3.6  # كيلومتر/ساعة
        return speed_kmh

class LocationTracker:
    """متتبع المواقع الجغرافية"""
    
    def __init__(self, device_id: str, db: GeoFencingDatabase):
        self.device_id = device_id
        self.db = db
        self.is_tracking = False
        self.tracking_thread = None
        self.last_location = None
        self.geo_fences = []
        self.tracking_interval = 30  # ثانية
    
    def start_tracking(self):
        """بدء تتبع الموقع"""
        self.is_tracking = True
        self.geo_fences = self.db.get_geo_fences(self.device_id)
        
        self.tracking_thread = threading.Thread(target=self._tracking_worker)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()
        
        logger.info(f"بدء تتبع الموقع للجهاز {self.device_id}")
    
    def stop_tracking(self):
        """إيقاف تتبع الموقع"""
        self.is_tracking = False
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.tracking_thread.join(timeout=5)
        
        logger.info(f"تم إيقاف تتبع الموقع للجهاز {self.device_id}")
    
    def _tracking_worker(self):
        """عامل تتبع الموقع"""
        while self.is_tracking:
            try:
                # الحصول على الموقع الحالي
                current_location = self._get_current_location()
                
                if current_location:
                    # معالجة الموقع الجديد
                    self._process_location(current_location)
                    
                    # حفظ الموقع في قاعدة البيانات
                    self.db.insert_location_point(current_location)
                    
                    # تحديث آخر موقع
                    self.last_location = current_location
                
                time.sleep(self.tracking_interval)
                
            except Exception as e:
                logger.error(f"خطأ في تتبع الموقع: {e}")
                time.sleep(60)
    
    def _get_current_location(self) -> Optional[LocationPoint]:
        """الحصول على الموقع الحالي (محاكاة)"""
        import random
        
        # محاكاة إحداثيات GPS
        base_lat = 24.7136  # الرياض
        base_lng = 46.6753
        
        # إضافة تغيير عشوائي صغير
        lat_offset = random.uniform(-0.01, 0.01)
        lng_offset = random.uniform(-0.01, 0.01)
        
        latitude = base_lat + lat_offset
        longitude = base_lng + lng_offset
        
        # حساب السرعة إذا كان هناك موقع سابق
        speed = 0
        bearing = 0
        
        if self.last_location:
            distance = GeoCalculator.calculate_distance(
                self.last_location.latitude, self.last_location.longitude,
                latitude, longitude
            )
            
            time_diff = self.tracking_interval
            speed = GeoCalculator.calculate_speed(distance, time_diff)
            
            bearing = GeoCalculator.calculate_bearing(
                self.last_location.latitude, self.last_location.longitude,
                latitude, longitude
            )
        
        # فحص المناطق الجغرافية
        inside_fences = []
        for fence in self.geo_fences:
            if GeoCalculator.is_point_in_circle(
                latitude, longitude,
                fence['center_lat'], fence['center_lng'],
                fence['radius_meters']
            ):
                inside_fences.append(fence['fence_id'])
        
        location = LocationPoint(
            location_id=f"loc_{self.device_id}_{int(time.time())}",
            device_id=self.device_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=random.uniform(3, 15),
            altitude=random.uniform(600, 800),
            speed=speed,
            bearing=bearing,
            timestamp=datetime.now().isoformat(),
            address=self._get_address_from_coordinates(latitude, longitude),
            is_inside_fence=len(inside_fences) > 0,
            fence_ids=inside_fences,
            metadata={'provider': 'gps', 'satellites': random.randint(4, 12)}
        )
        
        return location
    
    def _get_address_from_coordinates(self, lat: float, lng: float) -> str:
        """الحصول على العنوان من الإحداثيات (محاكاة)"""
        # في التطبيق الحقيقي، سيتم استخدام خدمة Reverse Geocoding
        addresses = [
            "شارع الملك فهد، الرياض",
            "طريق الملك عبدالعزيز، الرياض",
            "حي العليا، الرياض",
            "شارع التحلية، الرياض",
            "طريق الأمير محمد بن عبدالعزيز، الرياض"
        ]
        
        import random
        return random.choice(addresses)
    
    def _process_location(self, location: LocationPoint):
        """معالجة الموقع الجديد"""
        # فحص دخول أو خروج من المناطق الجغرافية
        if self.last_location:
            self._check_fence_transitions(self.last_location, location)
        
        # فحص السرعة
        self._check_speed_limits(location)
        
        # تحديث الإحصائيات
        self._update_location_statistics(location)
    
    def _check_fence_transitions(self, old_location: LocationPoint, new_location: LocationPoint):
        """فحص الانتقالات بين المناطق الجغرافية"""
        old_fences = set(old_location.fence_ids)
        new_fences = set(new_location.fence_ids)
        
        # المناطق التي تم دخولها
        entered_fences = new_fences - old_fences
        
        # المناطق التي تم الخروج منها
        exited_fences = old_fences - new_fences
        
        for fence_id in entered_fences:
            fence = self._get_fence_by_id(fence_id)
            if fence and fence['entry_alert']:
                self._create_fence_alert(fence, new_location, 'entry')
        
        for fence_id in exited_fences:
            fence = self._get_fence_by_id(fence_id)
            if fence and fence['exit_alert']:
                self._create_fence_alert(fence, new_location, 'exit')
    
    def _get_fence_by_id(self, fence_id: str) -> Optional[Dict]:
        """الحصول على منطقة جغرافية بالمعرف"""
        for fence in self.geo_fences:
            if fence['fence_id'] == fence_id:
                return fence
        return None
    
    def _create_fence_alert(self, fence: Dict, location: LocationPoint, action: str):
        """إنشاء تنبيه منطقة جغرافية"""
        alert_type = AlertType.LOCATION_ENTER if action == 'entry' else AlertType.LOCATION_EXIT
        
        title = f"{'دخول' if action == 'entry' else 'خروج'} منطقة {fence['name']}"
        message = f"تم {'دخول' if action == 'entry' else 'الخروج من'} منطقة {fence['name']} في {location.timestamp}"
        
        alert = SmartAlert(
            alert_id=f"fence_{fence['fence_id']}_{action}_{int(time.time())}",
            device_id=self.device_id,
            alert_type=alert_type,
            priority=AlertPriority.HIGH if fence['fence_type'] == 'restricted_zone' else AlertPriority.MEDIUM,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            is_read=False,
            is_resolved=False,
            trigger_data={
                'fence_id': fence['fence_id'],
                'fence_name': fence['name'],
                'fence_type': fence['fence_type'],
                'action': action,
                'location': {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'address': location.address
                }
            },
            actions_taken=[],
            metadata={'auto_generated': True}
        )
        
        self.db.insert_alert(alert)
        logger.info(f"تم إنشاء تنبيه منطقة جغرافية: {title}")
    
    def _check_speed_limits(self, location: LocationPoint):
        """فحص حدود السرعة"""
        speed_limit = 120  # كم/ساعة
        
        if location.speed > speed_limit:
            alert = SmartAlert(
                alert_id=f"speed_{self.device_id}_{int(time.time())}",
                device_id=self.device_id,
                alert_type=AlertType.SPEED_LIMIT,
                priority=AlertPriority.HIGH,
                title="تجاوز حد السرعة",
                message=f"السرعة الحالية {location.speed:.1f} كم/ساعة تتجاوز الحد المسموح {speed_limit} كم/ساعة",
                timestamp=datetime.now().isoformat(),
                is_read=False,
                is_resolved=False,
                trigger_data={
                    'current_speed': location.speed,
                    'speed_limit': speed_limit,
                    'location': {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'address': location.address
                    }
                },
                actions_taken=[],
                metadata={'auto_generated': True}
            )
            
            self.db.insert_alert(alert)
            logger.warning(f"تجاوز حد السرعة: {location.speed:.1f} كم/ساعة")
    
    def _update_location_statistics(self, location: LocationPoint):
        """تحديث إحصائيات الموقع"""
        today = datetime.now().date().isoformat()
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # الحصول على الإحصائيات الحالية
        cursor.execute('''
            SELECT total_locations, distance_traveled_km, max_speed_kmh
            FROM location_statistics 
            WHERE device_id = ? AND date = ?
        ''', (self.device_id, today))
        
        result = cursor.fetchone()
        
        if result:
            total_locations, distance_km, max_speed = result
            new_total = total_locations + 1
            new_max_speed = max(max_speed, location.speed)
            
            # حساب المسافة المقطوعة
            new_distance = distance_km
            if self.last_location:
                distance_meters = GeoCalculator.calculate_distance(
                    self.last_location.latitude, self.last_location.longitude,
                    location.latitude, location.longitude
                )
                new_distance += distance_meters / 1000  # تحويل إلى كيلومتر
            
            cursor.execute('''
                UPDATE location_statistics 
                SET total_locations = ?, distance_traveled_km = ?, max_speed_kmh = ?
                WHERE device_id = ? AND date = ?
            ''', (new_total, new_distance, new_max_speed, self.device_id, today))
        else:
            cursor.execute('''
                INSERT INTO location_statistics 
                (device_id, date, total_locations, distance_traveled_km, max_speed_kmh)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.device_id, today, 1, 0, location.speed))
        
        conn.commit()
        conn.close()

class SmartAlertEngine:
    """محرك التنبيهات الذكية"""
    
    def __init__(self, device_id: str, db: GeoFencingDatabase):
        self.device_id = device_id
        self.db = db
        self.is_running = False
        self.engine_thread = None
        self.alert_rules = []
        self.notification_channels = []
    
    def start_engine(self):
        """بدء محرك التنبيهات"""
        self.is_running = True
        self._load_alert_rules()
        self._load_notification_settings()
        
        self.engine_thread = threading.Thread(target=self._engine_worker)
        self.engine_thread.daemon = True
        self.engine_thread.start()
        
        logger.info("بدء محرك التنبيهات الذكية")
    
    def stop_engine(self):
        """إيقاف محرك التنبيهات"""
        self.is_running = False
        if self.engine_thread and self.engine_thread.is_alive():
            self.engine_thread.join(timeout=5)
        
        logger.info("تم إيقاف محرك التنبيهات الذكية")
    
    def _load_alert_rules(self):
        """تحميل قواعد التنبيهات"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rule_id, rule_name, rule_type, conditions, actions, priority, cooldown_minutes
            FROM alert_rules 
            WHERE device_id = ? AND is_active = 1
        ''', (self.device_id,))
        
        self.alert_rules = []
        for row in cursor.fetchall():
            rule = {
                'rule_id': row[0],
                'rule_name': row[1],
                'rule_type': row[2],
                'conditions': json.loads(row[3]),
                'actions': json.loads(row[4]),
                'priority': row[5],
                'cooldown_minutes': row[6]
            }
            self.alert_rules.append(rule)
        
        conn.close()
        logger.info(f"تم تحميل {len(self.alert_rules)} قاعدة تنبيه")
    
    def _load_notification_settings(self):
        """تحميل إعدادات الإشعارات"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email_notifications, sms_notifications, push_notifications, 
                   telegram_notifications, email_address, phone_number, telegram_chat_id
            FROM alert_settings 
            WHERE device_id = ?
        ''', (self.device_id,))
        
        result = cursor.fetchone()
        
        if result:
            self.notification_channels = {
                'email': {'enabled': bool(result[0]), 'address': result[4]},
                'sms': {'enabled': bool(result[1]), 'phone': result[5]},
                'push': {'enabled': bool(result[2])},
                'telegram': {'enabled': bool(result[3]), 'chat_id': result[6]}
            }
        else:
            # إعدادات افتراضية
            self.notification_channels = {
                'email': {'enabled': False, 'address': ''},
                'sms': {'enabled': False, 'phone': ''},
                'push': {'enabled': True},
                'telegram': {'enabled': False, 'chat_id': ''}
            }
        
        conn.close()
    
    def _engine_worker(self):
        """عامل محرك التنبيهات"""
        while self.is_running:
            try:
                # فحص قواعد التنبيهات
                self._check_alert_rules()
                
                # معالجة التنبيهات المعلقة
                self._process_pending_alerts()
                
                time.sleep(30)  # فحص كل 30 ثانية
                
            except Exception as e:
                logger.error(f"خطأ في محرك التنبيهات: {e}")
                time.sleep(60)
    
    def _check_alert_rules(self):
        """فحص قواعد التنبيهات"""
        for rule in self.alert_rules:
            try:
                if self._evaluate_rule_conditions(rule):
                    self._execute_rule_actions(rule)
            except Exception as e:
                logger.error(f"خطأ في فحص قاعدة {rule['rule_name']}: {e}")
    
    def _evaluate_rule_conditions(self, rule: Dict) -> bool:
        """تقييم شروط قاعدة التنبيه"""
        conditions = rule['conditions']
        rule_type = rule['rule_type']
        
        # فحص فترة التهدئة
        if self._is_rule_in_cooldown(rule['rule_id'], rule['cooldown_minutes']):
            return False
        
        if rule_type == 'battery_low':
            return self._check_battery_condition(conditions)
        elif rule_type == 'app_usage':
            return self._check_app_usage_condition(conditions)
        elif rule_type == 'device_offline':
            return self._check_device_offline_condition(conditions)
        elif rule_type == 'keyword_detected':
            return self._check_keyword_condition(conditions)
        elif rule_type == 'suspicious_activity':
            return self._check_suspicious_activity_condition(conditions)
        
        return False
    
    def _is_rule_in_cooldown(self, rule_id: str, cooldown_minutes: int) -> bool:
        """فحص ما إذا كانت القاعدة في فترة تهدئة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT last_triggered FROM alert_rules 
            WHERE rule_id = ?
        ''', (rule_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            last_triggered = datetime.fromisoformat(result[0])
            cooldown_end = last_triggered + timedelta(minutes=cooldown_minutes)
            return datetime.now() < cooldown_end
        
        return False
    
    def _check_battery_condition(self, conditions: Dict) -> bool:
        """فحص شرط البطارية المنخفضة"""
        threshold = conditions.get('battery_threshold', 20)
        
        # محاكاة مستوى البطارية
        import random
        current_battery = random.randint(5, 100)
        
        return current_battery <= threshold
    
    def _check_app_usage_condition(self, conditions: Dict) -> bool:
        """فحص شرط استخدام التطبيقات"""
        app_package = conditions.get('app_package', '')
        usage_threshold = conditions.get('usage_minutes', 60)
        
        # محاكاة استخدام التطبيق
        import random
        current_usage = random.randint(0, 120)
        
        return current_usage >= usage_threshold
    
    def _check_device_offline_condition(self, conditions: Dict) -> bool:
        """فحص شرط الجهاز غير متصل"""
        offline_threshold = conditions.get('offline_minutes', 30)
        
        # محاكاة حالة الاتصال
        import random
        return random.random() < 0.1  # 10% احتمال أن يكون الجهاز غير متصل
    
    def _check_keyword_condition(self, conditions: Dict) -> bool:
        """فحص شرط الكلمات المفتاحية"""
        keywords = conditions.get('keywords', [])
        
        # فحص الرسائل الحديثة للكلمات المفتاحية
        # هذا مثال مبسط
        return len(keywords) > 0
    
    def _check_suspicious_activity_condition(self, conditions: Dict) -> bool:
        """فحص شرط النشاط المشبوه"""
        # محاكاة كشف النشاط المشبوه
        import random
        return random.random() < 0.05  # 5% احتمال نشاط مشبوه
    
    def _execute_rule_actions(self, rule: Dict):
        """تنفيذ إجراءات قاعدة التنبيه"""
        actions = rule['actions']
        
        # إنشاء تنبيه
        alert = SmartAlert(
            alert_id=f"rule_{rule['rule_id']}_{int(time.time())}",
            device_id=self.device_id,
            alert_type=AlertType(rule['rule_type']),
            priority=AlertPriority(rule['priority']),
            title=f"تنبيه: {rule['rule_name']}",
            message=actions.get('message', f"تم تفعيل قاعدة {rule['rule_name']}"),
            timestamp=datetime.now().isoformat(),
            is_read=False,
            is_resolved=False,
            trigger_data={'rule_id': rule['rule_id'], 'rule_name': rule['rule_name']},
            actions_taken=[],
            metadata={'rule_generated': True}
        )
        
        # حفظ التنبيه
        self.db.insert_alert(alert)
        
        # تحديث وقت آخر تفعيل للقاعدة
        self._update_rule_last_triggered(rule['rule_id'])
        
        # إرسال الإشعارات
        if actions.get('send_notification', True):
            self._send_notifications(alert)
        
        logger.info(f"تم تنفيذ قاعدة التنبيه: {rule['rule_name']}")
    
    def _update_rule_last_triggered(self, rule_id: str):
        """تحديث وقت آخر تفعيل للقاعدة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE alert_rules 
            SET last_triggered = ?, trigger_count = trigger_count + 1
            WHERE rule_id = ?
        ''', (datetime.now().isoformat(), rule_id))
        
        conn.commit()
        conn.close()
    
    def _process_pending_alerts(self):
        """معالجة التنبيهات المعلقة"""
        # الحصول على التنبيهات غير المقروءة
        unread_alerts = self.db.get_alerts(self.device_id, limit=50)
        unread_alerts = [alert for alert in unread_alerts if not alert['is_read']]
        
        for alert_data in unread_alerts:
            # معالجة التنبيهات عالية الأولوية
            if alert_data['priority'] in ['high', 'critical']:
                self._handle_high_priority_alert(alert_data)
    
    def _handle_high_priority_alert(self, alert_data: Dict):
        """معالجة التنبيهات عالية الأولوية"""
        # إرسال إشعارات إضافية للتنبيهات المهمة
        logger.warning(f"تنبيه عالي الأولوية: {alert_data['title']}")
        
        # يمكن إضافة منطق إضافي هنا مثل:
        # - إرسال رسائل SMS
        # - إرسال إيميلات
        # - تفعيل إنذارات صوتية
    
    def _send_notifications(self, alert: SmartAlert):
        """إرسال الإشعارات"""
        # إرسال إشعار push
        if self.notification_channels['push']['enabled']:
            self._send_push_notification(alert)
        
        # إرسال إيميل
        if self.notification_channels['email']['enabled'] and self.notification_channels['email']['address']:
            self._send_email_notification(alert)
        
        # إرسال SMS
        if self.notification_channels['sms']['enabled'] and self.notification_channels['sms']['phone']:
            self._send_sms_notification(alert)
        
        # إرسال Telegram
        if self.notification_channels['telegram']['enabled'] and self.notification_channels['telegram']['chat_id']:
            self._send_telegram_notification(alert)
    
    def _send_push_notification(self, alert: SmartAlert):
        """إرسال إشعار push"""
        logger.info(f"إرسال إشعار push: {alert.title}")
        # في التطبيق الحقيقي، سيتم استخدام خدمة push notifications
    
    def _send_email_notification(self, alert: SmartAlert):
        """إرسال إشعار إيميل"""
        logger.info(f"إرسال إيميل: {alert.title}")
        # في التطبيق الحقيقي، سيتم استخدام SMTP
    
    def _send_sms_notification(self, alert: SmartAlert):
        """إرسال إشعار SMS"""
        logger.info(f"إرسال SMS: {alert.title}")
        # في التطبيق الحقيقي، سيتم استخدام خدمة SMS
    
    def _send_telegram_notification(self, alert: SmartAlert):
        """إرسال إشعار Telegram"""
        logger.info(f"إرسال Telegram: {alert.title}")
        # في التطبيق الحقيقي، سيتم استخدام Telegram Bot API

class GeoFencingCore:
    """النواة الأساسية لنظام Geo-Fencing والتنبيهات الذكية"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.db = GeoFencingDatabase()
        self.location_tracker = LocationTracker(device_id, self.db)
        self.alert_engine = SmartAlertEngine(device_id, self.db)
        
        self.is_active = False
    
    def start_system(self):
        """بدء النظام الكامل"""
        self.is_active = True
        
        # بدء تتبع الموقع
        self.location_tracker.start_tracking()
        
        # بدء محرك التنبيهات
        self.alert_engine.start_engine()
        
        logger.info("تم بدء نظام Geo-Fencing والتنبيهات الذكية")
    
    def stop_system(self):
        """إيقاف النظام الكامل"""
        self.is_active = False
        
        # إيقاف تتبع الموقع
        self.location_tracker.stop_tracking()
        
        # إيقاف محرك التنبيهات
        self.alert_engine.stop_engine()
        
        logger.info("تم إيقاف نظام Geo-Fencing والتنبيهات الذكية")
    
    def create_geo_fence(self, name: str, description: str, center_lat: float, 
                        center_lng: float, radius_meters: float, fence_type: str = 'safe_zone') -> str:
        """إنشاء منطقة جغرافية جديدة"""
        fence_id = f"fence_{self.device_id}_{int(time.time())}"
        
        fence = GeoFence(
            fence_id=fence_id,
            device_id=self.device_id,
            name=name,
            description=description,
            center_lat=center_lat,
            center_lng=center_lng,
            radius_meters=radius_meters,
            fence_type=fence_type,
            is_active=True,
            entry_alert=True,
            exit_alert=True,
            created_at=datetime.now().isoformat(),
            metadata={}
        )
        
        self.db.insert_geo_fence(fence)
        
        # تحديث قائمة المناطق في المتتبع
        self.location_tracker.geo_fences = self.db.get_geo_fences(self.device_id)
        
        logger.info(f"تم إنشاء منطقة جغرافية جديدة: {name}")
        return fence_id
    
    def create_alert_rule(self, rule_name: str, rule_type: str, conditions: Dict, 
                         actions: Dict, priority: str = 'medium') -> str:
        """إنشاء قاعدة تنبيه جديدة"""
        rule_id = f"rule_{self.device_id}_{int(time.time())}"
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alert_rules 
            (rule_id, device_id, rule_name, rule_type, conditions, actions, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            rule_id, self.device_id, rule_name, rule_type,
            json.dumps(conditions, ensure_ascii=False),
            json.dumps(actions, ensure_ascii=False),
            priority
        ))
        
        conn.commit()
        conn.close()
        
        # إعادة تحميل القواعد
        self.alert_engine._load_alert_rules()
        
        logger.info(f"تم إنشاء قاعدة تنبيه جديدة: {rule_name}")
        return rule_id

class GeoFencingAPI:
    """واجهة برمجة التطبيقات لنظام Geo-Fencing والتنبيهات الذكية"""
    
    def __init__(self, device_id: str):
        self.geo_system = GeoFencingCore(device_id)
    
    def start_monitoring(self) -> Dict:
        """بدء المراقبة"""
        self.geo_system.start_system()
        return {"status": "started", "message": "تم بدء نظام Geo-Fencing والتنبيهات الذكية"}
    
    def stop_monitoring(self) -> Dict:
        """إيقاف المراقبة"""
        self.geo_system.stop_system()
        return {"status": "stopped", "message": "تم إيقاف نظام Geo-Fencing والتنبيهات الذكية"}
    
    def create_geo_fence(self, name: str, description: str, center_lat: float, 
                        center_lng: float, radius_meters: float, fence_type: str = 'safe_zone') -> Dict:
        """إنشاء منطقة جغرافية"""
        fence_id = self.geo_system.create_geo_fence(name, description, center_lat, center_lng, radius_meters, fence_type)
        return {
            "status": "created",
            "fence_id": fence_id,
            "message": f"تم إنشاء منطقة جغرافية: {name}"
        }
    
    def get_geo_fences(self) -> List[Dict]:
        """الحصول على المناطق الجغرافية"""
        return self.geo_system.db.get_geo_fences(self.geo_system.device_id)
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """الحصول على التنبيهات"""
        return self.geo_system.db.get_alerts(self.geo_system.device_id, limit)
    
    def get_location_history(self, limit: int = 100) -> List[Dict]:
        """الحصول على تاريخ المواقع"""
        conn = sqlite3.connect(self.geo_system.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM location_points 
            WHERE device_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (self.geo_system.device_id, limit))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        """الحصول على الإحصائيات"""
        conn = sqlite3.connect(self.geo_system.db.db_path)
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute('SELECT COUNT(*) FROM geo_fences WHERE device_id = ? AND is_active = 1', (self.geo_system.device_id,))
        total_fences = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM smart_alerts WHERE device_id = ?', (self.geo_system.device_id,))
        total_alerts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM smart_alerts WHERE device_id = ? AND is_read = 0', (self.geo_system.device_id,))
        unread_alerts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM location_points WHERE device_id = ?', (self.geo_system.device_id,))
        total_locations = cursor.fetchone()[0]
        
        # إحصائيات اليوم
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT distance_traveled_km, max_speed_kmh, fence_violations, alerts_generated
            FROM location_statistics 
            WHERE device_id = ? AND date = ?
        ''', (self.geo_system.device_id, today))
        
        today_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_geo_fences': total_fences,
            'total_alerts': total_alerts,
            'unread_alerts': unread_alerts,
            'total_locations': total_locations,
            'today_distance_km': today_stats[0] if today_stats else 0,
            'today_max_speed': today_stats[1] if today_stats else 0,
            'today_fence_violations': today_stats[2] if today_stats else 0,
            'today_alerts': today_stats[3] if today_stats else 0,
            'system_active': self.geo_system.is_active
        }

# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مثيل من نظام Geo-Fencing
    device_id = "test_device_001"
    geo_api = GeoFencingAPI(device_id)
    
    # بدء النظام
    print("بدء نظام Geo-Fencing والتنبيهات الذكية...")
    result = geo_api.start_monitoring()
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # إنشاء منطقة جغرافية (المنزل)
    print("إنشاء منطقة جغرافية للمنزل...")
    fence_result = geo_api.create_geo_fence(
        name="المنزل",
        description="منطقة المنزل الآمنة",
        center_lat=24.7136,
        center_lng=46.6753,
        radius_meters=100,
        fence_type="home_zone"
    )
    print(f"النتيجة: {json.dumps(fence_result, ensure_ascii=False, indent=2)}")
    
    # إنشاء منطقة جغرافية (العمل)
    print("إنشاء منطقة جغرافية للعمل...")
    work_fence = geo_api.create_geo_fence(
        name="مكان العمل",
        description="منطقة العمل",
        center_lat=24.7500,
        center_lng=46.7000,
        radius_meters=200,
        fence_type="work_zone"
    )
    print(f"النتيجة: {json.dumps(work_fence, ensure_ascii=False, indent=2)}")
    
    # انتظار لمحاكاة النشاط
    print("انتظار لمحاكاة النشاط...")
    time.sleep(10)
    
    # الحصول على الإحصائيات
    stats = geo_api.get_statistics()
    print(f"الإحصائيات: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # الحصول على التنبيهات
    alerts = geo_api.get_alerts(limit=5)
    print(f"التنبيهات: {json.dumps(alerts, ensure_ascii=False, indent=2)}")
    
    # إيقاف النظام
    result = geo_api.stop_monitoring()
    print(f"إيقاف النظام: {json.dumps(result, ensure_ascii=False, indent=2)}")

