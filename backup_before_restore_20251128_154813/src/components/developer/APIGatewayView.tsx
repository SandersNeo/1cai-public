import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Alert, AlertDescription } from '../ui/alert';
import { Switch } from '../ui/switch';
import { Progress } from '../ui/progress';
import APIGatewayService, { GatewayRoute, GatewayMetrics } from '../../services/api-gateway-service';
import APIIntegrationService from '../../services/api-integration-service';
import { 
  Router, 
  Plus, 
  Trash2, 
  Edit, 
  Play, 
  Pause,
  RefreshCw,
  ArrowRight,
  Shield,
  Zap,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Settings,
  Eye,
  EyeOff,
  Copy,
  Download,
  Upload,
  Activity,
  Filter,
  Route
} from 'lucide-react';

export const APIGatewayView: React.FC = () => {
  const [apiService] = useState(() => new APIIntegrationService());
  const [gatewayService] = useState(() => new APIGatewayService(apiService));
  const [routes, setRoutes] = useState<GatewayRoute[]>([]);
  const [metrics, setMetrics] = useState<GatewayMetrics | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddRouteDialog, setShowAddRouteDialog] = useState(false);

  // Форма нового маршрута
  const [newRoute, setNewRoute] = useState<Partial<GatewayRoute>>({
    name: '',
    path: '/api/*',
    methods: ['GET'],
    priority: 1,
    enabled: true,
    target: {
      type: 'api-endpoint',
      config: {}
    }
  });

  useEffect(() => {
    loadData();
    
    // Подписка на события
    gatewayService.on('route-registered', loadData);
    gatewayService.on('route-updated', loadData);
    gatewayService.on('route-unregistered', loadData);
    gatewayService.on('request-success', updateMetrics);
    gatewayService.on('request-error', updateMetrics);

    return () => {
      gatewayService.removeAllListeners();
    };
  }, []);

  const loadData = useCallback(() => {
    try {
      setRoutes(gatewayService.getRoutes());
      setMetrics(gatewayService.getMetrics());
    } catch (error) {
      console.error('Failed to load gateway data:', error);
    }
  }, [gatewayService]);

  const updateMetrics = useCallback(() => {
    setMetrics(gatewayService.getMetrics());
  }, [gatewayService]);

  const handleAddRoute = async () => {
    try {
      setIsLoading(true);
      
      const route: GatewayRoute = {
        id: `route_${Date.now()}`,
        name: newRoute.name || '',
        path: newRoute.path || '',
        methods: newRoute.methods || ['GET'],
        target: newRoute.target!,
        priority: newRoute.priority || 1,
        enabled: newRoute.enabled !== false
      };

      await gatewayService.registerRoute(route);
      setShowAddRouteDialog(false);
      setNewRoute({
        name: '',
        path: '/api/*',
        methods: ['GET'],
        priority: 1,
        enabled: true,
        target: {
          type: 'api-endpoint',
          config: {}
        }
      });
      
      alert('Маршрут успешно добавлен');
      
    } catch (error) {
      console.error('Failed to add route:', error);
      alert(`Ошибка добавления маршрута: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteRoute = async (routeId: string) => {
    if (!confirm('Вы уверены, что хотите удалить этот маршрут?')) return;

    try {
      setIsLoading(true);
      await gatewayService.unregisterRoute(routeId);
      if (selectedRoute === routeId) {
        setSelectedRoute(null);
      }
    } catch (error) {
      console.error('Failed to delete route:', error);
      alert(`Ошибка удаления маршрута: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleRoute = async (routeId: string, enabled: boolean) => {
    try {
      setIsLoading(true);
      await gatewayService.updateRoute(routeId, { enabled });
    } catch (error) {
      console.error('Failed to toggle route:', error);
      alert(`Ошибка переключения маршрута: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestRoute = async (routeId: string) => {
    try {
      setIsLoading(true);
      
      const testRequest = {
        method: 'GET',
        path: '/test',
        headers: { 'User-Agent': 'GatewayTest/1.0' },
        query: {},
        ip: '127.0.0.1',
        userAgent: 'GatewayTest/1.0'
      };

      const response = await gatewayService.handleRequest(testRequest);
      alert(`Тест маршрута!\nСтатус: ${response.status}\nВремя: ${JSON.stringify(response)}`);
      
    } catch (error) {
      console.error('Route test failed:', error);
      alert(`Тест маршрута не удался: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleHealthCheck = async () => {
    try {
      setIsLoading(true);
      const healthStatus = await gatewayService.healthCheck();
      
      let healthyCount = 0;
      let degradedCount = 0;
      let unhealthyCount = 0;
      
      healthStatus.routes.forEach(result => {
        if (result.status === 'healthy') healthyCount++;
        else if (result.status === 'degraded') degradedCount++;
        else unhealthyCount++;
      });
      
      alert(`Проверка здоровья завершена!\n\nЗдоровые: ${healthyCount}\nСниженная производительность: ${degradedCount}\nНе работающие: ${unhealthyCount}`);
    } catch (error) {
      console.error('Health check failed:', error);
      alert(`Проверка здоровья не удалась: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const exportRoutes = () => {
    try {
      const config = gatewayService.exportRoutes();
      const blob = new Blob([config], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `gateway-routes-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Экспорт не удался: ${(error as Error).message}`);
    }
  };

  const importRoutes = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const config = e.target?.result as string;
        await gatewayService.importRoutes(config);
        alert('Маршруты успешно импортированы!');
      } catch (error) {
        console.error('Import failed:', error);
        alert(`Импорт не удался: ${(error as Error).message}`);
      }
    };
    reader.readAsText(file);
  };

  const clearCache = () => {
    try {
      gatewayService.clearCache();
      alert('Кэш успешно очищен');
    } catch (error) {
      console.error('Cache clear failed:', error);
      alert(`Очистка кэша не удалась: ${(error as Error).message}`);
    }
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'bg-green-100 text-green-800 border-green-200';
      case 'POST': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'PUT': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'DELETE': return 'bg-red-100 text-red-800 border-red-200';
      case 'PATCH': return 'bg-purple-100 text-purple-800 border-purple-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTargetTypeIcon = (type: string) => {
    switch (type) {
      case 'api-endpoint': return <Zap className="w-4 h-4" />;
      case 'static-content': return <Eye className="w-4 h-4" />;
      case 'proxy': return <ArrowRight className="w-4 h-4" />;
      case 'function': return <Settings className="w-4 h-4" />;
      default: return <Route className="w-4 h-4" />;
    }
  };

  const getTargetTypeLabel = (type: string) => {
    switch (type) {
      case 'api-endpoint': return 'API Endpoint';
      case 'static-content': return 'Static Content';
      case 'proxy': return 'Proxy';
      case 'function': return 'Function';
      default: return type;
    }
  };

  return (
    <div className="api-gateway-view p-6">
      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Router className="w-8 h-8 text-purple-500" />
              API Gateway
            </h1>
            <p className="text-gray-600 mt-2">
              Маршрутизация запросов, аутентификация и мониторинг API
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm"
              onClick={clearCache}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Очистить кэш
            </Button>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleHealthCheck}
              disabled={isLoading || routes.length === 0}
            >
              <Shield className="w-4 h-4 mr-2" />
              Проверка здоровья
            </Button>

            <Button variant="outline" size="sm" onClick={exportRoutes}>
              <Download className="w-4 h-4 mr-2" />
              Экспорт
            </Button>

            <Button variant="outline" size="sm" asChild>
              <label className="cursor-pointer">
                <Upload className="w-4 h-4 mr-2" />
                Импорт
                <input 
                  type="file" 
                  accept=".json"
                  onChange={importRoutes}
                  className="hidden"
                />
              </label>
            </Button>

            <Dialog open={showAddRouteDialog} onOpenChange={setShowAddRouteDialog}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Добавить маршрут
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Добавить новый маршрут</DialogTitle>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="route-name">Название</Label>
                      <Input
                        id="route-name"
                        value={newRoute.name}
                        onChange={(e) => setNewRoute(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="My API Route"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="route-path">Путь</Label>
                      <Input
                        id="route-path"
                        value={newRoute.path}
                        onChange={(e) => setNewRoute(prev => ({ ...prev, path: e.target.value }))}
                        placeholder="/api/users/*"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="route-methods">Методы</Label>
                    <div className="flex gap-2 mt-2">
                      {['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].map(method => (
                        <Button
                          key={method}
                          size="sm"
                          variant={newRoute.methods?.includes(method) ? 'default' : 'outline'}
                          onClick={() => {
                            const methods = newRoute.methods || [];
                            if (methods.includes(method)) {
                              setNewRoute(prev => ({
                                ...prev,
                                methods: methods.filter(m => m !== method)
                              }));
                            } else {
                              setNewRoute(prev => ({
                                ...prev,
                                methods: [...methods, method]
                              }));
                            }
                          }}
                        >
                          {method}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="target-type">Тип цели</Label>
                      <Select value={newRoute.target?.type} onValueChange={(value) => setNewRoute(prev => ({
                        ...prev,
                        target: { ...prev.target!, type: value as any }
                      }))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="api-endpoint">API Endpoint</SelectItem>
                          <SelectItem value="static-content">Static Content</SelectItem>
                          <SelectItem value="proxy">Proxy</SelectItem>
                          <SelectItem value="function">Function</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="route-priority">Приоритет</Label>
                      <Input
                        id="route-priority"
                        type="number"
                        value={newRoute.priority}
                        onChange={(e) => setNewRoute(prev => ({ ...prev, priority: parseInt(e.target.value) || 1 }))}
                      />
                    </div>
                  </div>

                  {newRoute.target?.type === 'api-endpoint' && (
                    <div>
                      <Label htmlFor="endpoint-id">ID API Endpoint</Label>
                      <Input
                        id="endpoint-id"
                        value={newRoute.target.config.endpointId || ''}
                        onChange={(e) => setNewRoute(prev => ({
                          ...prev,
                          target: {
                            ...prev.target!,
                            config: { ...prev.target!.config, endpointId: e.target.value }
                          }
                        }))}
                        placeholder="api_endpoint_id"
                      />
                    </div>
                  )}

                  {newRoute.target?.type === 'proxy' && (
                    <div>
                      <Label htmlFor="proxy-url">URL для проксирования</Label>
                      <Input
                        id="proxy-url"
                        value={newRoute.target.config.url || ''}
                        onChange={(e) => setNewRoute(prev => ({
                          ...prev,
                          target: {
                            ...prev.target!,
                            config: { ...prev.target!.config, url: e.target.value }
                          }
                        }))}
                        placeholder="https://external-api.com/"
                      />
                    </div>
                  )}

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="route-enabled"
                      checked={newRoute.enabled}
                      onCheckedChange={(checked) => setNewRoute(prev => ({ ...prev, enabled: checked }))}
                    />
                    <Label htmlFor="route-enabled">Маршрут активен</Label>
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setShowAddRouteDialog(false)}>
                      Отмена
                    </Button>
                    <Button onClick={handleAddRoute} disabled={isLoading}>
                      {isLoading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
                      Добавить
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Маршруты</p>
                <p className="text-2xl font-bold text-gray-900">{routes.length}</p>
              </div>
              <Route className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Запросы</p>
                <p className="text-2xl font-bold text-blue-600">{metrics?.totalRequests || 0}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Успешность</p>
                <p className="text-2xl font-bold text-green-600">
                  {metrics ? Math.round((metrics.successfulRequests / Math.max(1, metrics.totalRequests)) * 100) : 0}%
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Среднее время</p>
                <p className="text-2xl font-bold text-orange-600">
                  {metrics ? Math.round(metrics.averageResponseTime) : 0}ms
                </p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Список маршрутов */}
      <Card>
        <CardHeader>
          <CardTitle>Маршруты Gateway</CardTitle>
        </CardHeader>
        <CardContent>
          {routes.length === 0 ? (
            <div className="text-center py-12">
              <Router className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Нет настроенных маршрутов</h3>
              <p className="text-gray-600 mb-4">Добавьте первый маршрут для начала работы с Gateway</p>
              <Button onClick={() => setShowAddRouteDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Добавить маршрут
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {routes
                .sort((a, b) => a.priority - b.priority)
                .map((route) => {
                  const routeMetrics = metrics?.routeMetrics.get(route.id);
                  
                  return (
                    <div 
                      key={route.id} 
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedRoute === route.id ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-gray-300'
                      } ${!route.enabled ? 'opacity-50' : ''}`}
                      onClick={() => setSelectedRoute(selectedRoute === route.id ? null : route.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            {route.enabled ? (
                              <Play className="w-4 h-4 text-green-500" />
                            ) : (
                              <Pause className="w-4 h-4 text-gray-400" />
                            )}
                            
                            <div className="text-sm text-gray-500">
                              Приоритет: {route.priority}
                            </div>
                          </div>
                          
                          <div>
                            <h3 className="font-medium text-gray-900">{route.name}</h3>
                            <div className="flex items-center gap-2 mt-1">
                              {route.methods.map(method => (
                                <Badge key={method} className={getMethodColor(method)}>
                                  {method}
                                </Badge>
                              ))}
                              <Badge variant="outline" className="flex items-center gap-1">
                                {getTargetTypeIcon(route.target.type)}
                                {getTargetTypeLabel(route.target.type)}
                              </Badge>
                            </div>
                            <code className="text-sm text-gray-600">{route.path}</code>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {routeMetrics && (
                            <div className="text-right text-sm text-gray-600">
                              <div>Запросов: {routeMetrics.requests}</div>
                              <div>Успешно: {routeMetrics.successes}</div>
                              <div className="text-xs text-gray-500">
                                {Math.round(routeMetrics.averageResponseTime)}ms
                              </div>
                            </div>
                          )}
                          
                          <div className="flex items-center gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleToggleRoute(route.id, !route.enabled);
                              }}
                            >
                              {route.enabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                            </Button>
                            
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleTestRoute(route.id);
                              }}
                              disabled={isLoading}
                            >
                              <Settings className="w-4 h-4" />
                            </Button>
                            
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteRoute(route.id);
                              }}
                              disabled={isLoading}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>

                      {/* Детали маршрута */}
                      {selectedRoute === route.id && routeMetrics && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                              <Label className="text-sm text-gray-600">Статус</Label>
                              <div className="mt-1">
                                <Badge className={route.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                                  {route.enabled ? 'Активен' : 'Отключен'}
                                </Badge>
                              </div>
                            </div>
                            
                            <div>
                              <Label className="text-sm text-gray-600">Успешность</Label>
                              <div className="mt-1">
                                <span className="text-sm font-medium">
                                  {routeMetrics.requests > 0 ? Math.round((routeMetrics.successes / routeMetrics.requests) * 100) : 0}%
                                </span>
                              </div>
                            </div>
                            
                            <div>
                              <Label className="text-sm text-gray-600">Ошибки</Label>
                              <div className="mt-1">
                                <span className="text-sm font-medium">
                                  {routeMetrics.failures}
                                </span>
                              </div>
                            </div>
                            
                            <div>
                              <Label className="text-sm text-gray-600">Rate Limit</Label>
                              <div className="mt-1">
                                <span className="text-sm font-medium">
                                  {routeMetrics.rateLimitHits} превышений
                                </span>
                              </div>
                            </div>
                          </div>

                          {route.authentication?.required && (
                            <div className="mt-4">
                              <Label className="text-sm text-gray-600">Аутентификация</Label>
                              <div className="mt-1">
                                <Badge variant="outline">
                                  <Shield className="w-3 h-3 mr-1" />
                                  {route.authentication.type}
                                </Badge>
                                {route.authentication.scopes && (
                                  <div className="mt-1">
                                    {route.authentication.scopes.map((scope, index) => (
                                      <Badge key={index} variant="secondary" className="mr-1 text-xs">
                                        {scope}
                                      </Badge>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {route.cache?.enabled && (
                            <div className="mt-4">
                              <Label className="text-sm text-gray-600">Кэширование</Label>
                              <div className="mt-1">
                                <Badge variant="outline" className="flex items-center gap-1 w-fit">
                                  <RefreshCw className="w-3 h-3" />
                                  TTL: {route.cache.ttl}s
                                </Badge>
                                <span className="text-sm text-gray-500 ml-2">
                                  Попаданий: {routeMetrics.cacheHits}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Алерты и уведомления */}
      <div className="mt-6 space-y-4">
        <Alert>
          <Router className="h-4 w-4" />
          <AlertDescription>
            <strong>Маршрутизация:</strong> Маршруты обрабатываются в порядке приоритета. 
            Более высокий приоритет означает более раннюю обработку.
          </AlertDescription>
        </Alert>

        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            <strong>Безопасность:</strong> Используйте аутентификацию и rate limiting для защиты ваших API. 
            Настройте CORS политики для междоменных запросов.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
};