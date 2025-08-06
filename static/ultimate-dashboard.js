class UltimateDashboard {
    constructor() {
        this.socket = io();
        this.currentTab = 'devices';
        this.devices = [];
        this.monitoringActive = false;
        
        this.initializeWebSocket();
        this.startDataSimulation();
        this.updateClock();
    }
    
    initializeWebSocket() {
        this.socket.on('connect', () => {
            console.log('Connected to Ultimate Monitoring System');
            this.addMonitoringFeed('🟢 متصل بالنظام الشامل للمراقبة');
        });
        
        this.socket.on('device_update', (data) => {
            this.updateDeviceStatus(data);
        });
        
        this.socket.on('monitoring_data', (data) => {
            this.updateMonitoringStats(data);
            this.addMonitoringFeed(`📱 ${data.device}: ${data.activity}`);
        });
        
        this.socket.on('real_time_stats', (stats) => {
            this.updateDashboardStats(stats);
        });
    }
    
    startDataSimulation() {
        setInterval(() => {
            if (this.monitoringActive) {
                this.simulateMonitoringActivity();
            }
        }, 3000);
        
        setInterval(() => {
            this.updateSystemStats();
        }, 5000);
        
        this.loadSimulatedDevices();
    }
    
    loadSimulatedDevices() {
        fetch('/api/simulated-devices')
            .then(response => response.json())
            .then(data => {
                this.devices = data.devices;
                this.renderDeviceList();
                this.updateDashboardStats({
                    active_devices: this.devices.filter(d => d.status === 'online').length,
                    total_devices: this.devices.length
                });
            });
    }
    
    simulateMonitoringActivity() {
        const activities = [
            'رسالة واتساب جديدة',
            'مكالمة تليجرام',
            'نشاط إنستغرام',
            'تصفح فيسبوك',
            'التقاط صورة',
            'تسجيل صوتي',
            'تغيير الموقع',
            'فتح تطبيق'
        ];
        
        const randomDevice = this.devices[Math.floor(Math.random() * this.devices.length)];
        const randomActivity = activities[Math.floor(Math.random() * activities.length)];
        
        this.socket.emit('simulate_activity', {
            device: randomDevice.name,
            activity: randomActivity,
            timestamp: new Date().toISOString()
        });
        
        this.incrementCounter('total-messages');
        if (Math.random() > 0.7) this.incrementCounter('total-calls');
        if (Math.random() > 0.8) this.incrementCounter('total-screenshots');
    }
    
    renderDeviceList() {
        const deviceList = document.getElementById('device-list');
        deviceList.innerHTML = '';
        
        this.devices.forEach(device => {
            const deviceElement = document.createElement('div');
            deviceElement.className = 'device-item';
            deviceElement.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${device.name}</strong>
                        <div style="font-size: 12px; color: #ccc;">${device.type} | ${device.battery}%</div>
                    </div>
                    <div>
                        <span class="status-indicator ${device.status}"></span>
                        ${device.status}
                    </div>
                </div>
            `;
            
            deviceElement.onclick = () => this.selectDevice(device);
            deviceList.appendChild(deviceElement);
        });
    }
    
    addMonitoringFeed(message) {
        const feed = document.getElementById('monitoring-feed');
        const feedItem = document.createElement('div');
        feedItem.className = 'feed-item';
        feedItem.innerHTML = `[${new Date().toLocaleTimeString('ar-SA')}] ${message}`;
        
        feed.insertBefore(feedItem, feed.firstChild);
        
        while (feed.children.length > 50) {
            feed.removeChild(feed.lastChild);
        }
    }
    
    updateSystemStats() {
        document.getElementById('cpu-usage').textContent = Math.floor(Math.random() * 30 + 10) + '%';
        document.getElementById('memory-usage').textContent = Math.floor(Math.random() * 40 + 30) + '%';
        document.getElementById('network-status').textContent = 'متصل - ' + Math.floor(Math.random() * 100 + 50) + ' Mbps';
    }
    
    incrementCounter(elementId) {
        const element = document.getElementById(elementId);
        const currentValue = parseInt(element.textContent) || 0;
        element.textContent = currentValue + 1;
    }
    
    updateClock() {
        setInterval(() => {
            document.getElementById('current-time').textContent = 
                new Date().toLocaleString('ar-SA');
        }, 1000);
    }
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

function startMonitoring() {
    dashboard.monitoringActive = true;
    dashboard.addMonitoringFeed('🚀 تم بدء المراقبة الشاملة');
}

function stopMonitoring() {
    dashboard.monitoringActive = false;
    dashboard.addMonitoringFeed('⏹️ تم إيقاف المراقبة');
}

function activateStealth() {
    dashboard.addMonitoringFeed('🥷 تم تفعيل وضع التخفي المتقدم');
}

function generateAPK() {
    dashboard.addMonitoringFeed('📱 جاري إنشاء APK مع الميزات المتقدمة...');
    setTimeout(() => {
        dashboard.addMonitoringFeed('✅ تم إنشاء APK بنجاح - calculator_monitoring.apk');
    }, 3000);
}

function generateQR() {
    dashboard.addMonitoringFeed('📱 تم إنشاء QR Code للتثبيت');
}

function generateNFC() {
    dashboard.addMonitoringFeed('📡 تم إعداد NFC للتثبيت التلقائي');
}

function remoteInstall() {
    dashboard.addMonitoringFeed('🌐 جاري التثبيت عن بُعد...');
}

let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new UltimateDashboard();
});
