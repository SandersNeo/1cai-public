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
import { Progress } from '../ui/progress';
import { Switch } from '../ui/switch';
import APIIntegrationService, { APIEndpoint, APIMetrics } from '../../services/api-integration-service';
import { 
  Plus, 
  Settings, 
  Trash2, 
  Edit, 
  Play, 
  Pause, 
  RefreshCw,
  Download,
  Upload,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Zap,
  Database,
  Key,
  Shield,
  Globe,
  Server,
  Eye,
  EyeOff,
  Copy,
  ExternalLink
} from 'lucide-react';

export const APIIntegrationView: React.FC = () => {
  const [apiService] = useState(() => new APIIntegrationService());
  const [endpoints, setEndpoints] = useState<APIEndpoint[]>([]);
  const [metrics, setMetrics] = useState<Map<string, APIMetrics>>(new Map());
  const [selectedEndpoint, setSelectedEndpoint] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showSecrets, setShowSecrets] = useState(false);

  // Форма нового endpoint
  const [newEndpoint, setNewEndpoint] = useState<Partial<APIEndpoint>>({
    name: '',
    url: '',
    method: 'GET',
    headers: {},
    timeout: 10000,
    retries: 3
  });

  useEffect(() => {
    loadData();
    
    // Подписка на события
    apiService.on('endpoint-registered', loadData);
    apiService.on('endpoint-updated', loadData);
    apiService.on('endpoint-unregistered', loadData);
    apiService.on('request-success', updateMetrics);
    apiService.on('request-error', updateMetrics);

    return () => {
      apiService.removeAllListeners();
    };
  }, []);

  const loadData = useCallback(() => {
    try {
      setEndpoints(apiService.getEndpoints());
      setMetrics(apiService.getAllMetrics());
    } catch (error) {
      console.error('Failed to load API data:', error);
    }
  }, [apiService]);

  const updateMetrics = useCallback(() => {
    setMetrics(apiService.getAllMetrics());
  }, [apiService]);

  const handleAddEndpoint = async () => {
    try {
      setIsLoading(true);
      
      const endpoint: APIEndpoint = {
        id: `api_${Date.now()}`,
        name: newEndpoint.name || '',
        url: newEndpoint.url || '',
        method: newEndpoint.method || 'GET',
        headers: newEndpoint.headers || {},
        timeout: newEndpoint.timeout || 10000,
        retries: newEndpoint.retries || 3,
        auth: newEndpoint.auth
      };

      await apiService.registerEndpoint(endpoint);
      setShowAddDialog(false);
      setNewEndpoint({
        name: '',
        url: '',
        method: 'GET',
        headers: {},
        timeout: 10000,
        retries: 3
      });
    } catch (error) {
      console.error('Failed to add endpoint:', error);
      alert(`Ошибка добавления endpoint: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteEndpoint = async (endpointId: string) => {
    if (!confirm('Вы уверены, что хотите удалить этот endpoint?')) return;

    try {
      setIsLoading(true);
      await apiService.unregisterEndpoint(endpointId);
      if (selectedEndpoint === endpointId) {
        setSelectedEndpoint(null);
      }
    } catch (error) {
      console.error('Failed to delete endpoint:', error);
      alert(`Ошибка удаления endpoint: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestEndpoint = async (endpointId: string) => {
    try {
      setIsLoading(true);
      const response = await apiService.request(endpointId);
      alert(`Тест успешен! Статус: ${response.status}, Время: ${response.timing.duration}ms`);
    } catch (error) {
      console.error('Test failed:', error);
      alert(`Тест не удался: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBatchTest = async () => {
    try {
      setIsLoading(true);
      const requests = endpoints.map(ep => ({ endpointId: ep.id }));
      const results = await apiService.batchRequest(requests);
      
      const successCount = results.size;
      const totalCount = endpoints.length;
      
      alert(`Пакетное тестирование завершено!\nУспешно: ${successCount}/${totalCount}`);
    } catch (error) {
      console.error('Batch test failed:', error);
      alert(`Пакетное тестирование не удалось: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleHealthCheck = async () => {
    try {
      setIsLoading(true);
      const healthResults = await apiService.healthCheckAll();
      
      let healthyCount = 0;
      let degradedCount = 0;
      let unhealthyCount = 0;
      
      healthResults.forEach(result => {
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

  const exportConfiguration = () => {
    try {
      const config = apiService.exportConfiguration();
      const blob = new Blob([config], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `api-config-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Экспорт не удался: ${(error as Error).message}`);
    }
  };

  const importConfiguration = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const config = e.target?.result as string;
        await apiService.importConfiguration(config);
        alert('Конфигурация успешно импортирована!');
      } catch (error) {
        console.error('Import failed:', error);
        alert(`Импорт не удался: ${(error as Error).message}`);
      }
    };
    reader.readAsText(file);
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

  const getStatusIcon = (metrics: APIMetrics | null) => {
    if (!metrics) return <Clock className="w-4 h-4 text-gray-400" />;
    
    const errorRate = metrics.errorRate;
    if (errorRate === 0) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (errorRate < 10) return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    return <XCircle className="w-4 h-4 text-red-500" />;
  };

  return (
    <div className="api-integration-view p-6">
      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Globe className="w-8 h-8 text-blue-500" />
              Интеграции с внешними API
            </h1>
            <p className="text-gray-600 mt-2">
              Управление внешними API, аутентификацией и мониторингом
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleBatchTest}
              disabled={isLoading || endpoints.length === 0}
            >
              <Activity className="w-4 h-4 mr-2" />
              Пакетный тест
            </Button>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleHealthCheck}
              disabled={isLoading || endpoints.length === 0}
            >
              <Shield className="w-4 h-4 mr-2" />
              Проверка здоровья
            </Button>

            <Button variant="outline" size="sm" onClick={exportConfiguration}>
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
                  onChange={importConfiguration}
                  className="hidden"
                />
              </label>
            </Button>

            <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Добавить API
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Добавить новый API endpoint</DialogTitle>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">Название</Label>
                      <Input
                        id="name"
                        value={newEndpoint.name}
                        onChange={(e) => setNewEndpoint(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="My API Endpoint"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="method">Метод</Label>
                      <Select value={newEndpoint.method} onValueChange={(value) => setNewEndpoint(prev => ({ ...prev, method: value as any }))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="GET">GET</SelectItem>
                          <SelectItem value="POST">POST</SelectItem>
                          <SelectItem value="PUT">PUT</SelectItem>
                          <SelectItem value="DELETE">DELETE</SelectItem>
                          <SelectItem value="PATCH">PATCH</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="url">URL</Label>
                    <Input
                      id="url"
                      value={newEndpoint.url}
                      onChange={(e) => setNewEndpoint(prev => ({ ...prev, url: e.target.value }))}
                      placeholder="https://api.example.com/v1/endpoint"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="timeout">Таймаут (мс)</Label>
                      <Input
                        id="timeout"
                        type="number"
                        value={newEndpoint.timeout}
                        onChange={(e) => setNewEndpoint(prev => ({ ...prev, timeout: parseInt(e.target.value) || 10000 }))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="retries">Попытки</Label>
                      <Input
                        id="retries"
                        type="number"
                        value={newEndpoint.retries}
                        onChange={(e) => setNewEndpoint(prev => ({ ...prev, retries: parseInt(e.target.value) || 3 }))}
                      />
                    </div>
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                      Отмена
                    </Button>
                    <Button onClick={handleAddEndpoint} disabled={isLoading}>
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
                <p className="text-sm font-medium text-gray-600">Всего API</p>
                <p className="text-2xl font-bold text-gray-900">{endpoints.length}</p>
              </div>
              <Database className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Запросы сегодня</p>
                <p className="text-2xl font-bold text-green-600">
                  {Array.from(metrics.values()).reduce((sum, m) => sum + m.totalRequests, 0)}
                </p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Успешность</p>
                <p className="text-2xl font-bold text-blue-600">
                  {metrics.size > 0 ? Math.round(
                    (Array.from(metrics.values()).reduce((sum, m) => sum + m.successfulRequests, 0) /
                     Math.max(1, Array.from(metrics.values()).reduce((sum, m) => sum + m.totalRequests, 0))) * 100
                  ) : 0}%
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Среднее время</p>
                <p className="text-2xl font-bold text-purple-600">
                  {metrics.size > 0 ? Math.round(
                    Array.from(metrics.values()).reduce((sum, m) => sum + m.averageResponseTime, 0) / metrics.size
                  ) : 0}ms
                </p>
              </div>
              <Clock className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Список API endpoints */}
      <Card>
        <CardHeader>
          <CardTitle>API Endpoints</CardTitle>
        </CardHeader>
        <CardContent>
          {endpoints.length === 0 ? (
            <div className="text-center py-12">
              <Database className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Нет настроенных API</h3>
              <p className="text-gray-600 mb-4">Добавьте первый API endpoint для начала работы</p>
              <Button onClick={() => setShowAddDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Добавить API
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {endpoints.map((endpoint) => {
                const endpointMetrics = metrics.get(endpoint.id);
                
                return (
                  <div 
                    key={endpoint.id} 
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedEndpoint === endpoint.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedEndpoint(selectedEndpoint === endpoint.id ? null : endpoint.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        {getStatusIcon(endpointMetrics)}
                        
                        <div>
                          <h3 className="font-medium text-gray-900">{endpoint.name}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={getMethodColor(endpoint.method)}>
                              {endpoint.method}
                            </Badge>
                            <code className="text-sm text-gray-600">{endpoint.url}</code>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {endpointMetrics && (
                          <div className="text-right text-sm text-gray-600">
                            <div>Запросов: {endpointMetrics.totalRequests}</div>
                            <div>Успешно: {endpointMetrics.successfulRequests}</div>
                            <div className="text-xs text-gray-500">
                              {Math.round(endpointMetrics.averageResponseTime)}ms
                            </div>
                          </div>
                        )}
                        
                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleTestEndpoint(endpoint.id);
                            }}
                            disabled={isLoading}
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              // TODO: Открыть диалог редактирования
                            }}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteEndpoint(endpoint.id);
                            }}
                            disabled={isLoading}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Детали endpoint */}
                    {selectedEndpoint === endpoint.id && endpointMetrics && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <Label className="text-sm text-gray-600">Статус</Label>
                            <div className="flex items-center gap-2 mt-1">
                              {endpointMetrics.errorRate === 0 ? (
                                <Badge className="bg-green-100 text-green-800">Здоровый</Badge>
                              ) : endpointMetrics.errorRate < 10 ? (
                                <Badge className="bg-yellow-100 text-yellow-800">Предупреждение</Badge>
                              ) : (
                                <Badge className="bg-red-100 text-red-800">Критично</Badge>
                              )}
                            </div>
                          </div>
                          
                          <div>
                            <Label className="text-sm text-gray-600">Ошибки</Label>
                            <div className="mt-1">
                              <span className="text-sm font-medium">
                                {endpointMetrics.failedRequests} ({endpointMetrics.errorRate.toFixed(1)}%)
                              </span>
                            </div>
                          </div>
                          
                          <div>
                            <Label className="text-sm text-gray-600">Кэш</Label>
                            <div className="mt-1">
                              <span className="text-sm font-medium">
                                {Math.round(endpointMetrics.cacheHitRate)}% попаданий
                              </span>
                            </div>
                          </div>
                          
                          <div>
                            <Label className="text-sm text-gray-600">Rate Limit</Label>
                            <div className="mt-1">
                              <span className="text-sm font-medium">
                                {endpointMetrics.rateLimitHits} превышений
                              </span>
                            </div>
                          </div>
                        </div>

                        {endpoint.auth && (
                          <div className="mt-4">
                            <Label className="text-sm text-gray-600">Аутентификация</Label>
                            <div className="mt-1">
                              <Badge variant="outline">
                                {endpoint.auth.type === 'bearer' && 'Bearer Token'}
                                {endpoint.auth.type === 'api-key' && 'API Key'}
                                {endpoint.auth.type === 'basic' && 'Basic Auth'}
                                {endpoint.auth.type === 'oauth2' && 'OAuth2'}
                              </Badge>
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
      <div className="mt-6">
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            <strong>Совет:</strong> Используйте переменные окружения для хранения API ключей и секретов.
            Никогда не коммитьте чувствительные данные в код.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
};