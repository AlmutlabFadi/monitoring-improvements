const { contextBridge, ipcRenderer } = require('electron');

// تعريض APIs آمنة للواجهة الأمامية
contextBridge.exposeInMainWorld('electronAPI', {
    // معلومات التطبيق
    getAppInfo: () => ipcRenderer.invoke('get-app-info'),
    
    // إدارة الإعدادات
    openSettings: () => ipcRenderer.invoke('open-settings'),
    updateSettings: (settings) => ipcRenderer.invoke('update-settings', settings),
    updateServerUrl: (url) => ipcRenderer.invoke('update-server-url', url),
    
    // الإشعارات
    showNotification: (title, body) => ipcRenderer.invoke('show-notification', title, body),
    
    // إدارة الملفات
    saveFile: (data, filename) => ipcRenderer.invoke('save-file', data, filename),
    selectFolder: () => ipcRenderer.invoke('select-folder'),
    openFolder: (path) => ipcRenderer.invoke('open-folder', path),
    
    // أحداث النافذة
    onWindowEvent: (event, callback) => {
        ipcRenderer.on(event, callback);
    },
    
    removeWindowEventListener: (event, callback) => {
        ipcRenderer.removeListener(event, callback);
    },
    
    // إدارة الاتصال
    checkConnection: async (url) => {
        try {
            const response = await fetch(url + '/api/status');
            return response.ok;
        } catch (error) {
            return false;
        }
    },
    
    // تحديث البيانات
    fetchData: async (endpoint) => {
        try {
            const appInfo = await ipcRenderer.invoke('get-app-info');
            const response = await fetch(appInfo.serverUrl + endpoint);
            if (response.ok) {
                return await response.json();
            }
            throw new Error('Failed to fetch data');
        } catch (error) {
            console.error('Error fetching data:', error);
            return null;
        }
    },
    
    // إرسال البيانات
    sendData: async (endpoint, data) => {
        try {
            const appInfo = await ipcRenderer.invoke('get-app-info');
            const response = await fetch(appInfo.serverUrl + endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                return await response.json();
            }
            throw new Error('Failed to send data');
        } catch (error) {
            console.error('Error sending data:', error);
            return null;
        }
    },
    
    // إدارة التخزين المحلي
    localStorage: {
        setItem: (key, value) => {
            localStorage.setItem(key, JSON.stringify(value));
        },
        getItem: (key) => {
            const item = localStorage.getItem(key);
            try {
                return item ? JSON.parse(item) : null;
            } catch {
                return item;
            }
        },
        removeItem: (key) => {
            localStorage.removeItem(key);
        },
        clear: () => {
            localStorage.clear();
        }
    },
    
    // أدوات مساعدة
    utils: {
        formatDate: (date) => {
            return new Date(date).toLocaleString('ar-SA');
        },
        
        formatFileSize: (bytes) => {
            const sizes = ['بايت', 'كيلوبايت', 'ميجابايت', 'جيجابايت'];
            if (bytes === 0) return '0 بايت';
            const i = Math.floor(Math.log(bytes) / Math.log(1024));
            return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
        },
        
        generateId: () => {
            return Date.now().toString(36) + Math.random().toString(36).substr(2);
        },
        
        debounce: (func, wait) => {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    },
    
    // إدارة الحالة
    state: {
        isOnline: navigator.onLine,
        
        onOnline: (callback) => {
            window.addEventListener('online', callback);
        },
        
        onOffline: (callback) => {
            window.addEventListener('offline', callback);
        },
        
        removeOnlineListener: (callback) => {
            window.removeEventListener('online', callback);
        },
        
        removeOfflineListener: (callback) => {
            window.removeEventListener('offline', callback);
        }
    },
    
    // أمان وتشفير
    security: {
        hashString: async (str) => {
            const encoder = new TextEncoder();
            const data = encoder.encode(str);
            const hashBuffer = await crypto.subtle.digest('SHA-256', data);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        },
        
        generateRandomString: (length = 16) => {
            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
            let result = '';
            for (let i = 0; i < length; i++) {
                result += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            return result;
        }
    }
});

// إضافة معالجات الأحداث العامة
window.addEventListener('DOMContentLoaded', () => {
    // إعداد معالجات الأحداث الأساسية
    
    // معالج حالة الاتصال
    const updateConnectionStatus = () => {
        const isOnline = navigator.onLine;
        document.body.classList.toggle('offline', !isOnline);
        
        // إرسال حدث تغيير حالة الاتصال
        window.dispatchEvent(new CustomEvent('connection-status-changed', {
            detail: { isOnline }
        }));
    };
    
    window.addEventListener('online', updateConnectionStatus);
    window.addEventListener('offline', updateConnectionStatus);
    
    // تحديث الحالة الأولية
    updateConnectionStatus();
    
    // إضافة أنماط CSS للحالة غير المتصلة
    const style = document.createElement('style');
    style.textContent = `
        body.offline {
            filter: grayscale(50%);
        }
        
        body.offline::before {
            content: "⚠️ غير متصل بالإنترنت";
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #f39c12;
            color: white;
            text-align: center;
            padding: 5px;
            z-index: 10000;
            font-size: 14px;
        }
    `;
    document.head.appendChild(style);
});

// إضافة معالج الأخطاء العام
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    
    // إرسال تقرير الخطأ (اختياري)
    if (window.electronAPI) {
        window.electronAPI.sendData('/api/error-report', {
            message: event.error.message,
            stack: event.error.stack,
            timestamp: new Date().toISOString(),
            url: window.location.href
        }).catch(() => {
            // تجاهل أخطاء إرسال التقرير
        });
    }
});

// إضافة معالج الأخطاء للـ Promise
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    
    // منع إظهار الخطأ في وحدة التحكم
    event.preventDefault();
});

// إضافة دوال مساعدة عامة
window.utils = {
    // تحديث العنوان
    setTitle: (title) => {
        document.title = title || 'تطبيق المراقبة والتسجيل';
    },
    
    // إظهار رسالة تحميل
    showLoading: (message = 'جاري التحميل...') => {
        const loading = document.createElement('div');
        loading.id = 'global-loading';
        loading.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                color: white;
                font-size: 18px;
            ">
                <div style="text-align: center;">
                    <div style="margin-bottom: 20px;">⏳</div>
                    <div>${message}</div>
                </div>
            </div>
        `;
        document.body.appendChild(loading);
    },
    
    // إخفاء رسالة التحميل
    hideLoading: () => {
        const loading = document.getElementById('global-loading');
        if (loading) {
            loading.remove();
        }
    },
    
    // إظهار رسالة نجاح
    showSuccess: (message) => {
        window.electronAPI?.showNotification('نجح', message);
    },
    
    // إظهار رسالة خطأ
    showError: (message) => {
        window.electronAPI?.showNotification('خطأ', message);
    }
};

