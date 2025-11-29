# [NEXUS IDENTITY] ID: -8334077302848246648 | DATE: 2025-11-19

"""
Kubernetes Health Probes Configuration
Настройка Liveness, Readiness и Startup probes
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml


class ProbeType(Enum):
    LIVENESS = "livenessProbe"
    READINESS = "readinessProbe"
    STARTUP = "startupProbe"

class ProbeProtocol(Enum):
    HTTP = "httpGet"
    TCP = "tcpSocket"
    EXEC = "exec"

@dataclass
class HTTPProbeConfig:
    """Конфигурация HTTP probe"""
    scheme: str = "HTTP"
    host: str = "localhost"
    port: int = 8080
    path: str = "/health"
    httpHeaders: Optional[List[Dict[str, str]]] = None

@dataclass
class ExecProbeConfig:
    """Конфигурация Exec probe"""
    command: List[str]

@dataclass
class TCPProbeConfig:
    """Конфигурация TCP probe"""
    port: int
    host: str = "localhost"

@dataclass
class ProbeConfig:
    """Общая конфигурация probe"""
    type: ProbeType
    protocol: ProbeProtocol
    initialDelaySeconds: int
    periodSeconds: int
    timeoutSeconds: int
    successThreshold: int = 1
    failureThreshold: int = 3
    
    # HTTP конфигурация
    http_config: Optional[HTTPProbeConfig] = None
    
    # Exec конфигурация
    exec_config: Optional[ExecProbeConfig] = None
    
    # TCP конфигурация
    tcp_config: Optional[TCPProbeConfig] = None

class KubernetesProbesGenerator:
    """Генератор Kubernetes probes конфигураций"""
    
    def __init__(self, service_name: str, base_port: int = 8080):
        self.service_name = service_name
        self.base_port = base_port
    
    def create_liveness_probe(self, probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Создать LivenessProbe конфигурацию"""
        
        config = probe_config.get('liveness', {
            'initialDelaySeconds': 60,
            'periodSeconds': 30,
            'timeoutSeconds': 10,
            'failureThreshold': 3,
            'http_path': '/health/basic'
        })
        
        if config.get('type') == 'http':
            return {
                'livenessProbe': {
                    'httpGet': {
                        'scheme': config.get('scheme', 'HTTP'),
                        'path': config.get('http_path', '/health/basic'),
                        'port': self.base_port,
                        'httpHeaders': config.get('headers', [])
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 60),
                    'periodSeconds': config.get('periodSeconds', 30),
                    'timeoutSeconds': config.get('timeoutSeconds', 10),
                    'failureThreshold': config.get('failureThreshold', 3)
                }
            }
        elif config.get('type') == 'tcp':
            return {
                'livenessProbe': {
                    'tcpSocket': {
                        'port': self.base_port,
                        'host': config.get('host', 'localhost')
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 60),
                    'periodSeconds': config.get('periodSeconds', 30),
                    'timeoutSeconds': config.get('timeoutSeconds', 10),
                    'failureThreshold': config.get('failureThreshold', 3)
                }
            }
        else:  # exec
            return {
                'livenessProbe': {
                    'exec': {
                        'command': config.get('command', ['curl', '-f', f'http://localhost:{self.base_port}/health/basic'])
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 60),
                    'periodSeconds': config.get('periodSeconds', 30),
                    'timeoutSeconds': config.get('timeoutSeconds', 10),
                    'failureThreshold': config.get('failureThreshold', 3)
                }
            }
    
    def create_readiness_probe(self, probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Создать ReadinessProbe конфигурацию"""
        
        config = probe_config.get('readiness', {
            'initialDelaySeconds': 30,
            'periodSeconds': 10,
            'timeoutSeconds': 5,
            'failureThreshold': 3,
            'http_path': '/health/dependencies'
        })
        
        if config.get('type') == 'http':
            return {
                'readinessProbe': {
                    'httpGet': {
                        'scheme': config.get('scheme', 'HTTP'),
                        'path': config.get('http_path', '/health/dependencies'),
                        'port': self.base_port,
                        'httpHeaders': config.get('headers', [
                            {'name': 'X-Health-Check', 'value': 'readiness'}
                        ])
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 30),
                    'periodSeconds': config.get('periodSeconds', 10),
                    'timeoutSeconds': config.get('timeoutSeconds', 5),
                    'failureThreshold': config.get('failureThreshold', 3)
                }
            }
        elif config.get('type') == 'tcp':
            return {
                'readinessProbe': {
                    'tcpSocket': {
                        'port': self.base_port,
                        'host': config.get('host', 'localhost')
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 30),
                    'periodSeconds': config.get('periodSeconds', 10),
                    'timeoutSeconds': config.get('timeoutSeconds', 5),
                    'failureThreshold': config.get('failureThreshold', 3)
                }
            }
        else:  # exec
            return {
                'readinessProbe': {
                    'exec': {
                        'command': config.get('command', ['wget', '--no-verbose', '--tries=1', '--spider', f'http://localhost:{self.base_port}/health/dependencies'])
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 30),
                    'periodSeconds': config.get('periodSeconds', 10),
                    'timeoutSeconds': config.get('timeoutSeconds', 5),
                    'failureThreshold': config.get('failureThreshold', 3)
                }
            }
    
    def create_startup_probe(self, probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Создать StartupProbe конфигурацию"""
        
        config = probe_config.get('startup', {
            'initialDelaySeconds': 10,
            'periodSeconds': 10,
            'timeoutSeconds': 5,
            'failureThreshold': 30,
            'http_path': '/health/basic'
        })
        
        if config.get('type') == 'http':
            return {
                'startupProbe': {
                    'httpGet': {
                        'scheme': config.get('scheme', 'HTTP'),
                        'path': config.get('http_path', '/health/basic'),
                        'port': self.base_port,
                        'httpHeaders': config.get('headers', [])
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 10),
                    'periodSeconds': config.get('periodSeconds', 10),
                    'timeoutSeconds': config.get('timeoutSeconds', 5),
                    'failureThreshold': config.get('failureThreshold', 30)
                }
            }
        elif config.get('type') == 'tcp':
            return {
                'startupProbe': {
                    'tcpSocket': {
                        'port': self.base_port,
                        'host': config.get('host', 'localhost')
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 10),
                    'periodSeconds': config.get('periodSeconds', 10),
                    'timeoutSeconds': config.get('timeoutSeconds', 5),
                    'failureThreshold': config.get('failureThreshold', 30)
                }
            }
        else:  # exec
            return {
                'startupProbe': {
                    'exec': {
                        'command': config.get('command', ['sh', '-c', f'wget --no-verbose --tries=1 --spider http://localhost:{self.base_port}/health/basic'])
                    },
                    'initialDelaySeconds': config.get('initialDelaySeconds', 10),
                    'periodSeconds': config.get('periodSeconds', 10),
                    'timeoutSeconds': config.get('timeoutSeconds', 5),
                    'failureThreshold': config.get('failureThreshold', 30)
                }
            }
    
    def generate_deployment_yaml(self, probe_config: Dict[str, Any], 
                               container_config: Dict[str, Any]) -> str:
        """Сгенерировать полный Kubernetes Deployment YAML"""
        
        # Получение всех probe конфигураций
        liveness_config = self.create_liveness_probe(probe_config)
        readiness_config = self.create_readiness_probe(probe_config)
        startup_config = self.create_startup_probe(probe_config)
        
        # Основная структура Deployment
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': self.service_name,
                'labels': {
                    'app': self.service_name,
                    'version': container_config.get('version', '1.0.0')
                }
            },
            'spec': {
                'replicas': container_config.get('replicas', 3),
                'selector': {
                    'matchLabels': {
                        'app': self.service_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': self.service_name,
                            'version': container_config.get('version', '1.0.0')
                        }
                    },
                    'spec': {
                        'containers': [
                            {
                                'name': self.service_name,
                                'image': container_config.get('image'),
                                'imagePullPolicy': container_config.get('imagePullPolicy', 'Always'),
                                'ports': [
                                    {
                                        'containerPort': self.base_port,
                                        'name': 'http',
                                        'protocol': 'TCP'
                                    }
                                ],
                                **liveness_config,
                                **readiness_config,
                                **startup_config,
                                'env': container_config.get('env', []),
                                'resources': container_config.get('resources', {
                                    'limits': {
                                        'cpu': container_config.get('cpu_limit', '500m'),
                                        'memory': container_config.get('memory_limit', '512Mi')
                                    },
                                    'requests': {
                                        'cpu': container_config.get('cpu_request', '100m'),
                                        'memory': container_config.get('memory_request', '128Mi')
                                    }
                                }),
                                'volumeMounts': container_config.get('volumeMounts', []),
                                'securityContext': container_config.get('securityContext', {
                                    'allowPrivilegeEscalation': False,
                                    'runAsNonRoot': True,
                                    'runAsUser': 1000,
                                    'capabilities': {
                                        'drop': ['ALL']
                                    }
                                })
                            }
                        ],
                        'volumes': container_config.get('volumes', []),
                        'restartPolicy': 'Always',
                        'terminationGracePeriodSeconds': 30
                    }
                }
            }
        }
        
        return yaml.dump(deployment, default_flow_style=False, allow_unicode=True)
    
    def generate_service_yaml(self, service_config: Dict[str, Any] = None) -> str:
        """Сгенерировать Kubernetes Service YAML"""
        
        config = service_config or {}
        
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': self.service_name,
                'labels': {
                    'app': self.service_name
                },
                'annotations': config.get('annotations', {})
            },
            'spec': {
                'type': config.get('type', 'ClusterIP'),
                'selector': {
                    'app': self.service_name
                },
                'ports': [
                    {
                        'port': config.get('port', 80),
                        'targetPort': self.base_port,
                        'protocol': 'TCP',
                        'name': 'http'
                    }
                ],
                **({'sessionAffinity': config.get('sessionAffinity', 'ClientIP')} if config.get('sessionAffinity') else {})
            }
        }
        
        return yaml.dump(service, default_flow_style=False, allow_unicode=True)
    
    def generate_ingress_yaml(self, ingress_config: Dict[str, Any]) -> str:
        """Сгенерировать Kubernetes Ingress YAML"""
        
        ingress = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': f"{self.service_name}-ingress",
                'labels': {
                    'app': self.service_name
                },
                'annotations': {
                    'kubernetes.io/ingress.class': ingress_config.get('ingress_class', 'nginx'),
                    'nginx.ingress.kubernetes.io/rewrite-target': '/$2',
                    'nginx.ingress.kubernetes.io/use-regex': 'true',
                    **ingress_config.get('annotations', {})
                }
            },
            'spec': {
                'rules': [
                    {
                        'host': ingress_config.get('host'),
                        'http': {
                            'paths': [
                                {
                                    'path': f"/{self.service_name}(/|$)(.*)",
                                    'pathType': 'Prefix',
                                    'backend': {
                                        'service': {
                                            'name': self.service_name,
                                            'port': {
                                                'number': 80
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        return yaml.dump(ingress, default_flow_style=False, allow_unicode=True)
    
    def generate_hpa_yaml(self, hpa_config: Dict[str, Any]) -> str:
        """Сгенерировать Kubernetes HPA YAML"""
        
        config = hpa_config or {}
        
        hpa = {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': f"{self.service_name}-hpa",
                'labels': {
                    'app': self.service_name
                }
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': self.service_name
                },
                'minReplicas': config.get('min_replicas', 2),
                'maxReplicas': config.get('max_replicas', 10),
                'metrics': [
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'cpu',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': config.get('cpu_target', 70)
                            }
                        }
                    },
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'memory',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': config.get('memory_target', 80)
                            }
                        }
                    }
                ],
                'behavior': {
                    'scaleDown': {
                        'stabilizationWindowSeconds': config.get('scale_down_stabilization', 300),
                        'policies': [
                            {
                                'type': 'Percent',
                                'value': config.get('scale_down_percent', 50),
                                'periodSeconds': 60
                            }
                        ]
                    },
                    'scaleUp': {
                        'stabilizationWindowSeconds': config.get('scale_up_stabilization', 60),
                        'policies': [
                            {
                                'type': 'Percent',
                                'value': config.get('scale_up_percent', 100),
                                'periodSeconds': 60
                            }
                        ]
                    }
                }
            }
        }
        
        return yaml.dump(hpa, default_flow_style=False, allow_unicode=True)

# Предварительно настроенные конфигурации для разных типов сервисов
SERVICE_CONFIGS = {
    'api_gateway': {
        'probes': {
            'liveness': {
                'type': 'http',
                'http_path': '/health',
                'initialDelaySeconds': 60,
                'periodSeconds': 30,
                'timeoutSeconds': 10,
                'failureThreshold': 3
            },
            'readiness': {
                'type': 'http',
                'http_path': '/health/dependencies',
                'initialDelaySeconds': 30,
                'periodSeconds': 10,
                'timeoutSeconds': 5,
                'failureThreshold': 3
            },
            'startup': {
                'type': 'http',
                'http_path': '/health/basic',
                'initialDelaySeconds': 10,
                'periodSeconds': 10,
                'timeoutSeconds': 5,
                'failureThreshold': 30
            }
        },
        'resources': {
            'cpu_limit': '1000m',
            'memory_limit': '1Gi',
            'cpu_request': '200m',
            'memory_request': '256Mi'
        }
    },
    
    'ml_service': {
        'probes': {
            'liveness': {
                'type': 'http',
                'http_path': '/health',
                'initialDelaySeconds': 120,
                'periodSeconds': 60,
                'timeoutSeconds': 30,
                'failureThreshold': 3
            },
            'readiness': {
                'type': 'http',
                'http_path': '/health/business',
                'initialDelaySeconds': 60,
                'periodSeconds': 30,
                'timeoutSeconds': 15,
                'failureThreshold': 5
            },
            'startup': {
                'type': 'http',
                'http_path': '/health/basic',
                'initialDelaySeconds': 30,
                'periodSeconds': 15,
                'timeoutSeconds': 10,
                'failureThreshold': 60
            }
        },
        'resources': {
            'cpu_limit': '2000m',
            'memory_limit': '4Gi',
            'cpu_request': '500m',
            'memory_request': '1Gi'
        }
    },
    
    'database_service': {
        'probes': {
            'liveness': {
                'type': 'tcp',
                'host': 'localhost',
                'initialDelaySeconds': 30,
                'periodSeconds': 30,
                'timeoutSeconds': 10,
                'failureThreshold': 3
            },
            'readiness': {
                'type': 'exec',
                'command': ['pg_isready', '-h', 'localhost', '-p', '5432'],
                'initialDelaySeconds': 10,
                'periodSeconds': 10,
                'timeoutSeconds': 5,
                'failureThreshold': 3
            },
            'startup': {
                'type': 'exec',
                'command': ['pg_isready', '-h', 'localhost', '-p', '5432'],
                'initialDelaySeconds': 5,
                'periodSeconds': 5,
                'timeoutSeconds': 3,
                'failureThreshold': 60
            }
        },
        'resources': {
            'cpu_limit': '500m',
            'memory_limit': '2Gi',
            'cpu_request': '100m',
            'memory_request': '512Mi'
        }
    },
    
    'cache_service': {
        'probes': {
            'liveness': {
                'type': 'tcp',
                'host': 'localhost',
                'initialDelaySeconds': 30,
                'periodSeconds': 30,
                'timeoutSeconds': 10,
                'failureThreshold': 3
            },
            'readiness': {
                'type': 'exec',
                'command': ['redis-cli', 'ping'],
                'initialDelaySeconds': 10,
                'periodSeconds': 10,
                'timeoutSeconds': 5,
                'failureThreshold': 3
            },
            'startup': {
                'type': 'exec',
                'command': ['redis-cli', 'ping'],
                'initialDelaySeconds': 5,
                'periodSeconds': 5,
                'timeoutSeconds': 3,
                'failureThreshold': 30
            }
        },
        'resources': {
            'cpu_limit': '300m',
            'memory_limit': '1Gi',
            'cpu_request': '50m',
            'memory_request': '256Mi'
        }
    },
    
    'frontend_app': {
        'probes': {
            'liveness': {
                'type': 'http',
                'http_path': '/health',
                'initialDelaySeconds': 30,
                'periodSeconds': 30,
                'timeoutSeconds': 10,
                'failureThreshold': 3
            },
            'readiness': {
                'type': 'http',
                'http_path': '/health/basic',
                'initialDelaySeconds': 15,
                'periodSeconds': 10,
                'timeoutSeconds': 5,
                'failureThreshold': 3
            },
            'startup': {
                'type': 'http',
                'http_path': '/health/basic',
                'initialDelaySeconds': 5,
                'periodSeconds': 5,
                'timeoutSeconds': 3,
                'failureThreshold': 20
            }
        },
        'resources': {
            'cpu_limit': '200m',
            'memory_limit': '512Mi',
            'cpu_request': '50m',
            'memory_request': '128Mi'
        }
    }
}

def generate_all_k8s_configs(service_type: str, service_name: str, 
                           custom_config: Dict[str, Any] = None) -> Dict[str, str]:
    """Сгенерировать все Kubernetes конфигурации для сервиса"""
    
    base_config = SERVICE_CONFIGS.get(service_type, {})
    if custom_config:
        base_config = {**base_config, **custom_config}
    
    generator = KubernetesProbesGenerator(service_name)
    
    # Probe конфигурации
    probe_config = base_config.get('probes', {})
    
    # Container конфигурация
    container_config = {
        'image': custom_config.get('image') if custom_config else f"{service_name}:latest",
        'version': custom_config.get('version', '1.0.0'),
        'replicas': custom_config.get('replicas', 3),
        'resources': base_config.get('resources', {}),
        'env': custom_config.get('env', []),
        'volumeMounts': custom_config.get('volumeMounts', []),
        'securityContext': custom_config.get('securityContext'),
        'imagePullPolicy': custom_config.get('imagePullPolicy', 'Always')
    }
    
    # Service конфигурация
    service_config = custom_config.get('service', {}) if custom_config else {}
    
    # Ingress конфигурация
    ingress_config = custom_config.get('ingress', {}) if custom_config else {}
    
    # HPA конфигурация
    hpa_config = custom_config.get('hpa', {}) if custom_config else {}
    
    configs = {
        'deployment': generator.generate_deployment_yaml(probe_config, container_config),
        'service': generator.generate_service_yaml(service_config)
    }
    
    # Добавление дополнительных конфигураций если указано
    if ingress_config:
        configs['ingress'] = generator.generate_ingress_yaml(ingress_config)
    
    if hpa_config:
        configs['hpa'] = generator.generate_hpa_yaml(hpa_config)
    
    return configs

if __name__ == "__main__":
    # Пример использования
    configs = generate_all_k8s_configs(
        service_type='api_gateway',
        service_name='api-gateway',
        custom_config={
            'image': 'myregistry.com/api-gateway:v1.2.0',
            'version': '1.2.0',
            'env': [
                {'name': 'HEALTH_CHECK_INTERVAL', 'value': '30'},
                {'name': 'LOG_LEVEL', 'value': 'INFO'}
            ],
            'ingress': {
                'host': 'api.example.com',
                'ingress_class': 'nginx'
            }
        }
    )
    
    for config_name, config_content in configs.items():
        print(f"=== {config_name.upper()}.YAML ===")
        print(config_content)
        print()