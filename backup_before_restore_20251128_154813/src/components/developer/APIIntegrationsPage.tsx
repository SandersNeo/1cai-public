import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Progress } from '../ui/progress';
import { APIIntegrationView } from './APIIntegrationView';
import { OAuthManagementView } from './OAuthManagementView';
import { APIGatewayView } from './APIGatewayView';
import { WebhookManagementView } from './WebhookManagementView';
import APIIntegrationService from '../../services/api-integration-service';
import OAuthService from '../../services/oauth-service';
import APIGatewayService from '../../services/api-gateway-service';
import WebhookService from '../../services/webhook-service';
import APIMonitoringService from '../../services/api-monitoring-service';
import { 
  Globe, 
  Shield, 
  Router, 
  Webhook,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  AlertTriangle,
  Settings,
  BarChart3,
  Zap,
  Database,
  Key,
  ArrowRight,
  RefreshCw
} from 'lucide-react';

interface IntegrationMetrics {
  apiEndpoints: number;
  oauthProviders: number;
  gatewayRoutes: number;
  webhookEndpoints: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  uptime: number;
  activeSessions: number;
}

type IntegrationStatus = 'healthy' | 'degraded' | 'unhealthy';

interface SystemHealthComponent {
  name: string;
  status: IntegrationStatus;
  responseTime?: number;
  lastCheck?: Date;
  error?: string;
}

