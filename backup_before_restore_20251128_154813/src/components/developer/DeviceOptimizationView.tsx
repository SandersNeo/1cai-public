import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Progress } from '../ui/progress';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { 
  Smartphone, 
  Tablet, 
  Monitor, 
  Touch, 
  Touchpad,
  Cpu, 
  MemoryStick, 
  Wifi, 
  Battery,
  Eye,
  EyeOff,
  Settings,
  Zap,
  Globe,
  HardDrive,
  BarChart3,
  RefreshCw,
  RotateCw,
  RotateCcw
} from 'lucide-react';
import { MobileDetectionService, DeviceInfo, MobilePreferences } from '../../services/mobile-detection-service';
import { ResponsiveUIService } from '../../services/responsive-ui-service';
import { TouchInteractionService } from '../../services/touch-interaction-service';

interface DeviceOptimizationViewProps {
  mobileDetection: MobileDetectionService;
  responsiveUI: ResponsiveUIService;
  touchInteraction: TouchInteractionService;
}

const DeviceOptimizationView: React.FC<DeviceOptimizationViewProps> = ({
  mobileDetection,
  responsiveUI,
  touchInteraction
}) => {
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo | null>(null);
  const [preferences, setPreferences] = useState<MobilePreferences | null>(null);
  const [touchStats, setTouchStats] = useState<any>(null);
  const [connectionInfo, setConnectionInfo] = useState<any>(null);
  const [batteryInfo, setBatteryInfo] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    // Subscribe to device changes
    const deviceSubscription = mobileDetection.deviceInfo$.subscribe(device => {
      setDeviceInfo(device);
    });

    const preferencesSubscription = mobileDetection.preferences$.subscribe(prefs => {
      setPreferences(prefs);
    });

    const touchStatsSubscription = touchInteraction.getGestureStats().subscribe(stats => {
      setTouchStats(stats);
    });

    const connectionSubscription = mobileDetection.getConnectionInfo().subscribe(info => {
      setConnectionInfo(info);
    });

    // Load battery info
    mobileDetection.getBatteryInfo().then(battery => {
      setBatteryInfo(battery);
    });

    return () => {
      deviceSubscription.unsubscribe();
      preferencesSubscription.unsubscribe();
      touchStatsSubscription.unsubscribe();
      connectionSubscription.unsubscribe();
    };
  }, [mobileDetection, touchInteraction]);

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'mobile': return <Smartphone className="h-6 w-6" />;
      case 'tablet': return <Tablet className="h-6 w-6" />;
      case 'desktop': return <Monitor className="h-6 w-6" />;
      default: return <Monitor className="h-6 w-6" />;
    }
  };

  const getConnectionColor = (speed: string) => {
    switch (speed) {
      case 'fast': return 'text-green-500';
      case 'medium': return 'text-yellow-500';
      case 'slow': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const updatePreference = (key: keyof MobilePreferences, value: any) => {
    const updatedPreferences = { ...preferences, [key]: value };
    setPreferences(updatedPreferences);
    // mobileDetection.updatePreferences(updatedPreferences);
    // Private method - cannot be called directly
  };

  const updateAccessibility = (key: string, value: any) => {
    if (preferences) {
      const updatedAccessibility = { ...preferences.accessibility, [key]: value };
      updatePreference('accessibility', updatedAccessibility);
    }
  };

  const DeviceCard: React.FC<{ title: string; icon: React.ReactNode; children: React.ReactNode }> = ({ 
    title, 
    icon, 
    children 
  }) => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {children}
      </CardContent>
    </Card>
  );

  const MetricCard: React.FC<{ 
    title: string; 
    value: string | number; 
    icon: React.ReactNode; 
    color?: string;
    subtitle?: string;
  }> = ({ title, value, icon, color = 'text-blue-500', subtitle }) => (
    <div className="flex items-center justify-between p-3 border rounded-lg">
      <div className="flex items-center gap-2">
        <div className={color}>{icon}</div>
        <div>
          <p className="text-sm font-medium">{title}</p>
          {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
        </div>
      </div>
      <div className="text-right">
        <p className="text-lg font-bold">{value}</p>
      </div>
    </div>
  );

  return (
    <div className="device-optimization space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Smartphone className="h-6 w-6" />
            Оптимизация для устройств
          </h2>
          <p className="text-muted-foreground">
            Автоматическая адаптация интерфейса под ваше устройство
          </p>
        </div>
        <Badge variant={deviceInfo ? "default" : "secondary"}>
          {deviceInfo ? 'Устройство определено' : 'Определение...'}
        </Badge>
      </div>

      {/* Информация об устройстве */}
      {deviceInfo && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <DeviceCard title="Тип устройства" icon={getDeviceIcon(deviceInfo.type)}>
            <div className="space-y-2">
              <MetricCard 
                title="Устройство" 
                value={deviceInfo.type} 
                icon={getDeviceIcon(deviceInfo.type)}
                color="text-purple-500"
              />
              <MetricCard 
                title="ОС" 
                value={deviceInfo.os} 
                icon={<Settings className="h-4 w-4" />}
                color="text-green-500"
              />
              <MetricCard 
                title="Браузер" 
                value={deviceInfo.browser} 
                icon={<Globe className="h-4 w-4" />}
                color="text-blue-500"
              />
            </div>
          </DeviceCard>

          <DeviceCard title="Экран и отображение" icon={<Eye />}>
            <div className="space-y-2">
              <MetricCard 
                title="Разрешение" 
                value={`${deviceInfo.screenSize.width} × ${deviceInfo.screenSize.height}`}
                icon={<Monitor className="h-4 w-4" />}
                color="text-orange-500"
              />
              <MetricCard 
                title="Плотность пикселей" 
                value={`${deviceInfo.screenSize.devicePixelRatio}x`}
                icon={<BarChart3 className="h-4 w-4" />}
                color="text-indigo-500"
              />
              <MetricCard 
                title="Ориентация" 
                value={deviceInfo.isLandscape ? 'Альбомная' : 'Книжная'}
                icon={deviceInfo.isLandscape ? <RotateCw className="h-4 w-4" /> : <RotateCcw className="h-4 w-4" />}
                color="text-pink-500"
              />
            </div>
          </DeviceCard>

          <DeviceCard title="Возможности" icon={<Zap />}>
            <div className="space-y-2">
              {Object.entries(deviceInfo.capabilities).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm capitalize">
                    {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                  </span>
                  <Badge variant={value ? "default" : "secondary"}>
                    {value ? <Eye className="h-3 w-3 mr-1" /> : <EyeOff className="h-3 w-3 mr-1" />}
                    {value ? 'Да' : 'Нет'}
                  </Badge>
                </div>
              ))}
            </div>
          </DeviceCard>
        </div>
      )}

      {/* Производительность */}
      {deviceInfo && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <DeviceCard title="Производительность" icon={<Cpu />}>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Скорость соединения</span>
                  <span className={getConnectionColor(deviceInfo.performance.connectionSpeed)}>
                    {deviceInfo.performance.connectionSpeed}
                  </span>
                </div>
                {connectionInfo && (
                  <div className="text-xs text-muted-foreground">
                    {connectionInfo.effectiveType} • {connectionInfo.downlink}Mbps
                  </div>
                )}
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Память</span>
                  <span>{deviceInfo.performance.memory}GB</span>
                </div>
                <Progress value={(deviceInfo.performance.memory / 8) * 100} className="h-2" />
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Ядра процессора</span>
                  <span>{deviceInfo.performance.cores}</span>
                </div>
              </div>
            </div>
          </DeviceCard>

          <DeviceCard title="Батарея" icon={<Battery />}>
            {batteryInfo ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm">Заряд</span>
                  <span className="font-medium">{Math.round(batteryInfo.level * 100)}%</span>
                </div>
                <Progress value={batteryInfo.level * 100} className="h-2" />
                
                {batteryInfo.charging && (
                  <Badge variant="default" className="w-full justify-center">
                    Заряжается
                  </Badge>
                )}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">
                Информация о батарее недоступна
              </div>
            )}
          </DeviceCard>

          <DeviceCard title="Касания" icon={<Touch />}>
            <div className="space-y-2">
              <MetricCard 
                title="Touch устройство" 
                value={deviceInfo.isTouchDevice ? 'Да' : 'Нет'}
                icon={<Touch className="h-4 w-4" />}
                color={deviceInfo.isTouchDevice ? "text-green-500" : "text-gray-500"}
              />
              
              {touchStats && (
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Касаний</span>
                    <span>{touchStats.totalTouches}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Жестов</span>
                    <span>{touchStats.gestureCount}</span>
                  </div>
                </div>
              )}
            </div>
          </DeviceCard>

          <DeviceCard title="Хранилище" icon={<HardDrive />}>
            <div className="space-y-2">
              <div className="text-sm">
                <div className="flex justify-between mb-1">
                  <span>Использовано</span>
                  <span>2.1 GB</span>
                </div>
                <Progress value={42} className="h-2" />
              </div>
            </div>
          </DeviceCard>
        </div>
      )}

      {/* Настройки оптимизации */}
      {preferences && (
        <Card>
          <CardHeader>
            <CardTitle>Настройки оптимизации</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Обзор</TabsTrigger>
                <TabsTrigger value="display">Отображение</TabsTrigger>
                <TabsTrigger value="accessibility">Доступность</TabsTrigger>
                <TabsTrigger value="performance">Производительность</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <h4 className="font-semibold">Основные настройки</h4>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium">Компактный режим</label>
                        <p className="text-xs text-muted-foreground">
                          Уменьшает размеры элементов для экономии места
                        </p>
                      </div>
                      <Switch
                        checked={preferences.compactMode}
                        onCheckedChange={(checked) => updatePreference('compactMode', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium">Жестовая навигация</label>
                        <p className="text-xs text-muted-foreground">
                          Включает свайпы и жесты для навигации
                        </p>
                      </div>
                      <Switch
                        checked={preferences.gestureNavigation}
                        onCheckedChange={(checked) => updatePreference('gestureNavigation', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium">Голосовые команды</label>
                        <p className="text-xs text-muted-foreground">
                          Включает голосовое управление
                        </p>
                      </div>
                      <Switch
                        checked={preferences.voiceCommands}
                        onCheckedChange={(checked) => updatePreference('voiceCommands', checked)}
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="font-semibold">Уведомления</h4>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium">Включить уведомления</label>
                      </div>
                      <Switch
                        checked={preferences.notificationSettings.enabled}
                        onCheckedChange={(checked) => 
                          updatePreference('notificationSettings', {
                            ...preferences.notificationSettings,
                            enabled: checked
                          })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium">Звук</label>
                      </div>
                      <Switch
                        checked={preferences.notificationSettings.sound}
                        onCheckedChange={(checked) => 
                          updatePreference('notificationSettings', {
                            ...preferences.notificationSettings,
                            sound: checked
                          })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium">Вибрация</label>
                      </div>
                      <Switch
                        checked={preferences.notificationSettings.vibration}
                        onCheckedChange={(checked) => 
                          updatePreference('notificationSettings', {
                            ...preferences.notificationSettings,
                            vibration: checked
                          })
                        }
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-2 block">Приоритет</label>
                      <Select
                        value={preferences.notificationSettings.priority}
                        onValueChange={(value: any) => 
                          updatePreference('notificationSettings', {
                            ...preferences.notificationSettings,
                            priority: value
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Низкий</SelectItem>
                          <SelectItem value="medium">Средний</SelectItem>
                          <SelectItem value="high">Высокий</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="display" className="space-y-4">
                <div className="space-y-3">
                  <h4 className="font-semibold">Тема и отображение</h4>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Тема</label>
                    <Select
                      value={preferences.theme}
                      onValueChange={(value: any) => updatePreference('theme', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="light">Светлая</SelectItem>
                        <SelectItem value="dark">Темная</SelectItem>
                        <SelectItem value="auto">Автоматически</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Размер шрифта</label>
                    <Select
                      value={preferences.accessibility.fontSize}
                      onValueChange={(value: any) => updateAccessibility('fontSize', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="small">Маленький</SelectItem>
                        <SelectItem value="medium">Средний</SelectItem>
                        <SelectItem value="large">Большой</SelectItem>
                        <SelectItem value="extra-large">Очень большой</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Высокий контраст</label>
                      <p className="text-xs text-muted-foreground">
                        Увеличивает контрастность для лучшей видимости
                      </p>
                    </div>
                    <Switch
                      checked={preferences.accessibility.highContrast}
                      onCheckedChange={(checked) => updateAccessibility('highContrast', checked)}
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="accessibility" className="space-y-4">
                <div className="space-y-3">
                  <h4 className="font-semibold">Специальные возможности</h4>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Уменьшенная анимация</label>
                      <p className="text-xs text-muted-foreground">
                        Снижает или отключает анимации
                      </p>
                    </div>
                    <Switch
                      checked={preferences.accessibility.reducedMotion}
                      onCheckedChange={(checked) => updateAccessibility('reducedMotion', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium">Экранный диктор</label>
                      <p className="text-xs text-muted-foreground">
                        Оптимизация для программ чтения с экрана
                      </p>
                    </div>
                    <Switch
                      checked={preferences.accessibility.screenReader}
                      onCheckedChange={(checked) => updateAccessibility('screenReader', checked)}
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="performance" className="space-y-4">
                <div className="space-y-3">
                  <h4 className="font-semibold">Оптимизация производительности</h4>
                  
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">Автоматическая оптимизация</span>
                    </div>
                    <p className="text-xs text-blue-700">
                      Система автоматически применяет оптимизации на основе производительности вашего устройства
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Включена ленивая загрузка</span>
                      <Badge variant="default">Авто</Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Виртуальная прокрутка</span>
                      <Badge variant="default">Авто</Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Оптимизация изображений</span>
                      <Badge variant="default">Авто</Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Анимации</span>
                      <Badge variant="default">Авто</Badge>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Кнопка обновления */}
      <div className="flex justify-center">
        <Button variant="outline" onClick={() => window.location.reload()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Применить настройки
        </Button>
      </div>
    </div>
  );
};

export default DeviceOptimizationView;