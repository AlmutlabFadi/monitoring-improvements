#!/usr/bin/env python3
"""
World-Class Web Dashboard Server for Advanced Monitoring System
خادم لوحة التحكم الويب عالمي المستوى لنظام المراقبة المتقدم
"""

from flask import Flask, render_template_string, jsonify, request, redirect
import os
import json
import requests
from datetime import datetime

app = Flask(__name__)

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام المراقبة العالمي المتقدم - World-Class Monitoring System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #00ff88;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #00ff88, #00ccff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 136, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.3);
        }
        
        .stat-card h3 {
            color: #00ff88;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #00ccff;
        }
        
        .stat-label {
            color: #cccccc;
            font-size: 0.9em;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 8px;
        }
        
        .status-online { background-color: #00ff88; }
        .status-offline { background-color: #ff4444; }
        .status-warning { background-color: #ffaa00; }
        
        .refresh-btn {
            background: linear-gradient(45deg, #00ff88, #00ccff);
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 20px auto;
            display: block;
        }
        
        .refresh-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0, 255, 136, 0.4);
        }
        
        .system-info {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
        }
        
        .progress-bar {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .progress-cpu { background: linear-gradient(90deg, #00ff88, #ffaa00); }
        .progress-memory { background: linear-gradient(90deg, #00ccff, #ff4444); }
        .progress-disk { background: linear-gradient(90deg, #aa88ff, #ff88aa); }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .pulse { animation: pulse 2s infinite; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌍 نظام المراقبة العالمي المتقدم</h1>
        <h2>World-Class Advanced Monitoring System</h2>
        <p>🛡️ Military-Grade Security • 🤖 AI-Powered Analytics • 🌐 Global Infrastructure</p>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📱 الأجهزة المتصلة</h3>
                <div class="stat-value" id="active-devices">-</div>
                <div class="stat-label">من إجمالي <span id="total-devices">-</span> جهاز</div>
                <span class="status-indicator status-online pulse"></span>
            </div>
            
            <div class="stat-card">
                <h3>🎵 التسجيلات الصوتية</h3>
                <div class="stat-value" id="recordings">-</div>
                <div class="stat-label">تسجيل صوتي محفوظ</div>
            </div>
            
            <div class="stat-card">
                <h3>📸 لقطات الشاشة</h3>
                <div class="stat-value" id="screenshots">-</div>
                <div class="stat-label">لقطة شاشة محفوظة</div>
            </div>
            
            <div class="stat-card">
                <h3>⚡ الأنشطة</h3>
                <div class="stat-value" id="activities">-</div>
                <div class="stat-label">نشاط مسجل</div>
            </div>
            
            <div class="stat-card">
                <h3>💬 الرسائل</h3>
                <div class="stat-value" id="messages">-</div>
                <div class="stat-label">رسالة مراقبة</div>
            </div>
            
            <div class="stat-card">
                <h3>📞 المكالمات</h3>
                <div class="stat-value" id="calls">-</div>
                <div class="stat-label">مكالمة مسجلة</div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 تحديث البيانات</button>
        
        <div class="system-info">
            <h3>🖥️ معلومات النظام</h3>
            <div style="margin-top: 20px;">
                <div>
                    <strong>استخدام المعالج:</strong>
                    <div class="progress-bar">
                        <div class="progress-fill progress-cpu" id="cpu-bar" style="width: 0%"></div>
                    </div>
                    <span id="cpu-percent">0%</span>
                </div>
                
                <div>
                    <strong>استخدام الذاكرة:</strong>
                    <div class="progress-bar">
                        <div class="progress-fill progress-memory" id="memory-bar" style="width: 0%"></div>
                    </div>
                    <span id="memory-percent">0%</span>
                </div>
                
                <div>
                    <strong>استخدام القرص:</strong>
                    <div class="progress-bar">
                        <div class="progress-fill progress-disk" id="disk-bar" style="width: 0%"></div>
                    </div>
                    <span id="disk-percent">0%</span>
                </div>
            </div>
            
            <div style="margin-top: 20px; text-align: center;">
                <p><strong>آخر تحديث:</strong> <span id="last-update">-</span></p>
                <p><strong>حالة النظام:</strong> <span id="system-status" class="pulse">🟢 نشط</span></p>
            </div>
        </div>
    </div>
    
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();
                
                if (data.success) {
                    // Update statistics
                    document.getElementById('active-devices').textContent = data.active_devices || 0;
                    document.getElementById('total-devices').textContent = data.total_devices || 0;
                    document.getElementById('recordings').textContent = data.total_recordings || 0;
                    document.getElementById('screenshots').textContent = data.total_screenshots || 0;
                    document.getElementById('activities').textContent = data.total_activities || 0;
                    document.getElementById('messages').textContent = data.total_messages || 0;
                    document.getElementById('calls').textContent = data.total_calls || 0;
                    
                    // Update system info
                    const systemInfo = data.system_info || {};
                    const cpuPercent = systemInfo.cpu_percent || 0;
                    const memoryPercent = systemInfo.memory?.percent || 0;
                    const diskPercent = systemInfo.disk?.percent || 0;
                    
                    document.getElementById('cpu-bar').style.width = cpuPercent + '%';
                    document.getElementById('cpu-percent').textContent = cpuPercent.toFixed(1) + '%';
                    
                    document.getElementById('memory-bar').style.width = memoryPercent + '%';
                    document.getElementById('memory-percent').textContent = memoryPercent.toFixed(1) + '%';
                    
                    document.getElementById('disk-bar').style.width = diskPercent + '%';
                    document.getElementById('disk-percent').textContent = diskPercent.toFixed(1) + '%';
                    
                    document.getElementById('last-update').textContent = new Date().toLocaleString('ar-SA');
                }
            } catch (error) {
                console.error('Error refreshing data:', error);
                document.getElementById('system-status').innerHTML = '🔴 خطأ في الاتصال';
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Serve the world-class dashboard"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Proxy dashboard stats from the main backend"""
    try:
        response = requests.get('http://localhost:5000/api/dashboard/stats', timeout=5)
        return response.json()
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'active_devices': 0,
            'total_devices': 0,
            'total_recordings': 0,
            'total_screenshots': 0,
            'total_activities': 0,
            'total_messages': 0,
            'total_calls': 0
        })

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'World-Class Web Dashboard',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/ultimate-dashboard')
def ultimate_dashboard():
    """Serve the ultimate comprehensive dashboard"""
    return redirect('http://localhost:9000/ultimate-dashboard')

@app.route('/simulators')
def device_simulators():
    """Serve device simulators page"""
    return redirect('http://localhost:9000/simulators')

@app.route('/installation-demos')
def installation_demos():
    """Serve installation demos page"""
    return redirect('http://localhost:9000/installation-demos')

@app.route('/api/simulated-devices')
def get_simulated_devices():
    """Get simulated devices data"""
    devices = [
        {
            'id': 'SIM_001',
            'name': 'Samsung Galaxy S23',
            'type': 'Android',
            'status': 'online',
            'battery': 85,
            'location': {'lat': 24.7136, 'lng': 46.6753},
            'monitoring_data': {'messages': 245, 'calls': 12, 'screenshots': 67, 'apps_monitored': 8}
        },
        {
            'id': 'SIM_002', 
            'name': 'iPhone 15 Pro',
            'type': 'iOS',
            'status': 'monitoring',
            'battery': 92,
            'location': {'lat': 24.7140, 'lng': 46.6750},
            'monitoring_data': {'messages': 189, 'calls': 8, 'screenshots': 43, 'apps_monitored': 6}
        },
        {
            'id': 'SIM_003',
            'name': 'Huawei P50',
            'type': 'Android',
            'status': 'online',
            'battery': 78,
            'location': {'lat': 24.7130, 'lng': 46.6760},
            'monitoring_data': {'messages': 156, 'calls': 5, 'screenshots': 29, 'apps_monitored': 7}
        }
    ]
    
    return jsonify({'success': True, 'devices': devices})

@app.route('/api/simulate/app-activity', methods=['POST'])
def simulate_app_activity():
    """Handle simulated app activity"""
    data = request.get_json()
    
    activity_log = {
        'timestamp': datetime.now().isoformat(),
        'app': data.get('app'),
        'device': data.get('device'),
        'activity_type': 'app_launch'
    }
    
    print(f"Simulated Activity: {activity_log}")
    
    return jsonify({'success': True, 'logged': activity_log})

if __name__ == '__main__':
    print("🌍 Starting World-Class Web Dashboard...")
    print("نظام لوحة التحكم الويب عالمي المستوى")
    print("Dashboard will be available at: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
