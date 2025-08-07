#!/usr/bin/env python3
"""
Integrated Telegram Bot for Advanced Monitoring System
بوت تليجرام متكامل لنظام المراقبة المتقدم
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import aiohttp
import json
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    token: str
    api_url: str
    admin_users: list = None
    
    def __post_init__(self):
        if self.admin_users is None:
            self.admin_users = []

class IntegratedMonitoringBot:
    def __init__(self, config: BotConfig):
        self.config = config
        self.session = None
        self.application = Application.builder().token(config.token).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        handlers = [
            CommandHandler("start", self.handle_start),
            CommandHandler("help", self.handle_help),
            CommandHandler("analytics", self.handle_analytics),
            CommandHandler("devices", self.handle_devices),
            CommandHandler("status", self.handle_status),
            CommandHandler("security", self.handle_security),
            CommandHandler("performance", self.handle_performance),
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)
    
    async def make_api_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"{self.config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url) as response:
                    return await response.json()
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = (
            "🎯 مرحباً بك في نظام المراقبة المتقدم!\n"
            "Welcome to Advanced Monitoring System!\n\n"
            "الأوامر المتاحة - Available Commands:\n"
            "/analytics - التحليل الشامل\n"
            "/devices - إدارة الأجهزة\n"
            "/status - حالة النظام\n"
            "/security - حالة الأمان\n"
            "/performance - مقاييس الأداء\n"
            "/help - المساعدة"
        )
        await update.message.reply_text(message)
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = (
            "📚 دليل الاستخدام - User Guide:\n\n"
            "🔍 **التحليل والمراقبة - Analysis & Monitoring:**\n"
            "• /analytics - عرض التحليل الشامل للبيانات\n"
            "• /devices - عرض وإدارة الأجهزة\n"
            "• /status - حالة النظام العام\n\n"
            "🛡️ **الأمان والأداء - Security & Performance:**\n"
            "• /security - حالة الأمان والتهديدات\n"
            "• /performance - مقاييس الأداء والموارد\n\n"
            "💡 **نصائح - Tips:**\n"
            "• النظام يدعم التنبيهات التلقائية للتهديدات\n"
            "• System supports automatic threat alerts"
        )
        await update.message.reply_text(message)
    
    async def handle_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = await self.make_api_request('/api/dashboard/stats')
            if 'error' in response:
                await update.message.reply_text(f"❌ خطأ في الحصول على التحليل: {response['error']}")
                return
            
            message = (
                "📊 **التحليل الشامل - Comprehensive Analytics:**\n\n"
                f"📈 **الأجهزة النشطة - Active Devices:** {response.get('active_devices', 0)}\n"
                f"📱 **إجمالي الأجهزة - Total Devices:** {response.get('total_devices', 0)}\n"
                f"📝 **إجمالي التسجيلات - Total Recordings:** {response.get('total_recordings', 0)}\n"
                f"📸 **لقطات الشاشة - Screenshots:** {response.get('screenshots', 0)}\n"
                f"📍 **تحديثات الموقع - Location Updates:** {response.get('locations', 0)}\n\n"
                "💡 استخدم /devices لإدارة الأجهزة"
            )
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الحصول على التحليل: {str(e)}")
    
    async def handle_devices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = await self.make_api_request('/api/devices')
            if 'error' in response:
                await update.message.reply_text(f"❌ خطأ في قائمة الأجهزة: {response['error']}")
                return
            
            devices = response.get('devices', [])
            if not devices:
                await update.message.reply_text("📱 لا توجد أجهزة مسجلة حالياً\nNo devices registered currently")
                return
            
            message = "📱 **الأجهزة المسجلة - Registered Devices:**\n\n"
            for i, device in enumerate(devices[:5], 1):
                status_emoji = "🟢" if device.get('status') == 'online' else "🔴"
                message += (
                    f"{i}. {status_emoji} **{device.get('device_name', 'Unknown')}**\n"
                    f"   📱 ID: {device.get('device_id', 'N/A')}\n"
                    f"   📍 Location: {device.get('location', 'Unknown')}\n"
                    f"   ⏰ Last Seen: {device.get('last_seen', 'Never')}\n\n"
                )
            
            if len(devices) > 5:
                message += f"... و {len(devices) - 5} جهاز آخر\n... and {len(devices) - 5} more devices"
            
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في قائمة الأجهزة: {str(e)}")
    
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = await self.make_api_request('/api/system/status')
            if 'error' in response:
                await update.message.reply_text(f"❌ خطأ في حالة النظام: {response['error']}")
                return
            
            message = (
                "🖥️ **حالة النظام - System Status:**\n\n"
                f"🟢 **الحالة العامة - Overall Status:** {response.get('status', 'مستقر')}\n"
                f"📊 **استخدام المعالج - CPU Usage:** {response.get('cpu_usage', '0%')}\n"
                f"💾 **استخدام الذاكرة - Memory Usage:** {response.get('memory_usage', '0%')}\n"
                f"💿 **مساحة التخزين - Storage Usage:** {response.get('storage_usage', '0%')}\n"
                f"🌐 **حالة الشبكة - Network Status:** {response.get('network_status', 'مستقر')}\n"
                f"📱 **الأجهزة المتصلة - Connected Devices:** {response.get('connected_devices', 0)}\n"
                f"⏰ **وقت التشغيل - Uptime:** {response.get('uptime', 'غير محدد')}\n\n"
                "💡 استخدم /help للحصول على المساعدة"
            )
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حالة النظام: {str(e)}")
    
    async def handle_security(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = await self.make_api_request('/api/security/status')
            if 'error' in response:
                await update.message.reply_text(f"❌ خطأ في حالة الأمان: {response['error']}")
                return
            
            message = (
                "🛡️ **حالة الأمان - Security Status:**\n\n"
                f"🟢 **الحالة العامة - Overall Status:** {response.get('overall_status', 'آمن')}\n"
                f"⚠️ **التهديدات النشطة - Active Threats:** {response.get('active_threats', 0)}\n"
                f"🔒 **الأجهزة المحمية - Protected Devices:** {response.get('protected_devices', 0)}\n"
                f"🚨 **التنبيهات الأمنية - Security Alerts:** {response.get('security_alerts', 0)}\n"
                f"📊 **مستوى الحماية - Protection Level:** {response.get('protection_level', 'متوسط')}\n"
                f"🕒 **آخر فحص - Last Scan:** {response.get('last_scan', 'غير محدد')}\n\n"
                "💡 استخدم /performance لمراقبة الأداء"
            )
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حالة الأمان: {str(e)}")
    
    async def handle_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = await self.make_api_request('/api/performance/metrics')
            if 'error' in response:
                await update.message.reply_text(f"❌ خطأ في مقاييس الأداء: {response['error']}")
                return
            
            message = (
                "📊 **مقاييس الأداء - Performance Metrics:**\n\n"
                f"⚡ **استخدام المعالج - CPU Usage:** {response.get('cpu_usage', '0%')}\n"
                f"💾 **استخدام الذاكرة - Memory Usage:** {response.get('memory_usage', '0%')}\n"
                f"💿 **استخدام التخزين - Storage Usage:** {response.get('storage_usage', '0%')}\n"
                f"🌐 **استخدام الشبكة - Network Usage:** {response.get('network_usage', '0%')}\n"
                f"🔋 **مستوى البطارية - Battery Level:** {response.get('battery_level', '0%')}\n"
                f"📱 **الأجهزة النشطة - Active Devices:** {response.get('active_devices', 0)}\n\n"
                "💡 استخدم /analytics للتحليل الشامل"
            )
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في مقاييس الأداء: {str(e)}")
    
    async def run(self):
        logger.info("Starting integrated monitoring bot...")
        await self.application.run_polling()

def main():
    config = BotConfig(
        token=os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here'),
        api_url=os.getenv('API_URL', 'http://localhost:5000'),
        admin_users=[int(x) for x in os.getenv('ADMIN_USERS', '').split(',') if x.strip()]
    )
    
    bot = IntegratedMonitoringBot(config)
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()
