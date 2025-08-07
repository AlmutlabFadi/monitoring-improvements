const { contextBridge, ipcRenderer } = require('electron');

// تعريض APIs آمنة للصفحة الرئيسية
contextBridge.exposeInMainWorld('electronAPI', {
  // معلومات التطبيق
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // حوارات النظام
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  
  // إشعارات النظام
  showNotification: (title, body) => {
    if (Notification.permission === 'granted') {
      new Notification(title, { body });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          new Notification(title, { body });
        }
      });
    }
  },
  
  // معلومات النظام
  platform: process.platform,
  
  // تحديث العنوان
  setTitle: (title) => {
    document.title = title;
  }
});

// إضافة أنماط مخصصة للتطبيق
window.addEventListener('DOMContentLoaded', () => {
  // إضافة فئة CSS للتطبيق المكتبي
  document.body.classList.add('electron-app');
  
  // إضافة أنماط مخصصة
  const style = document.createElement('style');
  style.textContent = `
    .electron-app {
      user-select: none;
      -webkit-user-select: none;
    }
    
    .electron-app input,
    .electron-app textarea,
    .electron-app [contenteditable] {
      user-select: text;
      -webkit-user-select: text;
    }
    
    /* شريط التمرير المخصص */
    .electron-app ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    
    .electron-app ::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 4px;
    }
    
    .electron-app ::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 4px;
    }
    
    .electron-app ::-webkit-scrollbar-thumb:hover {
      background: #a8a8a8;
    }
    
    /* إخفاء شريط التمرير الأفقي إذا لم يكن مطلوباً */
    .electron-app body {
      overflow-x: hidden;
    }
  `;
  document.head.appendChild(style);
  
  // إضافة معالج للاختصارات
  document.addEventListener('keydown', (event) => {
    // منع F5 (تحديث)
    if (event.key === 'F5') {
      event.preventDefault();
    }
    
    // منع Ctrl+Shift+I (أدوات المطور)
    if (event.ctrlKey && event.shiftKey && event.key === 'I') {
      event.preventDefault();
    }
    
    // منع Ctrl+U (عرض المصدر)
    if (event.ctrlKey && event.key === 'u') {
      event.preventDefault();
    }
  });
  
  // منع القائمة السياقية
  document.addEventListener('contextmenu', (event) => {
    event.preventDefault();
  });
});

// معالج للأخطاء
window.addEventListener('error', (event) => {
  console.error('خطأ في التطبيق:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('رفض غير معالج:', event.reason);
});

