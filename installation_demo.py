#!/usr/bin/env python3
"""
📱 عرض توضيحي لطرق التثبيت المتقدمة
Advanced Installation Methods Demonstration
"""

import qrcode
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

class InstallationDemo:
    """عرض توضيحي لطرق التثبيت"""
    
    def __init__(self):
        self.server_url = "https://your-monitoring-server.com"
        self.encryption_key = os.getenv('MONITORING_ENCRYPTION_KEY', 'DEMO_KEY_PLACEHOLDER')
        
        os.makedirs('static', exist_ok=True)
    
    def generate_qr_demo(self):
        """إنشاء QR Code للعرض التوضيحي"""
        installation_data = {
            'server_url': self.server_url,
            'device_id': 'DEMO_DEVICE_001',
            'encryption_key': 'ENCRYPTED_KEY_PLACEHOLDER',
            'features': [
                'social_media_monitoring',
                'call_recording',
                'screen_capture',
                'stealth_mode',
                'auto_permissions'
            ],
            'installation_type': 'qr_code'
        }
        
        encoded_data = base64.b64encode(
            json.dumps(installation_data).encode()
        ).decode()
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(encoded_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        demo_frame = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(demo_frame)
        
        qr_img = qr_img.resize((300, 300))
        demo_frame.paste(qr_img, (250, 50))
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        draw.text((400, 380), "QR Code Installation", font=title_font, fill='black', anchor="mm")
        draw.text((400, 420), "1. Scan this QR code with target device", font=font, fill='black', anchor="mm")
        draw.text((400, 450), "2. Automatic download and installation", font=font, fill='black', anchor="mm")
        draw.text((400, 480), "3. Stealth activation with auto-permissions", font=font, fill='black', anchor="mm")
        draw.text((400, 510), "4. Monitoring begins immediately", font=font, fill='green', anchor="mm")
        
        output_path = 'static/qr_installation_demo.png'
        demo_frame.save(output_path)
        return output_path
    
    def generate_nfc_demo(self):
        """إنشاء عرض توضيحي لـ NFC"""
        demo_frame = Image.new('RGB', (800, 600), color='#f0f0f0')
        draw = ImageDraw.Draw(demo_frame)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        draw.ellipse([300, 100, 500, 300], fill='#4CAF50', outline='#2E7D32', width=3)
        draw.text((400, 200), "NFC", font=title_font, fill='white', anchor="mm")
        
        instructions = [
            "NFC Installation Method:",
            "",
            "1. Program NFC chip with encrypted data",
            "2. Target device touches NFC chip",
            "3. Automatic trigger and download",
            "4. Silent installation with permissions",
            "5. Format-resistant persistence",
            "",
            "Chip Data:",
            "• Server: [CONFIGURED_SERVER_URL]",
            "• Encryption: AES-256",
            "• Auto-permissions: Enabled",
            "• Stealth mode: Maximum"
        ]
        
        y_pos = 320
        for instruction in instructions:
            color = '#2E7D32' if instruction.startswith('•') else 'black'
            if instruction == "":
                y_pos += 10
                continue
            draw.text((50, y_pos), instruction, font=font, fill=color)
            y_pos += 25
        
        output_path = 'static/nfc_installation_demo.png'
        demo_frame.save(output_path)
        return output_path
    
    def generate_remote_demo(self):
        """إنشاء عرض توضيحي للتثبيت عن بُعد"""
        demo_frame = Image.new('RGB', (800, 600), color='#1a1a2e')
        draw = ImageDraw.Draw(demo_frame)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Title
        draw.text((400, 50), "Remote Installation System", font=title_font, fill='#00ff88', anchor="mm")
        
        draw.rectangle([350, 100, 450, 150], fill='#00ff88', outline='white', width=2)
        draw.text((400, 125), "Server", font=font, fill='black', anchor="mm")
        
        devices = [
            (200, 250, "Android"),
            (400, 250, "iPhone"), 
            (600, 250, "Windows")
        ]
        
        for x, y, device_type in devices:
            draw.rectangle([x-50, y-25, x+50, y+25], fill='#16213e', outline='#00ff88', width=2)
            draw.text((x, y), device_type, font=font, fill='white', anchor="mm")
            
            draw.line([(400, 150), (x, y-25)], fill='#00ff88', width=2)
        
        features = [
            "🌐 Network-based installation",
            "🔒 Encrypted payload delivery", 
            "🎯 Multi-device targeting",
            "⚡ Instant deployment",
            "🛡️ Bypass security systems",
            "🔄 Auto-update capability"
        ]
        
        y_pos = 320
        for feature in features:
            draw.text((50, y_pos), feature, font=font, fill='#00ff88')
            y_pos += 30
        
        output_path = 'static/remote_installation_demo.png'
        demo_frame.save(output_path)
        return output_path
    
    def generate_all_demos(self):
        """إنشاء جميع العروض التوضيحية"""
        demos = {}
        demos['qr'] = self.generate_qr_demo()
        demos['nfc'] = self.generate_nfc_demo()
        demos['remote'] = self.generate_remote_demo()
        return demos

if __name__ == '__main__':
    demo = InstallationDemo()
    demos = demo.generate_all_demos()
    
    for demo_type, path in demos.items():
        print(f"Generated {demo_type} demo: {path}")
