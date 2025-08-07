#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام تسجيل المكالمات الصوتية المتقدم
Advanced Call Recording System
"""

import os
import json
import time
import sqlite3
import threading
import wave
import audioop
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
import base64
from dataclasses import dataclass, asdict
import logging

# إعداد نظام السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CallRecord:
    """فئة لتمثيل تسجيل مكالمة"""
    call_id: str
    device_id: str
    phone_number: str
    contact_name: str
    call_type: str  # 'incoming', 'outgoing', 'missed'
    start_time: str
    end_time: str
    duration: int  # بالثواني
    recording_path: str
    recording_size: int  # بالبايت
    audio_quality: str  # 'high', 'medium', 'low'
    is_encrypted: bool
    metadata: Dict

class CallRecorderDatabase:
    """مدير قاعدة بيانات تسجيل المكالمات"""
    
    def __init__(self, db_path: str = "call_recorder.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول المكالمات المسجلة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                contact_name TEXT,
                call_type TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                duration INTEGER DEFAULT 0,
                recording_path TEXT,
                recording_size INTEGER DEFAULT 0,
                audio_quality TEXT DEFAULT 'medium',
                is_encrypted BOOLEAN DEFAULT 0,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول جهات الاتصال
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                contact_name TEXT,
                contact_photo TEXT,
                last_call_time DATETIME,
                total_calls INTEGER DEFAULT 0,
                total_duration INTEGER DEFAULT 0,
                is_favorite BOOLEAN DEFAULT 0,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, phone_number)
            )
        ''')
        
        # جدول إعدادات التسجيل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recording_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                auto_record BOOLEAN DEFAULT 1,
                record_incoming BOOLEAN DEFAULT 1,
                record_outgoing BOOLEAN DEFAULT 1,
                audio_quality TEXT DEFAULT 'medium',
                max_duration INTEGER DEFAULT 3600,
                storage_limit_mb INTEGER DEFAULT 1000,
                auto_upload BOOLEAN DEFAULT 1,
                encryption_enabled BOOLEAN DEFAULT 1,
                delete_after_upload BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول إحصائيات التسجيل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recording_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                date DATE NOT NULL,
                total_calls INTEGER DEFAULT 0,
                recorded_calls INTEGER DEFAULT 0,
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
    
    def insert_call_record(self, record: CallRecord):
        """إدراج تسجيل مكالمة جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO call_recordings 
            (call_id, device_id, phone_number, contact_name, call_type, 
             start_time, end_time, duration, recording_path, recording_size,
             audio_quality, is_encrypted, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.call_id, record.device_id, record.phone_number, record.contact_name,
            record.call_type, record.start_time, record.end_time, record.duration,
            record.recording_path, record.recording_size, record.audio_quality,
            record.is_encrypted, json.dumps(record.metadata, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def get_call_recordings(self, device_id: str = None, limit: int = 100) -> List[Dict]:
        """استرجاع تسجيلات المكالمات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('''
                SELECT * FROM call_recordings 
                WHERE device_id = ? 
                ORDER BY start_time DESC 
                LIMIT ?
            ''', (device_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM call_recordings 
                ORDER BY start_time DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def update_contact(self, device_id: str, phone_number: str, contact_name: str):
        """تحديث معلومات جهة اتصال"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO contacts 
            (device_id, phone_number, contact_name, last_call_time, total_calls)
            VALUES (?, ?, ?, ?, 
                COALESCE((SELECT total_calls FROM contacts WHERE device_id = ? AND phone_number = ?), 0) + 1)
        ''', (device_id, phone_number, contact_name, datetime.now().isoformat(), device_id, phone_number))
        
        conn.commit()
        conn.close()

class AudioProcessor:
    """معالج الصوت المتقدم"""
    
    def __init__(self):
        self.sample_rate = 44100
        self.channels = 2
        self.sample_width = 2
        self.chunk_size = 1024
    
    def process_audio_chunk(self, audio_data: bytes, quality: str = 'medium') -> bytes:
        """معالجة قطعة صوتية"""
        try:
            # تحسين جودة الصوت حسب الإعداد
            if quality == 'high':
                # لا تغيير للجودة العالية
                return audio_data
            elif quality == 'medium':
                # ضغط متوسط
                return audioop.lin2lin(audio_data, self.sample_width, self.sample_width)
            else:  # low quality
                # ضغط عالي لتوفير المساحة
                compressed = audioop.ratecv(audio_data, self.sample_width, self.channels, 
                                          self.sample_rate, self.sample_rate // 2, None)[0]
                return compressed
        except Exception as e:
            logger.error(f"خطأ في معالجة الصوت: {e}")
            return audio_data
    
    def enhance_audio(self, audio_data: bytes) -> bytes:
        """تحسين جودة الصوت"""
        try:
            # تطبيق فلاتر تحسين الصوت
            # إزالة الضوضاء
            enhanced = audioop.mul(audio_data, self.sample_width, 1.2)
            
            # تطبيع مستوى الصوت
            max_amplitude = audioop.max(enhanced, self.sample_width)
            if max_amplitude > 0:
                factor = 32767 / max_amplitude
                enhanced = audioop.mul(enhanced, self.sample_width, factor * 0.8)
            
            return enhanced
        except Exception as e:
            logger.error(f"خطأ في تحسين الصوت: {e}")
            return audio_data
    
    def save_audio_file(self, audio_data: bytes, file_path: str, quality: str = 'medium'):
        """حفظ ملف صوتي"""
        try:
            with wave.open(file_path, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)
                
                # معالجة وتحسين الصوت قبل الحفظ
                processed_audio = self.process_audio_chunk(audio_data, quality)
                enhanced_audio = self.enhance_audio(processed_audio)
                
                wav_file.writeframes(enhanced_audio)
            
            logger.info(f"تم حفظ الملف الصوتي: {file_path}")
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ الملف الصوتي: {e}")
            return False

class CallRecorderCore:
    """النواة الأساسية لنظام تسجيل المكالمات"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.db = CallRecorderDatabase()
        self.audio_processor = AudioProcessor()
        self.is_recording = False
        self.current_call = None
        self.recording_thread = None
        self.audio_buffer = []
        
        # إعدادات التسجيل
        self.recordings_dir = f"recordings/{device_id}"
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # تحميل إعدادات الجهاز
        self.settings = self._load_device_settings()
    
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
                'auto_record': True,
                'record_incoming': True,
                'record_outgoing': True,
                'audio_quality': 'medium',
                'max_duration': 3600,
                'storage_limit_mb': 1000,
                'auto_upload': True,
                'encryption_enabled': True,
                'delete_after_upload': False
            }
            
            cursor.execute('''
                INSERT INTO recording_settings 
                (device_id, auto_record, record_incoming, record_outgoing, audio_quality,
                 max_duration, storage_limit_mb, auto_upload, encryption_enabled, delete_after_upload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                settings['device_id'], settings['auto_record'], settings['record_incoming'],
                settings['record_outgoing'], settings['audio_quality'], settings['max_duration'],
                settings['storage_limit_mb'], settings['auto_upload'], settings['encryption_enabled'],
                settings['delete_after_upload']
            ))
            conn.commit()
        
        conn.close()
        return settings
    
    def start_call_recording(self, phone_number: str, contact_name: str, call_type: str) -> str:
        """بدء تسجيل مكالمة"""
        if not self._should_record_call(call_type):
            logger.info(f"تم تخطي تسجيل المكالمة: {call_type}")
            return None
        
        # إنشاء معرف فريد للمكالمة
        call_id = self._generate_call_id(phone_number)
        
        # إنشاء سجل المكالمة
        self.current_call = CallRecord(
            call_id=call_id,
            device_id=self.device_id,
            phone_number=phone_number,
            contact_name=contact_name or "غير معروف",
            call_type=call_type,
            start_time=datetime.now().isoformat(),
            end_time="",
            duration=0,
            recording_path="",
            recording_size=0,
            audio_quality=self.settings['audio_quality'],
            is_encrypted=self.settings['encryption_enabled'],
            metadata={}
        )
        
        # بدء التسجيل
        self.is_recording = True
        self.audio_buffer = []
        
        # بدء خيط التسجيل
        self.recording_thread = threading.Thread(target=self._recording_worker)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        logger.info(f"بدء تسجيل المكالمة: {call_id}")
        return call_id
    
    def stop_call_recording(self) -> Optional[CallRecord]:
        """إيقاف تسجيل المكالمة"""
        if not self.is_recording or not self.current_call:
            return None
        
        self.is_recording = False
        
        # انتظار انتهاء خيط التسجيل
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)
        
        # حفظ التسجيل
        recording_path = self._save_recording()
        
        if recording_path:
            # تحديث معلومات المكالمة
            self.current_call.end_time = datetime.now().isoformat()
            self.current_call.duration = self._calculate_duration()
            self.current_call.recording_path = recording_path
            self.current_call.recording_size = os.path.getsize(recording_path) if os.path.exists(recording_path) else 0
            
            # حفظ في قاعدة البيانات
            self.db.insert_call_record(self.current_call)
            
            # تحديث معلومات جهة الاتصال
            self.db.update_contact(self.device_id, self.current_call.phone_number, self.current_call.contact_name)
            
            # تحديث الإحصائيات
            self._update_daily_stats()
            
            logger.info(f"تم حفظ تسجيل المكالمة: {self.current_call.call_id}")
            
            # رفع التسجيل إلى السحابة إذا كان مفعلاً
            if self.settings['auto_upload']:
                self._upload_recording(recording_path)
            
            completed_call = self.current_call
            self.current_call = None
            return completed_call
        
        return None
    
    def _should_record_call(self, call_type: str) -> bool:
        """تحديد ما إذا كان يجب تسجيل المكالمة"""
        if not self.settings['auto_record']:
            return False
        
        if call_type == 'incoming' and not self.settings['record_incoming']:
            return False
        
        if call_type == 'outgoing' and not self.settings['record_outgoing']:
            return False
        
        # فحص مساحة التخزين
        if self._get_storage_usage() > self.settings['storage_limit_mb']:
            logger.warning("تم تجاوز حد مساحة التخزين")
            return False
        
        return True
    
    def _generate_call_id(self, phone_number: str) -> str:
        """توليد معرف فريد للمكالمة"""
        timestamp = str(int(time.time()))
        phone_hash = hashlib.md5(phone_number.encode()).hexdigest()[:8]
        device_hash = hashlib.md5(self.device_id.encode()).hexdigest()[:8]
        return f"call_{device_hash}_{phone_hash}_{timestamp}"
    
    def _recording_worker(self):
        """عامل التسجيل في خيط منفصل"""
        start_time = time.time()
        max_duration = self.settings['max_duration']
        
        while self.is_recording and (time.time() - start_time) < max_duration:
            try:
                # محاكاة التقاط الصوت (في التطبيق الحقيقي، سيتم استخدام مكتبة تسجيل صوتي)
                audio_chunk = self._capture_audio_chunk()
                if audio_chunk:
                    self.audio_buffer.append(audio_chunk)
                
                time.sleep(0.1)  # 100ms chunks
                
            except Exception as e:
                logger.error(f"خطأ في التسجيل: {e}")
                break
    
    def _capture_audio_chunk(self) -> bytes:
        """التقاط قطعة صوتية (محاكاة)"""
        # في التطبيق الحقيقي، سيتم استخدام مكتبة مثل pyaudio أو sounddevice
        # هنا نقوم بمحاكاة بيانات صوتية
        import random
        chunk_size = 1024
        sample_data = bytes([random.randint(0, 255) for _ in range(chunk_size)])
        return sample_data
    
    def _save_recording(self) -> Optional[str]:
        """حفظ التسجيل الصوتي"""
        if not self.audio_buffer:
            return None
        
        # دمج جميع قطع الصوت
        combined_audio = b''.join(self.audio_buffer)
        
        # إنشاء مسار الملف
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.current_call.call_id}_{timestamp}.wav"
        file_path = os.path.join(self.recordings_dir, filename)
        
        # حفظ الملف
        success = self.audio_processor.save_audio_file(
            combined_audio, 
            file_path, 
            self.current_call.audio_quality
        )
        
        if success:
            # تشفير الملف إذا كان مفعلاً
            if self.current_call.is_encrypted:
                encrypted_path = self._encrypt_recording(file_path)
                if encrypted_path:
                    os.remove(file_path)  # حذف الملف غير المشفر
                    return encrypted_path
            
            return file_path
        
        return None
    
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
    
    def _calculate_duration(self) -> int:
        """حساب مدة المكالمة بالثواني"""
        if not self.current_call or not self.current_call.start_time:
            return 0
        
        start = datetime.fromisoformat(self.current_call.start_time)
        end = datetime.now()
        duration = (end - start).total_seconds()
        return int(duration)
    
    def _update_daily_stats(self):
        """تحديث الإحصائيات اليومية"""
        today = datetime.now().date().isoformat()
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # الحصول على الإحصائيات الحالية
        cursor.execute('''
            SELECT recorded_calls, total_duration, storage_used_mb 
            FROM recording_stats 
            WHERE device_id = ? AND date = ?
        ''', (self.device_id, today))
        
        result = cursor.fetchone()
        
        if result:
            recorded_calls, total_duration, storage_used = result
            new_recorded_calls = recorded_calls + 1
            new_total_duration = total_duration + self.current_call.duration
            new_storage_used = storage_used + (self.current_call.recording_size / (1024 * 1024))
            
            cursor.execute('''
                UPDATE recording_stats 
                SET recorded_calls = ?, total_duration = ?, storage_used_mb = ?
                WHERE device_id = ? AND date = ?
            ''', (new_recorded_calls, new_total_duration, new_storage_used, self.device_id, today))
        else:
            cursor.execute('''
                INSERT INTO recording_stats 
                (device_id, date, recorded_calls, total_duration, storage_used_mb)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.device_id, today, 1, self.current_call.duration,
                self.current_call.recording_size / (1024 * 1024)
            ))
        
        conn.commit()
        conn.close()
    
    def _get_storage_usage(self) -> float:
        """حساب استخدام مساحة التخزين بالميجابايت"""
        total_size = 0
        if os.path.exists(self.recordings_dir):
            for filename in os.listdir(self.recordings_dir):
                file_path = os.path.join(self.recordings_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        
        return total_size / (1024 * 1024)  # تحويل إلى ميجابايت
    
    def _upload_recording(self, file_path: str):
        """رفع التسجيل إلى السحابة"""
        # في التطبيق الحقيقي، سيتم رفع الملف إلى خدمة سحابية
        logger.info(f"رفع التسجيل إلى السحابة: {file_path}")
        
        # محاكاة عملية الرفع
        time.sleep(1)
        
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

class CallRecorderAPI:
    """واجهة برمجة التطبيقات لنظام تسجيل المكالمات"""
    
    def __init__(self, device_id: str):
        self.recorder = CallRecorderCore(device_id)
    
    def start_recording(self, phone_number: str, contact_name: str = "", call_type: str = "incoming") -> Dict:
        """بدء تسجيل مكالمة"""
        call_id = self.recorder.start_call_recording(phone_number, contact_name, call_type)
        return {
            "status": "started" if call_id else "skipped",
            "call_id": call_id,
            "message": "تم بدء التسجيل" if call_id else "تم تخطي التسجيل"
        }
    
    def stop_recording(self) -> Dict:
        """إيقاف تسجيل المكالمة"""
        completed_call = self.recorder.stop_call_recording()
        return {
            "status": "completed" if completed_call else "no_active_recording",
            "call_record": asdict(completed_call) if completed_call else None,
            "message": "تم حفظ التسجيل" if completed_call else "لا يوجد تسجيل نشط"
        }
    
    def get_recordings(self, limit: int = 50) -> List[Dict]:
        """الحصول على قائمة التسجيلات"""
        return self.recorder.db.get_call_recordings(self.recorder.device_id, limit)
    
    def get_recording_stats(self) -> Dict:
        """إحصائيات التسجيل"""
        conn = sqlite3.connect(self.recorder.db.db_path)
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute('SELECT COUNT(*) FROM call_recordings WHERE device_id = ?', (self.recorder.device_id,))
        total_recordings = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(duration) FROM call_recordings WHERE device_id = ?', (self.recorder.device_id,))
        total_duration = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(recording_size) FROM call_recordings WHERE device_id = ?', (self.recorder.device_id,))
        total_size = cursor.fetchone()[0] or 0
        
        # إحصائيات اليوم
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM call_recordings 
            WHERE device_id = ? AND DATE(start_time) = ?
        ''', (self.recorder.device_id, today))
        today_recordings = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_recordings': total_recordings,
            'total_duration_seconds': total_duration,
            'total_size_bytes': total_size,
            'today_recordings': today_recordings,
            'storage_usage_mb': self.recorder._get_storage_usage(),
            'settings': self.recorder.settings,
            'is_recording': self.recorder.is_recording,
            'current_call': asdict(self.recorder.current_call) if self.recorder.current_call else None
        }
    
    def update_settings(self, settings: Dict) -> Dict:
        """تحديث إعدادات التسجيل"""
        conn = sqlite3.connect(self.recorder.db.db_path)
        cursor = conn.cursor()
        
        # تحديث الإعدادات في قاعدة البيانات
        update_fields = []
        values = []
        
        for key, value in settings.items():
            if key in ['auto_record', 'record_incoming', 'record_outgoing', 'audio_quality',
                      'max_duration', 'storage_limit_mb', 'auto_upload', 'encryption_enabled', 'delete_after_upload']:
                update_fields.append(f"{key} = ?")
                values.append(value)
        
        if update_fields:
            values.append(self.recorder.device_id)
            cursor.execute(f'''
                UPDATE recording_settings 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE device_id = ?
            ''', values)
            
            conn.commit()
            
            # تحديث الإعدادات في الذاكرة
            self.recorder.settings.update(settings)
        
        conn.close()
        
        return {"status": "updated", "settings": self.recorder.settings}

# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مثيل من نظام تسجيل المكالمات
    device_id = "test_device_001"
    call_recorder_api = CallRecorderAPI(device_id)
    
    # بدء تسجيل مكالمة
    print("بدء تسجيل مكالمة...")
    result = call_recorder_api.start_recording("+966501234567", "أحمد محمد", "incoming")
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # محاكاة مدة المكالمة
    time.sleep(5)
    
    # إيقاف التسجيل
    print("إيقاف التسجيل...")
    result = call_recorder_api.stop_recording()
    print(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # الحصول على الإحصائيات
    stats = call_recorder_api.get_recording_stats()
    print(f"الإحصائيات: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # الحصول على قائمة التسجيلات
    recordings = call_recorder_api.get_recordings(10)
    print(f"التسجيلات: {json.dumps(recordings, ensure_ascii=False, indent=2)}")

