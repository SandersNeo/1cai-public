# [NEXUS IDENTITY] ID: 507477995251717824 | DATE: 2025-11-19

"""
Health Monitoring Dashboard
Real-time dashboard для мониторинга состояния всех сервисов
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import plotly.graph_objs as go
import plotly.utils
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"

@dataclass
class DashboardService:
    """Данные сервиса для dashboard"""
    name: str
    status: ServiceStatus
    last_check: str
    response_time_ms: float
    uptime_percentage: float
    error_rate: float
    dependencies_count: int
    healthy_dependencies: int
    issues_count: int
    metrics: Dict[str, Any]

@dataclass
class DashboardMetrics:
    """Метрики для dashboard"""
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    critical_services: int
    overall_health_score: float
    average_response_time: float
    system_uptime: float
    active_incidents: int

@dataclass
class Incident:
    """Инцидент для dashboard"""
    id: str
    title: str
    severity: str
    affected_services: List[str]
    start_time: str
    status: str  # active, investigating, resolved
    description: str
    timeline: List[Dict[str, str]]

class HealthDashboardServer:
    """Сервер dashboard для мониторинга здоровья"""
    
    def __init__(self, health_manager=None):
        self.health_manager = health_manager
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'health-dashboard-secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.services_data = {}
        self.incidents = []
        self.metrics_history = []
        self.websocket_connections = set()
        
        self.setup_routes()
        self.setup_websocket_handlers()
        self.setup_background_tasks()
    
    def setup_routes(self):
        """Настройка HTTP routes"""
        
        @self.app.route('/')
        def dashboard_home():
            """Главная страница dashboard"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/services')
        def get_services():
            """API endpoint для получения списка сервисов"""
            return jsonify({
                'services': [
                    asdict(service) for service in self.services_data.values()
                ],
                'last_update': datetime.now().isoformat()
            })
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """API endpoint для получения общих метрик"""
            dashboard_metrics = self.calculate_dashboard_metrics()
            return jsonify(asdict(dashboard_metrics))
        
        @self.app.route('/api/incidents')
        def get_incidents():
            """API endpoint для получения активных инцидентов"""
            active_incidents = [inc for inc in self.incidents if inc['status'] != 'resolved']
            return jsonify({
                'incidents': active_incidents,
                'total_count': len(active_incidents)
            })
        
        @self.app.route('/api/history')
        def get_history():
            """API endpoint для получения истории метрик"""
            hours = int(request.args.get('hours', 24))
            return jsonify({
                'history': self.metrics_history[-hours*60:],  # Последние часы
                'period': f'{hours}h'
            })
        
        @self.app.route('/api/dependency-map')
        def get_dependency_map():
            """API endpoint для карты зависимостей"""
            return jsonify(self.generate_dependency_map())
        
        @self.app.route('/api/alerts', methods=['POST'])
        def handle_alert():
            """API endpoint для создания алертов"""
            data = request.json
            incident = self.create_incident(data)
            self.broadcast_incident(incident)
            return jsonify({'status': 'created', 'incident_id': incident['id']})
    
    def setup_websocket_handlers(self):
        """Настройка WebSocket handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Обработчик подключения клиента"""
            self.websocket_connections.add(request.sid)
            print(f"Client connected: {request.sid}")
            
            # Отправка текущего состояния при подключении
            self.send_current_state()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Обработчик отключения клиента"""
            self.websocket_connections.discard(request.sid)
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('subscribe_alerts')
        def handle_alert_subscription():
            """Подписка на алерты"""
            emit('subscription_confirmed', {'channel': 'alerts'})
        
        @self.socketio.on('request_service_details')
        def handle_service_details_request(service_name):
            """Запрос детальной информации о сервисе"""
            service_data = self.services_data.get(service_name)
            if service_data:
                emit('service_details', asdict(service_data))
    
    def setup_background_tasks(self):
        """Настройка фоновых задач для обновления данных"""
        
        @self.socketio.on('connect')
        def start_background_tasks():
            """Запуск фоновых задач при первом подключении"""
            if not hasattr(self, '_background_started'):
                self._background_started = True
                self.socketio.start_background_task(self.data_update_loop)
                self.socketio.start_background_task(self.metrics_update_loop)
    
    async def data_update_loop(self):
        """Фоновый цикл обновления данных"""
        while True:
            try:
                await self.update_services_data()
                self.broadcast_services_update()
                await asyncio.sleep(30)  # Обновление каждые 30 секунд
            except Exception as e:
                print(f"Error in data update loop: {e}")
                await asyncio.sleep(60)  # При ошибке ждать дольше
    
    async def metrics_update_loop(self):
        """Фоновый цикл обновления метрик"""
        while True:
            try:
                await self.update_metrics_history()
                self.broadcast_metrics_update()
                await asyncio.sleep(60)  # Обновление каждую минуту
            except Exception as e:
                print(f"Error in metrics update loop: {e}")
                await asyncio.sleep(120)
    
    async def update_services_data(self):
        """Обновление данных сервисов"""
        if self.health_manager:
            try:
                overall_health = await self.health_manager.get_overall_health()
                
                # Обновление данных сервисов
                for service_name, service_data in overall_health.get('services', {}).items():
                    service_info = DashboardService(
                        name=service_name,
                        status=ServiceStatus(service_data.get('status', 'unknown')),
                        last_check=service_data.get('last_check'),
                        response_time_ms=service_data.get('response_time_ms', 0),
                        uptime_percentage=95.0,  # Рассчитывается
                        error_rate=service_data.get('error_rate', 0),
                        dependencies_count=len(service_data.get('dependencies_status', {})),
                        healthy_dependencies=sum(
                            1 for status in service_data.get('dependencies_status', {}).values()
                            if status == 'healthy'
                        ),
                        issues_count=len(service_data.get('issues', [])),
                        metrics=service_data.get('metrics', {})
                    )
                    
                    self.services_data[service_name] = service_info
                
                # Обновление инцидентов
                self.update_incidents_from_health_data(overall_health)
                
            except Exception as e:
                print(f"Error updating services data: {e}")
        else:
            # Генерация демо данных если health_manager не предоставлен
            self.generate_demo_data()
    
    def update_incidents_from_health_data(self, health_data: Dict[str, Any]):
        """Обновление инцидентов на основе данных health"""
        new_issues = health_data.get('issues', [])
        
        # Преобразование проблем в инциденты
        for issue in new_issues:
            if issue.get('severity') in ['high', 'critical']:
                incident = {
                    'id': issue.get('id'),
                    'title': issue.get('title'),
                    'severity': issue.get('severity'),
                    'affected_services': issue.get('affected_services', []),
                    'start_time': issue.get('detected_at'),
                    'status': 'active',
                    'description': issue.get('description'),
                    'timeline': [
                        {
                            'timestamp': issue.get('detected_at'),
                            'event': 'Issue detected',
                            'description': issue.get('description')
                        }
                    ]
                }
                
                # Проверка существования инцидента
                existing_incident = next(
                    (inc for inc in self.incidents if inc['id'] == incident['id']), None
                )
                
                if not existing_incident:
                    self.incidents.append(incident)
    
    def generate_demo_data(self):
        """Генерация демо данных для тестирования"""
        import random
        
        demo_services = [
            'api-gateway', 'auth-service', 'user-service', 'notification-service',
            'ml-service', 'database-service', 'cache-service', 'file-service',
            'email-service', 'payment-service', 'analytics-service'
        ]
        
        status_weights = [0.7, 0.15, 0.1, 0.04, 0.01]  # healthy, degraded, unhealthy, critical, unknown
        
        for service_name in demo_services:
            status = random.choices(
                list(ServiceStatus),
                weights=status_weights
            )[0]
            
            service_info = DashboardService(
                name=service_name,
                status=status,
                last_check=datetime.now().isoformat(),
                response_time_ms=random.uniform(50, 500),
                uptime_percentage=random.uniform(95, 100),
                error_rate=random.uniform(0, 5),
                dependencies_count=random.randint(2, 8),
                healthy_dependencies=random.randint(1, 8),
                issues_count=random.randint(0, 3),
                metrics={
                    'cpu_usage': random.uniform(10, 90),
                    'memory_usage': random.uniform(20, 85),
                    'disk_usage': random.uniform(15, 70),
                    'network_io': random.uniform(1, 50)
                }
            )
            
            self.services_data[service_name] = service_info
    
    def calculate_dashboard_metrics(self) -> DashboardMetrics:
        """Вычисление общих метрик для dashboard"""
        
        total_services = len(self.services_data)
        healthy_count = sum(
            1 for s in self.services_data.values()
            if s.status == ServiceStatus.HEALTHY
        )
        degraded_count = sum(
            1 for s in self.services_data.values()
            if s.status == ServiceStatus.DEGRADED
        )
        unhealthy_count = sum(
            1 for s in self.services_data.values()
            if s.status == ServiceStatus.UNHEALTHY
        )
        critical_count = sum(
            1 for s in self.services_data.values()
            if s.status == ServiceStatus.CRITICAL
        )
        
        overall_score = sum(
            s.uptime_percentage for s in self.services_data.values()
        ) / max(1, total_services)
        
        avg_response_time = sum(
            s.response_time_ms for s in self.services_data.values()
        ) / max(1, total_services)
        
        system_uptime = sum(
            s.uptime_percentage for s in self.services_data.values()
        ) / max(1, total_services)
        
        active_incidents = len([
            inc for inc in self.incidents
            if inc['status'] == 'active'
        ])
        
        return DashboardMetrics(
            total_services=total_services,
            healthy_services=healthy_count,
            degraded_services=degraded_count,
            unhealthy_services=unhealthy_count,
            critical_services=critical_count,
            overall_health_score=overall_score,
            average_response_time=avg_response_time,
            system_uptime=system_uptime,
            active_incidents=active_incidents
        )
    
    async def update_metrics_history(self):
        """Обновление истории метрик"""
        metrics = self.calculate_dashboard_metrics()
        
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': metrics.overall_health_score,
            'healthy_services': metrics.healthy_services,
            'degraded_services': metrics.degraded_services,
            'unhealthy_services': metrics.unhealthy_services,
            'critical_services': metrics.critical_services,
            'avg_response_time': metrics.average_response_time,
            'active_incidents': metrics.active_incidents
        }
        
        self.metrics_history.append(history_entry)
        
        # Ограничение размера истории (хранить последние 7 дней)
        if len(self.metrics_history) > 10080:  # 7 дней * 24 часа * 60 минут
            self.metrics_history.pop(0)
    
    def broadcast_services_update(self):
        """Отправка обновлений сервисов через WebSocket"""
        services_data = {
            'services': [
                {
                    **asdict(service),
                    'status': service.status.value
                }
                for service in self.services_data.values()
            ],
            'last_update': datetime.now().isoformat()
        }
        
        self.socketio.emit('services_update', services_data)
    
    def broadcast_metrics_update(self):
        """Отправка обновлений метрик через WebSocket"""
        metrics = self.calculate_dashboard_metrics()
        metrics_data = asdict(metrics)
        
        self.socketio.emit('metrics_update', {
            'metrics': metrics_data,
            'timestamp': datetime.now().isoformat()
        })
    
    def broadcast_incident(self, incident: Dict[str, Any]):
        """Отправка уведомления об инциденте"""
        self.socketio.emit('incident_alert', incident, broadcast=True)
    
    def send_current_state(self):
        """Отправка текущего состояния при подключении"""
        # Отправка данных сервисов
        services_data = {
            'services': [
                {
                    **asdict(service),
                    'status': service.status.value
                }
                for service in self.services_data.values()
            ],
            'last_update': datetime.now().isoformat()
        }
        
        emit('services_update', services_data)
        
        # Отправка метрик
        metrics = self.calculate_dashboard_metrics()
        emit('metrics_update', {
            'metrics': asdict(metrics),
            'timestamp': datetime.now().isoformat()
        })
        
        # Отправка активных инцидентов
        active_incidents = [
            inc for inc in self.incidents
            if inc['status'] == 'active'
        ]
        emit('incidents_update', {
            'incidents': active_incidents,
            'total_count': len(active_incidents)
        })
    
    def generate_dependency_map(self) -> Dict[str, Any]:
        """Генерация карты зависимостей сервисов"""
        dependencies = {}
        
        for service_name, service_data in self.services_data.items():
            # Симуляция зависимостей (в реальной системе это должно приходить из health_manager)
            service_dependencies = []
            if service_name == 'api-gateway':
                service_dependencies = [
                    {'name': 'auth-service', 'status': 'healthy'},
                    {'name': 'user-service', 'status': 'healthy'},
                    {'name': 'database-service', 'status': 'degraded'}
                ]
            elif service_name == 'ml-service':
                service_dependencies = [
                    {'name': 'database-service', 'status': 'degraded'},
                    {'name': 'cache-service', 'status': 'healthy'}
                ]
            elif service_name == 'user-service':
                service_dependencies = [
                    {'name': 'database-service', 'status': 'degraded'},
                    {'name': 'cache-service', 'status': 'healthy'}
                ]
            
            dependencies[service_name] = service_dependencies
        
        return {
            'nodes': [
                {
                    'id': service_name,
                    'label': service_name,
                    'status': service_data.status.value,
                    'group': service_data.status.value
                }
                for service_name, service_data in self.services_data.items()
            ],
            'edges': [
                {'from': service, 'to': dep['name'], 'status': dep['status']}
                for service, deps in dependencies.items()
                for dep in deps
            ]
        }
    
    def create_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание нового инцидента"""
        incident = {
            'id': f"inc_{int(time.time())}",
            'title': data.get('title', 'Unknown Incident'),
            'severity': data.get('severity', 'medium'),
            'affected_services': data.get('affected_services', []),
            'start_time': datetime.now().isoformat(),
            'status': 'active',
            'description': data.get('description', ''),
            'timeline': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'event': 'Incident created',
                    'description': data.get('description', '')
                }
            ]
        }
        
        self.incidents.append(incident)
        return incident
    
    def create_plotly_charts(self) -> Dict[str, str]:
        """Создание графиков для dashboard"""
        
        # График тренда здоровья системы
        if self.metrics_history:
            timestamps = [entry['timestamp'] for entry in self.metrics_history]
            scores = [entry['overall_score'] for entry in self.metrics_history]
            
            health_trend = go.Scatter(
                x=timestamps,
                y=scores,
                mode='lines+markers',
                name='Health Score',
                line=dict(color='#2E8B57', width=2)
            )
            
            health_fig = go.Figure(data=[health_trend])
            health_fig.update_layout(
                title='System Health Trend',
                xaxis_title='Time',
                yaxis_title='Health Score (%)',
                template='plotly_dark'
            )
        else:
            health_fig = go.Figure()
        
        # График распределения статусов сервисов
        status_counts = {}
        for service in self.services_data.values():
            status = service.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        status_pie = go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            marker=dict(colors=['#2E8B57', '#FFD700', '#FFA500', '#FF4500', '#8B4513'])
        )
        
        status_fig = go.Figure(data=[status_pie])
        status_fig.update_layout(
            title='Service Status Distribution',
            template='plotly_dark'
        )
        
        # График времени ответа сервисов
        service_names = list(self.services_data.keys())
        response_times = [service.response_time_ms for service in self.services_data.values()]
        
        response_bar = go.Bar(
            x=service_names,
            y=response_times,
            name='Response Time (ms)',
            marker=dict(color='#4CAF50')
        )
        
        response_fig = go.Figure(data=[response_bar])
        response_fig.update_layout(
            title='Service Response Times',
            xaxis_title='Service',
            yaxis_title='Response Time (ms)',
            template='plotly_dark'
        )
        
        return {
            'health_trend': json.dumps(health_fig, cls=plotly.utils.PlotlyJSONEncoder),
            'status_distribution': json.dumps(status_fig, cls=plotly.utils.PlotlyJSONEncoder),
            'response_times': json.dumps(response_fig, cls=plotly.utils.PlotlyJSONEncoder)
        }
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Запуск dashboard сервера"""
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )

def create_dashboard_template():
    """Создание HTML шаблона для dashboard"""
    
    template = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Monitoring Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        
        .metric-value {
            font-size: 2.2rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .healthy { color: #2E8B57; }
        .degraded { color: #FFD700; }
        .unhealthy { color: #FFA500; }
        .critical { color: #FF4500; }
        .unknown { color: #8B4513; }
        
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .service-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
        }
        
        .service-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }
        
        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .service-name {
            font-size: 1.3rem;
            font-weight: bold;
            color: #333;
        }
        
        .service-status {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .service-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.9rem;
        }
        
        .service-metric {
            display: flex;
            justify-content: space-between;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .chart-title {
            font-size: 1.3rem;
            font-weight: bold;
            margin-bottom: 20px;
            text-align: center;
            color: #333;
        }
        
        .incidents-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .incidents-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .incidents-title {
            font-size: 1.5rem;
            font-weight: bold;
            color: #333;
        }
        
        .incident-badge {
            background: #FF4500;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9rem;
        }
        
        .incident-item {
            padding: 15px;
            border-left: 4px solid #FF4500;
            background: #FFF5F5;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .incident-title {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .incident-meta {
            font-size: 0.9rem;
            color: #666;
        }
        
        .loading {
            text-align: center;
            color: white;
            font-size: 1.2rem;
            padding: 50px;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            transform: scale(1.1);
            background: #45a049;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-healthy { background: #2E8B57; }
        .status-degraded { background: #FFD700; }
        .status-unhealthy { background: #FFA500; }
        .status-critical { background: #FF4500; }
        .status-unknown { background: #8B4513; }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1><i class="fas fa-heartbeat"></i> Health Monitoring Dashboard</h1>
            <p>Real-time monitoring of system health and service status</p>
        </div>
        
        <div id="metrics-section" class="metrics-grid">
            <!-- Метрики будут загружены динамически -->
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">System Health Trend</div>
                <div id="health-chart"></div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Service Status Distribution</div>
                <div id="status-chart"></div>
            </div>
        </div>
        
        <div class="services-grid" id="services-section">
            <!-- Сервисы будут загружены динамически -->
        </div>
        
        <div class="incidents-section">
            <div class="incidents-header">
                <div class="incidents-title">
                    <i class="fas fa-exclamation-triangle"></i> Active Incidents
                </div>
                <div class="incident-badge" id="incident-count">0</div>
            </div>
            <div id="incidents-list">
                <!-- Инциденты будут загружены динамически -->
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshDashboard()">
        <i class="fas fa-sync-alt"></i>
    </button>
    
    <script>
        const socket = io();
        
        // Инициализация при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            loadInitialData();
        });
        
        function connectWebSocket() {
            socket.on('connect', function() {
                console.log('Connected to dashboard server');
            });
            
            socket.on('services_update', function(data) {
                updateServices(data.services);
            });
            
            socket.on('metrics_update', function(data) {
                updateMetrics(data.metrics);
            });
            
            socket.on('incident_alert', function(incident) {
                showIncidentAlert(incident);
            });
        }
        
        function loadInitialData() {
            // Загрузка начальных данных через REST API
            fetch('/api/services')
                .then(response => response.json())
                .then(data => updateServices(data.services))
                .catch(error => console.error('Error loading services:', error));
            
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => updateMetrics(data))
                .catch(error => console.error('Error loading metrics:', error));
        }
        
        function updateMetrics(metrics) {
            const metricsSection = document.getElementById('metrics-section');
            
            metricsSection.innerHTML = `
                <div class="metric-card">
                    <div class="metric-icon healthy">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="metric-value healthy">${metrics.healthy_services}</div>
                    <div class="metric-label">Healthy Services</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-icon">
                        <div class="metric-value degraded">${metrics.degraded_services}</div>
                        <div class="metric-label">Degraded Services</div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-icon unhealthy">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="metric-value unhealthy">${metrics.unhealthy_services}</div>
                    <div class="metric-label">Unhealthy Services</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-icon critical">
                        <i class="fas fa-times-circle"></i>
                    </div>
                    <div class="metric-value critical">${metrics.critical_services}</div>
                    <div class="metric-label">Critical Services</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-icon">
                        <i class="fas fa-heartbeat"></i>
                    </div>
                    <div class="metric-value">${Math.round(metrics.overall_health_score)}%</div>
                    <div class="metric-label">Overall Health Score</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="metric-value">${Math.round(metrics.average_response_time)}ms</div>
                    <div class="metric-label">Avg Response Time</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-icon">
                        <i class="fas fa-percentage"></i>
                    </div>
                    <div class="metric-value">${Math.round(metrics.system_uptime)}%</div>
                    <div class="metric-label">System Uptime</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-icon">
                        <i class="fas fa-fire"></i>
                    </div>
                    <div class="metric-value">${metrics.active_incidents}</div>
                    <div class="metric-label">Active Incidents</div>
                </div>
            `;
        }
        
        function updateServices(services) {
            const servicesSection = document.getElementById('services-section');
            
            servicesSection.innerHTML = services.map(service => `
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-name">
                            <span class="status-indicator status-${service.status}"></span>
                            ${service.name}
                        </div>
                        <div class="service-status ${service.status}">${service.status}</div>
                    </div>
                    
                    <div class="service-metrics">
                        <div class="service-metric">
                            <span>Response Time:</span>
                            <span>${Math.round(service.response_time_ms)}ms</span>
                        </div>
                        <div class="service-metric">
                            <span>Uptime:</span>
                            <span>${Math.round(service.uptime_percentage)}%</span>
                        </div>
                        <div class="service-metric">
                            <span>Error Rate:</span>
                            <span>${service.error_rate.toFixed(1)}%</span>
                        </div>
                        <div class="service-metric">
                            <span>Issues:</span>
                            <span>${service.issues_count}</span>
                        </div>
                        <div class="service-metric">
                            <span>Dependencies:</span>
                            <span>${service.healthy_dependencies}/${service.dependencies_count}</span>
                        </div>
                        <div class="service-metric">
                            <span>Last Check:</span>
                            <span>${new Date(service.last_check).toLocaleTimeString()}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        function showIncidentAlert(incident) {
            // Добавить новое уведомление об инциденте
            console.log('New incident:', incident);
            loadInitialData(); // Перезагрузка данных
        }
        
        function refreshDashboard() {
            loadInitialData();
            location.reload();
        }
    </script>
</body>
</html>
    """
    
    return template

if __name__ == "__main__":
    # Создание шаблона
    template = create_dashboard_template()
    
    # Сохранение шаблона
    import os
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(template)
    
    # Создание и запуск dashboard
    dashboard = HealthDashboardServer()
    print("Starting Health Monitoring Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    
    dashboard.run(host='0.0.0.0', port=5000, debug=True)