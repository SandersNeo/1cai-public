import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Plug, 
  Store, 
  Settings, 
  Activity, 
  Package,
  Users,
  Shield,
  BarChart3,
  Cpu,
  HardDrive,
  Network,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';

// Import services
import { PluginManagerService } from '@/services/plugin-manager-service';
import { PluginRegistryService } from '@/services/plugin-registry-service';
import { PluginIntegrationService } from '@/services/plugin-integration-service';
import { PluginAPIService } from '@/services/plugin-api-service';

// Import components
import PluginMarketplace from './PluginMarketplace';
import PluginManagerView from './PluginManagerView';

const PluginSystemPage: React.FC = () => {
  // Initialize services
  const [pluginManager] = useState(() => new PluginManagerService());
  const [registryService] = useState(() => new PluginRegistryService());
  const [integrationService] = useState(() => new PluginIntegrationService(
    pluginManager,
    new PluginAPIService(),
    registryService
  ));
  const [apiService] = useState(() => new PluginAPIService());

  const [activeTab, setActiveTab] = useState('overview');
  const [isInitialized, setIsInitialized] = useState(false);
  const [systemStats, setSystemStats] = useState<any>(null);
  const [integrationStats, setIntegrationStats] = useState<any>(null);
  const [apiDocs, setApiDocs] = useState<any>(null);

  useEffect(() => {
    initializeServices();
    loadStatistics();
    loadAPIDocumentation();
  }, []);

  useEffect(() => {
    const statsSubscription = integrationService.metrics$.subscribe(stats => {
      setIntegrationStats(stats);
    });

    const pluginSubscription = pluginManager.pluginList$.subscribe(() => {
      loadStatistics();
    });

    return () => {
      statsSubscription.unsubscribe();
      pluginSubscription.unsubscribe();
    };
  }, [integrationService, pluginManager]);

  const initializeServices = async () => {
    try {
      await integrationService.initialize();
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize plugin services:', error);
    }
  };

  const loadStatistics = () => {
    const pluginStats = pluginManager.getPluginStatistics();
    const integrationStats = integrationService.getIntegrationStatistics();
    setSystemStats({
      plugins: pluginStats,
      integration: integrationStats
    });
  };

  const loadAPIDocumentation = () => {
    const docs = apiService.getAPIDocumentation();
    setApiDocs(docs);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'inactive': return <Clock className="h-4 w-4 text-gray-500" />;
      case 'error': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return <Activity className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'development': return '💻';
      case 'analytics': return '📊';
      case 'integration': return '🔗';
      case 'productivity': return '⚡';
      case 'visualization': return '📈';
      case 'automation': return '🤖';
      case 'theme': return '🎨';
      case 'utility': return '🛠️';
      default: return '📦';
    }
  };

  const handlePluginSelect = (plugin: any) => {
    console.log('Selected plugin:', plugin);
    // Handle plugin selection - could navigate to install dialog
  };

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4 animate-pulse" />
          <p className="text-muted-foreground">Инициализация системы плагинов...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="plugin-system-page space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Plug className="h-8 w-8" />
            Система плагинов
          </h1>
          <p className="text-muted-foreground mt-2">
            Расширьте функциональность агентной системы с помощью плагинов
          </p>
        </div>
        <Badge variant={isInitialized ? "default" : "secondary"}>
          {isInitialized ? "Активна" : "Неактивна"}
        </Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Обзор</TabsTrigger>
          <TabsTrigger value="marketplace">Маркетплейс</TabsTrigger>
          <TabsTrigger value="manager">Управление</TabsTrigger>
          <TabsTrigger value="integrations">Интеграции</TabsTrigger>
          <TabsTrigger value="api">API документация</TabsTrigger>
        </TabsList>

        {/* Обзор */}
        <TabsContent value="overview" className="space-y-6">
          {/* Основная статистика */}
          {systemStats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Package className="h-8 w-8 text-muted-foreground" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-muted-foreground">Всего плагинов</p>
                      <p className="text-2xl font-bold">{systemStats.plugins.totalPlugins}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Activity className="h-8 w-8 text-muted-foreground" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-muted-foreground">Активных плагинов</p>
                      <p className="text-2xl font-bold">{systemStats.plugins.activePlugins}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Users className="h-8 w-8 text-muted-foreground" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-muted-foreground">Интеграций</p>
                      <p className="text-2xl font-bold">{systemStats.integration.activeIntegrations}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <BarChart3 className="h-8 w-8 text-muted-foreground" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-muted-foreground">Ошибок</p>
                      <p className="text-2xl font-bold">{systemStats.plugins.errorCount}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Категории плагинов */}
          <Card>
            <CardHeader>
              <CardTitle>Категории плагинов</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {systemStats && Object.entries(systemStats.plugins.pluginsByCategory).map(([category, count]) => (
                  <div key={category} className="flex items-center gap-3 p-3 border rounded-lg">
                    <span className="text-2xl">{getCategoryIcon(category)}</span>
                    <div>
                      <p className="font-medium capitalize">{category}</p>
                      <p className="text-sm text-muted-foreground">{count as number} плагинов</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Состояние интеграций */}
          {integrationStats && (
            <Card>
              <CardHeader>
                <CardTitle>Состояние интеграций</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-semibold">Производительность</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Использование памяти</span>
                        <span className="text-sm text-muted-foreground">
                          {formatBytes(integrationStats.memoryUsage)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Уровень ошибок</span>
                        <span className="text-sm text-muted-foreground">
                          {(integrationStats.errorRate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h4 className="font-semibold">Распределение по агентам</h4>
                    <div className="space-y-2">
                      {Object.entries(integrationStats.integrationsByAgent).map(([agent, count]) => (
                        <div key={agent} className="flex items-center justify-between">
                          <span className="text-sm capitalize">{agent}</span>
                          <Badge variant="outline">{count as number}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Последние события */}
          <Card>
            <CardHeader>
              <CardTitle>Последние события</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Placeholder for recent events */}
                <div className="flex items-center gap-3 p-2 text-sm text-muted-foreground">
                  <Activity className="h-4 w-4" />
                  <span>Система плагинов инициализирована</span>
                  <span className="ml-auto">Только что</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Маркетплейс */}
        <TabsContent value="marketplace">
          <PluginMarketplace 
            registryService={registryService}
            onPluginSelect={handlePluginSelect}
          />
        </TabsContent>

        {/* Управление */}
        <TabsContent value="manager">
          <PluginManagerView
            pluginManager={pluginManager}
            integrationService={integrationService}
          />
        </TabsContent>

        {/* Интеграции */}
        <TabsContent value="integrations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Управление интеграциями</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Settings className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Настройка интеграций</h3>
                <p className="text-muted-foreground mb-4">
                  Управляйте взаимодействием плагинов с агентами системы
                </p>
                <Button>
                  <Settings className="h-4 w-4 mr-2" />
                  Настроить интеграции
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API документация */}
        <TabsContent value="api" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>API для разработчиков плагинов</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="overview">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="overview">Обзор</TabsTrigger>
                  <TabsTrigger value="endpoints">Эндпоинты</TabsTrigger>
                  <TabsTrigger value="hooks">Хуки</TabsTrigger>
                  <TabsTrigger value="examples">Примеры</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                  <div className="prose max-w-none">
                    <h3>Добро пожаловать в API плагинов</h3>
                    <p>
                      Этот API позволяет создавать плагины, которые расширяют функциональность 
                      агентной системы для 1C-разработки.
                    </p>
                    
                    <h4>Быстрый старт</h4>
                    <ol>
                      <li>Создайте манифест плагина</li>
                      <li>Реализуйте точки входа</li>
                      <li>Зарегистрируйте ресурсы</li>
                      <li>Установите и активируйте</li>
                    </ol>

                    <h4>Доступные сервисы</h4>
                    <ul>
                      <li><strong>Plugin Manager</strong> - Управление жизненным циклом плагинов</li>
                      <li><strong>Plugin API</strong> - REST API для плагинов</li>
                      <li><strong>Plugin Registry</strong> - Поиск и установка плагинов</li>
                      <li><strong>Plugin Integration</strong> - Интеграция с агентами</li>
                    </ul>
                  </div>
                </TabsContent>

                <TabsContent value="endpoints" className="space-y-4">
                  <div className="space-y-4">
                    <h4>Основные эндпоинты</h4>
                    {apiDocs && Object.entries(apiDocs.endpoints).map(([category, endpoints]) => (
                      <div key={category} className="border rounded-lg p-4">
                        <h5 className="font-semibold capitalize mb-2">{category}</h5>
                        <div className="space-y-2">
                          {(endpoints as any[]).map((endpoint, index) => (
                            <div key={index} className="flex items-center gap-2 text-sm">
                              <Badge variant="outline" className="font-mono">
                                {endpoint.method}
                              </Badge>
                              <code className="flex-1">{endpoint.path}</code>
                              <span className="text-muted-foreground">{endpoint.description}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="hooks" className="space-y-4">
                  <div className="space-y-4">
                    <h4>Системные хуки</h4>
                    {apiDocs && Object.entries(apiDocs.hooks).map(([category, hooks]) => (
                      <div key={category} className="border rounded-lg p-4">
                        <h5 className="font-semibold capitalize mb-2">{category}</h5>
                        <div className="space-y-2">
                          {(hooks as any[]).map((hook, index) => (
                            <div key={index} className="text-sm">
                              <code className="font-mono text-blue-600">{hook.name}</code>
                              <p className="text-muted-foreground">{hook.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="examples" className="space-y-4">
                  <div className="prose max-w-none">
                    <h4>Пример манифеста плагина</h4>
                    <pre><code>{`{
  "id": "my-custom-plugin",
  "name": "My Custom Plugin",
  "version": "1.0.0",
  "description": "Описание плагина",
  "author": "Your Name",
  "category": "development",
  "compatibility": {
    "minAgentVersion": "1.0.0",
    "supportedAgents": ["developer", "architect"]
  },
  "permissions": [
    { "type": "storage", "description": "Доступ к хранилищу", "required": true }
  ],
  "resources": [
    { "type": "service", "name": "MyService", "path": "./services/MyService" }
  ],
  "scripts": {
    "entry": "./index.js",
    "activation": "./activate.js"
  }
}`}</code></pre>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PluginSystemPage;