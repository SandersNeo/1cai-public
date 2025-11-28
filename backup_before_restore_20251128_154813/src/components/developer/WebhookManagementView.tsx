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
import WebhookService, { WebhookEndpoint, WebhookEvent, WebhookDelivery, WebhookMetrics } from '../../services/webhook-service';
import { 
  Webhook, 
  Plus, 
  Trash2, 
  Edit, 
  Send,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Settings,
  Activity,
  BarChart3,
  Play,
  Pause,
  Copy,
  Download,
  Upload,
  Eye,
  Filter
} from 'lucide-react';

export const WebhookManagementView: React.FC = () => {
  const [webhookService] = useState(() => new WebhookService());
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[]>([]);
  const [events, setEvents] = useState<WebhookEvent[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [metrics, setMetrics] = useState<WebhookMetrics | null>(null);
  const [selectedEndpoint, setSelectedEndpoint] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddEndpointDialog, setShowAddEndpointDialog] = useState(false);
  const [testEventData, setTestEventData] = useState('{"message": "Test webhook event"}');

  // Форма нового webhook endpoint
  const [newEndpoint, setNewEndpoint] = useState<Partial<WebhookEndpoint>>({
    name: '',
    url: '',
    events: [],
    active: true,
    timeout: 10000,
    maxRetries: 3,
    retryPolicy: {
      maxAttempts: 3,
      backoffStrategy: 'exponential',
      baseDelay: 1000,
      retryableStatusCodes: [500, 502, 503, 504]
    }
  });

  useEffect(() => {
    loadData();
    
    // Подписка на события
    webhookService.on('webhook-registered', loadData);
    webhookService.on('webhook-updated', loadData);
    webhookService.on('webhook-unregistered', loadData);
    webhookService.on('event-triggered', loadData);
    webhookService.on('delivery-processed', loadData);

    return () => {
      webhookService.removeAllListeners();
    };
  }, []);

  const loadData = useCallback(() => {
    try {
      setEndpoints(webhookService.getEndpoints());
      setEvents(webhookService.getEvents());
      setDeliveries(webhookService.getDeliveries());
      setMetrics(webhookService.getMetrics());
    } catch (error) {
      console.error('Failed to load webhook data:', error);
    }
  }, [webhookService]);

  const handleAddEndpoint = async () => {
    try {
      setIsLoading(true);
      
      const endpoint: WebhookEndpoint = {
        id: `webhook_${Date.now()}`,
        name: newEndpoint.name || '',
        url: newEndpoint.url || '',
        events: newEndpoint.events || [],
        active: newEndpoint.active !== false,
        timeout: newEndpoint.timeout || 10000,
        maxRetries: newEndpoint.maxRetries || 3,
        retryPolicy: newEndpoint.retryPolicy!
      };

      // Валидация
      if (!endpoint.name || !endpoint.url) {
        throw new Error('Название и URL обязательны для заполнения');
      }

      webhookService.registerEndpoint(endpoint);
      setShowAddEndpointDialog(false);
      setNewEndpoint({
        name: '',
        url: '',
        events: [],
        active: true,
        timeout: 10000,
        maxRetries: 3,
        retryPolicy: {
          maxAttempts: 3,
          backoffStrategy: 'exponential',
          baseDelay: 1000,
          retryableStatusCodes: [500, 502, 503, 504]
        }
      });
      
      alert('Webhook endpoint успешно добавлен');
      
    } catch (error) {
      console.error('Failed to add endpoint:', error);
      alert(`Ошибка добавления webhook: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteEndpoint = async (endpointId: string) => {
    if (!confirm('Вы уверены, что хотите удалить этот webhook endpoint?')) return;

    try {
      setIsLoading(true);
      await webhookService.unregisterEndpoint(endpointId);
      if (selectedEndpoint === endpointId) {
        setSelectedEndpoint(null);
      }
    } catch (error) {
      console.error('Failed to delete endpoint:', error);
      alert(`Ошибка удаления webhook: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleEndpoint = async (endpointId: string, active: boolean) => {
    try {
      setIsLoading(true);
      await webhookService.updateEndpoint(endpointId, { active });
    } catch (error) {
      console.error('Failed to toggle endpoint:', error);
      alert(`Ошибка переключения webhook: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestEndpoint = async (endpointId: string) => {
    try {
      setIsLoading(true);
      
      const testData = JSON.parse(testEventData);
      const result = await webhookService.testEndpoint(endpointId, testData);
      
      if (result.success) {
        alert(`Тест успешен!\nСтатус: ${result.response?.status}\nВремя: ${result.duration}ms`);
      } else {
        alert(`Тест не удался!\nОшибка: ${result.error}\nВремя: ${result.duration}ms`);
      }
      
    } catch (error) {
      console.error('Endpoint test failed:', error);
      alert(`Тест endpoint не удался: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerEvent = async (endpointId: string) => {
    try {
      setIsLoading(true);
      
      const testData = JSON.parse(testEventData);
      await webhookService.triggerEvent({
        source: 'manual',
        type: 'manual.test',
        data: testData
      });
      
      alert('Событие успешно отправлено!');
      
    } catch (error) {
      console.error('Event trigger failed:', error);
      alert(`Отправка события не удалась: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetryDelivery = async (deliveryId: string) => {
    try {
      setIsLoading(true);
      await webhookService.retryDelivery(deliveryId);
      alert('Доставка запланирована для повторной отправки');
    } catch (error) {
      console.error('Retry delivery failed:', error);
      alert(`Повторная отправка не удалась: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const exportEndpoints = () => {
    try {
      const config = webhookService.exportEndpoints();
      const blob = new Blob([config], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `webhook-endpoints-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Экспорт не удался: ${(error as Error).message}`);
    }
  };

  const importEndpoints = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const config = e.target?.result as string;
        await webhookService.importEndpoints(config);
        alert('Webhook endpoints успешно импортированы!');
      } catch (error) {
        console.error('Import failed:', error);
        alert(`Импорт не удался: ${(error as Error).message}`);
      }
    };
    reader.readAsText(file);
  };

  const clearQueue = () => {
    try {
      webhookService.clearQueue();
      alert('Очередь событий очищена');
    } catch (error) {
      console.error('Clear queue failed:', error);
      alert(`Очистка очереди не удалась: ${(error as Error).message}`);
    }
  };

  const copyWebhookUrl = (endpointId: string) => {
    const webhookUrl = `${window.location.origin}/webhooks/${endpointId}`;
    navigator.clipboard.writeText(webhookUrl).then(() => {
      alert('URL webhook скопирован в буфер обмена');
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'delivered': 
        return <Badge className="bg-green-100 text-green-800">Доставлено</Badge>;
      case 'failed': 
        return <Badge className="bg-red-100 text-red-800">Ошибка</Badge>;
      case 'retrying': 
        return <Badge className="bg-yellow-100 text-yellow-800">Повтор</Badge>;
      case 'pending': 
        return <Badge className="bg-blue-100 text-blue-800">Ожидает</Badge>;
      default: 
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getDeliveryIcon = (status: string) => {
    switch (status) {
      case 'delivered': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'retrying': return <RefreshCw className="w-4 h-4 text-yellow-500" />;
      case 'pending': return <Clock className="w-4 h-4 text-blue-500" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className="webhook-management-view p-6">
      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Webhook className="w-8 h-8 text-orange-500" />
              Управление Webhooks
            </h1>
            <p className="text-gray-600 mt-2">
              Настройка webhook endpoints и мониторинг доставки событий
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm"
              onClick={clearQueue}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Очистить очередь
            </Button>

            <Button variant="outline" size="sm" onClick={exportEndpoints}>
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
                  onChange={importEndpoints}
                  className="hidden"
                />
              </label>
            </Button>

            <Dialog open={showAddEndpointDialog} onOpenChange={setShowAddEndpointDialog}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Добавить webhook
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Добавить новый webhook endpoint</DialogTitle>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="endpoint-name">Название</Label>
                      <Input
                        id="endpoint-name"
                        value={newEndpoint.name}
                        onChange={(e) => setNewEndpoint(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="My Webhook Endpoint"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="endpoint-url">URL</Label>
                      <Input
                        id="endpoint-url"
                        value={newEndpoint.url}
                        onChange={(e) => setNewEndpoint(prev => ({ ...prev, url: e.target.value }))}
                        placeholder="https://example.com/webhook"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="endpoint-events">События</Label>
                    <Input
                      id="endpoint-events"
                      value={newEndpoint.events?.join(', ') || ''}
                      onChange={(e) => setNewEndpoint(prev => ({ 
                        ...prev, 
                        events: e.target.value.split(',').map(s => s.trim()).filter(Boolean) 
                      }))}
                      placeholder="user.created, order.completed"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="endpoint-timeout">Таймаут (мс)</Label>
                      <Input
                        id="endpoint-timeout"
                        type="number"
                        value={newEndpoint.timeout}
                        onChange={(e) => setNewEndpoint(prev => ({ ...prev, timeout: parseInt(e.target.value) || 10000 }))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="max-retries">Макс. попыток</Label>
                      <Input
                        id="max-retries"
                        type="number"
                        value={newEndpoint.maxRetries}
                        onChange={(e) => setNewEndpoint(prev => ({ ...prev, maxRetries: parseInt(e.target.value) || 3 }))}
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="endpoint-active"
                      checked={newEndpoint.active}
                      onCheckedChange={(checked) => setNewEndpoint(prev => ({ ...prev, active: checked }))}
                    />
                    <Label htmlFor="endpoint-active">Webhook активен</Label>
                  </div>

                  <div>
                    <Label>Тестовые данные</Label>
                    <Textarea
                      value={testEventData}
                      onChange={(e) => setTestEventData(e.target.value)}
                      rows={3}
                      placeholder='{"message": "Test event"}'
                    />
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setShowAddEndpointDialog(false)}>
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
                <p className="text-sm font-medium text-gray-600">Webhook endpoints</p>
                <p className="text-2xl font-bold text-gray-900">{endpoints.length}</p>
              </div>
              <Webhook className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">События</p>
                <p className="text-2xl font-bold text-blue-600">{events.length}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Доставлено</p>
                <p className="text-2xl font-bold text-green-600">{metrics?.deliveredEvents || 0}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Успешность</p>
                <p className="text-2xl font-bold text-purple-600">
                  {metrics ? Math.round((metrics.deliveredEvents / Math.max(1, metrics.totalEvents)) * 100) : 0}%
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Основной контент */}
      <Tabs defaultValue="endpoints" className="webhook-tabs">
        <TabsList>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="events">События</TabsTrigger>
          <TabsTrigger value="deliveries">Доставка</TabsTrigger>
          <TabsTrigger value="analytics">Аналитика</TabsTrigger>
        </TabsList>

        {/* Endpoints */}
        <TabsContent value="endpoints">
          <Card>
            <CardHeader>
              <CardTitle>Webhook Endpoints</CardTitle>
            </CardHeader>
            <CardContent>
              {endpoints.length === 0 ? (
                <div className="text-center py-12">
                  <Webhook className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Нет настроенных webhook endpoints</h3>
                  <p className="text-gray-600 mb-4">Добавьте первый webhook endpoint для начала работы</p>
                  <Button onClick={() => setShowAddEndpointDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить webhook
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {endpoints.map((endpoint) => {
                    const endpointDeliveries = deliveries.filter(d => d.webhookId === endpoint.id);
                    const successfulDeliveries = endpointDeliveries.filter(d => d.status === 'delivered').length;
                    const failedDeliveries = endpointDeliveries.filter(d => d.status === 'failed').length;
                    
                    return (
                      <div 
                        key={endpoint.id} 
                        className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                          selectedEndpoint === endpoint.id ? 'border-orange-500 bg-orange-50' : 'border-gray-200 hover:border-gray-300'
                        } ${!endpoint.active ? 'opacity-50' : ''}`}
                        onClick={() => setSelectedEndpoint(selectedEndpoint === endpoint.id ? null : endpoint.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div>
                              {endpoint.active ? (
                                <Play className="w-4 h-4 text-green-500" />
                              ) : (
                                <Pause className="w-4 h-4 text-gray-400" />
                              )}
                            </div>
                            
                            <div>
                              <h3 className="font-medium text-gray-900">{endpoint.name}</h3>
                              <p className="text-sm text-gray-600 mt-1">{endpoint.url}</p>
                              <div className="flex items-center gap-2 mt-2">
                                {endpoint.events.slice(0, 3).map((event, index) => (
                                  <Badge key={index} variant="secondary" className="text-xs">
                                    {event}
                                  </Badge>
                                ))}
                                {endpoint.events.length > 3 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{endpoint.events.length - 3}
                                  </Badge>
                                )}
                                <Badge variant="outline" className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {endpoint.timeout}ms
                                </Badge>
                                {successfulDeliveries + failedDeliveries > 0 && (
                                  <Badge variant="outline" className="flex items-center gap-1">
                                    <Activity className="w-3 h-3" />
                                    {endpointDeliveries.length} доставок
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            {endpointDeliveries.length > 0 && (
                              <div className="text-right text-sm text-gray-600">
                                <div>Успешно: {successfulDeliveries}</div>
                                <div>Ошибок: {failedDeliveries}</div>
                              </div>
                            )}
                            
                            <div className="flex items-center gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  copyWebhookUrl(endpoint.id);
                                }}
                              >
                                <Copy className="w-4 h-4" />
                              </Button>
                              
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleToggleEndpoint(endpoint.id, !endpoint.active);
                                }}
                              >
                                {endpoint.active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                              </Button>
                              
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTriggerEvent(endpoint.id);
                                }}
                                disabled={isLoading}
                              >
                                <Send className="w-4 h-4" />
                              </Button>
                              
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTestEndpoint(endpoint.id);
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
                        {selectedEndpoint === endpoint.id && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                              <div>
                                <Label className="text-sm text-gray-600">Статус</Label>
                                <div className="mt-1">
                                  <Badge className={endpoint.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                                    {endpoint.active ? 'Активен' : 'Отключен'}
                                  </Badge>
                                </div>
                              </div>
                              
                              <div>
                                <Label className="text-sm text-gray-600">Retry Policy</Label>
                                <div className="mt-1">
                                  <span className="text-sm font-medium">
                                    {endpoint.retryPolicy.maxAttempts} попыток, {endpoint.retryPolicy.backoffStrategy}
                                  </span>
                                </div>
                              </div>
                              
                              <div>
                                <Label className="text-sm text-gray-600">URL</Label>
                                <div className="mt-1">
                                  <code className="text-xs bg-gray-100 px-2 py-1 rounded break-all">
                                    {`${window.location.origin}/webhooks/${endpoint.id}`}
                                  </code>
                                </div>
                              </div>
                            </div>

                            {endpointDeliveries.length > 0 && (
                              <div className="mt-4">
                                <Label className="text-sm text-gray-600 mb-2 block">Последние доставки</Label>
                                <div className="space-y-2 max-h-48 overflow-y-auto">
                                  {endpointDeliveries
                                    .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
                                    .slice(0, 5)
                                    .map((delivery) => (
                                      <div key={delivery.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                                        <div className="flex items-center gap-2">
                                          {getDeliveryIcon(delivery.status)}
                                          <span className="text-sm">{delivery.event.type}</span>
                                          <span className="text-xs text-gray-500">
                                            {delivery.createdAt.toLocaleString()}
                                          </span>
                                        </div>
                                        
                                        <div className="flex items-center gap-2">
                                          {getStatusBadge(delivery.status)}
                                          {delivery.response && (
                                            <span className="text-xs text-gray-500">
                                              {delivery.response.timing.duration}ms
                                            </span>
                                          )}
                                          {delivery.status === 'failed' && (
                                            <Button
                                              size="sm"
                                              variant="ghost"
                                              onClick={() => handleRetryDelivery(delivery.id)}
                                            >
                                              Повторить
                                            </Button>
                                          )}
                                        </div>
                                      </div>
                                    ))}
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
        </TabsContent>

        {/* События */}
        <TabsContent value="events">
          <Card>
            <CardHeader>
              <CardTitle>События в очереди</CardTitle>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <div className="text-center py-12">
                  <Activity className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Нет событий в очереди</h3>
                  <p className="text-gray-600">События будут отображаться здесь после триггера</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {events
                    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
                    .map((event) => (
                      <div key={event.id} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-gray-900">{event.type}</h3>
                            <p className="text-sm text-gray-600">Источник: {event.source}</p>
                            <p className="text-xs text-gray-500">{event.timestamp.toLocaleString()}</p>
                          </div>
                          
                          <div className="text-right">
                            <Badge variant="outline">
                              ID: {event.id.slice(-8)}
                            </Badge>
                          </div>
                        </div>
                        
                        {event.data && (
                          <div className="mt-2">
                            <Label className="text-sm text-gray-600">Данные:</Label>
                            <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                              {JSON.stringify(event.data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Доставка */}
        <TabsContent value="deliveries">
          <Card>
            <CardHeader>
              <CardTitle>История доставки</CardTitle>
            </CardHeader>
            <CardContent>
              {deliveries.length === 0 ? (
                <div className="text-center py-12">
                  <Send className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Нет доставок</h3>
                  <p className="text-gray-600">История доставки будет отображаться здесь</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {deliveries
                    .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
                    .map((delivery) => {
                      const endpoint = endpoints.find(e => e.id === delivery.webhookId);
                      
                      return (
                        <div key={delivery.id} className="p-4 border rounded-lg">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              {getDeliveryIcon(delivery.status)}
                              
                              <div>
                                <h3 className="font-medium text-gray-900">
                                  {endpoint?.name || delivery.webhookId}
                                </h3>
                                <p className="text-sm text-gray-600">{delivery.event.type}</p>
                                <p className="text-xs text-gray-500">{delivery.createdAt.toLocaleString()}</p>
                              </div>
                            </div>
                            
                            <div className="text-right">
                              {getStatusBadge(delivery.status)}
                              {delivery.attempts > 1 && (
                                <p className="text-xs text-gray-500 mt-1">
                                  Попытка {delivery.attempts}
                                </p>
                              )}
                            </div>
                          </div>
                          
                          {delivery.error && (
                            <div className="mt-2">
                              <Label className="text-sm text-red-600">Ошибка:</Label>
                              <p className="text-sm text-red-700">{delivery.error}</p>
                            </div>
                          )}
                          
                          {delivery.response && (
                            <div className="mt-2">
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-600">Статус:</span> {delivery.response.status}
                                </div>
                                <div>
                                  <span className="text-gray-600">Время:</span> {formatDuration(delivery.response.timing.duration)}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Аналитика */}
        <TabsContent value="analytics">
          <Card>
            <CardHeader>
              <CardTitle>Аналитика Webhook</CardTitle>
            </CardHeader>
            <CardContent>
              {metrics ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="text-center">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Общая статистика</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Всего событий:</span>
                        <span className="font-medium">{metrics.totalEvents}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Доставлено:</span>
                        <span className="font-medium text-green-600">{metrics.deliveredEvents}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Ошибки:</span>
                        <span className="font-medium text-red-600">{metrics.failedEvents}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Повторы:</span>
                        <span className="font-medium text-yellow-600">{metrics.retryEvents}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Среднее время доставки:</span>
                        <span className="font-medium">{Math.round(metrics.averageDeliveryTime)}ms</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Производительность</h3>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm">Успешность</span>
                          <span className="text-sm font-medium">
                            {Math.round((metrics.deliveredEvents / Math.max(1, metrics.totalEvents)) * 100)}%
                          </span>
                        </div>
                        <Progress 
                          value={metrics.totalEvents > 0 ? (metrics.deliveredEvents / metrics.totalEvents) * 100 : 0} 
                          className="h-2"
                        />
                      </div>
                      
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm">Ошибки</span>
                          <span className="text-sm font-medium">
                            {metrics.totalEvents > 0 ? Math.round((metrics.failedEvents / metrics.totalEvents) * 100) : 0}%
                          </span>
                        </div>
                        <Progress 
                          value={metrics.totalEvents > 0 ? (metrics.failedEvents / metrics.totalEvents) * 100 : 0} 
                          className="h-2"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Последняя активность</h3>
                    <p className="text-sm text-gray-600">
                      {metrics.lastEvent ? metrics.lastEvent.toLocaleString() : 'Нет данных'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <BarChart3 className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-600">Загрузка аналитики...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Алерты и уведомления */}
      <div className="mt-6 space-y-4">
        <Alert>
          <Webhook className="h-4 w-4" />
          <AlertDescription>
            <strong>Webhook URL:</strong> Используйте уникальный URL для каждого endpoint. 
            Все webhook'и подписываются секретом для проверки подлинности.
          </AlertDescription>
        </Alert>

        <Alert>
          <RefreshCw className="h-4 w-4" />
          <AlertDescription>
            <strong>Повторные попытки:</strong> Неудачные доставки автоматически повторяются согласно 
            настройкам backoff стратегии.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
};