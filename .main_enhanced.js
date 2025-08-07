const { app, BrowserWindow, Menu, Tray, ipcMain, dialog, shell, screen, Notification } = require('electron');
const path = require('path');
const fs = require('fs');

class MonitoringControlApp {
    constructor() {
        this.mainWindow = null;
        this.settingsWindow = null;
        this.tray = null;
        this.isQuitting = false;
        this.serverUrl = 'https://e5h6i7cn9xxe.manus.space';
        this.settings = {};
        
        this.initializeApp();
    }
    
    initializeApp() {
        // تعطيل تحذيرات الأمان في التطوير
        process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';
        
        // تحميل الإعدادات
        this.loadSettings();
        
        // إعداد أحداث التطبيق
        app.whenReady().then(() => {
            this.createMainWindow();
            this.createTray();
            this.setupMenu();
            this.setupIpcHandlers();
            
            // إظهار شاشة البداية أولاً
            this.showSplashScreen();
        });
        
        app.on('window-all-closed', () => {
            if (process.platform !== 'darwin') {
                app.quit();
            }
        });
        
        app.on('activate', () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                this.createMainWindow();
            }
        });
        
        app.on('before-quit', () => {
            this.isQuitting = true;
        });
        
        // حفظ الإعدادات عند إغلاق التطبيق
        app.on('will-quit', () => {
            this.saveSettings();
        });
    }
    
    createMainWindow() {
        const { width, height } = screen.getPrimaryDisplay().workAreaSize;
        
        // استخدام الأبعاد المحفوظة أو الافتراضية
        const windowBounds = this.settings.windowBounds || {
            width: Math.min(1400, width - 100),
            height: Math.min(900, height - 100)
        };
        
        this.mainWindow = new BrowserWindow({
            ...windowBounds,
            minWidth: 1000,
            minHeight: 700,
            center: true,
            show: false,
            icon: path.join(__dirname, 'assets', 'icon.png'),
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                enableRemoteModule: false,
                preload: path.join(__dirname, 'preload.js'),
                webSecurity: false // للسماح بتحميل المحتوى من الخادم
            },
            titleBarStyle: 'default',
            frame: true,
            resizable: true,
            maximizable: true,
            minimizable: true,
            closable: true,
            title: 'تطبيق المراقبة والتسجيل'
        });
        
        // تحميل لوحة التحكم
        this.loadDashboard();
        
        // إعداد أحداث النافذة
        this.setupWindowEvents();
        
        // إعداد قائمة السياق
        this.setupContextMenu();
    }
    
    loadDashboard() {
        // محاولة تحميل لوحة التحكم من الخادم
        this.mainWindow.loadURL(this.serverUrl).catch((error) => {
            console.error('Failed to load dashboard:', error);
            // في حالة فشل الاتصال، تحميل صفحة محلية
            this.loadOfflinePage();
        });
    }
    
    loadOfflinePage() {
        const offlineHtml = `
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>وضع عدم الاتصال</title>
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    
                    .offline-container {
                        text-align: center;
                        max-width: 500px;
                        padding: 40px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    }
                    
                    .offline-icon {
                        font-size: 80px;
                        margin-bottom: 20px;
                        animation: pulse 2s infinite;
                    }
                    
                    @keyframes pulse {
                        0% { transform: scale(1); }
                        50% { transform: scale(1.1); }
                        100% { transform: scale(1); }
                    }
                    
                    .offline-title {
                        font-size: 28px;
                        margin-bottom: 15px;
                        font-weight: 600;
                    }
                    
                    .offline-message {
                        font-size: 16px;
                        margin-bottom: 30px;
                        opacity: 0.9;
                        line-height: 1.6;
                    }
                    
                    .retry-button {
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 12px 30px;
                        border-radius: 25px;
                        font-size: 16px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin: 10px;
                    }
                    
                    .retry-button:hover {
                        background: #45a049;
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    }
                    
                    .settings-button {
                        background: #2196F3;
                        color: white;
                        border: none;
                        padding: 12px 30px;
                        border-radius: 25px;
                        font-size: 16px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin: 10px;
                    }
                    
                    .settings-button:hover {
                        background: #1976D2;
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    }
                    
                    .status-info {
                        margin-top: 30px;
                        padding: 20px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        font-size: 14px;
                    }
                    
                    .server-url {
                        color: #FFD700;
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <div class="offline-container">
                    <div class="offline-icon">🌐</div>
                    <h1 class="offline-title">وضع عدم الاتصال</h1>
                    <p class="offline-message">
                        تعذر الاتصال بخادم لوحة التحكم. يرجى التحقق من اتصال الإنترنت أو إعدادات الخادم.
                    </p>
                    
                    <button class="retry-button" onclick="retryConnection()">
                        🔄 إعادة المحاولة
                    </button>
                    
                    <button class="settings-button" onclick="openSettings()">
                        ⚙️ الإعدادات
                    </button>
                    
                    <div class="status-info">
                        <p><strong>عنوان الخادم:</strong></p>
                        <p class="server-url">${this.serverUrl}</p>
                        <p style="margin-top: 10px;"><strong>الحالة:</strong> غير متصل</p>
                    </div>
                </div>
                
                <script>
                    function retryConnection() {
                        location.reload();
                    }
                    
                    function openSettings() {
                        if (window.electronAPI) {
                            window.electronAPI.openSettings();
                        }
                    }
                    
                    // محاولة إعادة الاتصال كل 30 ثانية
                    setInterval(() => {
                        fetch('${this.serverUrl}/api/status')
                            .then(response => {
                                if (response.ok) {
                                    location.reload();
                                }
                            })
                            .catch(() => {
                                // لا تفعل شيئاً، ابق في وضع عدم الاتصال
                            });
                    }, 30000);
                </script>
            </body>
            </html>
        `;
        
        this.mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(offlineHtml)}`);
    }
    
    setupWindowEvents() {
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
            
            // فحص الاتصال بالخادم
            this.checkServerConnection();
        });
        
        this.mainWindow.on('close', (event) => {
            if (!this.isQuitting) {
                event.preventDefault();
                this.mainWindow.hide();
                
                // إظهار إشعار في شريط المهام
                this.showNotification('تطبيق المراقبة', 'التطبيق يعمل في الخلفية');
            }
        });
        
        this.mainWindow.on('minimize', () => {
            if (this.settings.minimizeToTray !== false) {
                this.mainWindow.hide();
            }
        });
        
        // حفظ موقع وحجم النافذة
        this.mainWindow.on('resize', () => {
            this.settings.windowBounds = this.mainWindow.getBounds();
        });
        
        this.mainWindow.on('move', () => {
            this.settings.windowBounds = this.mainWindow.getBounds();
        });
        
        // إعداد أحداث التنقل
        this.mainWindow.webContents.on('new-window', (event, navigationUrl) => {
            event.preventDefault();
            shell.openExternal(navigationUrl);
        });
        
        this.mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
            console.error('Failed to load:', errorCode, errorDescription);
            this.handleConnectionError();
        });
        
        // إعداد معالج الروابط الخارجية
        this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
            shell.openExternal(url);
            return { action: 'deny' };
        });
    }
    
    setupContextMenu() {
        const contextMenu = Menu.buildFromTemplate([
            {
                label: 'إعادة تحميل',
                accelerator: 'CmdOrCtrl+R',
                click: () => {
                    this.mainWindow.reload();
                }
            },
            {
                label: 'أدوات المطور',
                accelerator: 'F12',
                click: () => {
                    this.mainWindow.webContents.toggleDevTools();
                }
            },
            { type: 'separator' },
            {
                label: 'الإعدادات',
                click: () => {
                    this.openSettings();
                }
            },
            {
                label: 'حول التطبيق',
                click: () => {
                    this.showAboutDialog();
                }
            }
        ]);
        
        this.mainWindow.webContents.on('context-menu', (event, params) => {
            contextMenu.popup(this.mainWindow, params.x, params.y);
        });
    }
    
    createTray() {
        const trayIconPath = path.join(__dirname, 'assets', 'tray-icon.png');
        
        // إنشاء أيقونة افتراضية إذا لم توجد
        if (!fs.existsSync(trayIconPath)) {
            this.createDefaultTrayIcon();
        }
        
        this.tray = new Tray(trayIconPath);
        
        const trayMenu = Menu.buildFromTemplate([
            {
                label: 'إظهار التطبيق',
                click: () => {
                    this.showMainWindow();
                }
            },
            {
                label: 'لوحة التحكم',
                click: () => {
                    this.openDashboard();
                }
            },
            { type: 'separator' },
            {
                label: 'الإعدادات',
                click: () => {
                    this.openSettings();
                }
            },
            {
                label: 'إعادة الاتصال',
                click: () => {
                    this.reconnectToServer();
                }
            },
            { type: 'separator' },
            {
                label: 'إنهاء التطبيق',
                click: () => {
                    this.quitApplication();
                }
            }
        ]);
        
        this.tray.setContextMenu(trayMenu);
        this.tray.setToolTip('تطبيق المراقبة والتسجيل');
        
        this.tray.on('double-click', () => {
            this.showMainWindow();
        });
    }
    
    setupMenu() {
        const template = [
            {
                label: 'ملف',
                submenu: [
                    {
                        label: 'لوحة التحكم الجديدة',
                        accelerator: 'CmdOrCtrl+N',
                        click: () => {
                            this.openDashboard();
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'الإعدادات',
                        accelerator: 'CmdOrCtrl+,',
                        click: () => {
                            this.openSettings();
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'إنهاء',
                        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                        click: () => {
                            this.quitApplication();
                        }
                    }
                ]
            },
            {
                label: 'عرض',
                submenu: [
                    {
                        label: 'إعادة تحميل',
                        accelerator: 'CmdOrCtrl+R',
                        click: () => {
                            this.mainWindow.reload();
                        }
                    },
                    {
                        label: 'تكبير',
                        accelerator: 'CmdOrCtrl+Plus',
                        click: () => {
                            this.zoomIn();
                        }
                    },
                    {
                        label: 'تصغير',
                        accelerator: 'CmdOrCtrl+-',
                        click: () => {
                            this.zoomOut();
                        }
                    },
                    {
                        label: 'الحجم الطبيعي',
                        accelerator: 'CmdOrCtrl+0',
                        click: () => {
                            this.resetZoom();
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'ملء الشاشة',
                        accelerator: 'F11',
                        click: () => {
                            this.toggleFullscreen();
                        }
                    }
                ]
            },
            {
                label: 'أدوات',
                submenu: [
                    {
                        label: 'أدوات المطور',
                        accelerator: 'F12',
                        click: () => {
                            this.mainWindow.webContents.toggleDevTools();
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'فحص الاتصال',
                        click: () => {
                            this.checkServerConnection();
                        }
                    },
                    {
                        label: 'إعادة الاتصال',
                        click: () => {
                            this.reconnectToServer();
                        }
                    }
                ]
            },
            {
                label: 'مساعدة',
                submenu: [
                    {
                        label: 'حول التطبيق',
                        click: () => {
                            this.showAboutDialog();
                        }
                    },
                    {
                        label: 'دليل الاستخدام',
                        click: () => {
                            shell.openExternal('https://docs.example.com');
                        }
                    }
                ]
            }
        ];
        
        const menu = Menu.buildFromTemplate(template);
        Menu.setApplicationMenu(menu);
    }
    
    setupIpcHandlers() {
        // معالج فتح الإعدادات
        ipcMain.handle('open-settings', () => {
            this.openSettings();
        });
        
        // معالج الحصول على معلومات التطبيق
        ipcMain.handle('get-app-info', () => {
            return {
                version: app.getVersion(),
                name: app.getName(),
                serverUrl: this.serverUrl,
                settings: this.settings
            };
        });
        
        // معالج تحديث عنوان الخادم
        ipcMain.handle('update-server-url', (event, newUrl) => {
            this.serverUrl = newUrl;
            this.settings.serverUrl = newUrl;
            this.saveSettings();
            this.loadDashboard();
        });
        
        // معالج تحديث الإعدادات
        ipcMain.handle('update-settings', (event, newSettings) => {
            this.settings = { ...this.settings, ...newSettings };
            this.saveSettings();
        });
        
        // معالج إظهار الإشعارات
        ipcMain.handle('show-notification', (event, title, body) => {
            this.showNotification(title, body);
        });
        
        // معالج فتح مجلد
        ipcMain.handle('open-folder', async (event, folderPath) => {
            shell.openPath(folderPath);
        });
        
        // معالج حفظ ملف
        ipcMain.handle('save-file', async (event, data, filename) => {
            const result = await dialog.showSaveDialog(this.mainWindow, {
                defaultPath: filename,
                filters: [
                    { name: 'JSON Files', extensions: ['json'] },
                    { name: 'Text Files', extensions: ['txt'] },
                    { name: 'All Files', extensions: ['*'] }
                ]
            });
            
            if (!result.canceled) {
                fs.writeFileSync(result.filePath, data);
                return result.filePath;
            }
            
            return null;
        });
        
        // معالج اختيار مجلد
        ipcMain.handle('select-folder', async () => {
            const result = await dialog.showOpenDialog(this.mainWindow, {
                properties: ['openDirectory']
            });
            
            if (!result.canceled && result.filePaths.length > 0) {
                return result.filePaths[0];
            }
            
            return null;
        });
    }
    
    showSplashScreen() {
        const splash = new BrowserWindow({
            width: 400,
            height: 300,
            frame: false,
            alwaysOnTop: true,
            transparent: true,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true
            }
        });
        
        splash.loadFile(path.join(__dirname, 'splash.html'));
        
        splash.on('closed', () => {
            splash.destroy();
        });
        
        // إغلاق شاشة البداية بعد 3 ثوان
        setTimeout(() => {
            splash.close();
            if (this.mainWindow) {
                this.mainWindow.show();
            }
        }, 3000);
    }
    
    openSettings() {
        if (this.settingsWindow) {
            this.settingsWindow.focus();
            return;
        }
        
        this.settingsWindow = new BrowserWindow({
            width: 600,
            height: 500,
            parent: this.mainWindow,
            modal: true,
            show: false,
            resizable: false,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            }
        });
        
        this.settingsWindow.loadFile(path.join(__dirname, 'settings.html'));
        
        this.settingsWindow.once('ready-to-show', () => {
            this.settingsWindow.show();
        });
        
        this.settingsWindow.on('closed', () => {
            this.settingsWindow = null;
        });
    }
    
    showMainWindow() {
        if (this.mainWindow) {
            if (this.mainWindow.isMinimized()) {
                this.mainWindow.restore();
            }
            this.mainWindow.show();
            this.mainWindow.focus();
        }
    }
    
    openDashboard() {
        this.showMainWindow();
        this.loadDashboard();
    }
    
    checkServerConnection() {
        this.mainWindow.webContents.executeJavaScript(`
            fetch('${this.serverUrl}/api/status')
                .then(response => response.ok)
                .catch(() => false)
        `).then(isConnected => {
            if (isConnected) {
                this.showNotification('حالة الاتصال', 'متصل بالخادم بنجاح');
            } else {
                this.handleConnectionError();
            }
        });
    }
    
    reconnectToServer() {
        this.showNotification('إعادة الاتصال', 'جاري إعادة الاتصال بالخادم...');
        this.loadDashboard();
    }
    
    handleConnectionError() {
        this.showNotification('خطأ في الاتصال', 'فشل الاتصال بالخادم');
        this.loadOfflinePage();
    }
    
    showNotification(title, body) {
        if (Notification.isSupported()) {
            new Notification({
                title: title,
                body: body,
                icon: path.join(__dirname, 'assets', 'icon.png')
            }).show();
        }
        
        // إظهار في شريط المهام أيضاً
        if (this.tray) {
            this.tray.displayBalloon({
                title: title,
                content: body,
                icon: path.join(__dirname, 'assets', 'icon.png')
            });
        }
    }
    
    showAboutDialog() {
        dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'حول التطبيق',
            message: 'تطبيق المراقبة والتسجيل',
            detail: `الإصدار: ${app.getVersion()}\nمطور بواسطة فريق التطوير\n\nتطبيق متقدم للمراقبة والتحكم عن بعد مع ميزات الأمان والتشفير.`,
            buttons: ['موافق']
        });
    }
    
    zoomIn() {
        const currentZoom = this.mainWindow.webContents.getZoomFactor();
        this.mainWindow.webContents.setZoomFactor(Math.min(currentZoom + 0.1, 3.0));
    }
    
    zoomOut() {
        const currentZoom = this.mainWindow.webContents.getZoomFactor();
        this.mainWindow.webContents.setZoomFactor(Math.max(currentZoom - 0.1, 0.5));
    }
    
    resetZoom() {
        this.mainWindow.webContents.setZoomFactor(1.0);
    }
    
    toggleFullscreen() {
        const isFullscreen = this.mainWindow.isFullScreen();
        this.mainWindow.setFullScreen(!isFullscreen);
    }
    
    createDefaultTrayIcon() {
        // إنشاء أيقونة افتراضية بسيطة
        const assetsDir = path.join(__dirname, 'assets');
        if (!fs.existsSync(assetsDir)) {
            fs.mkdirSync(assetsDir, { recursive: true });
        }
        
        // نسخ أيقونة افتراضية (يمكن تحسينها لاحقاً)
        const defaultIcon = path.join(assetsDir, 'tray-icon.png');
        if (!fs.existsSync(defaultIcon)) {
            // إنشاء ملف أيقونة فارغ
            fs.writeFileSync(defaultIcon, '');
        }
    }
    
    saveSettings() {
        const settings = {
            ...this.settings,
            serverUrl: this.serverUrl,
            lastUpdated: new Date().toISOString()
        };
        
        const settingsPath = path.join(__dirname, 'app-settings.json');
        try {
            fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }
    
    loadSettings() {
        const settingsPath = path.join(__dirname, 'app-settings.json');
        if (fs.existsSync(settingsPath)) {
            try {
                const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
                this.settings = settings;
                this.serverUrl = settings.serverUrl || this.serverUrl;
                return settings;
            } catch (error) {
                console.error('Error loading settings:', error);
            }
        }
        
        // الإعدادات الافتراضية
        this.settings = {
            serverUrl: this.serverUrl,
            minimizeToTray: true,
            autoStart: false,
            notifications: true,
            darkMode: false,
            refreshInterval: 30
        };
        
        return this.settings;
    }
    
    quitApplication() {
        this.isQuitting = true;
        this.saveSettings();
        app.quit();
    }
}

// إنشاء وتشغيل التطبيق
new MonitoringControlApp();

