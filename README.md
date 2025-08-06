# Advanced Monitoring and Control System
# نظام المراقبة والتحكم المتقدم

A comprehensive monitoring and control application with desktop interface, Telegram bot integration, and advanced security features.

نظام مراقبة وتحكم شامل مع واجهة مكتبية وتكامل بوت تليجرام وميزات أمان متقدمة.

## Features / الميزات

### 🖥️ Desktop Application / التطبيق المكتبي
- Real-time system monitoring / مراقبة النظام في الوقت الفعلي
- Device management interface / واجهة إدارة الأجهزة
- Comprehensive dashboard / لوحة تحكم شاملة
- Bilingual support (Arabic/English) / دعم ثنائي اللغة

### 🤖 Telegram Bot Integration / تكامل بوت تليجرام
- Remote monitoring via Telegram / مراقبة عن بعد عبر تليجرام
- Real-time alerts and notifications / تنبيهات وإشعارات فورية
- Comprehensive analytics commands / أوامر تحليل شاملة
- Secure admin-only access / وصول آمن للمدراء فقط

### 🔧 Backend API System / نظام API الخلفي
- RESTful API with 25+ endpoints / واجهة برمجية مع أكثر من 25 نقطة نهاية
- JWT authentication / مصادقة JWT
- Real-time WebSocket communication / تواصل فوري عبر WebSocket
- Comprehensive database management / إدارة قاعدة بيانات شاملة

### 🛡️ Security Features / ميزات الأمان
- AES-256 encryption / تشفير AES-256
- Anti-detection mechanisms / آليات مقاومة الاكتشاف
- Stealth mode operation / تشغيل في وضع التخفي
- Secure file handling / معالجة آمنة للملفات

## Quick Start / البدء السريع

### Prerequisites / المتطلبات المسبقة
- Python 3.8 or higher / بايثون 3.8 أو أحدث
- pip package manager / مدير الحزم pip
- Internet connection / اتصال بالإنترنت

### Installation / التثبيت

1. **Clone the repository / استنساخ المستودع**
```bash
git clone <repository-url>
cd monitoring-improvements
```

2. **Run setup script / تشغيل سكريبت الإعداد**
```bash
python setup.py
```

3. **Configure environment / تكوين البيئة**
```bash
# Edit .env file with your settings
# قم بتحرير ملف .env بإعداداتك
cp .env.example .env
nano .env
```

4. **Start the services / بدء الخدمات**

**Backend Server / الخادم الخلفي:**
```bash
python enhanced_main.py
# Server will run on http://localhost:5000
```

**Desktop Application / التطبيق المكتبي:**
```bash
python enhanced_desktop_app.py
```

**Telegram Bot / بوت تليجرام:**
```bash
python integrated_telegram_bot.py
```

## Configuration / التكوين

### Environment Variables / متغيرات البيئة

Key configuration options in `.env` file:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USERS=123456789,987654321

# API Configuration
API_URL=http://localhost:5000
JWT_SECRET=your-secret-key-here

# Security
ENABLE_STEALTH_MODE=True
ENABLE_ENCRYPTION=True
```

### Database Setup / إعداد قاعدة البيانات

The system uses SQLite by default. The database is automatically initialized on first run.

يستخدم النظام SQLite افتراضياً. يتم تهيئة قاعدة البيانات تلقائياً عند التشغيل الأول.

## Usage / الاستخدام

### Desktop Application / التطبيق المكتبي

1. Launch the desktop application / تشغيل التطبيق المكتبي
2. Use the Dashboard tab for system overview / استخدم تبويب لوحة التحكم للنظرة العامة
3. Monitor devices in the Devices tab / راقب الأجهزة في تبويب الأجهزة
4. View logs in the Monitoring tab / اعرض السجلات في تبويب المراقبة

### Telegram Bot Commands / أوامر بوت تليجرام

- `/start` - Welcome message / رسالة ترحيب
- `/help` - Command help / مساعدة الأوامر
- `/analytics` - System analytics / تحليل النظام
- `/devices` - Device management / إدارة الأجهزة
- `/status` - System status / حالة النظام
- `/security` - Security status / حالة الأمان
- `/performance` - Performance metrics / مقاييس الأداء

## API Documentation / توثيق API

### Authentication / المصادقة
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

### Device Management / إدارة الأجهزة
```bash
GET /api/devices
Authorization: Bearer <jwt_token>
```

### System Status / حالة النظام
```bash
GET /api/dashboard/stats
Authorization: Bearer <jwt_token>
```

## Development / التطوير

### Project Structure / هيكل المشروع
```
monitoring-improvements/
├── enhanced_main.py              # Backend server / الخادم الخلفي
├── enhanced_desktop_app.py       # Desktop application / التطبيق المكتبي
├── integrated_telegram_bot.py    # Telegram bot / بوت تليجرام
├── requirements_unified.txt      # Python dependencies / تبعيات بايثون
├── .env.example                  # Environment template / قالب البيئة
├── setup.py                      # Setup script / سكريبت الإعداد
└── README.md                     # This file / هذا الملف
```

### Contributing / المساهمة

1. Fork the repository / انسخ المستودع
2. Create a feature branch / أنشئ فرع ميزة
3. Make your changes / قم بتغييراتك
4. Test thoroughly / اختبر بدقة
5. Submit a pull request / أرسل طلب دمج

## Troubleshooting / استكشاف الأخطاء

### Common Issues / المشاكل الشائعة

**Connection Error / خطأ الاتصال:**
- Check if backend server is running / تأكد من تشغيل الخادم الخلفي
- Verify API_URL in .env file / تحقق من API_URL في ملف .env

**Bot Not Responding / البوت لا يستجيب:**
- Check TELEGRAM_BOT_TOKEN / تحقق من TELEGRAM_BOT_TOKEN
- Verify admin user IDs / تحقق من معرفات المستخدمين المدراء

**Database Errors / أخطاء قاعدة البيانات:**
- Delete monitoring_system.db and restart / احذف monitoring_system.db وأعد التشغيل
- Check file permissions / تحقق من صلاحيات الملفات

## License / الترخيص

This project is licensed under the MIT License.

هذا المشروع مرخص تحت رخصة MIT.

## Support / الدعم

For support and questions:
- Create an issue on GitHub
- Contact the development team

للدعم والأسئلة:
- أنشئ مشكلة على GitHub
- اتصل بفريق التطوير