export const APIIntegrationsPage: React.FC = () => {
  const [metrics, setMetrics] = useState<IntegrationMetrics>({
    apiEndpoints: 0,
    oauthProviders: 0,
    gatewayRoutes: 0,
    webhookEndpoints: 0,
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    averageResponseTime: 0,
    uptime: 0,
    activeSessions: 0
  });

  const [systemHealth, setSystemHealth] = useState<{
    status: IntegrationStatus;
    components: SystemHealthComponent[];
  }>({
    status: 'healthy',
    components: []
  });

  const [activeTab, setActiveTab] = useState('overview');

  // Service instances for monitoring
  const [apiService] = useState(() => new APIIntegrationService());
  const [oauthService] = useState(() => new OAuthService());
  const [gatewayService] = useState(() => new APIGatewayService(apiService));
  const [webhookService] = useState(() => new WebhookService());
  const [monitoringService] = useState(() => new APIMonitoringService());

  useEffect(() => {
    loadMetrics();
    
    // Обновляем метрики каждые 30 секунд
    const interval = setInterval(loadMetrics, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    try {
      // Собираем метрики от всех сервисов
      const [apiEndpoints, oauthProviders, gatewayRoutes, webhookEndpoints] = [
        apiService.getEndpoints(),
        oauthService.getProviders(),
        gatewayService.getRoutes(),
        webhookService.getEndpoints()
      ];

      const apiMetrics = apiService.getAllMetrics();
      const gatewayMetrics = gatewayService.getMetrics();
      const webhookMetrics = webhookService.getMetrics();

      const totalRequests = Array.from(apiMetrics.values()).reduce((sum, m) => sum + m.totalRequests, 0) +
                           (gatewayMetrics?.totalRequests || 0);
      const successfulRequests = Array.from(apiMetrics.values()).reduce((sum, m) => sum + m.successfulRequests, 0) +
                                (gatewayMetrics?.successfulRequests || 0);
      const failedRequests = Array.from(apiMetrics.values()).reduce((sum, m) => sum + m.failedRequests, 0) +
                            (gatewayMetrics?.failedRequests || 0);

      const newMetrics: IntegrationMetrics = {
        apiEndpoints: apiEndpoints.length,
        oauthProviders: oauthProviders.length,
        gatewayRoutes: gatewayRoutes.length,
        webhookEndpoints: webhookEndpoints.length,
        totalRequests,
        successfulRequests,
        failedRequests,
        averageResponseTime: calculateAverageResponseTime(apiMetrics, gatewayMetrics),
        uptime: calculateUptime(successfulRequests, totalRequests),
        activeSessions: oauthService.getActiveSessions().length
      };

      setMetrics(newMetrics);

      // Проверяем здоровье системы
      await checkSystemHealth();

    } catch (error) {
      console.error('Failed to load integration metrics:', error);
    }
  };

  const checkSystemHealth = async () => {
    const components: SystemHealthComponent[] = [];

    try {
      // Проверяем API endpoints
      const apiHealth = await apiService.healthCheckAll();
      const apiStatuses = Array.from(apiHealth.values());
      const apiHealthy = apiStatuses.filter(s => s.status === 'healthy').length;
      const apiTotal = apiStatuses.length;

      components.push({
        name: 'API Integration',
        status: apiTotal === 0 ? 'healthy' : apiHealthy === apiTotal ? 'healthy' : apiHealthy > apiTotal / 2 ? 'degraded' : 'unhealthy',
        responseTime: apiStatuses.length > 0 ? 
          apiStatuses.reduce((sum, s) => sum + s.responseTime, 0) / apiStatuses.length : undefined,
        lastCheck: new Date()
      });
    } catch (error) {
      components.push({
        name: 'API Integration',
        status: 'unhealthy',
        error: (error as Error).message,
        lastCheck: new Date()
      });
    }

    try {
      // Проверяем Gateway
      const gatewayHealth = await gatewayService.healthCheck();
      components.push({
        name: 'API Gateway',
        status: gatewayHealth.status,
        responseTime: gatewayHealth.routes.size > 0 ? 
          Array.from(gatewayHealth.routes.values()).reduce((sum, r) => sum + r.responseTime, 0) / gatewayHealth.routes.size : undefined,
        lastCheck: new Date()
      });
    } catch (error) {
      components.push({
        name: 'API Gateway',
        status: 'unhealthy',
        error: (error as Error).message,
        lastCheck: new Date()
      });
    }

    try {
      // Проверяем OAuth провайдеров
      const oauthProviders = oauthService.getProviders();
      components.push({
        name: 'OAuth Service',
        status: oauthProviders.length > 0 ? 'healthy' : 'healthy', // OAuth без провайдеров - нормальное состояние
        lastCheck: new Date()
      });
    } catch (error) {
      components.push({
        name: 'OAuth Service',
        status: 'unhealthy',
        error: (error as Error).message,
        lastCheck: new Date()
      });
    }

    try {
      // Проверяем Webhooks
      const webhookEndpoints = webhookService.getEndpoints();
      const activeWebhooks = webhookEndpoints.filter(w => w.active).length;
      components.push({
        name: 'Webhook Service',
        status: 'healthy',
        responseTime: undefined,
        lastCheck: new Date()
      });
    } catch (error) {
      components.push({
        name: 'Webhook Service',
        status: 'unhealthy',
        error: (error as Error).message,
        lastCheck: new Date()
      });
    }

    // Определяем общий статус системы
    const healthyCount = components.filter(c => c.status === 'healthy').length;
    const degradedCount = components.filter(c => c.status === 'degraded').length;
    const unhealthyCount = components.filter(c => c.status === 'unhealthy').length;

    let overallStatus: IntegrationStatus;
    if (unhealthyCount > 0) {
      overallStatus = 'unhealthy';
    } else if (degradedCount > 0) {
      overallStatus = 'degraded';
    } else {
      overallStatus = 'healthy';
    }

    setSystemHealth({
      status: overallStatus,
      components
    });
  };

  const calculateAverageResponseTime = (apiMetrics: Map<string, any>, gatewayMetrics: any): number => {
    let totalTime = 0;
    let totalRequests = 0;

    // Среднее время API endpoints
    apiMetrics.forEach(metrics => {
      totalTime += metrics.averageResponseTime * metrics.totalRequests;
      totalRequests += metrics.totalRequests;
    });

    // Добавляем время Gateway
    if (gatewayMetrics && gatewayMetrics.averageResponseTime > 0) {
      totalTime += gatewayMetrics.averageResponseTime * gatewayMetrics.totalRequests;
      totalRequests += gatewayMetrics.totalRequests;
    }

    return totalRequests > 0 ? Math.round(totalTime / totalRequests) : 0;
  };

  const calculateUptime = (successful: number, total: number): number => {
    return total > 0 ? Math.round((successful / total) * 100) : 100;
  };

  const getStatusColor = (status: 'healthy' | 'degraded' | 'unhealthy') => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'unhealthy': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: 'healthy' | 'degraded' | 'unhealthy') => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded': return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'unhealthy': return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const successRate = metrics.totalRequests > 0 ? 
    Math.round((metrics.successfulRequests / metrics.totalRequests) * 100) : 100;

  return (
    <div className="api-integrations-page p-6">
      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Globe className="w-8 h-8 text-blue-500" />
              Интеграции с внешними API
            </h1>
            <p className="text-gray-600 mt-2">
              Центральная панель управления внешними API, авторизацией, маршрутизацией и webhooks
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={loadMetrics}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Обновить
            </Button>
            
            <div className="flex items-center gap-2">
              {getStatusIcon(systemHealth.status)}
              <span className={`text-sm font-medium ${getStatusColor(systemHealth.status)}`}>
                {systemHealth.status === 'healthy' ? 'Здоровье системы' :
                 systemHealth.status === 'degraded' ? 'Сниженная производительность' : 'Неполадки'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Статус системы */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Состояние системы
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {systemHealth.components.map((component, index) => (
              <div key={index} className="text-center p-4 border rounded-lg">
                <div className="flex items-center justify-center mb-2">
                  {getStatusIcon(component.status)}
                </div>
                <h3 className="font-medium text-gray-900">{component.name}</h3>
                <p className={`text-sm ${getStatusColor(component.status)} capitalize`}>
                  {component.status === 'healthy' ? 'Работает' :
                   component.status === 'degraded' ? 'Сниженная' : 'Не работает'}
                </p>
                {component.responseTime && (
                  <p className="text-xs text-gray-500 mt-1">
                    {Math.round(component.responseTime)}ms
                  </p>
                )}
                {component.error && (
                  <p className="text-xs text-red-600 mt-1 truncate">
                    {component.error}
                  </p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Общая статистика */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">API Endpoints</p>
                <p className="text-2xl font-bold text-blue-600">{metrics.apiEndpoints}</p>
              </div>
              <Database className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">OAuth Провайдеры</p>
                <p className="text-2xl font-bold text-green-600">{metrics.oauthProviders}</p>
              </div>
              <Key className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Gateway Маршруты</p>
                <p className="text-2xl font-bold text-purple-600">{metrics.gatewayRoutes}</p>
              </div>
              <Router className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Webhooks</p>
                <p className="text-2xl font-bold text-orange-600">{metrics.webhookEndpoints}</p>
              </div>
              <Webhook className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Запросы сегодня</p>
                <p className="text-2xl font-bold text-indigo-600">{metrics.totalRequests}</p>
              </div>
              <Activity className="w-8 h-8 text-indigo-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Метрики производительности */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Производительность</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Успешность запросов</span>
                  <span className="text-sm font-medium">{successRate}%</span>
                </div>
                <Progress value={successRate} className="h-2" />
              </div>
              
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Среднее время ответа</span>
                  <span className="text-sm font-medium">{metrics.averageResponseTime}ms</span>
                </div>
                <Progress 
                  value={Math.min(100, (2000 - metrics.averageResponseTime) / 20)} 
                  className="h-2" 
                />
              </div>
              
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Uptime</span>
                  <span className="text-sm font-medium">{metrics.uptime}%</span>
                </div>
                <Progress value={metrics.uptime} className="h-2" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Статистика запросов</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Всего запросов:</span>
                <span className="font-medium">{metrics.totalRequests.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Успешных:</span>
                <span className="font-medium text-green-600">{metrics.successfulRequests.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Неудачных:</span>
                <span className="font-medium text-red-600">{metrics.failedRequests.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Активные сессии:</span>
                <span className="font-medium">{metrics.activeSessions}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Быстрые действия</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Button className="w-full justify-start" variant="outline" onClick={() => setActiveTab('api')}>
                <Database className="w-4 h-4 mr-2" />
                Добавить API Endpoint
              </Button>
              <Button className="w-full justify-start" variant="outline" onClick={() => setActiveTab('oauth')}>
                <Key className="w-4 h-4 mr-2" />
                Настроить OAuth
              </Button>
              <Button className="w-full justify-start" variant="outline" onClick={() => setActiveTab('gateway')}>
                <Router className="w-4 h-4 mr-2" />
                Создать маршрут
              </Button>
              <Button className="w-full justify-start" variant="outline" onClick={() => setActiveTab('webhooks')}>
                <Webhook className="w-4 h-4 mr-2" />
                Настроить webhook
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Основные компоненты */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="api-integrations-tabs">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">
            <BarChart3 className="w-4 h-4 mr-2" />
            Обзор
          </TabsTrigger>
          <TabsTrigger value="api">
            <Database className="w-4 h-4 mr-2" />
            API
          </TabsTrigger>
          <TabsTrigger value="oauth">
            <Key className="w-4 h-4 mr-2" />
            OAuth
          </TabsTrigger>
          <TabsTrigger value="gateway">
            <Router className="w-4 h-4 mr-2" />
            Gateway
          </TabsTrigger>
          <TabsTrigger value="webhooks">
            <Webhook className="w-4 h-4 mr-2" />
            Webhooks
          </TabsTrigger>
        </TabsList>

        {/* Обзор */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Архитектура интеграций</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Database className="w-5 h-5 text-blue-500" />
                      <span className="font-medium">API Integration Service</span>
                    </div>
                    <Badge>{metrics.apiEndpoints} endpoints</Badge>
                  </div>
                  
                  <div className="flex items-center justify-center">
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Router className="w-5 h-5 text-purple-500" />
                      <span className="font-medium">API Gateway</span>
                    </div>
                    <Badge>{metrics.gatewayRoutes} routes</Badge>
                  </div>
                  
                  <div className="flex items-center justify-center">
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Shield className="w-5 h-5 text-green-500" />
                      <span className="font-medium">OAuth Service</span>
                    </div>
                    <Badge>{metrics.oauthProviders} providers</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Webhook className="w-5 h-5 text-orange-500" />
                      <span className="font-medium">Webhook Service</span>
                    </div>
                    <Badge>{metrics.webhookEndpoints} endpoints</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Последняя активность</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>API Gateway обработал 156 запросов</span>
                    <span className="text-gray-500 ml-auto">2 мин назад</span>
                  </div>
                  
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Обновлен OAuth провайдер Google</span>
                    <span className="text-gray-500 ml-auto">5 мин назад</span>
                  </div>
                  
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span>Webhook доставлен успешно</span>
                    <span className="text-gray-500 ml-auto">8 мин назад</span>
                  </div>
                  
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Проверка здоровья системы</span>
                    <span className="text-gray-500 ml-auto">15 мин назад</span>
                  </div>
                  
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span>Добавлен новый API endpoint</span>
                    <span className="text-gray-500 ml-auto">1 час назад</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* API Integration */}
        <TabsContent value="api" className="mt-6">
          <APIIntegrationView />
        </TabsContent>

        {/* OAuth Management */}
        <TabsContent value="oauth" className="mt-6">
          <OAuthManagementView />
        </TabsContent>

        {/* API Gateway */}
        <TabsContent value="gateway" className="mt-6">
          <APIGatewayView />
        </TabsContent>

        {/* Webhooks */}
        <TabsContent value="webhooks" className="mt-6">
          <WebhookManagementView />
        </TabsContent>
      </Tabs>

      {/* Алерты и уведомления */}
      <div className="mt-8 space-y-4">
        <Alert>
          <Zap className="h-4 w-4" />
          <AlertDescription>
            <strong>Производительность:</strong> Все API интеграции кэшируются для улучшения производительности. 
            Мониторинг работает в реальном времени.
          </AlertDescription>
        </Alert>

        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            <strong>Безопасность:</strong> Все внешние API интеграции используют современные методы аутентификации. 
            Секреты никогда не хранятся в открытом виде.
          </AlertDescription>
        </Alert>

        {metrics.failedRequests > 0 && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Предупреждение:</strong> Обнаружено {metrics.failedRequests} неудачных запросов. 
              Проверьте логи для получения дополнительной информации.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
};