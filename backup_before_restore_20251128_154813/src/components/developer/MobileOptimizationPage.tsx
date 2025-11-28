import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Progress } from '../ui/progress';
import { ResponsiveDashboard } from './ResponsiveDashboard';
import DeviceOptimizationView from './DeviceOptimizationView';
import MobileNavigation from './MobileNavigation';
import { MobileSettingsPanel } from './MobileSettingsPanel';
import { MobileDetectionService } from '../../services/mobile-detection-service';
import { ResponsiveUIService } from '../../services/responsive-ui-service';
import { TouchInteractionService } from '../../services/touch-interaction-service';
import { MobileNavigationService } from '../../services/mobile-navigation-service';
import { MobilePerformanceService } from '../../services/mobile-performance-service';
import { DeviceInfo } from '../../services/mobile-detection-service';
import { 
  Smartphone, 
  Tablet, 
  Monitor, 
  Zap, 
  Battery, 
  Wifi, 
  Settings, 
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RotateCcw,
  Play,
  Pause,
  RefreshCw,
  Download,
  Upload,
  Eye,
  EyeOff,
  Navigation,
  Database,
  Cpu,
  MemoryStick,
  HardDrive,
  Clock,
  TrendingUp,
  Users,
  Code,
  Touchpad
} from 'lucide-react';

interface OptimizationMetrics {
  performance: {
    score: number;
    loadTime: number;
    memoryUsage: number;
    fps: number;
    batteryImpact: number;
  };
  device: {
    detectedType: string;
    screenSize: string;
    orientation: string;
    touchSupport: boolean;
    browserSupport: string;
  };
  accessibility: {
    touchTargets: number;
    colorContrast: number;
    fontSize: number;
    screenReader: boolean;
  };
  network: {
    connectionType: string;
    downloadSpeed: number;
    latency: number;
    dataUsage: number;
  };
  userExperience: {
    navigationEase: number;
    contentReadability: number;
    interactionResponsiveness: number;
    visualStability: number;
  };
}

interface OptimizationAction {
  id: string;
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  category: 'performance' | 'accessibility' | 'ui' | 'network';
  status: 'pending' | 'applied' | 'failed';
  automatic: boolean;
}

