# 🏥 Комплексная система Health Checks

> **Продвинутая система мониторинга здоровья сервисов** с автоматическим восстановлением, Kubernetes интеграцией и real-time dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-orange.svg)](https://flask.palletsprojects.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28+-blue.svg)](https://kubernetes.io/)

## 📋 Содержание

- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Быстрый старт](#-быстрый-старт)
- [Интеграция](#-интеграция)
- [Компоненты системы](#-компоненты-системы)
- [Kubernetes интеграция](#-kubernetes-интеграция)
- [Мониторинг и алерты](#-мониторинг-и-алерты)
- [Примеры](#-примеры)
- [Документация](#-документация)

## 🚀 Возможности

### ✅ Основные функции

- **🔍 Комплексный мониторинг** - от системных метрик до бизнес-показателей
- **🔄 Автоматическое восстановление** - self-healing механизмы при проблемах
- **⚡ Kubernetes Probes** - готовые Liveness, Readiness и Startup probes
- **📊 Real-time Dashboard** - веб-интерфейс с live обновлениями
- **🔒 Circuit Breaker** - защита от каскадных отказов
- **📈 Метрики и тренды** - исторические данные и аналитика
- **🚨 Умные алерты** - персонализированные уведомления
- **🛡️ Безопасность** - защита sensitive данных и rate limiting

### 🎯 Типы проверок здоровья

1. **Basic Health** - базовое состояние сервиса
2. **Dependencies** - БД, Redis, внешние API, внутренние сервисы
3. **Business Logic** - критические бизнес-функции
4. **Performance** - время отклика, память, нагрузка
5. **Custom Metrics** - пользовательские бизнес-показатели

### 🔧 Автоматическое восстановление

- **Перезапуск сервисов** (Pod, Container, SystemD)
- **Очистка кэша** (Redis, Memory, Application)
- **Переключение трафика** (Traffic Switching)
- **Graceful Degradation** - постепенное ухудшение функций
- **Emergency Procedures** - процедуры экстренного восстановления

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Health Check System                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Basic     │  │Dependencies │  │  Business   │          │
│  │   Health    │  │   Health    │  │   Health    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │Performance  │  │Custom       │  │Comprehensive│          │
│  │   Health    │  │   Metrics   │  │   Health    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   Health Check Manager                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Issue       │  │Recommendation│  │ Alert       │          │
│  │ Detector    │  │   Engine    │  │ System      │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                  Automated Recovery System                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Circuit     │  │ Self-Healing│  │ Emergency   │          │
│  │  Breaker    │  │ Mechanisms  │  │Procedures   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                  Dashboard & Monitoring                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Real-time │  │ Historical  │  │ Dependency  │          │
│  │  Dashboard  │  │   Trends    │  │   Mapping   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## ⚡ Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Минимальный пример (FastAPI)

```python
from fastapi import FastAPI
from health_check import setup_health_checks_for_service

# Создание приложения с health checks
app = setup_health_checks_for_service(
    service_name="my-api",
    framework="fastapi",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Hello World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Комплексный пример

```python
import asyncio
from health_check import HealthCheckSystem

async def main():
    # Создание системы health checks
    config = {
        'dashboard': {'enabled': True, 'port': 5000},
        'recovery': {'enabled': True, 'auto_recovery': True}
    }
    
    health_system = HealthCheckSystem(config)
    
    # Регистрация кастомного health check
    async def my_health_check():
        return {
            'service_name': 'my-service',
            'status': 'healthy',
            'cpu_percent': 45.2,
            'memory_percent': 67.8,
            'response_time_ms': 250
        }
    
    health_system.register_service('my-service', my_health_check)
    
    # Запуск мониторинга
    await health_system.start_monitoring()
    
    # Генерация Kubernetes конфигураций
    k8s_configs = health_system.generate_kubernetes_configs(
        service_type='api_gateway',
        service_name='my-api'
    )
    
    # Запуск dashboard
    health_system.start_dashboard(port=5000)

asyncio.run(main())
```

### Flask интеграция

```python
from flask import Flask
from health_check import setup_health_checks_for_service

app = setup_health_checks_for_service(
    service_name="my-flask-app",
    framework="flask",
    version="1.0.0"
)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## 🔧 Интеграция

### Существующее FastAPI приложение

```python
from fastapi import FastAPI
from health_check import HealthCheckSystem

# Существующее приложение
app = FastAPI()

@app.get("/api/users")
async def get_users():
    return {"users": []}

# Интеграция health checks
health_system = HealthCheckSystem()
health_system.setup_fastapi_app(app, "my-api", "1.0.0")

# Регистрация сервиса
async def api_health():
    return {
        'service_name': 'my-api',
        'status': 'healthy',
        'users_count': len(await get_users()),
        'response_time_ms': 150
    }

health_system.register_service('my-api', api_health)
```

### Интеграция с Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  template:
    spec:
      containers:
      - name: my-service
        image: myregistry.com/my-service:v1.0.0
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health/basic
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/dependencies
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Генерация конфигураций

```python
from health_check.kubernetes import generate_all_k8s_configs

# Генерация всех конфигураций
configs = generate_all_k8s_configs(
    service_type='api_gateway',
    service_name='my-api',
    custom_config={
        'image': 'myregistry.com/my-api:v1.0.0',
        'env': [{'name': 'LOG_LEVEL', 'value': 'INFO'}]
    }
)

# Сохранение файлов
for config_name, config_content in configs.items():
    with open(f'{config_name}.yaml', 'w') as f:
        f.write(config_content)
```

## 📦 Компоненты системы

### 1. Health Check Endpoints

#### Basic Health Checker

```python
from health_check.endpoints import BasicHealthChecker

checker = BasicHealthChecker("my-service", "1.0.0")
health_info = checker.check()

print(f"Status: {health_info.status}")
print(f"CPU: {health_info.cpu_percent}%")
print(f"Memory: {health_info.memory_usage_mb}MB")
```

#### Dependencies Health Checker

```python
from health_check.endpoints import DependenciesHealthChecker

config = {
    'databases': [
        {
            'name': 'postgres',
            'host': 'postgres-service',
            'port': 5432,
            'user': 'user',
            'password': 'password',
            'database': 'app_db'
        }
    ],
    'redis': [
        {
            'name': 'redis',
            'host': 'redis-service',
            'port': 6379
        }
    ]
}

checker = DependenciesHealthChecker(config)
health_info = await checker.async_check()
```

### 2. Health Check Manager

```python
from health_check.manager import HealthCheckManager

manager = HealthCheckManager()

# Регистрация сервиса
async def my_health_check():
    return {
        'service_name': 'my-service',
        'status': 'healthy',
        'cpu_percent': 45.2
    }

manager.register_service('my-service', my_health_check)

# Получение общего состояния
overall_health = await manager.get_overall_health()
print(f"Overall Status: {overall_health['overall_status']}")
```

### 3. Automated Recovery System

```python
from health_check.recovery import AutomatedRecoverySystem

recovery_system = AutomatedRecoverySystem(health_manager)

# Добавление circuit breaker
recovery_system.add_circuit_breaker('my-service', failure_threshold=5)

# Запуск автоматического восстановления
await recovery_system.start_auto_recovery()
```

### 4. Health Monitoring Dashboard

```python
from health_check.dashboard import HealthDashboardServer

dashboard = HealthDashboardServer(health_manager)
dashboard.run(host='0.0.0.0', port=5000)
```

**Доступно по адресу:** http://localhost:5000

### 5. Kubernetes Probes

```python
from health_check.kubernetes import generate_all_k8s_configs

configs = generate_all_k8s_configs(
    service_type='api_gateway',
    service_name='my-api'
)
```

## ☸️ Kubernetes интеграция

### Поколение конфигураций

Система автоматически генерирует:

- **Deployment** - с настроенными probes
- **Service** - для внутренней коммуникации
- **Ingress** - для внешнего доступа
- **HPA** - горизонтальное масштабирование
- **PodDisruptionBudget** - обеспечение доступности
- **NetworkPolicy** - сетевая безопасность
- **ServiceMonitor** - интеграция с Prometheus

### Типы сервисов

Доступны предварительные конфигурации для:

- `api_gateway` - API Gateway сервисы
- `ml_service` - ML/AI сервисы
- `database_service` - Базы данных
- `cache_service` - Кэш сервисы
- `frontend_app` - Frontend приложения

### Probes конфигурации

#### Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health/basic
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 30
```

#### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /health/dependencies
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

#### Startup Probe
```yaml
startupProbe:
  httpGet:
    path: /health/basic
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 30
```

## 📊 Мониторинг и алерты

### Интеграция с Prometheus

```python
from prometheus_client import Counter, Histogram

health_checks_total = Counter('health_checks_total', 'Total health checks', ['service', 'status'])
health_check_duration = Histogram('health_check_duration_seconds', 'Health check duration')
```

### AlertManager конфигурации

```yaml
route:
  group_by: ['alertname']
  group_wait: 10s
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'

receivers:
- name: 'critical-alerts'
  slack_configs:
  - channel: '#alerts'
    title: '🚨 Critical Health Alert'
```

### Графики и метрики

- **System Health Trend** - тренд здоровья системы
- **Service Status Distribution** - распределение статусов сервисов
- **Response Time Heatmap** - карта времени отклика
- **Dependency Graph** - граф зависимостей
- **Incident Timeline** - таймлайн инцидентов

## 📖 Примеры

### Демо система

```bash
# Запуск полной демонстрации
python supabase/shared/health-check/demo.py

# Запуск конкретного демо
python supabase/shared/health-check/demo.py
# Выберите опцию 1-9
```

### Быстрый старт

```bash
# Запуск примера быстрого старта
python supabase/shared/health-check/examples/quick_start.py

# Тестирование системы
python supabase/shared/health-check/examples/quick_start.py test
```

### Kubernetes примеры

```bash
# Просмотр примеров YAML
cat supabase/shared/health-check/kubernetes/examples.yaml
```

## 📚 Документация

### Полная документация

📖 **[docs/health-checks.md](#features)** - Полная документация системы

### API Reference

#### Health Endpoints

- `GET /health` - Комплексная проверка здоровья
- `GET /health/basic` - Базовая проверка
- `GET /health/dependencies` - Проверка зависимостей
- `GET /health/business` - Проверка бизнес-логики
- `GET /health/performance` - Проверка производительности
- `GET /health/custom-metrics` - Кастомные метрики

#### Dashboard API

- `GET /api/services` - Список всех сервисов
- `GET /api/metrics` - Общие метрики системы
- `GET /api/incidents` - Активные инциденты
- `GET /api/history` - Исторические данные
- `GET /api/dependency-map` - Карта зависимостей

### Конфигурация

```python
config = {
    'manager': {
        'check_intervals': {
            'basic': 30,
            'dependencies': 60,
            'business': 300,
            'performance': 60,
            'custom_metrics': 600
        }
    },
    'dashboard': {
        'enabled': True,
        'host': '0.0.0.0',
        'port': 5000
    },
    'recovery': {
        'enabled': True,
        'auto_recovery': True,
        'circuit_breakers': {
            'default_failure_threshold': 5,
            'default_timeout': 60
        }
    }
}
```

## 🛠️ Структура проекта

```
supabase/shared/health-check/
├── __init__.py                 # Главный интерфейс системы
├── requirements.txt            # Зависимости
├── demo.py                     # Демонстрация возможностей
├── examples/
│   └── quick_start.py         # Примеры быстрого старта
├── endpoints/                  # Health Check Endpoints
│   ├── __init__.py
│   ├── basic_health.py        # Базовая проверка здоровья
│   ├── dependencies_health.py # Проверка зависимостей
│   ├── business_health.py     # Проверка бизнес-логики
│   ├── performance_health.py  # Проверка производительности
│   └── custom_metrics_health.py # Кастомные метрики
├── manager/                    # Health Check Manager
│   ├── __init__.py
│   └── health_manager.py      # Основной менеджер
├── kubernetes/                 # Kubernetes интеграция
│   ├── __init__.py
│   ├── k8s_probes.py          # Генератор probes
│   └── examples.yaml          # Примеры YAML
├── dashboard/                  # Веб Dashboard
│   ├── __init__.py
│   └── dashboard_server.py    # Dashboard сервер
└── recovery/                   # Автоматическое восстановление
    ├── __init__.py
    └── auto_recovery.py       # Система восстановления
```

## 🔧 Установка и настройка

### Development

```bash
# Клонирование
git clone <repository>
cd health-check-system

# Установка зависимостей
pip install -r requirements.txt

# Запуск демо
python supabase/shared/health-check/demo.py
```

### Production

```bash
# Production установка
pip install -r requirements.txt

# Настройка переменных окружения
export HEALTH_CHECK_DB_URL="postgresql://..."
export HEALTH_CHECK_REDIS_URL="redis://..."

# Запуск системы
python -m supabase.shared.health_check.examples.quick_start
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY supabase/shared/health-check/ ./health-check/

EXPOSE 8080 5000

CMD ["python", "-m", "health_check.examples.quick_start"]
```

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста:

1. Создайте форк репозитория
2. Создайте ветку для новой функции (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

### Разработка

```bash
# Установка dev зависимостей
pip install -r requirements.txt

# Запуск тестов
pytest

# Форматирование кода
black supabase/shared/health-check/
isort supabase/shared/health-check/

# Проверка типов
mypy supabase/shared/health-check/
```

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](../../../LICENSE) для деталей.

## 🆘 Поддержка

- 📖 [Документация](#features)
- 🐛 [Issues](https://github.com/DmitrL-dev/1cai-public/issues)
- 💬 [Discussions](https://github.com/DmitrL-dev/1cai-public/discussions)
- 📧 `Email`

## 🗺️ Дорожная карта

- [ ] Интеграция с Istio Service Mesh
- [ ] Поддержка gRPC health checks
- [ ] Machine Learning для предсказания проблем
- [ ] Интеграция с Elasticsearch для логов
- [ ] WebAssembly health checks
- [ ] GraphQL health endpoints
- [ ] Blockchain health verification

---

**⭐ Если проект полезен, поставьте звезду на GitHub!**

Сделано с ❤️ для надежных и масштабируемых систем