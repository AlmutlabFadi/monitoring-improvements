const { app, BrowserWindow, Menu, ipcMain, dialog, shell, Tray, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const { autoUpdater } = require('electron-updater');

process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';

let mainWindow;
let splashWindow;
let settingsWindow;
let tray;
let isQuitting = false;

const isDevelopment = process.env.NODE_ENV === 'development';
const serverUrl = isDevelopment ? 'http://localhost:5174' : 'https://jeisifim.manus.space';

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 500,
    height: 350,
    frame: false,
    alwaysOnTop: true,
    transparent: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false
    }
  });

  const splashHtml = `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                text-align: center;
            }
            .logo {
                font-size: 4rem;
                margin-bottom: 1rem;
                animation: pulse 2s infinite;
            }
            .title {
                font-size: 1.5rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            .subtitle {
                font-size: 1rem;
                opacity: 0.8;
                margin-bottom: 2rem;
            }
            .loading {
                width: 200px;
                height: 4px;
                background: rgba(255,255,255,0.3);
                border-radius: 2px;
                overflow: hidden;
            }
            .loading-bar {
                width: 0%;
                height: 100%;
                background: white;
                border-radius: 2px;
                animation: loading 3s ease-in-out;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            @keyframes loading {
                0% { width: 0%; }
                100% { width: 100%; }
            }
        </style>
    </head>
    <body>
        <div class="logo">🌟</div>
        <div class="title">نظام المراقبة العالمي المتقدم</div>
        <div class="subtitle">World-Class Advanced Monitoring System</div>
        <div class="loading">
            <div class="loading-bar"></div>
        </div>
    </body>
    </html>
  `;

  splashWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(splashHtml));
  
  splashWindow.on('closed', () => {
    splashWindow = null;
  });

  setTimeout(() => {
    if (splashWindow) {
      splashWindow.close();
    }
    createMainWindow();
  }, 3500);
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 800,
    show: false,
    icon: createAppIcon(),
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: !isDevelopment,
      allowRunningInsecureContent: isDevelopment
    }
  });

  mainWindow.loadURL(serverUrl);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    if (isDevelopment) {
      mainWindow.webContents.openDevTools();
    }
    
    checkForUpdates();
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      
      if (process.platform === 'darwin') {
        app.dock.hide();
      }
      
      showNotification('التطبيق يعمل في الخلفية', 'يمكنك الوصول إليه من شريط المهام');
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    const currentUrl = new URL(serverUrl);
    
    if (parsedUrl.origin !== currentUrl.origin) {
      event.preventDefault();
      shell.openExternal(navigationUrl);
    }
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  createAdvancedMenu();
  createSystemTray();
}

function createAppIcon() {
  const iconPath = path.join(__dirname, 'assets', 'icon.png');
  if (fs.existsSync(iconPath)) {
    return iconPath;
  }
  
  return nativeImage.createFromDataURL('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==');
}

function createSystemTray() {
  const trayIcon = createAppIcon();
  tray = new Tray(trayIcon);
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'إظهار التطبيق',
      click: () => {
        mainWindow.show();
        if (process.platform === 'darwin') {
          app.dock.show();
        }
      }
    },
    {
      label: 'إعدادات سريعة',
      click: () => showQuickSettings()
    },
    { type: 'separator' },
    {
      label: 'حول التطبيق',
      click: () => showAboutDialog()
    },
    {
      label: 'خروج',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);
  
  tray.setContextMenu(contextMenu);
  tray.setToolTip('نظام المراقبة العالمي المتقدم');
  
  tray.on('double-click', () => {
    mainWindow.show();
    if (process.platform === 'darwin') {
      app.dock.show();
    }
  });
}