export const MobileOptimizationPage: React.FC = () => {
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo | null>(null);
  const [metrics, setMetrics] = useState<OptimizationMetrics>({
    performance: {
      score: 75,
      loadTime: 2.1,
      memoryUsage: 45,
      fps: 60,
      batteryImpact: 15
    },
    device: {
      detectedType: 'desktop',
      screenSize: '1920x1080',
      orientation: 'landscape',
      touchSupport: false,
      browserSupport: 'modern'
    },
    accessibility: {
      touchTargets: 85,
      colorContrast: 92,
      fontSize: 16,
      screenReader: true
    },
    network: {
      connectionType: 'wifi',
      downloadSpeed: 100,
      latency: 20,
      dataUsage: 25
    },
    userExperience: {
      navigationEase: 88,
      contentReadability: 91,
      interactionResponsiveness: 85,
      visualStability: 94
    }
  });

  const [suggestedActions, setSuggestedActions] = useState<OptimizationAction[]>([
    {
      id: '1',
      title: 'Включить отложенную загрузку',
      description: 'Уменьшить время загрузки страницы',
      impact: 'high',
      category: 'performance',
      status: 'pending',
      automatic: true
    },
    {
      id: '2',
      title: 'Оптимизировать изображения',
      description: 'Сжать изображения для экономии трафика',
      impact: 'high',
      category: 'performance',
      status: 'pending',
      automatic: true
    },
    {
      id: '3',
      title: 'Увеличить размеры элементов',
      description: 'Улучшить доступность для сенсорных устройств',
      impact: 'medium',
      category: 'accessibility',
      status: 'pending',
      automatic: false
    },
    {
      id: '4',
      title: 'Добавить жестовое управление',
      description: 'Внедрить свайпы для навигации',
      impact: 'medium',
      category: 'ui',
      status: 'pending',
      automatic: false
    }
  ]);

  const [isOptimizing, setIsOptimizing] = useState(false);
  const [autoOptimizationEnabled, setAutoOptimizationEnabled] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<string>('auto');

  // Service instances
  const mobileDetection = new MobileDetectionService();
  const touchInteraction = new TouchInteractionService();
  const responsiveUI = new ResponsiveUIService(mobileDetection);
  const mobileNavigation = new MobileNavigationService(mobileDetection, touchInteraction);
  const mobilePerformance = new MobilePerformanceService();

  useEffect(() => {
    // Detect device and initialize metrics
    const info = mobileDetection.getDeviceInfo();
    setDeviceInfo(info);
    
    // Update device metrics
    setMetrics(prev => ({
      ...prev,
      device: {
        detectedType: info.type,
        screenSize: `${info.screenSize.width}x${info.screenSize.height}`,
        orientation: info.orientation,
        touchSupport: info.isTouchDevice,
        browserSupport: 'modern'
      }
    }));

    // Generate context-specific suggestions
    generateOptimizationSuggestions(info);
  }, []);

  const generateOptimizationSuggestions = useCallback((deviceInfo: DeviceInfo) => {
    const actions: OptimizationAction[] = [];

    // Performance optimizations for mobile devices
    if (deviceInfo.type === 'mobile') {
      actions.push({
        id: 'perf1',
        title: 'Отложенная загрузка контента',
        description: 'Загружать контент по мере необходимости для экономии трафика',
        impact: 'high',
        category: 'performance',
        status: 'pending',
        automatic: true
      });

      actions.push({
        id: 'perf2',
        title: 'Оптимизация изображений',
        description: 'Сжимать изображения для мобильных устройств',
        impact: 'high',
        category: 'performance',
        status: 'pending',
        automatic: true
      });

      actions.push({
        id: 'perf3',
        title: 'Включить кэширование',
        description: 'Кэшировать ресурсы для быстрой загрузки',
        impact: 'medium',
        category: 'performance',
        status: 'pending',
        automatic: true
      });
    }

    // Touch accessibility for touch devices
    if (deviceInfo.isTouchDevice) {
      actions.push({
        id: 'acc1',
        title: 'Увеличить размеры кнопок',
        description: 'Обеспечить минимальный размер 44px для удобства касания',
        impact: 'high',
        category: 'accessibility',
        status: 'pending',
        automatic: false
      });

      actions.push({
        id: 'acc2',
        title: 'Добавить жестовое управление',
        description: 'Реализовать свайпы для навигации между разделами',
        impact: 'medium',
        category: 'ui',
        status: 'pending',
        automatic: false
      });
    }

    // Network optimizations
    actions.push({
      id: 'net1',
      title: 'Включить сжатие данных',
      description: 'Сжимать HTTP-ответы для экономии трафика',
      impact: 'medium',
      category: 'network',
      status: 'pending',
      automatic: true
    });

    setSuggestedActions(actions);
  }, []);

  const runOptimization = async () => {
    setIsOptimizing(true);
    
    try {
      // Run automated optimizations
      for (const action of suggestedActions.filter(a => a.automatic && a.status === 'pending')) {
        await applyOptimization(action);
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      // Update metrics based on applied optimizations
      setMetrics(prev => ({
        ...prev,
        performance: {
          ...prev.performance,
          score: Math.min(100, prev.performance.score + 15),
          loadTime: Math.max(0.5, prev.performance.loadTime - 0.8),
          batteryImpact: Math.max(5, prev.performance.batteryImpact - 5)
        }
      }));

      // Update action statuses
      setSuggestedActions(prev => prev.map(action => ({
        ...action,
        status: action.automatic ? 'applied' : action.status
      })));

    } catch (error) {
      console.error('Optimization failed:', error);
    } finally {
      setIsOptimizing(false);
    }
  };

  const applyOptimization = async (action: OptimizationAction): Promise<void> => {
    return new Promise((resolve) => {
      // Simulate optimization process
      setTimeout(() => {
        setSuggestedActions(prev => prev.map(a => 
          a.id === action.id ? { ...a, status: 'applied' as const } : a
        ));
        resolve();
      }, 1000);
    });
  };

  const resetOptimizations = () => {
    setSuggestedActions(prev => prev.map(action => ({
      ...action,
      status: 'pending' as const
    })));

    setMetrics(prev => ({
      ...prev,
      performance: {
        score: 75,
        loadTime: 2.1,
        memoryUsage: 45,
        fps: 60,
        batteryImpact: 15
      }
    }));
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'applied':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'performance':
        return <Zap className="w-4 h-4" />;
      case 'accessibility':
        return <Eye className="w-4 h-4" />;
      case 'ui':
        return <Smartphone className="w-4 h-4" />;
      case 'network':
        return <Wifi className="w-4 h-4" />;
      default:
        return <Settings className="w-4 h-4" />;
    }
  };

  const getOverallScore = () => {
    const scores = [
      metrics.performance.score,
      metrics.accessibility.touchTargets,
      metrics.userExperience.navigationEase,
      100 - metrics.network.dataUsage // Lower data usage is better
    ];
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  const isMobile = deviceInfo?.type === 'mobile';
  const isTablet = deviceInfo?.type === 'tablet';
  const overallScore = getOverallScore();

  return (
    <div className="mobile-optimization-page p-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Smartphone className="w-8 h-8 text-blue-500" />
              Мобильная оптимизация
            </h1>
            <p className="text-gray-600 mt-2">
              Комплексная оптимизация для мобильных устройств и планшетов
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Device Type Selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Режим просмотра:</span>
              <select 
                value={selectedDevice}
                onChange={(e) => setSelectedDevice(e.target.value)}
                className="px-3 py-1 border rounded-md text-sm"
              >
                <option value="auto">Авто</option>
                <option value="mobile">Мобильный</option>
                <option value="tablet">Планшет</option>
                <option value="desktop">Десктоп</option>
              </select>
            </div>

            {/* Auto Optimization Toggle */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Автооптимизация:</span>
              <button
                onClick={() => setAutoOptimizationEnabled(!autoOptimizationEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  autoOptimizationEnabled ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    autoOptimizationEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Overall Score Card */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className={`text-3xl font-bold ${overallScore >= 80 ? 'text-green-600' : overallScore >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {overallScore}%
                  </div>
                  <div className="text-sm text-gray-600">Общий балл</div>
                </div>
                
                <div className="h-16 w-px bg-gray-200" />
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-1">
                      <Zap className="w-4 h-4 text-blue-500 mr-1" />
                      <span className="text-lg font-semibold">{metrics.performance.score}</span>
                    </div>
                    <div className="text-xs text-gray-600">Performance</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-1">
                      <Eye className="w-4 h-4 text-green-500 mr-1" />
                      <span className="text-lg font-semibold">{metrics.accessibility.touchTargets}</span>
                    </div>
                    <div className="text-xs text-gray-600">Accessibility</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-1">
                      <Navigation className="w-4 h-4 text-purple-500 mr-1" />
                      <span className="text-lg font-semibold">{metrics.userExperience.navigationEase}</span>
                    </div>
                    <div className="text-xs text-gray-600">UX</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-1">
                      <Wifi className="w-4 h-4 text-orange-500 mr-1" />
                      <span className="text-lg font-semibold">{100 - metrics.network.dataUsage}</span>
                    </div>
                    <div className="text-xs text-gray-600">Network</div>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <Button 
                  onClick={runOptimization}
                  disabled={isOptimizing}
                  className="flex items-center gap-2"
                >
                  {isOptimizing ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  {isOptimizing ? 'Оптимизация...' : 'Запустить оптимизацию'}
                </Button>
                
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={resetOptimizations}
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Сбросить
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Device Status Alert */}
        <Alert className="mb-6">
          <Smartphone className="h-4 w-4" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span>
                Устройство: <strong>{deviceInfo?.type || 'Unknown'}</strong> • 
                Экран: <strong>{deviceInfo?.screenSize?.width}x{deviceInfo?.screenSize?.height}</strong> • 
                Touch: <strong>{deviceInfo?.isTouchDevice ? 'Да' : 'Нет'}</strong>
              </span>
              
              <div className="flex gap-1">
                {deviceInfo?.isTouchDevice && (
                  <Badge variant="outline" className="text-xs">
                    <Touchpad className="w-3 h-3 mr-1" />
                    Touch
                  </Badge>
                )}
                
                {deviceInfo?.isLandscape === false && (
                  <Badge variant="outline" className="text-xs">
                    📱 Portrait
                  </Badge>
                )}
                
                {deviceInfo?.isLandscape && (
                  <Badge variant="outline" className="text-xs">
                    🖥️ Landscape
                  </Badge>
                )}
              </div>
            </div>
          </AlertDescription>
        </Alert>

        {/* Main Content Tabs */}
        <Tabs defaultValue="overview" className="optimization-tabs">
          <TabsList className={`grid w-full ${isMobile ? 'grid-cols-2' : 'grid-cols-5'}`}>
            <TabsTrigger value="overview">
              {isMobile ? 'Обзор' : 'Overview'}
            </TabsTrigger>
            <TabsTrigger value="performance">
              {isMobile ? 'Производ.' : 'Performance'}
            </TabsTrigger>
            <TabsTrigger value="accessibility">
              {isMobile ? 'Доступность' : 'Accessibility'}
            </TabsTrigger>
            <TabsTrigger value="settings">
              {isMobile ? 'Настройки' : 'Settings'}
            </TabsTrigger>
            <TabsTrigger value="preview">
              {isMobile ? 'Превью' : 'Preview'}
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Optimization Suggestions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="w-5 h-5" />
                    Предложения по оптимизации
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {suggestedActions.map((action) => (
                      <div key={action.id} className="flex items-start gap-3 p-3 border rounded-lg">
                        {getStatusIcon(action.status)}
                        
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            {getCategoryIcon(action.category)}
                            <h4 className="font-medium">{action.title}</h4>
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${getImpactColor(action.impact)}`}
                            >
                              {action.impact}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600">{action.description}</p>
                          
                          <div className="flex items-center gap-2 mt-2">
                            {action.automatic && (
                              <Badge variant="secondary" className="text-xs">
                                Авто
                              </Badge>
                            )}
                            <Badge 
                              variant={action.status === 'applied' ? 'default' : 'outline'}
                              className="text-xs"
                            >
                              {action.status === 'applied' ? 'Применено' : 
                               action.status === 'failed' ? 'Ошибка' : 'Ожидает'}
                            </Badge>
                          </div>
                        </div>
                        
                        {!action.automatic && action.status === 'pending' && (
                          <Button 
                            size="sm"
                            onClick={() => applyOptimization(action)}
                          >
                            Применить
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Quick Stats */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Быстрая статистика
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Время загрузки</span>
                      <span className="text-sm font-bold">{metrics.performance.loadTime}с</span>
                    </div>
                    <Progress value={(3 - metrics.performance.loadTime) / 3 * 100} className="h-2" />

                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Использование памяти</span>
                      <span className="text-sm font-bold">{metrics.performance.memoryUsage}%</span>
                    </div>
                    <Progress value={metrics.performance.memoryUsage} className="h-2" />

                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Влияние на батарею</span>
                      <span className="text-sm font-bold">{metrics.performance.batteryImpact}%</span>
                    </div>
                    <Progress value={metrics.performance.batteryImpact} className="h-2" />

                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Использование данных</span>
                      <span className="text-sm font-bold">{metrics.network.dataUsage}MB</span>
                    </div>
                    <Progress value={metrics.network.dataUsage} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="mt-6">
            <ResponsiveDashboard />
          </TabsContent>

          {/* Accessibility Tab */}
          <TabsContent value="accessibility" className="mt-6">
            <DeviceOptimizationView 
              mobileDetection={mobileDetection}
              responsiveUI={responsiveUI}
              touchInteraction={touchInteraction}
            />
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="mt-6">
            <MobileSettingsPanel />
          </TabsContent>

          {/* Preview Tab */}
          <TabsContent value="preview" className="mt-6">
            <div className="space-y-6">
              {/* Mobile Navigation Preview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Navigation className="w-5 h-5" />
                    Навигация
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <MobileNavigation 
                    navigationService={mobileNavigation}
                    mobileDetection={mobileDetection}
                  />
                </CardContent>
              </Card>

              {/* Responsive Preview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="w-5 h-5" />
                    Адаптивный предпросмотр
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="border rounded-lg p-4 bg-gray-50 min-h-96">
                    <p className="text-gray-600 text-center">
                      Здесь будет предпросмотр адаптивного дизайна...
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                      {Array.from({ length: 6 }, (_, i) => (
                        <div key={i} className="bg-white p-4 rounded border">
                          <h4 className="font-medium mb-2">Карточка {i + 1}</h4>
                          <p className="text-sm text-gray-600">
                            Пример адаптивного контента
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};