#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام مراقبة التطبيقات الاجتماعية المتقدم
Advanced Social Media Monitoring System
"""

import os
import json
import time
import sqlite3
import threading
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import base64
from dataclasses import dataclass, asdict
import logging
from urllib.parse import urlparse
import mimetypes

# إعداد نظام السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SocialMediaMessage:
    """فئة لتمثيل رسالة من تطبيق اجتماعي"""
    message_id: str
    device_id: str
    app_name: str
    app_package: str
    sender_name: str
    sender_id: str
    recipient_name: str
    recipient_id: str
    message_type: str  # 'text', 'image', 'video', 'audio', 'file', 'location'
    content: str
    media_path: str
    timestamp: str
    is_incoming: bool
    is_group: bool
    group_name: str
    group_id: str
    message_status: str  # 'sent', 'delivered', 'read', 'deleted'
    metadata: Dict

@dataclass
class SocialMediaNotification:
    """فئة لتمثيل إشعار من تطبيق اجتماعي"""
    notification_id: str
    device_id: str
    app_name: str
    app_package: str
    title: str
    content: str
    timestamp: str
    action_type: str  # 'message', 'call', 'post', 'story', 'like', 'comment'
    sender_info: Dict
    metadata: Dict

class SocialMediaDatabase:
    """مدير قاعدة بيانات مراقبة التطبيقات الاجتماعية"""
    
    def __init__(self, db_path: str = "social_media_monitor.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول الرسائل الاجتماعية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                app_name TEXT NOT NULL,
                app_package TEXT NOT NULL,
                sender_name TEXT,
                sender_id TEXT,
                recipient_name TEXT,
                recipient_id TEXT,
                message_type TEXT DEFAULT 'text',
                content TEXT,
                media_path TEXT,
                timestamp DATETIME NOT NULL,
                is_incoming BOOLEAN DEFAULT 1,
                is_group BOOLEAN DEFAULT 0,
                group_name TEXT,
                group_id TEXT,
                message_status TEXT DEFAULT 'sent',
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الإشعارات الاجتماعية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                app_name TEXT NOT NULL,
                app_package TEXT NOT NULL,
                title TEXT,
                content TEXT,
                timestamp DATETIME NOT NULL,
                action_type TEXT,
                sender_info TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول جهات الاتصال الاجتماعية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                app_package TEXT NOT NULL,
                contact_id TEXT NOT NULL,
                contact_name TEXT,
                phone_number TEXT,
                profile_picture TEXT,
                status_message TEXT,
                last_seen DATETIME,
                is_online BOOLEAN DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                last_message_time DATETIME,
                contact_type TEXT DEFAULT 'individual',
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, app_package, contact_id)
            )
        ''')
        
        # جدول المجموعات الاجتماعية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                app_package TEXT NOT NULL,
                group_id TEXT NOT NULL,
                group_name TEXT,
                group_description TEXT,
                admin_id TEXT,
                member_count INTEGER DEFAULT 0,
                group_picture TEXT,
                created_date DATETIME,
                last_activity DATETIME,
                total_messages INTEGER DEFAULT 0,
                group_type TEXT DEFAULT 'private',
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, app_package, group_id)
            )
        ''')
        
        # جدول الملفات الوسائط
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_media_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                app_package TEXT NOT NULL,
                message_id TEXT,
                file_path TEXT NOT NULL,
                file_name TEXT,
                file_type TEXT,
                file_size INTEGER DEFAULT 0,
                mime_type TEXT,
                thumbnail_path TEXT,
                download_url TEXT,
                is_downloaded BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول إعدادات المراقبة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                app_package TEXT NOT NULL,
                is_enabled BOOLEAN DEFAULT 1,
                monitor_messages BOOLEAN DEFAULT 1,
                monitor_calls BOOLEAN DEFAULT 1,
                monitor_media BOOLEAN DEFAULT 1,
                monitor_notifications BOOLEAN DEFAULT 1,
                auto_download_media BOOLEAN DEFAULT 1,
                max_file_size_mb INTEGER DEFAULT 50,
                keywords_filter TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, app_package)
            )
        ''')
        
        # جدول إحصائيات التطبيقات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                app_package TEXT NOT NULL,
                date DATE NOT NULL,
                messages_count INTEGER DEFAULT 0,
                media_files_count INTEGER DEFAULT 0,
                notifications_count INTEGER DEFAULT 0,
                active_time_minutes INTEGER DEFAULT 0,
                data_usage_mb REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, app_package, date)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # إدراج إعدادات افتراضية للتطبيقات الشائعة
        self._insert_default_app_settings()
    
    def _insert_default_app_settings(self):
        """إدراج إعدادات افتراضية للتطبيقات الاجتماعية الشائعة"""
        default_apps = [
            ("com.whatsapp", "WhatsApp"),
            ("org.telegram.messenger", "Telegram"),
            ("com.instagram.android", "Instagram"),
            ("com.facebook.katana", "Facebook"),
            ("com.facebook.orca", "Messenger"),
            ("com.snapchat.android", "Snapchat"),
            ("com.twitter.android", "Twitter"),
            ("com.linkedin.android", "LinkedIn"),
            ("com.viber.voip", "Viber"),
            ("com.skype.raider", "Skype"),
            ("com.discord", "Discord"),
            ("com.zhiliaoapp.musically", "TikTok")
        ]
        
        # هذه الدالة ستُستدعى عند إضافة جهاز جديد
        # لا نقوم بإدراج البيانات هنا لتجنب التكرار
    
    def insert_message(self, message: SocialMediaMessage):
        """إدراج رسالة اجتماعية جديدة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO social_messages 
            (message_id, device_id, app_name, app_package, sender_name, sender_id,
             recipient_name, recipient_id, message_type, content, media_path, timestamp,
             is_incoming, is_group, group_name, group_id, message_status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            message.message_id, message.device_id, message.app_name, message.app_package,
            message.sender_name, message.sender_id, message.recipient_name, message.recipient_id,
            message.message_type, message.content, message.media_path, message.timestamp,
            message.is_incoming, message.is_group, message.group_name, message.group_id,
            message.message_status, json.dumps(message.metadata, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def insert_notification(self, notification: SocialMediaNotification):
        """إدراج إشعار اجتماعي جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO social_notifications 
            (notification_id, device_id, app_name, app_package, title, content,
             timestamp, action_type, sender_info, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            notification.notification_id, notification.device_id, notification.app_name,
            notification.app_package, notification.title, notification.content,
            notification.timestamp, notification.action_type,
            json.dumps(notification.sender_info, ensure_ascii=False),
            json.dumps(notification.metadata, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def get_messages(self, device_id: str = None, app_package: str = None, limit: int = 100) -> List[Dict]:
        """استرجاع الرسائل الاجتماعية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM social_messages"
        params = []
        conditions = []
        
        if device_id:
            conditions.append("device_id = ?")
            params.append(device_id)
        
        if app_package:
            conditions.append("app_package = ?")
            params.append(app_package)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results

class MessageExtractor:
    """مستخرج الرسائل من التطبيقات الاجتماعية"""
    
    def __init__(self, device_id: str, db: SocialMediaDatabase):
        self.device_id = device_id
        self.db = db
        self.app_handlers = {
            'com.whatsapp': self._extract_whatsapp_messages,
            'org.telegram.messenger': self._extract_telegram_messages,
            'com.instagram.android': self._extract_instagram_messages,
            'com.facebook.katana': self._extract_facebook_messages,
            'com.facebook.orca': self._extract_messenger_messages,
            'com.snapchat.android': self._extract_snapchat_messages
        }
    
    def extract_messages_from_app(self, app_package: str) -> List[SocialMediaMessage]:
        """استخراج الرسائل من تطبيق محدد"""
        if app_package in self.app_handlers:
            return self.app_handlers[app_package]()
        else:
            return self._extract_generic_messages(app_package)
    
    def _extract_whatsapp_messages(self) -> List[SocialMediaMessage]:
        """استخراج رسائل WhatsApp"""
        messages = []
        
        # في التطبيق الحقيقي، سيتم الوصول إلى قاعدة بيانات WhatsApp
        # هنا نقوم بمحاكاة استخراج الرسائل
        
        sample_messages = [
            {
                'sender': 'أحمد محمد',
                'content': 'مرحبا، كيف حالك؟',
                'timestamp': datetime.now() - timedelta(minutes=5),
                'is_group': False
            },
            {
                'sender': 'فاطمة علي',
                'content': 'هل يمكنك الحضور للاجتماع غداً؟',
                'timestamp': datetime.now() - timedelta(minutes=15),
                'is_group': False
            },
            {
                'sender': 'مجموعة العمل',
                'content': 'تم تحديث المشروع',
                'timestamp': datetime.now() - timedelta(minutes=30),
                'is_group': True
            }
        ]
        
        for i, msg_data in enumerate(sample_messages):
            message = SocialMediaMessage(
                message_id=f"whatsapp_{self.device_id}_{int(time.time())}_{i}",
                device_id=self.device_id,
                app_name="WhatsApp",
                app_package="com.whatsapp",
                sender_name=msg_data['sender'],
                sender_id=f"sender_{i}",
                recipient_name="أنت",
                recipient_id="self",
                message_type="text",
                content=msg_data['content'],
                media_path="",
                timestamp=msg_data['timestamp'].isoformat(),
                is_incoming=True,
                is_group=msg_data['is_group'],
                group_name=msg_data['sender'] if msg_data['is_group'] else "",
                group_id=f"group_{i}" if msg_data['is_group'] else "",
                message_status="delivered",
                metadata={"app_version": "2.23.20.0", "encryption": "end_to_end"}
            )
            messages.append(message)
        
        return messages
    
    def _extract_telegram_messages(self) -> List[SocialMediaMessage]:
        """استخراج رسائل Telegram"""
        messages = []
        
        sample_messages = [
            {
                'sender': 'محمد الأحمد',
                'content': 'شاهد هذا الفيديو الرائع!',
                'timestamp': datetime.now() - timedelta(minutes=10),
                'type': 'video'
            },
            {
                'sender': 'قناة الأخبار',
                'content': 'آخر الأخبار: تطورات جديدة في التكنولوجيا',
                'timestamp': datetime.now() - timedelta(hours=1),
                'type': 'text'
            }
        ]
        
        for i, msg_data in enumerate(sample_messages):
            message = SocialMediaMessage(
                message_id=f"telegram_{self.device_id}_{int(time.time())}_{i}",
                device_id=self.device_id,
                app_name="Telegram",
                app_package="org.telegram.messenger",
                sender_name=msg_data['sender'],
                sender_id=f"telegram_user_{i}",
                recipient_name="أنت",
                recipient_id="self",
                message_type=msg_data['type'],
                content=msg_data['content'],
                media_path=f"telegram_media_{i}.mp4" if msg_data['type'] == 'video' else "",
                timestamp=msg_data['timestamp'].isoformat(),
                is_incoming=True,
                is_group=False,
                group_name="",
                group_id="",
                message_status="read",
                metadata={"app_version": "10.2.0", "chat_type": "private"}
            )
            messages.append(message)
        
        return messages
    
    def _extract_instagram_messages(self) -> List[SocialMediaMessage]:
        """استخراج رسائل Instagram"""
        messages = []
        
        sample_messages = [
            {
                'sender': 'sara_photo',
                'content': 'أعجبني منشورك الأخير! 😍',
                'timestamp': datetime.now() - timedelta(minutes=20),
                'type': 'text'
            },
            {
                'sender': 'travel_blogger',
                'content': '',
                'timestamp': datetime.now() - timedelta(hours=2),
                'type': 'image'
            }
        ]
        
        for i, msg_data in enumerate(sample_messages):
            message = SocialMediaMessage(
                message_id=f"instagram_{self.device_id}_{int(time.time())}_{i}",
                device_id=self.device_id,
                app_name="Instagram",
                app_package="com.instagram.android",
                sender_name=msg_data['sender'],
                sender_id=f"ig_user_{i}",
                recipient_name="أنت",
                recipient_id="self",
                message_type=msg_data['type'],
                content=msg_data['content'],
                media_path=f"instagram_image_{i}.jpg" if msg_data['type'] == 'image' else "",
                timestamp=msg_data['timestamp'].isoformat(),
                is_incoming=True,
                is_group=False,
                group_name="",
                group_id="",
                message_status="seen",
                metadata={"app_version": "300.0.0", "message_type": "direct"}
            )
            messages.append(message)
        
        return messages
    
    def _extract_facebook_messages(self) -> List[SocialMediaMessage]:
        """استخراج رسائل Facebook"""
        return self._extract_generic_messages("com.facebook.katana", "Facebook")
    
    def _extract_messenger_messages(self) -> List[SocialMediaMessage]:
        """استخراج رسائل Messenger"""
        return self._extract_generic_messages("com.facebook.orca", "Messenger")
    
    def _extract_snapchat_messages(self) -> List[SocialMediaMessage]:
        """استخراج رسائل Snapchat"""
        return self._extract_generic_messages("com.snapchat.android", "Snapchat")
    
    def _extract_generic_messages(self, app_package: str, app_name: str = None) -> List[SocialMediaMessage]:
        """استخراج رسائل عام لأي تطبيق"""
        messages = []
        
        if not app_name:
            app_name = app_package.split('.')[-1].title()
        
        # محاكاة رسائل عامة
        sample_message = SocialMediaMessage(
            message_id=f"{app_package}_{self.device_id}_{int(time.time())}",
            device_id=self.device_id,
            app_name=app_name,
            app_package=app_package,
            sender_name="مستخدم",
            sender_id="generic_user",
            recipient_name="أنت",
            recipient_id="self",
            message_type="text",
            content=f"رسالة من {app_name}",
            media_path="",
            timestamp=datetime.now().isoformat(),
            is_incoming=True,
            is_group=False,
            group_name="",
            group_id="",
            message_status="delivered",
            metadata={"extraction_method": "generic"}
        )
        messages.append(sample_message)
        
        return messages

class NotificationMonitor:
    """مراقب الإشعارات للتطبيقات الاجتماعية"""
    
    def __init__(self, device_id: str, db: SocialMediaDatabase):
        self.device_id = device_id
        self.db = db
        self.is_monitoring = False
        self.monitor_thread = None
        self.notification_queue = []
    
    def start_monitoring(self):
        """بدء مراقبة الإشعارات"""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("بدء مراقبة الإشعارات الاجتماعية")
    
    def stop_monitoring(self):
        """إيقاف مراقبة الإشعارات"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("تم إيقاف مراقبة الإشعارات")
    
    def _monitor_worker(self):
        """عامل مراقبة الإشعارات"""
        while self.is_monitoring:
            try:
                # محاكاة استلام إشعارات
                notifications = self._capture_notifications()
                
                for notification in notifications:
                    self._process_notification(notification)
                
                time.sleep(5)  # فحص كل 5 ثوانٍ
                
            except Exception as e:
                logger.error(f"خطأ في مراقبة الإشعارات: {e}")
                time.sleep(10)
    
    def _capture_notifications(self) -> List[Dict]:
        """التقاط الإشعارات الجديدة"""
        # في التطبيق الحقيقي، سيتم الوصول إلى نظام الإشعارات
        # هنا نقوم بمحاكاة إشعارات عشوائية
        
        import random
        
        if random.random() < 0.3:  # 30% احتمال وجود إشعار جديد
            sample_notifications = [
                {
                    'app_package': 'com.whatsapp',
                    'app_name': 'WhatsApp',
                    'title': 'رسالة جديدة',
                    'content': 'أحمد: مرحبا، كيف حالك؟',
                    'action_type': 'message'
                },
                {
                    'app_package': 'com.instagram.android',
                    'app_name': 'Instagram',
                    'title': 'إعجاب جديد',
                    'content': 'أعجب sara_photo بمنشورك',
                    'action_type': 'like'
                },
                {
                    'app_package': 'org.telegram.messenger',
                    'app_name': 'Telegram',
                    'title': 'قناة الأخبار',
                    'content': 'منشور جديد في القناة',
                    'action_type': 'post'
                }
            ]
            
            return [random.choice(sample_notifications)]
        
        return []
    
    def _process_notification(self, notification_data: Dict):
        """معالجة إشعار واحد"""
        notification = SocialMediaNotification(
            notification_id=f"notif_{self.device_id}_{int(time.time())}_{hash(notification_data['content'])}",
            device_id=self.device_id,
            app_name=notification_data['app_name'],
            app_package=notification_data['app_package'],
            title=notification_data['title'],
            content=notification_data['content'],
            timestamp=datetime.now().isoformat(),
            action_type=notification_data['action_type'],
            sender_info={'name': 'مجهول', 'id': 'unknown'},
            metadata={'captured_method': 'notification_listener'}
        )
        
        # حفظ الإشعار في قاعدة البيانات
        self.db.insert_notification(notification)
        
        logger.info(f"تم التقاط إشعار من {notification.app_name}: {notification.content}")

class MediaDownloader:
    """منزل الملفات الوسائط من التطبيقات الاجتماعية"""
    
    def __init__(self, device_id: str, db: SocialMediaDatabase):
        self.device_id = device_id
        self.db = db
        self.download_dir = f"social_media/{device_id}"
        os.makedirs(self.download_dir, exist_ok=True)
    
    def download_media_file(self, message: SocialMediaMessage, download_url: str = None) -> Optional[str]:
        """تنزيل ملف وسائط"""
        if not message.media_path and not download_url:
            return None
        
        try:
            # تحديد نوع الملف
            file_extension = self._get_file_extension(message.message_type)
            
            # إنشاء اسم الملف
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{message.app_package}_{message.message_id}_{timestamp}{file_extension}"
            file_path = os.path.join(self.download_dir, filename)
            
            # محاكاة تنزيل الملف
            if download_url:
                # في التطبيق الحقيقي، سيتم تنزيل الملف من الرابط
                self._simulate_download(download_url, file_path)
            else:
                # نسخ الملف من مسار محلي
                self._copy_local_file(message.media_path, file_path)
            
            # حفظ معلومات الملف في قاعدة البيانات
            self._save_media_info(message, file_path)
            
            return file_path
            
        except Exception as e:
            logger.error(f"خطأ في تنزيل الملف: {e}")
            return None
    
    def _get_file_extension(self, message_type: str) -> str:
        """تحديد امتداد الملف حسب نوع الرسالة"""
        extensions = {
            'image': '.jpg',
            'video': '.mp4',
            'audio': '.mp3',
            'document': '.pdf',
            'file': '.bin'
        }
        return extensions.get(message_type, '.bin')
    
    def _simulate_download(self, url: str, file_path: str):
        """محاكاة تنزيل ملف من رابط"""
        # في التطبيق الحقيقي، سيتم استخدام requests لتنزيل الملف
        import random
        
        # إنشاء ملف وهمي
        with open(file_path, 'wb') as f:
            # كتابة بيانات وهمية
            data = bytes([random.randint(0, 255) for _ in range(1024 * 10)])  # 10KB
            f.write(data)
        
        logger.info(f"تم تنزيل الملف: {file_path}")
    
    def _copy_local_file(self, source_path: str, dest_path: str):
        """نسخ ملف محلي"""
        try:
            # في التطبيق الحقيقي، سيتم نسخ الملف الفعلي
            # هنا نقوم بإنشاء ملف وهمي
            with open(dest_path, 'w') as f:
                f.write(f"Simulated media file from {source_path}")
            
            logger.info(f"تم نسخ الملف: {dest_path}")
        except Exception as e:
            logger.error(f"خطأ في نسخ الملف: {e}")
    
    def _save_media_info(self, message: SocialMediaMessage, file_path: str):
        """حفظ معلومات الملف في قاعدة البيانات"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        mime_type, _ = mimetypes.guess_type(file_path)
        
        cursor.execute('''
            INSERT INTO social_media_files 
            (file_id, device_id, app_package, message_id, file_path, file_name,
             file_type, file_size, mime_type, is_downloaded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"file_{message.message_id}_{int(time.time())}",
            self.device_id,
            message.app_package,
            message.message_id,
            file_path,
            os.path.basename(file_path),
            message.message_type,
            file_size,
            mime_type,
            True
        ))
        
        conn.commit()
        conn.close()

class SocialMediaMonitorCore:
    """النواة الأساسية لنظام مراقبة التطبيقات الاجتماعية"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.db = SocialMediaDatabase()
        self.message_extractor = MessageExtractor(device_id, self.db)
        self.notification_monitor = NotificationMonitor(device_id, self.db)
        self.media_downloader = MediaDownloader(device_id, self.db)
        
        self.is_monitoring = False
        self.monitor_thread = None
        
        # تحميل إعدادات المراقبة
        self.settings = self._load_monitoring_settings()
    
    def _load_monitoring_settings(self) -> Dict[str, Dict]:
        """تحميل إعدادات المراقبة لكل تطبيق"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT app_package, is_enabled, monitor_messages, monitor_calls,
                   monitor_media, monitor_notifications, auto_download_media,
                   max_file_size_mb, keywords_filter
            FROM monitoring_settings 
            WHERE device_id = ?
        ''', (self.device_id,))
        
        settings = {}
        for row in cursor.fetchall():
            app_package = row[0]
            settings[app_package] = {
                'is_enabled': bool(row[1]),
                'monitor_messages': bool(row[2]),
                'monitor_calls': bool(row[3]),
                'monitor_media': bool(row[4]),
                'monitor_notifications': bool(row[5]),
                'auto_download_media': bool(row[6]),
                'max_file_size_mb': row[7],
                'keywords_filter': row[8] or ""
            }
        
        conn.close()
        return settings
    
    def start_monitoring(self):
        """بدء مراقبة التطبيقات الاجتماعية"""
        self.is_monitoring = True
        
        # بدء مراقبة الإشعارات
        self.notification_monitor.start_monitoring()
        
        # بدء خيط المراقبة الرئيسي
        self.monitor_thread = threading.Thread(target=self._monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("بدء مراقبة التطبيقات الاجتماعية")
    
    def stop_monitoring(self):
        """إيقاف مراقبة التطبيقات الاجتماعية"""
        self.is_monitoring = False
        
        # إيقاف مراقبة الإشعارات
        self.notification_monitor.stop_monitoring()
        
        # انتظار انتهاء خيط المراقبة
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        logger.info("تم إيقاف مراقبة التطبيقات الاجتماعية")
    
    def _monitor_worker(self):
        """عامل المراقبة الرئيسي"""
        while self.is_monitoring:
            try:
                # مراقبة كل تطبيق مفعل
                for app_package, app_settings in self.settings.items():
                    if app_settings['is_enabled']:
                        self._monitor_app(app_package, app_settings)
                
                # تحديث الإحصائيات
                self._update_daily_statistics()
                
                time.sleep(30)  # فحص كل 30 ثانية
                
            except Exception as e:
                logger.error(f"خطأ في مراقبة التطبيقات: {e}")
                time.sleep(60)
    
    def _monitor_app(self, app_package: str, settings: Dict):
        """مراقبة تطبيق واحد"""
        try:
            # استخراج الرسائل إذا كان مفعلاً
            if settings['monitor_messages']:
                messages = self.message_extractor.extract_messages_from_app(app_package)
                
                for message in messages:
                    # حفظ الرسالة
                    self.db.insert_message(message)
                    
                    # تنزيل الوسائط إذا كان مفعلاً
                    if settings['auto_download_media'] and message.media_path:
                        self.media_downloader.download_media_file(message)
                    
                    # فحص الكلمات المفتاحية
                    if settings['keywords_filter']:
                        self._check_keywords(message, settings['keywords_filter'])
            
        except Exception as e:
            logger.error(f"خطأ في مراقبة {app_package}: {e}")
    
    def _check_keywords(self, message: SocialMediaMessage, keywords_filter: str):
        """فحص الكلمات المفتاحية في الرسالة"""
        keywords = [kw.strip().lower() for kw in keywords_filter.split(',')]
        content_lower = message.content.lower()
        
        found_keywords = [kw for kw in keywords if kw in content_lower]
        
        if found_keywords:
            logger.warning(f"تم العثور على كلمات مفتاحية في {message.app_name}: {found_keywords}")
            
            # إضافة تنبيه للرسالة
            message.metadata['keywords_found'] = found_keywords
            message.metadata['alert_level'] = 'high'
    
    def _update_daily_statistics(self):
        """تحديث الإحصائيات اليومية"""
        today = datetime.now().date().isoformat()
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # حساب إحصائيات كل تطبيق
        for app_package in self.settings.keys():
            # عدد الرسائل اليوم
            cursor.execute('''
                SELECT COUNT(*) FROM social_messages 
                WHERE device_id = ? AND app_package = ? AND DATE(timestamp) = ?
            ''', (self.device_id, app_package, today))
            messages_count = cursor.fetchone()[0]
            
            # عدد الملفات الوسائط اليوم
            cursor.execute('''
                SELECT COUNT(*) FROM social_media_files 
                WHERE device_id = ? AND app_package = ? AND DATE(created_at) = ?
            ''', (self.device_id, app_package, today))
            media_count = cursor.fetchone()[0]
            
            # عدد الإشعارات اليوم
            cursor.execute('''
                SELECT COUNT(*) FROM social_notifications 
                WHERE device_id = ? AND app_package = ? AND DATE(timestamp) = ?
            ''', (self.device_id, app_package, today))
            notifications_count = cursor.fetchone()[0]
            
            # تحديث أو إدراج الإحصائيات
            cursor.execute('''
                INSERT OR REPLACE INTO app_statistics 
                (device_id, app_package, date, messages_count, media_files_count, notifications_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.device_id, app_package, today, messages_count, media_count, notifications_count))
        
        conn.commit()
        conn.close()

class SocialMediaMonitorAPI:
    """واجهة برمجة التطبيقات لنظام مراقبة التطبيقات الاجتماعية"""
    
    def __init__(self, device_id: str):
        self.monitor = SocialMediaMonitorCore(device_id)
    
    def start_monitoring(self) -> Dict:
        """بدء المراقبة"""
        self.monitor.start_monitoring()
        return {"status": "started", "message": "تم بدء مراقبة التطبيقات الاجتماعية"}
    
    def stop_monitoring(self) -> Dict:
        """إيقاف المراقبة"""
        self.monitor.stop_monitoring()
        return {"status": "stopped", "message": "تم إيقاف مراقبة التطبيقات الاجتماعية"}
    
    def get_messages(self, app_package: str = None, limit: int = 100) -> List[Dict]:
        """الحصول على الرسائل"""
        return self.monitor.db.get_messages(self.monitor.device_id, app_package, limit)
    
    def get_notifications(self, app_package: str = None, limit: int = 50) -> List[Dict]:
        """الحصول على الإشعارات"""
        conn = sqlite3.connect(self.monitor.db.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM social_notifications WHERE device_id = ?"
        params = [self.monitor.device_id]
        
        if app_package:
            query += " AND app_package = ?"
            params.append(app_package)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        """الحصول على الإحصائيات"""
        conn = sqlite3.connect(self.monitor.db.db_path)
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute('SELECT COUNT(*) FROM social_messages WHERE device_id = ?', (self.monitor.device_id,))
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM social_notifications WHERE device_id = ?', (self.monitor.device_id,))
        total_notifications = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM social_media_files WHERE device_id = ?', (self.monitor.device_id,))
        total_media_files = cursor.fetchone()[0]
        
        # إحصائيات اليوم
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM social_messages 
            WHERE device_id = ? AND DATE(timestamp) = ?
        ''', (self.monitor.device_id, today))
        today_messages = cursor.fetchone()[0]
        
        # إحصائيات حسب التطبيق
        cursor.execute('''
            SELECT app_package, COUNT(*) as count 
            FROM social_messages 
            WHERE device_id = ? 
            GROUP BY app_package 
            ORDER BY count DESC
        ''', (self.monitor.device_id,))
        
        app_stats = {}
        for row in cursor.fetchall():
            app_stats[row[0]] = row[1]
        
        conn.close()
        
        return {
            'total_messages': total_messages,
            'total_notifications': total_notifications,
            'total_media_files': total_media_files,
            'today_messages': today_messages,
            'app_statistics': app_stats,
            'monitoring_status': self.monitor.is_monitoring,
            'monitored_apps': list(self.monitor.settings.keys())
        }
    
    def update_app_settings(self, app_package: str, settings: Dict) -> Dict:
        """تحديث إعدادات مراقبة تطبيق"""
        conn = sqlite3.connect(self.monitor.db.db_path)
        cursor = conn.cursor()
        
        # تحديث الإعدادات في قاعدة البيانات
        cursor.execute('''
            INSERT OR REPLACE INTO monitoring_settings 
            (device_id, app_package, is_enabled, monitor_messages, monitor_calls,
             monitor_media, monitor_notifications, auto_download_media, max_file_size_mb, keywords_filter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.monitor.device_id, app_package,
            settings.get('is_enabled', True),
            settings.get('monitor_messages', True),
            settings.get('monitor_calls', True),
            settings.get('monitor_media', True),
            settings.get('monitor_notifications', True),
            settings.get('auto_download_media', True),
            settings.get('max_file_size_mb', 50),
            settings.get('keywords_filter', '')
        ))
        
        conn.commit()
        conn.close()
        
        # تحديث الإعدادات في الذاكرة
        if app_package not in self.monitor.settings:
            self.monitor.settings[app_package] = {}
        self.monitor.settings[app_package].update(settings)
        
        return {"status": "updated", "app_package": app_package}

# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مثيل من نظام مراقبة التطبيقات الاجتماعية
    device_id = "test_device_001"
    social_monitor_api = SocialMediaMonitorAPI(device_id)
    
    # بدء المراقبة
    print("بدء مراقبة التطبيقات الاجتماعية...")
    result = social_monitor_api.start_monitoring()
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # محاكاة فترة مراقبة
    time.sleep(10)
    
    # الحصول على الإحصائيات
    stats = social_monitor_api.get_statistics()
    print(f"الإحصائيات: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # الحصول على الرسائل
    messages = social_monitor_api.get_messages(limit=5)
    print(f"الرسائل: {json.dumps(messages, ensure_ascii=False, indent=2)}")
    
    # إيقاف المراقبة
    result = social_monitor_api.stop_monitoring()
    print(f"إيقاف المراقبة: {json.dumps(result, ensure_ascii=False, indent=2)}")

