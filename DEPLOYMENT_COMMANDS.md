# 🚀 أوامر النشر والتشغيل السريع - Quick Deployment Commands

## أوامر التشغيل السريع - Quick Start Commands

### 1. التثبيت السريع (دقيقة واحدة):
```bash
git clone https://github.com/AlmutlabFadi/monitoring-improvements.git
cd monitoring-improvements
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements_unified.txt
cp .env.example .env
python ULTIMATE_SYSTEM_INTEGRATOR.py
```

### 2. تشغيل العرض التوضيحي الشامل:
```bash
python ultimate_web_simulator.py
# افتح المتصفح على: http://localhost:9000
```

### 3. تشغيل جميع المكونات:
```bash
# الطريقة الأولى - النظام المتكامل
python ULTIMATE_SYSTEM_INTEGRATOR.py

# الطريقة الثانية - المكونات منفصلة
python .ULTIMATE_MONITORING_SYSTEM.py &
python .ULTIMATE_CENTRAL_DASHBOARD.py &
python .world_class_web_server.py &
python ultimate_web_simulator.py &
python ULTIMATE_TELEGRAM_BOT.py &
```

### 4. إنشاء تطبيق Android:
```bash
python .ULTIMATE_ANDROID_GENERATOR.py
# سيتم إنشاء: calculator_monitoring.apk
```

### 5. اختبار النظام:
```bash
python test_complete_system.py
```

## الروابط المباشرة - Direct Links

- **العرض التوضيحي الشامل:** http://localhost:9000
- **لوحة التحكم الرئيسية:** http://localhost:8080
- **الخادم الخلفي:** http://localhost:5000
- **لوحة التحكم المركزية:** http://localhost:3000

## أوامر الطوارئ - Emergency Commands

### إيقاف جميع العمليات:
```bash
pkill -f python
# أو
sudo kill -9 $(pgrep -f "ULTIMATE")
```

### إعادة تشغيل سريع:
```bash
pkill -f python && sleep 2 && python ULTIMATE_SYSTEM_INTEGRATOR.py
```

### حل مشاكل المنافذ:
```bash
sudo lsof -ti:5000,8080,9000,3000 | xargs sudo kill -9
```

## متطلبات سريعة - Quick Requirements

```bash
pip install flask flask-socketio qrcode[pil] opencv-python pillow cryptography psutil requests sqlite3
```

## نشر سريع على الخادم - Quick Server Deployment

```bash
# تثبيت على خادم Ubuntu
sudo apt update && sudo apt install python3 python3-pip git -y
git clone https://github.com/AlmutlabFadi/monitoring-improvements.git
cd monitoring-improvements
pip3 install -r requirements_unified.txt
nohup python3 ultimate_web_simulator.py > server.log 2>&1 &
```

## Docker (اختياري) - Docker (Optional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements_unified.txt .
RUN pip install -r requirements_unified.txt
COPY . .
EXPOSE 5000 8080 9000 3000
CMD ["python", "ULTIMATE_SYSTEM_INTEGRATOR.py"]
```

```bash
docker build -t monitoring-system .
docker run -p 5000:5000 -p 8080:8080 -p 9000:9000 -p 3000:3000 monitoring-system
```