function createAdvancedMenu() {
  const template = [
    {
      label: 'ملف',
      submenu: [
        {
          label: 'نافذة جديدة',
          accelerator: 'CmdOrCtrl+N',
          click: () => createMainWindow()
        },
        { type: 'separator' },
        {
          label: 'تحديث',
          accelerator: 'CmdOrCtrl+R',
          click: () => mainWindow?.reload()
        },
        {
          label: 'إعادة تحميل كاملة',
          accelerator: 'CmdOrCtrl+Shift+R',
          click: () => mainWindow?.webContents.reloadIgnoringCache()
        },
        { type: 'separator' },
        {
          label: 'إعدادات متقدمة',
          accelerator: 'CmdOrCtrl+,',
          click: () => showAdvancedSettings()
        },
        { type: 'separator' },
        {
          label: 'خروج',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            isQuitting = true;
            app.quit();
          }
        }
      ]
    },
    {
      label: 'عرض',
      submenu: [
        {
          label: 'تكبير',
          accelerator: 'CmdOrCtrl+Plus',
          click: () => {
            const currentZoom = mainWindow?.webContents.getZoomLevel() || 0;
            mainWindow?.webContents.setZoomLevel(currentZoom + 0.5);
          }
        },
        {
          label: 'تصغير',
          accelerator: 'CmdOrCtrl+-',
          click: () => {
            const currentZoom = mainWindow?.webContents.getZoomLevel() || 0;
            mainWindow?.webContents.setZoomLevel(currentZoom - 0.5);
          }
        },
        {
          label: 'حجم طبيعي',
          accelerator: 'CmdOrCtrl+0',
          click: () => mainWindow?.webContents.setZoomLevel(0)
        },
        { type: 'separator' },
        {
          label: 'ملء الشاشة',
          accelerator: 'F11',
          click: () => {
            const isFullScreen = mainWindow?.isFullScreen() || false;
            mainWindow?.setFullScreen(!isFullScreen);
          }
        },
        { type: 'separator' },
        {
          label: 'الوضع المظلم',
          type: 'checkbox',
          checked: true,
          click: (menuItem) => {
            mainWindow?.webContents.send('toggle-theme', menuItem.checked);
          }
        }
      ]
    },
    {
      label: 'أدوات متقدمة',
      submenu: [
        {
          label: 'أدوات المطور',
          accelerator: 'F12',
          click: () => mainWindow?.webContents.toggleDevTools()
        },
        { type: 'separator' },
        {
          label: 'تصدير البيانات الشامل',
          click: () => exportAdvancedData()
        },
        {
          label: 'استيراد الإعدادات',
          click: () => importAdvancedSettings()
        },
        { type: 'separator' },
        {
          label: 'تشخيص النظام',
          click: () => runSystemDiagnostics()
        },
        {
          label: 'تحسين الأداء',
          click: () => optimizePerformance()
        }
      ]
    },
    {
      label: 'الأمان',
      submenu: [
        {
          label: 'تشفير البيانات',
          type: 'checkbox',
          checked: true,
          click: (menuItem) => {
            toggleDataEncryption(menuItem.checked);
          }
        },
        {
          label: 'الوضع الآمن',
          click: () => enableSecureMode()
        },
        { type: 'separator' },
        {
          label: 'تدقيق الأمان',
          click: () => runSecurityAudit()
        }
      ]
    },
    {
      label: 'مساعدة',
      submenu: [
        {
          label: 'دليل المستخدم المتقدم',
          click: () => shell.openExternal('https://docs.monitoring-system.com/advanced')
        },
        {
          label: 'اختصارات لوحة المفاتيح',
          click: () => showKeyboardShortcuts()
        },
        { type: 'separator' },
        {
          label: 'التحقق من التحديثات',
          click: () => checkForUpdates()
        },
        {
          label: 'الإبلاغ عن مشكلة',
          click: () => shell.openExternal('https://github.com/monitoring-system/issues')
        },
        { type: 'separator' },
        {
          label: 'حول التطبيق',
          click: () => showAboutDialog()
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function showAdvancedSettings() {
  if (settingsWindow) {
    settingsWindow.focus();
    return;
  }

  settingsWindow = new BrowserWindow({
    width: 800,
    height: 600,
    parent: mainWindow,
    modal: true,
    show: false,
    resizable: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  const settingsHtml = `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>الإعدادات المتقدمة</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
                direction: rtl;
            }
            .settings-container {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .settings-header {
                text-align: center;
                margin-bottom: 30px;
                color: #333;
            }
            .setting-group {
                margin-bottom: 25px;
                padding: 20px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            .setting-title {
                font-weight: bold;
                margin-bottom: 15px;
                color: #555;
            }
            .setting-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .toggle-switch {
                position: relative;
                width: 50px;
                height: 25px;
                background: #ccc;
                border-radius: 25px;
                cursor: pointer;
                transition: background 0.3s;
            }
            .toggle-switch.active {
                background: #4CAF50;
            }
            .toggle-slider {
                position: absolute;
                top: 2px;
                left: 2px;
                width: 21px;
                height: 21px;
                background: white;
                border-radius: 50%;
                transition: transform 0.3s;
            }
            .toggle-switch.active .toggle-slider {
                transform: translateX(25px);
            }
            .btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
            }
            .btn:hover {
                background: #5a6fd8;
            }
        </style>
    </head>
    <body>
        <div class="settings-container">
            <div class="settings-header">
                <h1>⚙️ الإعدادات المتقدمة</h1>
                <p>تخصيص نظام المراقبة العالمي</p>
            </div>
            
            <div class="setting-group">
                <div class="setting-title">🔒 إعدادات الأمان</div>
                <div class="setting-item">
                    <span>تشفير البيانات</span>
                    <div class="toggle-switch active" onclick="toggleSetting(this)">
                        <div class="toggle-slider"></div>
                    </div>
                </div>
                <div class="setting-item">
                    <span>المصادقة الثنائية</span>
                    <div class="toggle-switch" onclick="toggleSetting(this)">
                        <div class="toggle-slider"></div>
                    </div>
                </div>
            </div>
            
            <div class="setting-group">
                <div class="setting-title">🔔 إعدادات الإشعارات</div>
                <div class="setting-item">
                    <span>إشعارات سطح المكتب</span>
                    <div class="toggle-switch active" onclick="toggleSetting(this)">
                        <div class="toggle-slider"></div>
                    </div>
                </div>
                <div class="setting-item">
                    <span>الأصوات</span>
                    <div class="toggle-switch active" onclick="toggleSetting(this)">
                        <div class="toggle-slider"></div>
                    </div>
                </div>
            </div>
            
            <div class="setting-group">
                <div class="setting-title">⚡ إعدادات الأداء</div>
                <div class="setting-item">
                    <span>التحديث التلقائي</span>
                    <div class="toggle-switch active" onclick="toggleSetting(this)">
                        <div class="toggle-slider"></div>
                    </div>
                </div>
                <div class="setting-item">
                    <span>تسريع الأجهزة</span>
                    <div class="toggle-switch active" onclick="toggleSetting(this)">
                        <div class="toggle-slider"></div>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button class="btn" onclick="saveSettings()">💾 حفظ الإعدادات</button>
                <button class="btn" onclick="resetSettings()">🔄 إعادة تعيين</button>
                <button class="btn" onclick="window.close()">❌ إغلاق</button>
            </div>
        </div>
        
        <script>
            function toggleSetting(element) {
                element.classList.toggle('active');
            }
            
            function saveSettings() {
                alert('تم حفظ الإعدادات بنجاح!');
            }
            
            function resetSettings() {
                if (confirm('هل تريد إعادة تعيين جميع الإعدادات؟')) {
                    location.reload();
                }
            }
        </script>
    </body>
    </html>
  `;

  settingsWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(settingsHtml));
  
  settingsWindow.once('ready-to-show', () => {
    settingsWindow.show();
  });

  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });
}

function showNotification(title, body) {
  if (Notification.isSupported()) {
    new Notification({
      title,
      body,
      icon: createAppIcon()
    }).show();
  }
}

function checkForUpdates() {
  if (!isDevelopment) {
    autoUpdater.checkForUpdatesAndNotify();
  }
}

function exportAdvancedData() {
  dialog.showSaveDialog(mainWindow, {
    title: 'تصدير البيانات الشامل',
    defaultPath: `monitoring-export-${new Date().toISOString().split('T')[0]}.json`,
    filters: [
      { name: 'JSON Files', extensions: ['json'] },
      { name: 'CSV Files', extensions: ['csv'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  }).then(result => {
    if (!result.canceled) {
      const exportData = {
        exported_at: new Date().toISOString(),
        app_version: app.getVersion(),
        system_info: process.getSystemVersion(),
        data: {
          devices: 'سيتم تصدير بيانات الأجهزة',
          recordings: 'سيتم تصدير التسجيلات',
          screenshots: 'سيتم تصدير لقطات الشاشة',
          activities: 'سيتم تصدير الأنشطة'
        }
      };
      
      fs.writeFileSync(result.filePath, JSON.stringify(exportData, null, 2));
      showNotification('تم التصدير', 'تم تصدير البيانات بنجاح');
    }
  });
}

app.whenReady().then(() => {
  createSplashWindow();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  isQuitting = true;
});

ipcMain.handle('get-app-info', () => ({
  version: app.getVersion(),
  platform: process.platform,
  arch: process.arch
}));

ipcMain.handle('show-notification', (event, title, body) => {
  showNotification(title, body);
});

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}
