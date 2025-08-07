#!/usr/bin/env python3
"""
نظام التشفير والأمان المتقدم - Advanced Encryption & Security System
يوفر تشفير متقدم وحماية للبيانات الحساسة
"""

import os
import json
import base64
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class AdvancedEncryptionSystem:
    def __init__(self):
        self.output_dir = "/home/ubuntu/monitoring-app/stealth_components"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # مفاتيح التشفير الافتراضية
        self.master_key = None
        self.device_key = None
        
    def generate_device_key(self, device_id: str) -> str:
        """توليد مفتاح تشفير خاص بالجهاز"""
        
        # استخدام معرف الجهاز لتوليد مفتاح فريد
        salt = hashlib.sha256(device_id.encode()).digest()
        
        # توليد مفتاح باستخدام PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # استخدام كلمة مرور أساسية + معرف الجهاز
        password = f"STEALTH_MASTER_KEY_{device_id}".encode()
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return key.decode()
    
    def encrypt_data(self, data: str, key: Optional[str] = None) -> str:
        """تشفير البيانات"""
        
        if key is None:
            key = self.generate_device_key("default_device")
        
        try:
            # إنشاء مشفر Fernet
            fernet = Fernet(key.encode())
            
            # تشفير البيانات
            encrypted_data = fernet.encrypt(data.encode())
            
            # ترميز base64 للنقل
            return base64.b64encode(encrypted_data).decode()
        
        except Exception as e:
            print(f"خطأ في التشفير: {e}")
            return ""
    
    def decrypt_data(self, encrypted_data: str, key: Optional[str] = None) -> str:
        """فك تشفير البيانات"""
        
        if key is None:
            key = self.generate_device_key("default_device")
        
        try:
            # فك ترميز base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # إنشاء مفكك التشفير
            fernet = Fernet(key.encode())
            
            # فك التشفير
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode()
        
        except Exception as e:
            print(f"خطأ في فك التشفير: {e}")
            return ""
    
    def generate_secure_hash(self, data: str, salt: Optional[str] = None) -> str:
        """توليد hash آمن للبيانات"""
        
        if salt is None:
            salt = secrets.token_hex(16)
        
        # دمج البيانات مع الملح
        salted_data = f"{data}{salt}"
        
        # توليد hash باستخدام SHA-256
        hash_object = hashlib.sha256(salted_data.encode())
        
        return hash_object.hexdigest()
    
    def generate_android_encryption_class(self) -> str:
        """توليد فئة التشفير لـ Android"""
        
        encryption_class = '''package com.stealth.security;

import android.util.Base64;
import android.util.Log;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;
import javax.crypto.spec.IvParameterSpec;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.nio.charset.StandardCharsets;

public class AdvancedEncryption {
    private static final String TAG = "AdvancedEncryption";
    private static final String ALGORITHM = "AES";
    private static final String TRANSFORMATION = "AES/CBC/PKCS5Padding";
    private static final String HASH_ALGORITHM = "SHA-256";
    
    private SecretKey secretKey;
    
    public AdvancedEncryption() {
        generateKey();
    }
    
    public AdvancedEncryption(String deviceId) {
        generateDeviceKey(deviceId);
    }
    
    /**
     * توليد مفتاح تشفير عشوائي
     */
    private void generateKey() {
        try {
            KeyGenerator keyGenerator = KeyGenerator.getInstance(ALGORITHM);
            keyGenerator.init(256);
            secretKey = keyGenerator.generateKey();
        } catch (Exception e) {
            Log.e(TAG, "Error generating key", e);
        }
    }
    
    /**
     * توليد مفتاح تشفير خاص بالجهاز
     */
    private void generateDeviceKey(String deviceId) {
        try {
            String keyMaterial = "STEALTH_MASTER_KEY_" + deviceId;
            MessageDigest digest = MessageDigest.getInstance(HASH_ALGORITHM);
            byte[] keyBytes = digest.digest(keyMaterial.getBytes(StandardCharsets.UTF_8));
            
            // استخدام أول 32 بايت للمفتاح (256 بت)
            byte[] key = new byte[32];
            System.arraycopy(keyBytes, 0, key, 0, Math.min(keyBytes.length, 32));
            
            secretKey = new SecretKeySpec(key, ALGORITHM);
        } catch (Exception e) {
            Log.e(TAG, "Error generating device key", e);
            generateKey(); // fallback إلى مفتاح عشوائي
        }
    }
    
    /**
     * تشفير النص
     */
    public String encrypt(String plainText) {
        try {
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            
            // توليد IV عشوائي
            byte[] iv = new byte[16];
            new SecureRandom().nextBytes(iv);
            IvParameterSpec ivSpec = new IvParameterSpec(iv);
            
            cipher.init(Cipher.ENCRYPT_MODE, secretKey, ivSpec);
            byte[] encryptedBytes = cipher.doFinal(plainText.getBytes(StandardCharsets.UTF_8));
            
            // دمج IV مع البيانات المشفرة
            byte[] encryptedWithIv = new byte[iv.length + encryptedBytes.length];
            System.arraycopy(iv, 0, encryptedWithIv, 0, iv.length);
            System.arraycopy(encryptedBytes, 0, encryptedWithIv, iv.length, encryptedBytes.length);
            
            return Base64.encodeToString(encryptedWithIv, Base64.DEFAULT);
        } catch (Exception e) {
            Log.e(TAG, "Error encrypting data", e);
            return null;
        }
    }
    
    /**
     * فك تشفير النص
     */
    public String decrypt(String encryptedText) {
        try {
            byte[] encryptedWithIv = Base64.decode(encryptedText, Base64.DEFAULT);
            
            // استخراج IV
            byte[] iv = new byte[16];
            System.arraycopy(encryptedWithIv, 0, iv, 0, iv.length);
            IvParameterSpec ivSpec = new IvParameterSpec(iv);
            
            // استخراج البيانات المشفرة
            byte[] encryptedBytes = new byte[encryptedWithIv.length - 16];
            System.arraycopy(encryptedWithIv, 16, encryptedBytes, 0, encryptedBytes.length);
            
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.DECRYPT_MODE, secretKey, ivSpec);
            byte[] decryptedBytes = cipher.doFinal(encryptedBytes);
            
            return new String(decryptedBytes, StandardCharsets.UTF_8);
        } catch (Exception e) {
            Log.e(TAG, "Error decrypting data", e);
            return null;
        }
    }
    
    /**
     * توليد hash آمن
     */
    public String generateHash(String data) {
        return generateHash(data, null);
    }
    
    /**
     * توليد hash آمن مع ملح
     */
    public String generateHash(String data, String salt) {
        try {
            if (salt == null) {
                salt = generateSalt();
            }
            
            String saltedData = data + salt;
            MessageDigest digest = MessageDigest.getInstance(HASH_ALGORITHM);
            byte[] hashBytes = digest.digest(saltedData.getBytes(StandardCharsets.UTF_8));
            
            StringBuilder hexString = new StringBuilder();
            for (byte b : hashBytes) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            
            return hexString.toString();
        } catch (Exception e) {
            Log.e(TAG, "Error generating hash", e);
            return null;
        }
    }
    
    /**
     * توليد ملح عشوائي
     */
    private String generateSalt() {
        byte[] salt = new byte[16];
        new SecureRandom().nextBytes(salt);
        return Base64.encodeToString(salt, Base64.DEFAULT);
    }
    
    /**
     * تشفير ملف
     */
    public boolean encryptFile(String inputFilePath, String outputFilePath) {
        try {
            java.io.FileInputStream fis = new java.io.FileInputStream(inputFilePath);
            java.io.FileOutputStream fos = new java.io.FileOutputStream(outputFilePath);
            
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            
            // توليد IV عشوائي
            byte[] iv = new byte[16];
            new SecureRandom().nextBytes(iv);
            IvParameterSpec ivSpec = new IvParameterSpec(iv);
            
            cipher.init(Cipher.ENCRYPT_MODE, secretKey, ivSpec);
            
            // كتابة IV في بداية الملف
            fos.write(iv);
            
            javax.crypto.CipherOutputStream cos = new javax.crypto.CipherOutputStream(fos, cipher);
            
            byte[] buffer = new byte[1024];
            int bytesRead;
            while ((bytesRead = fis.read(buffer)) != -1) {
                cos.write(buffer, 0, bytesRead);
            }
            
            cos.close();
            fos.close();
            fis.close();
            
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Error encrypting file", e);
            return false;
        }
    }
    
    /**
     * فك تشفير ملف
     */
    public boolean decryptFile(String inputFilePath, String outputFilePath) {
        try {
            java.io.FileInputStream fis = new java.io.FileInputStream(inputFilePath);
            java.io.FileOutputStream fos = new java.io.FileOutputStream(outputFilePath);
            
            // قراءة IV من بداية الملف
            byte[] iv = new byte[16];
            fis.read(iv);
            IvParameterSpec ivSpec = new IvParameterSpec(iv);
            
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.DECRYPT_MODE, secretKey, ivSpec);
            
            javax.crypto.CipherInputStream cis = new javax.crypto.CipherInputStream(fis, cipher);
            
            byte[] buffer = new byte[1024];
            int bytesRead;
            while ((bytesRead = cis.read(buffer)) != -1) {
                fos.write(buffer, 0, bytesRead);
            }
            
            cis.close();
            fos.close();
            fis.close();
            
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Error decrypting file", e);
            return false;
        }
    }
    
    /**
     * الحصول على المفتاح كـ string
     */
    public String getKeyAsString() {
        if (secretKey != null) {
            return Base64.encodeToString(secretKey.getEncoded(), Base64.DEFAULT);
        }
        return null;
    }
    
    /**
     * تحميل مفتاح من string
     */
    public void loadKeyFromString(String keyString) {
        try {
            byte[] keyBytes = Base64.decode(keyString, Base64.DEFAULT);
            secretKey = new SecretKeySpec(keyBytes, ALGORITHM);
        } catch (Exception e) {
            Log.e(TAG, "Error loading key from string", e);
        }
    }
}'''
        
        file_path = os.path.join(self.output_dir, "AdvancedEncryption.java")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(encryption_class)
        
        return file_path
    
    def generate_secure_storage_class(self) -> str:
        """توليد فئة التخزين الآمن"""
        
        storage_class = '''package com.stealth.security;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public class SecureStorage {
    private static final String TAG = "SecureStorage";
    private static final String PREFS_NAME = "stealth_secure_prefs";
    private static final String ENCRYPTED_DIR = "encrypted_data";
    
    private Context context;
    private AdvancedEncryption encryption;
    private SharedPreferences securePrefs;
    
    public SecureStorage(Context context) {
        this.context = context;
        this.encryption = new AdvancedEncryption();
        this.securePrefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        
        // إنشاء مجلد البيانات المشفرة
        createEncryptedDirectory();
    }
    
    public SecureStorage(Context context, String deviceId) {
        this.context = context;
        this.encryption = new AdvancedEncryption(deviceId);
        this.securePrefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        
        createEncryptedDirectory();
    }
    
    /**
     * إنشاء مجلد البيانات المشفرة
     */
    private void createEncryptedDirectory() {
        File encryptedDir = new File(context.getFilesDir(), ENCRYPTED_DIR);
        if (!encryptedDir.exists()) {
            encryptedDir.mkdirs();
        }
    }
    
    /**
     * حفظ نص مشفر في SharedPreferences
     */
    public boolean saveEncryptedString(String key, String value) {
        try {
            String encryptedValue = encryption.encrypt(value);
            if (encryptedValue != null) {
                securePrefs.edit().putString(key, encryptedValue).apply();
                return true;
            }
        } catch (Exception e) {
            Log.e(TAG, "Error saving encrypted string", e);
        }
        return false;
    }
    
    /**
     * قراءة نص مشفر من SharedPreferences
     */
    public String getEncryptedString(String key, String defaultValue) {
        try {
            String encryptedValue = securePrefs.getString(key, null);
            if (encryptedValue != null) {
                String decryptedValue = encryption.decrypt(encryptedValue);
                return decryptedValue != null ? decryptedValue : defaultValue;
            }
        } catch (Exception e) {
            Log.e(TAG, "Error getting encrypted string", e);
        }
        return defaultValue;
    }
    
    /**
     * حفظ ملف مشفر
     */
    public boolean saveEncryptedFile(String fileName, byte[] data) {
        try {
            File encryptedDir = new File(context.getFilesDir(), ENCRYPTED_DIR);
            File tempFile = new File(encryptedDir, fileName + ".tmp");
            File encryptedFile = new File(encryptedDir, fileName + ".enc");
            
            // كتابة البيانات في ملف مؤقت
            FileOutputStream fos = new FileOutputStream(tempFile);
            fos.write(data);
            fos.close();
            
            // تشفير الملف
            boolean success = encryption.encryptFile(tempFile.getAbsolutePath(), 
                                                   encryptedFile.getAbsolutePath());
            
            // حذف الملف المؤقت
            tempFile.delete();
            
            return success;
        } catch (Exception e) {
            Log.e(TAG, "Error saving encrypted file", e);
            return false;
        }
    }
    
    /**
     * قراءة ملف مشفر
     */
    public byte[] getEncryptedFile(String fileName) {
        try {
            File encryptedDir = new File(context.getFilesDir(), ENCRYPTED_DIR);
            File encryptedFile = new File(encryptedDir, fileName + ".enc");
            File tempFile = new File(encryptedDir, fileName + ".tmp");
            
            if (!encryptedFile.exists()) {
                return null;
            }
            
            // فك تشفير الملف
            boolean success = encryption.decryptFile(encryptedFile.getAbsolutePath(), 
                                                    tempFile.getAbsolutePath());
            
            if (success) {
                // قراءة البيانات
                FileInputStream fis = new FileInputStream(tempFile);
                byte[] data = new byte[(int) tempFile.length()];
                fis.read(data);
                fis.close();
                
                // حذف الملف المؤقت
                tempFile.delete();
                
                return data;
            }
        } catch (Exception e) {
            Log.e(TAG, "Error getting encrypted file", e);
        }
        return null;
    }
    
    /**
     * حذف ملف مشفر
     */
    public boolean deleteEncryptedFile(String fileName) {
        try {
            File encryptedDir = new File(context.getFilesDir(), ENCRYPTED_DIR);
            File encryptedFile = new File(encryptedDir, fileName + ".enc");
            
            return encryptedFile.delete();
        } catch (Exception e) {
            Log.e(TAG, "Error deleting encrypted file", e);
            return false;
        }
    }
    
    /**
     * حفظ كائن JSON مشفر
     */
    public boolean saveEncryptedJson(String key, org.json.JSONObject jsonObject) {
        try {
            String jsonString = jsonObject.toString();
            return saveEncryptedString(key, jsonString);
        } catch (Exception e) {
            Log.e(TAG, "Error saving encrypted JSON", e);
            return false;
        }
    }
    
    /**
     * قراءة كائن JSON مشفر
     */
    public org.json.JSONObject getEncryptedJson(String key) {
        try {
            String jsonString = getEncryptedString(key, null);
            if (jsonString != null) {
                return new org.json.JSONObject(jsonString);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error getting encrypted JSON", e);
        }
        return null;
    }
    
    /**
     * مسح جميع البيانات المشفرة
     */
    public boolean clearAllEncryptedData() {
        try {
            // مسح SharedPreferences
            securePrefs.edit().clear().apply();
            
            // مسح الملفات المشفرة
            File encryptedDir = new File(context.getFilesDir(), ENCRYPTED_DIR);
            if (encryptedDir.exists()) {
                File[] files = encryptedDir.listFiles();
                if (files != null) {
                    for (File file : files) {
                        file.delete();
                    }
                }
            }
            
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Error clearing encrypted data", e);
            return false;
        }
    }
    
    /**
     * فحص سلامة البيانات المشفرة
     */
    public boolean verifyDataIntegrity(String key) {
        try {
            String testData = "integrity_test_data";
            
            // تشفير بيانات اختبار
            if (saveEncryptedString(key + "_test", testData)) {
                // فك التشفير والتحقق
                String decryptedData = getEncryptedString(key + "_test", null);
                
                // حذف بيانات الاختبار
                securePrefs.edit().remove(key + "_test").apply();
                
                return testData.equals(decryptedData);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error verifying data integrity", e);
        }
        return false;
    }
}'''
        
        file_path = os.path.join(self.output_dir, "SecureStorage.java")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(storage_class)
        
        return file_path
    
    def generate_security_manager(self) -> str:
        """توليد مدير الأمان الشامل"""
        
        manager_content = '''package com.stealth.security;

import android.content.Context;
import android.util.Log;
import java.util.HashMap;
import java.util.Map;

public class SecurityManager {
    private static final String TAG = "SecurityManager";
    private static SecurityManager instance;
    
    private Context context;
    private AdvancedEncryption encryption;
    private SecureStorage secureStorage;
    private Map<String, String> securitySettings;
    
    private SecurityManager(Context context) {
        this.context = context;
        this.encryption = new AdvancedEncryption();
        this.secureStorage = new SecureStorage(context);
        this.securitySettings = new HashMap<>();
        
        initializeSecuritySettings();
    }
    
    public static synchronized SecurityManager getInstance(Context context) {
        if (instance == null) {
            instance = new SecurityManager(context.getApplicationContext());
        }
        return instance;
    }
    
    /**
     * تهيئة إعدادات الأمان
     */
    private void initializeSecuritySettings() {
        securitySettings.put("encryption_enabled", "true");
        securitySettings.put("stealth_mode", "true");
        securitySettings.put("anti_detection", "true");
        securitySettings.put("secure_storage", "true");
    }
    
    /**
     * تفعيل الوضع الآمن
     */
    public boolean enableSecureMode() {
        try {
            Log.i(TAG, "Enabling secure mode");
            
            // تفعيل التشفير
            enableEncryption();
            
            // تفعيل التخزين الآمن
            enableSecureStorage();
            
            // تفعيل وضع التخفي
            enableStealthMode();
            
            // حفظ الإعدادات
            saveSecuritySettings();
            
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Error enabling secure mode", e);
            return false;
        }
    }
    
    /**
     * تعطيل الوضع الآمن
     */
    public boolean disableSecureMode() {
        try {
            Log.i(TAG, "Disabling secure mode");
            
            securitySettings.put("encryption_enabled", "false");
            securitySettings.put("stealth_mode", "false");
            securitySettings.put("anti_detection", "false");
            securitySettings.put("secure_storage", "false");
            
            saveSecuritySettings();
            
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Error disabling secure mode", e);
            return false;
        }
    }
    
    /**
     * تفعيل التشفير
     */
    private void enableEncryption() {
        securitySettings.put("encryption_enabled", "true");
        Log.d(TAG, "Encryption enabled");
    }
    
    /**
     * تفعيل التخزين الآمن
     */
    private void enableSecureStorage() {
        securitySettings.put("secure_storage", "true");
        Log.d(TAG, "Secure storage enabled");
    }
    
    /**
     * تفعيل وضع التخفي
     */
    private void enableStealthMode() {
        securitySettings.put("stealth_mode", "true");
        Log.d(TAG, "Stealth mode enabled");
    }
    
    /**
     * حفظ إعدادات الأمان
     */
    private void saveSecuritySettings() {
        try {
            for (Map.Entry<String, String> entry : securitySettings.entrySet()) {
                secureStorage.saveEncryptedString(entry.getKey(), entry.getValue());
            }
        } catch (Exception e) {
            Log.e(TAG, "Error saving security settings", e);
        }
    }
    
    /**
     * تحميل إعدادات الأمان
     */
    private void loadSecuritySettings() {
        try {
            for (String key : securitySettings.keySet()) {
                String value = secureStorage.getEncryptedString(key, "false");
                securitySettings.put(key, value);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error loading security settings", e);
        }
    }
    
    /**
     * فحص ما إذا كان التشفير مفعل
     */
    public boolean isEncryptionEnabled() {
        return "true".equals(securitySettings.get("encryption_enabled"));
    }
    
    /**
     * فحص ما إذا كان وضع التخفي مفعل
     */
    public boolean isStealthModeEnabled() {
        return "true".equals(securitySettings.get("stealth_mode"));
    }
    
    /**
     * فحص ما إذا كان مقاومة الاكتشاف مفعل
     */
    public boolean isAntiDetectionEnabled() {
        return "true".equals(securitySettings.get("anti_detection"));
    }
    
    /**
     * تشفير البيانات الحساسة
     */
    public String encryptSensitiveData(String data) {
        if (isEncryptionEnabled()) {
            return encryption.encrypt(data);
        }
        return data;
    }
    
    /**
     * فك تشفير البيانات الحساسة
     */
    public String decryptSensitiveData(String encryptedData) {
        if (isEncryptionEnabled()) {
            return encryption.decrypt(encryptedData);
        }
        return encryptedData;
    }
    
    /**
     * حفظ بيانات حساسة
     */
    public boolean saveSensitiveData(String key, String data) {
        if (isEncryptionEnabled()) {
            return secureStorage.saveEncryptedString(key, data);
        } else {
            // حفظ بدون تشفير (غير آمن)
            return secureStorage.saveEncryptedString(key, data);
        }
    }
    
    /**
     * قراءة بيانات حساسة
     */
    public String getSensitiveData(String key, String defaultValue) {
        return secureStorage.getEncryptedString(key, defaultValue);
    }
    
    /**
     * مسح جميع البيانات الحساسة
     */
    public boolean clearAllSensitiveData() {
        return secureStorage.clearAllEncryptedData();
    }
    
    /**
     * فحص سلامة النظام الأمني
     */
    public boolean performSecurityCheck() {
        try {
            Log.i(TAG, "Performing security check");
            
            // فحص سلامة التشفير
            if (!secureStorage.verifyDataIntegrity("security_check")) {
                Log.w(TAG, "Encryption integrity check failed");
                return false;
            }
            
            // فحص إعدادات الأمان
            loadSecuritySettings();
            
            Log.i(TAG, "Security check completed successfully");
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Security check failed", e);
            return false;
        }
    }
    
    /**
     * إعادة تعيين النظام الأمني
     */
    public boolean resetSecuritySystem() {
        try {
            Log.i(TAG, "Resetting security system");
            
            // مسح جميع البيانات
            clearAllSensitiveData();
            
            // إعادة تهيئة الإعدادات
            initializeSecuritySettings();
            
            // إعادة تفعيل الوضع الآمن
            enableSecureMode();
            
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Error resetting security system", e);
            return false;
        }
    }
}'''
        
        file_path = os.path.join(self.output_dir, "SecurityManager.java")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(manager_content)
        
        return file_path
    
    def generate_all_security_components(self) -> Dict[str, Any]:
        """توليد جميع مكونات الأمان"""
        
        components = {
            "advanced_encryption": self.generate_android_encryption_class(),
            "secure_storage": self.generate_secure_storage_class(),
            "security_manager": self.generate_security_manager()
        }
        
        # إنشاء ملف معلومات مكونات الأمان
        security_info = {
            "package_name": "com.stealth.security",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "components": [
                "AdvancedEncryption - نظام التشفير المتقدم",
                "SecureStorage - التخزين الآمن",
                "SecurityManager - مدير الأمان الشامل"
            ],
            "features": [
                "تشفير AES-256 متقدم",
                "تخزين آمن للبيانات الحساسة",
                "إدارة مفاتيح التشفير",
                "فحص سلامة البيانات",
                "تشفير الملفات",
                "حماية SharedPreferences"
            ],
            "files": list(components.values())
        }
        
        info_file = os.path.join(self.output_dir, "security_info.json")
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(security_info, f, ensure_ascii=False, indent=2)
        
        return security_info

# تشغيل مولد الأمان
if __name__ == "__main__":
    encryption_system = AdvancedEncryptionSystem()
    security_components = encryption_system.generate_all_security_components()
    
    print("تم توليد مكونات الأمان والتشفير:")
    for component in security_components["components"]:
        print(f"✓ {component}")
    
    # اختبار النظام
    print("\nاختبار نظام التشفير:")
    test_data = "هذا نص سري للاختبار"
    device_key = encryption_system.generate_device_key("test_device_123")
    
    encrypted = encryption_system.encrypt_data(test_data, device_key)
    print(f"البيانات المشفرة: {encrypted[:50]}...")
    
    decrypted = encryption_system.decrypt_data(encrypted, device_key)
    print(f"البيانات بعد فك التشفير: {decrypted}")
    
    print(f"نجح الاختبار: {test_data == decrypted}")

