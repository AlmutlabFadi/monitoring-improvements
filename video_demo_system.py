#!/usr/bin/env python3
"""
🎥 نظام العرض التوضيحي بالفيديو
Video Demonstration System
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import threading
import time
from datetime import datetime
import os

class VideoDemoSystem:
    """نظام العرض التوضيحي المتقدم"""
    
    def __init__(self):
        self.recording = False
        self.demo_scenarios = [
            {
                'name': 'مراقبة التطبيقات الاجتماعية',
                'duration': 30,
                'actions': ['whatsapp_monitoring', 'telegram_capture', 'instagram_tracking']
            },
            {
                'name': 'تسجيل المكالمات والصوت',
                'duration': 25,
                'actions': ['call_recording', 'audio_capture', 'voice_analysis']
            },
            {
                'name': 'التحكم عن بُعد والتخفي',
                'duration': 35,
                'actions': ['remote_control', 'stealth_activation', 'permission_bypass']
            }
        ]
        
        os.makedirs('static/videos', exist_ok=True)
    
    def create_demo_frame(self, scenario_name, action, timestamp):
        """إنشاء إطار عرض توضيحي"""
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        for i in range(1080):
            color_intensity = int(255 * (i / 1080))
            frame[i, :] = [color_intensity // 4, color_intensity // 6, color_intensity // 2]
        
        pil_frame = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_frame)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        draw.text((960, 200), scenario_name, font=title_font, fill=(0, 255, 136), anchor="mm")
        
        draw.text((960, 300), f"الإجراء الحالي: {action}", font=subtitle_font, fill=(255, 255, 255), anchor="mm")
        
        draw.text((960, 400), f"الوقت: {timestamp}", font=subtitle_font, fill=(200, 200, 200), anchor="mm")
        
        indicators = [
            "🟢 النظام نشط",
            "📱 الأجهزة متصلة: 8",
            "🔍 المراقبة فعالة",
            "🛡️ وضع التخفي مفعل"
        ]
        
        for i, indicator in enumerate(indicators):
            draw.text((100, 600 + i * 50), indicator, font=subtitle_font, fill=(0, 255, 136))
        
        features = [
            "📱 مراقبة التطبيقات الاجتماعية",
            "🎤 تسجيل المكالمات والصوت",
            "📸 التقاط الشاشة والكاميرا",
            "🌍 تتبع الموقع الجغرافي",
            "🔐 تشفير البيانات",
            "🥷 وضع التخفي المتقدم"
        ]
        
        for i, feature in enumerate(features):
            draw.text((1200, 600 + i * 50), feature, font=subtitle_font, fill=(255, 255, 255))
        
        return np.array(pil_frame)
    
    def generate_demo_video(self, scenario_index=0):
        """إنشاء فيديو عرض توضيحي"""
        scenario = self.demo_scenarios[scenario_index]
        
        output_path = f'static/videos/demo_{scenario["name"].replace(" ", "_")}.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, 30.0, (1920, 1080))
        
        total_frames = scenario['duration'] * 30  # 30 FPS
        frames_per_action = total_frames // len(scenario['actions'])
        
        for action_index, action in enumerate(scenario['actions']):
            for frame_num in range(frames_per_action):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                frame = self.create_demo_frame(scenario['name'], action, timestamp)
                
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame_bgr)
        
        out.release()
        return output_path
    
    def create_monitoring_demo(self):
        """إنشاء عرض توضيحي للمراقبة"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        frame[:] = [20, 30, 40]
        
        pil_frame = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_frame)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Title
        draw.text((640, 100), "نظام المراقبة الشامل", font=title_font, fill=(0, 255, 136), anchor="mm")
        
        features = [
            "✅ مراقبة التطبيقات الاجتماعية (واتساب، تليجرام، إنستغرام)",
            "✅ تسجيل المكالمات الصوتية والفيديو",
            "✅ التقاط لقطات الشاشة والكاميرا",
            "✅ تتبع الموقع الجغرافي المباشر",
            "✅ مراقبة المتصفحات (بما في ذلك المخفية)",
            "✅ التحكم المطلق في الجهاز",
            "✅ اعتراض المكالمات بدون اكتشاف",
            "✅ تحليل النشاطات الذكي",
            "✅ وضع التخفي العسكري",
            "✅ مقاومة الفورمات وإعادة الضبط"
        ]
        
        y_pos = 200
        for feature in features:
            draw.text((100, y_pos), feature, font=font, fill=(255, 255, 255))
            y_pos += 40
        
        output_path = 'static/monitoring_demo.png'
        pil_frame.save(output_path)
        return output_path
    
    def start_live_demo(self):
        """بدء العرض التوضيحي المباشر"""
        self.recording = True
        
        def demo_thread():
            scenario_index = 0
            while self.recording and scenario_index < len(self.demo_scenarios):
                video_path = self.generate_demo_video(scenario_index)
                print(f"Generated demo video: {video_path}")
                scenario_index += 1
                time.sleep(2)
        
        threading.Thread(target=demo_thread, daemon=True).start()
    
    def stop_demo(self):
        """إيقاف العرض التوضيحي"""
        self.recording = False

if __name__ == '__main__':
    demo_system = VideoDemoSystem()
    
    demo_image = demo_system.create_monitoring_demo()
    print(f"Created monitoring demo: {demo_image}")
    
    for i in range(len(demo_system.demo_scenarios)):
        video_path = demo_system.generate_demo_video(i)
        print(f"Generated video: {video_path}")
