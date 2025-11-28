import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Plug, 
  Play, 
  Pause, 
  Trash2, 
  Settings, 
  Activity, 
  BarChart3,
  Shield,
  AlertCircle,
  CheckCircle,
  Clock,
  Eye,
  EyeOff,
  Download,
  Upload,
  RefreshCw
} from 'lucide-react';
import { PluginManagerService, PluginInstance } from '@/services/plugin-manager-service';
import { PluginIntegrationService } from '@/services/plugin-integration-service';

interface PluginManagerViewProps {
  pluginManager: PluginManagerService;
  integrationService: PluginIntegrationService;
}

const PluginManagerView: React.FC<PluginManagerViewProps> = ({
  pluginManager,
  integrationService
}) => {
  const [plugins, setPlugins] = useState<PluginInstance[]>([]);
  const [selectedPlugin, setSelectedPlugin] = useState<PluginInstance | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('installed');

  useEffect(() => {
    loadPlugins();
    loadStats();

    // Subscribe to plugin events
    const pluginSubscription = pluginManager.pluginList$.subscribe(plugins => {
      setPlugins(plugins);
    });

    const performanceSubscription = pluginManager.performance$.subscribe(performance => {
      // Update performance metrics
    });

    return () => {
      pluginSubscription.unsubscribe();
      performanceSubscription.unsubscribe();
    };
  }, [pluginManager]);

  const loadPlugins = () => {
    const allPlugins = pluginManager.getAllPlugins();
    setPlugins(allPlugins);
  };

  const loadStats = () => {
    const pluginStats = pluginManager.getPluginStatistics();
    const integrationStats = integrationService.getIntegrationStatistics();
    setStats({
      plugins: pluginStats,
      integration: integrationStats
    });
  };

  const handlePluginAction = async (plugin: PluginInstance, action: 'activate' | 'deactivate' | 'uninstall') => {
    try {
      switch (action) {
        case 'activate':
          await pluginManager.activatePlugin(plugin.id);
          break;
        case 'deactivate':
          await pluginManager.deactivatePlugin(plugin.id);
          break;
        case 'uninstall':
          if (confirm(`Удалить плагин "${plugin.manifest.name}"?`)) {
            await pluginManager.uninstallPlugin(plugin.id);
          }
          break;
      }
      loadPlugins();
      loadStats();
    } catch (error) {
      console.error(`Failed to ${action} plugin:`, error);
      alert(`Ошибка ${action === 'activate' ? 'активации' : action === 'deactivate' ? 'деактивации' : 'удаления'} плагина`);
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'inactive': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      case 'loading': return 'bg-yellow-500';
      default: return 'bg-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4" />;
      case 'inactive': return <Pause className="h-4 w-4" />;
      case 'error': return <AlertCircle className="h-4 w-4" />;
      case 'loading': return <Clock className="h-4 w-4 animate-spin" />;
      default: return <Plug className="h-4 w-4" />;
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'active': return 'Активен';
      case 'inactive': return 'Неактивен';
      case 'error': return 'Ошибка';
      case 'loading': return 'Загрузка';
      default: return 'Неизвестно';
    }
  };

  const formatMemoryUsage = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const PluginCard: React.FC<{ plugin: PluginInstance }> = ({ plugin }) => (
    <Card 
      className={`cursor-pointer transition-all hover:shadow-md ${
        selectedPlugin?.id === plugin.id ? 'ring-2 ring-primary' : ''
      }`}
      onClick={() => setSelectedPlugin(plugin)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(plugin.status)}`} />
            <Plug className="h-5 w-5" />
            <div>
              <CardTitle className="text-lg">{plugin.manifest.name}</CardTitle>
              <p className="text-sm text-muted-foreground">v{plugin.manifest.version}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={plugin.status === 'active' ? 'default' : 'secondary'}>
              {getStatusIcon(plugin.status)}
              <span className="ml-1">{getStatusText(plugin.status)}</span>
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground line-clamp-2">
          {plugin.manifest.description}
        </p>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <Activity className="h-4 w-4" />
            <span>{plugin.manifest.author}</span>
          </div>
          {plugin.performance && (
            <div className="flex items-center gap-1">
              <BarChart3 className="h-4 w-4" />
              <span>{formatMemoryUsage(plugin.performance.memoryUsage)}</span>
            </div>
          )}
        </div>

        {plugin.error && (
          <div className="p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            {plugin.error}
          </div>
        )}

        <div className="flex gap-2">
          {plugin.status === 'active' ? (
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => {
                e.stopPropagation();
                handlePluginAction(plugin, 'deactivate');
              }}
            >
              <Pause className="h-4 w-4 mr-2" />
              Деактивировать
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handlePluginAction(plugin, 'activate');
              }}
            >
              <Play className="h-4 w-4 mr-2" />
              Активировать
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              handlePluginAction(plugin, 'uninstall');
            }}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Удалить
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const PluginDetail: React.FC<{ plugin: PluginInstance }> = ({ plugin }) => (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Plug className="h-5 w-5" />
              {plugin.manifest.name}
            </CardTitle>
            <p className="text-sm text-muted-foreground">{plugin.manifest.description}</p>
          </div>
          <Badge variant={plugin.status === 'active' ? 'default' : 'secondary'}>
            {getStatusText(plugin.status)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs defaultValue="info">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="info">Информация</TabsTrigger>
            <TabsTrigger value="permissions">Разрешения</TabsTrigger>
            <TabsTrigger value="resources">Ресурсы</TabsTrigger>
            <TabsTrigger value="performance">Производительность</TabsTrigger>
          </TabsList>

          <TabsContent value="info" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Версия</label>
                <p className="text-sm text-muted-foreground">{plugin.manifest.version}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Автор</label>
                <p className="text-sm text-muted-foreground">{plugin.manifest.author}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Категория</label>
                <p className="text-sm text-muted-foreground">{plugin.manifest.category}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Дата установки</label>
                <p className="text-sm text-muted-foreground">
                  {plugin.createdAt.toLocaleDateString('ru-RU')}
                </p>
              </div>
            </div>
            
            {plugin.manifest.metadata.homepage && (
              <div>
                <label className="text-sm font-medium">Домашняя страница</label>
                <a 
                  href={plugin.manifest.metadata.homepage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:underline"
                >
                  {plugin.manifest.metadata.homepage}
                </a>
              </div>
            )}
          </TabsContent>

          <TabsContent value="permissions" className="space-y-4">
            <div className="space-y-2">
              {plugin.manifest.permissions.map((permission, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    <div>
                      <p className="text-sm font-medium">{permission.type}</p>
                      <p className="text-xs text-muted-foreground">{permission.description}</p>
                    </div>
                  </div>
                  <Badge variant={permission.required ? "destructive" : "secondary"}>
                    {permission.required ? 'Обязательно' : 'Опционально'}
                  </Badge>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="resources" className="space-y-4">
            <div className="space-y-2">
              {plugin.manifest.resources.map((resource, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <p className="text-sm font-medium">{resource.name}</p>
                    <p className="text-xs text-muted-foreground">{resource.description}</p>
                  </div>
                  <Badge variant="outline">{resource.type}</Badge>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="performance" className="space-y-4">
            {plugin.performance ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Использование памяти</label>
                    <div className="mt-1">
                      <Progress value={75} className="mb-1" />
                      <p className="text-xs text-muted-foreground">
                        {formatMemoryUsage(plugin.performance.memoryUsage)}
                      </p>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium">CPU</label>
                    <div className="mt-1">
                      <Progress value={plugin.performance.cpuUsage} className="mb-1" />
                      <p className="text-xs text-muted-foreground">
                        {plugin.performance.cpuUsage.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Время ответа</label>
                    <p className="text-sm text-muted-foreground">
                      {plugin.performance.responseTime.toFixed(2)}мс
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Количество ошибок</label>
                    <p className="text-sm text-muted-foreground">
                      {plugin.performance.errorCount}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Данные о производительности недоступны
              </p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );

  return (
    <div className="plugin-manager space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Plug className="h-6 w-6" />
            Управление плагинами
          </h2>
          <p className="text-muted-foreground">
            Установка, настройка и мониторинг плагинов
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadPlugins}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Обновить
          </Button>
        </div>
      </div>

      {/* Статистика */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Plug className="h-8 w-8 text-muted-foreground" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Всего плагинов</p>
                  <p className="text-2xl font-bold">{stats.plugins.totalPlugins}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Activity className="h-8 w-8 text-muted-foreground" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Активных</p>
                  <p className="text-2xl font-bold">{stats.plugins.activePlugins}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Интеграций</p>
                  <p className="text-2xl font-bold">{stats.integration.activeIntegrations}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <AlertCircle className="h-8 w-8 text-muted-foreground" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Ошибки</p>
                  <p className="text-2xl font-bold">{stats.plugins.errorCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="installed">Установленные</TabsTrigger>
          <TabsTrigger value="available">Доступные</TabsTrigger>
          <TabsTrigger value="integrations">Интеграции</TabsTrigger>
        </TabsList>

        <TabsContent value="installed" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Плагины ({plugins.length})</h3>
              <div className="space-y-3">
                {plugins.map(plugin => (
                  <PluginCard key={plugin.id} plugin={plugin} />
                ))}
                {plugins.length === 0 && (
                  <div className="text-center py-8">
                    <Plug className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">Плагины не установлены</p>
                  </div>
                )}
              </div>
            </div>
            
            {selectedPlugin && (
              <div>
                <PluginDetail plugin={selectedPlugin} />
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="available" className="mt-6">
          <div className="text-center py-12">
            <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Установка плагинов</h3>
            <p className="text-muted-foreground mb-4">
              Используйте маркетплейс для поиска и установки новых плагинов
            </p>
            <Button>
              <Download className="h-4 w-4 mr-2" />
              Перейти к маркетплейсу
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="integrations" className="mt-6">
          <div className="text-center py-12">
            <Settings className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Интеграции с агентами</h3>
            <p className="text-muted-foreground">
              Настройте взаимодействие плагинов с агентами системы
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PluginManagerView;