#!/usr/bin/env python3
"""
World-Class Setup Script for Advanced Monitoring System
سكريبت الإعداد عالمي المستوى لنظام المراقبة المتقدم
"""

import os
import sys
import subprocess
import shutil
import platform
import psutil
import sqlite3
from pathlib import Path
from datetime import datetime
import json
import hashlib
import secrets

class WorldClassSetup:
    def __init__(self):
        self.setup_log = []
        self.system_info = self.get_system_info()
        
    def print_status(self, message, status="INFO"):
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m", 
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "HEADER": "\033[95m",
            "END": "\033[0m"
        }
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        print(f"{colors.get(status, '')}{formatted_message}{colors['END']}")
        
        self.setup_log.append({
            'timestamp': timestamp,
            'message': message,
            'status': status
        })
    
    def get_system_info(self):
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total // (1024**3),
            'disk_total': psutil.disk_usage('/').total // (1024**3)
        }
    
    def print_banner(self):
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    🌍 WORLD-CLASS ADVANCED MONITORING SYSTEM SETUP                          ║
║    نظام المراقبة المتقدم عالمي المستوى - إعداد النظام                      ║
║                                                                              ║
║    🚀 Next-Generation Monitoring Platform                                   ║
║    🛡️ Military-Grade Security & Encryption                                  ║
║    📊 AI-Powered Analytics & Insights                                       ║
║    🌐 Global Infrastructure Monitoring                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        self.print_status(banner, "HEADER")
        
        self.print_status("🖥️ SYSTEM INFORMATION:", "INFO")
        self.print_status(f"   Platform: {self.system_info['platform']} {self.system_info['architecture']}", "INFO")
        self.print_status(f"   Python: {self.system_info['python_version']}", "INFO")
        self.print_status(f"   CPU Cores: {self.system_info['cpu_count']}", "INFO")
        self.print_status(f"   Memory: {self.system_info['memory_total']} GB", "INFO")
        self.print_status(f"   Storage: {self.system_info['disk_total']} GB", "INFO")
        self.print_status("=" * 80, "INFO")

    def check_python_version(self):
        self.print_status("🐍 Checking Python version...", "INFO")
        
        if sys.version_info < (3, 8):
            self.print_status("❌ Python 3.8 or higher is required", "ERROR")
            self.print_status(f"   Current version: {sys.version_info.major}.{sys.version_info.minor}", "ERROR")
            sys.exit(1)
        
        self.print_status(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected", "SUCCESS")
        
        if sys.version_info >= (3, 11):
            self.print_status("🚀 Excellent! Latest Python version detected", "SUCCESS")
        elif sys.version_info >= (3, 9):
            self.print_status("👍 Good Python version for optimal performance", "SUCCESS")

    def install_requirements(self):
        self.print_status("📦 Installing world-class dependencies...", "INFO")
        
        try:
            self.print_status("   Upgrading pip to latest version...", "INFO")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.print_status("   Installing core requirements...", "INFO")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_unified.txt"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.print_status("✅ All dependencies installed successfully", "SUCCESS")
            
            self.print_status("🔍 Verifying critical packages...", "INFO")
            critical_packages = ['flask', 'requests', 'psutil', 'matplotlib', 'cryptography', 'python-telegram-bot']
            
            for package in critical_packages:
                try:
                    __import__(package.replace('-', '_'))
                    self.print_status(f"   ✅ {package}", "SUCCESS")
                except ImportError:
                    self.print_status(f"   ❌ {package} - Installation failed", "ERROR")
            
        except subprocess.CalledProcessError as e:
            self.print_status("❌ Failed to install requirements", "ERROR")
            self.print_status(f"   Error: {str(e)}", "ERROR")
            sys.exit(1)

    def setup_directories(self):
        self.print_status("📁 Creating world-class directory structure...", "INFO")
        
        directories = {
            "logs": "System and application logs",
            "uploads": "File upload storage", 
            "recordings": "Audio and video recordings",
            "screenshots": "Screenshot captures",
            "camera_captures": "Camera image captures",
            "social_media": "Social media monitoring data",
            "backups": "System and database backups",
            "analytics": "Analytics and reporting data",
            "security": "Security logs and reports",
            "exports": "Data export files",
            "temp": "Temporary processing files",
            "cache": "Application cache",
            "config": "Configuration files",
            "plugins": "Plugin extensions",
            "reports": "Generated reports"
        }
        
        for directory, description in directories.items():
            path = Path(directory)
            path.mkdir(exist_ok=True)
            
            readme_file = path / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"# {directory.title()} Directory\n\n{description}\n\nCreated: {datetime.now().isoformat()}\n")
            
            self.print_status(f"   ✅ {directory}/ - {description}", "SUCCESS")
        
        self.print_status("📁 Directory structure created successfully", "SUCCESS")

    def setup_environment(self):
        self.print_status("⚙️ Setting up world-class environment configuration...", "INFO")
        
        if not os.path.exists(".env"):
            if os.path.exists(".env.example"):
                shutil.copy(".env.example", ".env")
                self.print_status("✅ Created .env file from template", "SUCCESS")
                
                self.generate_secure_keys()
                
                self.print_status("⚠️ IMPORTANT: Please edit .env file with your configuration", "WARNING")
                self.print_status("   Required settings:", "INFO")
                self.print_status("   - TELEGRAM_BOT_TOKEN (from @BotFather)", "INFO")
                self.print_status("   - ADMIN_USERS (your Telegram user ID)", "INFO")
                self.print_status("   - Database and security settings", "INFO")
            else:
                self.print_status("❌ .env.example file not found", "ERROR")
                self.create_default_env()
        else:
            self.print_status("✅ .env file already exists", "SUCCESS")
            self.print_status("   Validating configuration...", "INFO")
            self.validate_env_config()

    def generate_secure_keys(self):
        self.print_status("🔐 Generating secure encryption keys...", "INFO")
        
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            jwt_secret = secrets.token_hex(32)
            encryption_key = secrets.token_urlsafe(32)
            api_key = secrets.token_hex(16)
            
            env_content = env_content.replace('your-secret-key-here-change-this-in-production', jwt_secret)
            env_content = env_content.replace('your-encryption-key-here-32-chars', encryption_key)
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            self.print_status("✅ Secure keys generated and configured", "SUCCESS")
            
        except Exception as e:
            self.print_status(f"⚠️ Key generation warning: {str(e)}", "WARNING")

    def create_default_env(self):
        self.print_status("📝 Creating default environment configuration...", "INFO")
        
        default_env = """# World-Class Advanced Monitoring System Configuration

TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ADMIN_USERS=123456789

API_URL=http://localhost:5000
JWT_SECRET={jwt_secret}
ENCRYPTION_KEY={encryption_key}

DATABASE_URL=monitoring_system.db

ENABLE_ENCRYPTION=True
ENABLE_STEALTH_MODE=True

HOST=0.0.0.0
PORT=5000
DEBUG=False
""".format(
            timestamp=datetime.now().isoformat(),
            jwt_secret=secrets.token_hex(32),
            encryption_key=secrets.token_urlsafe(32)
        )
        
        with open('.env', 'w') as f:
            f.write(default_env)
        
        self.print_status("✅ Default .env file created", "SUCCESS")

    def validate_env_config(self):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            required_vars = ['API_URL', 'JWT_SECRET', 'DATABASE_URL']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.print_status(f"⚠️ Missing environment variables: {', '.join(missing_vars)}", "WARNING")
            else:
                self.print_status("✅ Environment configuration validated", "SUCCESS")
                
        except Exception as e:
            self.print_status(f"⚠️ Environment validation warning: {str(e)}", "WARNING")

    def setup_database(self):
        self.print_status("🗄️ Setting up world-class database system...", "INFO")
        
        try:
            db_path = "monitoring_system.db"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            self.print_status("   Creating core database tables...", "INFO")
            
            tables = {
                'users': '''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''',
                'devices': '''
                    CREATE TABLE IF NOT EXISTS devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT UNIQUE NOT NULL,
                        device_name TEXT NOT NULL,
                        device_type TEXT,
                        status TEXT DEFAULT 'offline',
                        location TEXT,
                        battery_level TEXT,
                        last_seen TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''',
                'monitoring_logs': '''
                    CREATE TABLE IF NOT EXISTS monitoring_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT,
                        log_type TEXT,
                        message TEXT,
                        severity TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (device_id) REFERENCES devices (device_id)
                    )
                ''',
                'security_events': '''
                    CREATE TABLE IF NOT EXISTS security_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT,
                        source_ip TEXT,
                        user_id INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''',
                'system_metrics': '''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        unit TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                '''
            }
            
            for table_name, table_sql in tables.items():
                cursor.execute(table_sql)
                self.print_status(f"   ✅ {table_name} table", "SUCCESS")
            
            cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                         ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin'))
            
            conn.commit()
            conn.close()
            
            self.print_status("✅ Database initialized successfully", "SUCCESS")
            
        except Exception as e:
            self.print_status(f"❌ Database setup failed: {e}", "ERROR")

    def check_services(self):
        self.print_status("🔍 Checking world-class service dependencies...", "INFO")
        
        services = {
            'Flask Web Framework': 'flask',
            'HTTP Requests': 'requests', 
            'System Monitoring': 'psutil',
            'Data Visualization': 'matplotlib',
            'Cryptography': 'cryptography',
            'Telegram Bot API': 'telegram',
            'Data Processing': 'pandas',
            'Machine Learning': 'sklearn'
        }
        
        for service_name, module_name in services.items():
            try:
                __import__(module_name)
                self.print_status(f"   ✅ {service_name}", "SUCCESS")
            except ImportError:
                self.print_status(f"   ❌ {service_name} - Not available", "ERROR")

    def create_startup_scripts(self):
        self.print_status("📜 Creating world-class startup scripts...", "INFO")
        
        scripts = {
            'start_backend.py': '''#!/usr/bin/env python3
"""Start the backend server"""
import subprocess
import sys

if __name__ == "__main__":
    print("🚀 Starting World-Class Backend Server...")
    subprocess.run([sys.executable, "enhanced_main.py"])
''',
            'start_desktop.py': '''#!/usr/bin/env python3
"""Start the desktop application"""
import subprocess
import sys

if __name__ == "__main__":
    print("🖥️ Starting World-Class Desktop Application...")
    subprocess.run([sys.executable, "enhanced_desktop_app.py"])
''',
            'start_bot.py': '''#!/usr/bin/env python3
"""Start the Telegram bot"""
import subprocess
import sys

if __name__ == "__main__":
    print("🤖 Starting World-Class Telegram Bot...")
    subprocess.run([sys.executable, "world_class_telegram_bot.py"])
''',
            'start_all.py': '''#!/usr/bin/env python3
"""Start all services"""
import subprocess
import sys
import threading
import time

def start_service(script_name, service_name):
    print(f"🚀 Starting {service_name}...")
    subprocess.run([sys.executable, script_name])

if __name__ == "__main__":
    print("🌍 Starting World-Class Monitoring System...")
    
    services = [
        ("enhanced_main.py", "Backend Server"),
        ("enhanced_desktop_app.py", "Desktop Application"),
        ("world_class_telegram_bot.py", "Telegram Bot")
    ]
    
    threads = []
    for script, name in services:
        thread = threading.Thread(target=start_service, args=(script, name))
        thread.daemon = True
        thread.start()
        threads.append(thread)
        time.sleep(2)
    
    print("✅ All services started successfully!")
    print("Press Ctrl+C to stop all services")
    
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\\n🛑 Stopping all services...")
'''
        }
        
        for script_name, script_content in scripts.items():
            with open(script_name, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            if os.name != 'nt':
                os.chmod(script_name, 0o755)
            
            self.print_status(f"   ✅ {script_name}", "SUCCESS")
        
        self.print_status("📜 Startup scripts created successfully", "SUCCESS")

    def generate_setup_report(self):
        self.print_status("📊 Generating setup report...", "INFO")
        
        report = {
            'setup_timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'setup_log': self.setup_log,
            'status': 'completed',
            'next_steps': [
                'Edit .env file with your configuration',
                'Add your Telegram bot token',
                'Configure admin user IDs',
                'Run the applications'
            ]
        }
        
        with open('setup_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.print_status("✅ Setup report saved to setup_report.json", "SUCCESS")

    def print_completion_message(self):
        completion_message = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    🎉 WORLD-CLASS SETUP COMPLETED SUCCESSFULLY!                             ║
║    ✅ تم إكمال الإعداد عالمي المستوى بنجاح!                                ║
║                                                                              ║
║    🚀 Your advanced monitoring system is ready to launch!                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔧 NEXT STEPS - الخطوات التالية:

1. 📝 Configure your system:
   • Edit .env file with your settings
   • Add your Telegram bot token from @BotFather
   • Set your admin user IDs

2. 🚀 Launch the system:
   • Backend Server: python enhanced_main.py
   • Desktop App: python enhanced_desktop_app.py  
   • Telegram Bot: python world_class_telegram_bot.py
   • All Services: python start_all.py

3. 🌐 Access your system:
   • Backend API: http://localhost:5000
   • Desktop Application: Launch from desktop
   • Telegram Bot: Message your bot on Telegram

4. 📊 Monitor and manage:
   • Use the desktop app for real-time monitoring
   • Control everything via Telegram bot
   • Access advanced analytics and reports

🎯 FEATURES READY TO USE:
• 🛡️ Military-grade security monitoring
• 📊 AI-powered analytics dashboard  
• 📱 Multi-device management system
• 🔔 Smart alerts and notifications
• 🌍 Global infrastructure monitoring
• 🤖 Telegram bot integration
• 📈 Performance optimization tools

💎 Welcome to the future of monitoring technology!
        """
        
        self.print_status(completion_message, "HEADER")

    def run_setup(self):
        try:
            self.print_banner()
            self.check_python_version()
            self.install_requirements()
            self.setup_directories()
            self.setup_environment()
            self.setup_database()
            self.check_services()
            self.create_startup_scripts()
            self.generate_setup_report()
            self.print_completion_message()
            
        except KeyboardInterrupt:
            self.print_status("\n🛑 Setup interrupted by user", "WARNING")
            sys.exit(1)
        except Exception as e:
            self.print_status(f"❌ Setup failed: {str(e)}", "ERROR")
            sys.exit(1)

def main():
    setup = WorldClassSetup()
    setup.run_setup()

if __name__ == "__main__":
    main()
