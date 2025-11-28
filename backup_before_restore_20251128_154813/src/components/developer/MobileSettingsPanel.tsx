import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Button } from '../ui/button';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Slider } from '../ui/slider';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Separator } from '../ui/separator';
import { MobileDetectionService } from '../../services/mobile-detection-service';
import { ResponsiveUIService } from '../../services/responsive-ui-service';
import { TouchInteractionService } from '../../services/touch-interaction-service';
import { MobilePerformanceService } from '../../services/mobile-performance-service';
import { 
  Settings, 
  Smartphone, 
  Monitor, 
  Battery, 
  Wifi, 
  Volume2, 
  Eye, 
  Zap,
  Touchpad,
  Navigation,
  Database,
  Cloud,
  HardDrive,
  Cpu,
  MemoryStick,
  Clock,
  RefreshCw,
  Download,
  Upload,
  Trash2,
  Save
} from 'lucide-react';

interface MobileSettingsData {
  display: {
    theme: 'light' | 'dark' | 'auto';
    fontSize: number;
    compactMode: boolean;
    animationsEnabled: boolean;
    layoutDensity: 'comfortable' | 'compact' | 'dense';
  };
  
  performance: {
    lazyLoadingEnabled: boolean;
    imageOptimization: boolean;
    prefetchEnabled: boolean;
    cacheStrategy: 'aggressive' | 'balanced' | 'minimal';
    serviceWorkerEnabled: boolean;
    backgroundSync: boolean;
  };
  
  interaction: {
    hapticFeedback: boolean;
    voiceControl: boolean;
    gestureNavigation: boolean;
    longPressDuration: number;
    swipeThreshold: number;
    touchSensitivity: number;
  };
  
  network: {
    offlineMode: boolean;
    dataCompression: boolean;
    requestTimeout: number;
    retryAttempts: number;
    cacheTimeout: number;
  };
  
  privacy: {
    analyticsEnabled: boolean;
    errorReporting: boolean;
    crashReports: boolean;
    usageTracking: boolean;
    dataExport: boolean;
  };
}

interface MobileSettingsPanelProps {
  className?: string;
  initialSettings?: Partial<MobileSettingsData>;
  onSettingsChange?: (settings: MobileSettingsData) => void;
  onSave?: (settings: MobileSettingsData) => void;
  onReset?: () => void;
}

export const MobileSettingsPanel: React.FC<MobileSettingsPanelProps> = ({
  className = '',
  initialSettings,
  onSettingsChange,
  onSave,
  onReset
}) => {
  const [deviceInfo, setDeviceInfo] = useState<any>(null);
  const [currentSettings, setCurrentSettings] = useState<MobileSettingsData>({
    display: {
      theme: 'auto',
      fontSize: 16,
      compactMode: false,
      animationsEnabled: true,
      layoutDensity: 'comfortable'
    },
    performance: {
      lazyLoadingEnabled: true,
      imageOptimization: true,
      prefetchEnabled: false,
      cacheStrategy: 'balanced',
      serviceWorkerEnabled: true,
      backgroundSync: false
    },
    interaction: {
      hapticFeedback: false,
      voiceControl: false,
      gestureNavigation: true,
      longPressDuration: 500,
      swipeThreshold: 50,
      touchSensitivity: 1.0
    },
    network: {
      offlineMode: false,
      dataCompression: true,
      requestTimeout: 10000,
      retryAttempts: 3,
      cacheTimeout: 300000
    },
    privacy: {
      analyticsEnabled: true,
      errorReporting: true,
      crashReports: true,
      usageTracking: false,
      dataExport: false
    },
    ...initialSettings
  });

  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Service instances
  const mobileDetection = new MobileDetectionService();
  const touchInteraction = new TouchInteractionService();
  const responsiveUI = new ResponsiveUIService(mobileDetection);
  const mobilePerformance = new MobilePerformanceService();

  useEffect(() => {
    // Detect current device capabilities
    const info = mobileDetection.getDeviceInfo();
    setDeviceInfo(info);
    
    // Apply initial device-optimized settings
    if (info.type === 'mobile') {
      setCurrentSettings(prev => ({
        ...prev,
        display: {
          ...prev.display,
          compactMode: true,
          animationsEnabled: false
        },
        performance: {
          ...prev.performance,
          lazyLoadingEnabled: true,
          imageOptimization: true
        }
      }));
    }
  }, []);

  const updateSetting = useCallback((category: keyof MobileSettingsData, key: string, value: any) => {
    setCurrentSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
    setHasChanges(true);
    
    if (onSettingsChange) {
      onSettingsChange(currentSettings);
    }
  }, [currentSettings, onSettingsChange]);

  const handleSave = async () => {
    setIsSaving(true);
    
    try {
      // Apply settings to services
      if (currentSettings.display.theme !== 'auto') {
        document.documentElement.setAttribute('data-theme', currentSettings.display.theme);
      }
      
      if (currentSettings.display.animationsEnabled) {
        document.body.classList.add('animations-enabled');
      } else {
        document.body.classList.remove('animations-enabled');
      }
      
      // Save to localStorage
      localStorage.setItem('mobileSettings', JSON.stringify(currentSettings));
      
      // Notify parent component
      if (onSave) {
        await onSave(currentSettings);
      }
      
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setCurrentSettings({
      display: {
        theme: 'auto',
        fontSize: 16,
        compactMode: false,
        animationsEnabled: true,
        layoutDensity: 'comfortable'
      },
      performance: {
        lazyLoadingEnabled: true,
        imageOptimization: true,
        prefetchEnabled: false,
        cacheStrategy: 'balanced',
        serviceWorkerEnabled: true,
        backgroundSync: false
      },
      interaction: {
        hapticFeedback: false,
        voiceControl: false,
        gestureNavigation: true,
        longPressDuration: 500,
        swipeThreshold: 50,
        touchSensitivity: 1.0
      },
      network: {
        offlineMode: false,
        dataCompression: true,
        requestTimeout: 10000,
        retryAttempts: 3,
        cacheTimeout: 300000
      },
      privacy: {
        analyticsEnabled: true,
        errorReporting: true,
        crashReports: true,
        usageTracking: false,
        dataExport: false
      }
    });
    setHasChanges(true);
    
    if (onReset) {
      onReset();
    }
  };

  const exportSettings = () => {
    const dataStr = JSON.stringify(currentSettings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'mobile-settings.json';
    link.click();
    
    URL.revokeObjectURL(url);
  };

  const importSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedSettings = JSON.parse(e.target?.result as string);
        setCurrentSettings({ ...currentSettings, ...importedSettings });
        setHasChanges(true);
      } catch (error) {
        console.error('Failed to import settings:', error);
      }
    };
    reader.readAsText(file);
  };

  const isMobile = deviceInfo?.type === 'mobile';
  const isLowPerformance = deviceInfo?.performance?.class === 'low';

  return (
    <div className={`mobile-settings-panel ${className}`}>
      {/* Settings Header */}
      <div className="settings-header mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Settings className="w-6 h-6" />
              Настройки мобильной версии
            </h2>
            <p className="text-gray-600 mt-1">
              Оптимизация для {deviceInfo?.type || 'неизвестного'} устройства
              {hasChanges && <Badge variant="destructive" className="ml-2">Несохранено</Badge>}
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {isMobile && (
              <Badge variant="outline" className="flex items-center gap-1">
                <Smartphone className="w-3 h-3" />
                Mobile
              </Badge>
            )}
            
            {isLowPerformance && (
              <Badge variant="outline" className="flex items-center gap-1">
                <Zap className="w-3 h-3 text-orange-500" />
                Оптимизация
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Device Information */}
      <Card className="mb-6">
        <CardHeader>
          <h3 className="text-lg font-semibold">Информация об устройстве</h3>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              {deviceInfo?.type === 'mobile' ? (
                <Smartphone className="w-8 h-8 mx-auto mb-2 text-blue-500" />
              ) : deviceInfo?.type === 'tablet' ? (
                <Monitor className="w-8 h-8 mx-auto mb-2 text-green-500" />
              ) : (
                <Monitor className="w-8 h-8 mx-auto mb-2 text-purple-500" />
              )}
              <p className="text-sm font-medium">{deviceInfo?.type || 'Unknown'}</p>
            </div>
            
            <div className="text-center">
              <Cpu className="w-8 h-8 mx-auto mb-2 text-gray-500" />
              <p className="text-sm font-medium">{deviceInfo?.browser || 'Unknown'}</p>
              <p className="text-xs text-gray-500">{deviceInfo?.os || 'Unknown OS'}</p>
            </div>
            
            <div className="text-center">
              <HardDrive className="w-8 h-8 mx-auto mb-2 text-orange-500" />
              <p className="text-sm font-medium">
                {deviceInfo?.screenSize?.width}x{deviceInfo?.screenSize?.height}
              </p>
              <p className="text-xs text-gray-500">Размер экрана</p>
            </div>
            
            <div className="text-center">
              <Touchpad className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <p className="text-sm font-medium">
                {deviceInfo?.isTouchDevice ? 'Да' : 'Нет'}
              </p>
              <p className="text-xs text-gray-500">Touch поддержка</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Settings Tabs */}
      <Tabs defaultValue="display" className="settings-tabs">
        <TabsList className={`grid w-full ${isMobile ? 'grid-cols-2' : 'grid-cols-5'}`}>
          <TabsTrigger value="display">
            <Eye className="w-4 h-4 mr-2" />
            {isMobile ? 'Экран' : 'Display'}
          </TabsTrigger>
          <TabsTrigger value="performance">
            <Zap className="w-4 h-4 mr-2" />
            {isMobile ? 'Производ.' : 'Performance'}
          </TabsTrigger>
          <TabsTrigger value="interaction">
            <Touchpad className="w-4 h-4 mr-2" />
            {isMobile ? 'Управление' : 'Interaction'}
          </TabsTrigger>
          <TabsTrigger value="network">
            <Wifi className="w-4 h-4 mr-2" />
            {isMobile ? 'Сеть' : 'Network'}
          </TabsTrigger>
          <TabsTrigger value="privacy">
            <Database className="w-4 h-4 mr-2" />
            {isMobile ? 'Приватность' : 'Privacy'}
          </TabsTrigger>
        </TabsList>

        {/* Display Settings */}
        <TabsContent value="display" className="mt-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Внешний вид</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="theme-select">Тема</Label>
                  <Select 
                    value={currentSettings.display.theme} 
                    onValueChange={(value) => updateSetting('display', 'theme', value)}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">Светлая</SelectItem>
                      <SelectItem value="dark">Темная</SelectItem>
                      <SelectItem value="auto">Авто</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Размер шрифта: {currentSettings.display.fontSize}px</Label>
                  <Slider
                    value={[currentSettings.display.fontSize]}
                    onValueChange={(value) => updateSetting('display', 'fontSize', value[0])}
                    min={12}
                    max={24}
                    step={1}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Плотность макета</Label>
                  <Select 
                    value={currentSettings.display.layoutDensity} 
                    onValueChange={(value) => updateSetting('display', 'layoutDensity', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="comfortable">Комфортная</SelectItem>
                      <SelectItem value="compact">Компактная</SelectItem>
                      <SelectItem value="dense">Плотная</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="compact-mode">Компактный режим</Label>
                    <p className="text-sm text-gray-500">Уменьшает размеры элементов</p>
                  </div>
                  <Switch
                    id="compact-mode"
                    checked={currentSettings.display.compactMode}
                    onCheckedChange={(checked) => updateSetting('display', 'compactMode', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="animations">Анимации</Label>
                    <p className="text-sm text-gray-500">Включить плавные переходы</p>
                  </div>
                  <Switch
                    id="animations"
                    checked={currentSettings.display.animationsEnabled}
                    onCheckedChange={(checked) => updateSetting('display', 'animationsEnabled', checked)}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Performance Settings */}
        <TabsContent value="performance" className="mt-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Оптимизация производительности</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="lazy-loading">Отложенная загрузка</Label>
                    <p className="text-sm text-gray-500">Загружает контент по мере необходимости</p>
                  </div>
                  <Switch
                    id="lazy-loading"
                    checked={currentSettings.performance.lazyLoadingEnabled}
                    onCheckedChange={(checked) => updateSetting('performance', 'lazyLoadingEnabled', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="image-optimization">Оптимизация изображений</Label>
                    <p className="text-sm text-gray-500">Сжимает изображения для экономии трафика</p>
                  </div>
                  <Switch
                    id="image-optimization"
                    checked={currentSettings.performance.imageOptimization}
                    onCheckedChange={(checked) => updateSetting('performance', 'imageOptimization', checked)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Стратегия кэширования</Label>
                  <Select 
                    value={currentSettings.performance.cacheStrategy} 
                    onValueChange={(value) => updateSetting('performance', 'cacheStrategy', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="aggressive">Агрессивное</SelectItem>
                      <SelectItem value="balanced">Сбалансированное</SelectItem>
                      <SelectItem value="minimal">Минимальное</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="service-worker">Service Worker</Label>
                    <p className="text-sm text-gray-500">Работа в автономном режиме</p>
                  </div>
                  <Switch
                    id="service-worker"
                    checked={currentSettings.performance.serviceWorkerEnabled}
                    onCheckedChange={(checked) => updateSetting('performance', 'serviceWorkerEnabled', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="background-sync">Фоновая синхронизация</Label>
                    <p className="text-sm text-gray-500">Синхронизация данных в фоне</p>
                  </div>
                  <Switch
                    id="background-sync"
                    checked={currentSettings.performance.backgroundSync}
                    onCheckedChange={(checked) => updateSetting('performance', 'backgroundSync', checked)}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Interaction Settings */}
        <TabsContent value="interaction" className="mt-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Способы взаимодействия</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="haptic-feedback">Тактильная обратная связь</Label>
                    <p className="text-sm text-gray-500">Вибрация при взаимодействии</p>
                  </div>
                  <Switch
                    id="haptic-feedback"
                    checked={currentSettings.interaction.hapticFeedback}
                    onCheckedChange={(checked) => updateSetting('interaction', 'hapticFeedback', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="voice-control">Голосовое управление</Label>
                    <p className="text-sm text-gray-500">Управление голосом</p>
                  </div>
                  <Switch
                    id="voice-control"
                    checked={currentSettings.interaction.voiceControl}
                    onCheckedChange={(checked) => updateSetting('interaction', 'voiceControl', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="gesture-navigation">Жестовое управление</Label>
                    <p className="text-sm text-gray-500">Навигация жестами</p>
                  </div>
                  <Switch
                    id="gesture-navigation"
                    checked={currentSettings.interaction.gestureNavigation}
                    onCheckedChange={(checked) => updateSetting('interaction', 'gestureNavigation', checked)}
                  />
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label>Длительность долгого нажатия: {currentSettings.interaction.longPressDuration}мс</Label>
                  <Slider
                    value={[currentSettings.interaction.longPressDuration]}
                    onValueChange={(value) => updateSetting('interaction', 'longPressDuration', value[0])}
                    min={300}
                    max={1000}
                    step={50}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Чувствительность касаний: {currentSettings.interaction.touchSensitivity.toFixed(1)}</Label>
                  <Slider
                    value={[currentSettings.interaction.touchSensitivity]}
                    onValueChange={(value) => updateSetting('interaction', 'touchSensitivity', value[0])}
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Network Settings */}
        <TabsContent value="network" className="mt-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Настройки сети</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="offline-mode">Автономный режим</Label>
                    <p className="text-sm text-gray-500">Работа без интернета</p>
                  </div>
                  <Switch
                    id="offline-mode"
                    checked={currentSettings.network.offlineMode}
                    onCheckedChange={(checked) => updateSetting('network', 'offlineMode', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="data-compression">Сжатие данных</Label>
                    <p className="text-sm text-gray-500">Уменьшает использование трафика</p>
                  </div>
                  <Switch
                    id="data-compression"
                    checked={currentSettings.network.dataCompression}
                    onCheckedChange={(checked) => updateSetting('network', 'dataCompression', checked)}
                  />
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label>Таймаут запроса: {Math.round(currentSettings.network.requestTimeout / 1000)}с</Label>
                  <Slider
                    value={[currentSettings.network.requestTimeout]}
                    onValueChange={(value) => updateSetting('network', 'requestTimeout', value[0])}
                    min={5000}
                    max={30000}
                    step={1000}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Попытки повтора: {currentSettings.network.retryAttempts}</Label>
                  <Slider
                    value={[currentSettings.network.retryAttempts]}
                    onValueChange={(value) => updateSetting('network', 'retryAttempts', value[0])}
                    min={1}
                    max={5}
                    step={1}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Privacy Settings */}
        <TabsContent value="privacy" className="mt-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Приватность и безопасность</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="analytics">Аналитика</Label>
                    <p className="text-sm text-gray-500">Сбор анонимной статистики</p>
                  </div>
                  <Switch
                    id="analytics"
                    checked={currentSettings.privacy.analyticsEnabled}
                    onCheckedChange={(checked) => updateSetting('privacy', 'analyticsEnabled', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="error-reporting">Отчеты об ошибках</Label>
                    <p className="text-sm text-gray-500">Автоматическая отправка ошибок</p>
                  </div>
                  <Switch
                    id="error-reporting"
                    checked={currentSettings.privacy.errorReporting}
                    onCheckedChange={(checked) => updateSetting('privacy', 'errorReporting', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="crash-reports">Отчеты о сбоях</Label>
                    <p className="text-sm text-gray-500">Отправка данных о сбоях</p>
                  </div>
                  <Switch
                    id="crash-reports"
                    checked={currentSettings.privacy.crashReports}
                    onCheckedChange={(checked) => updateSetting('privacy', 'crashReports', checked)}
                  />
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="usage-tracking">Отслеживание использования</Label>
                    <p className="text-sm text-gray-500">Мониторинг активности</p>
                  </div>
                  <Switch
                    id="usage-tracking"
                    checked={currentSettings.privacy.usageTracking}
                    onCheckedChange={(checked) => updateSetting('privacy', 'usageTracking', checked)}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <Card className="mt-6">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            {/* Primary Actions */}
            <div className={`flex ${isMobile ? 'flex-col' : 'justify-between'} gap-4`}>
              <div className="flex gap-2">
                <Button 
                  onClick={handleSave} 
                  disabled={!hasChanges || isSaving}
                  className="flex items-center gap-2"
                >
                  {isSaving ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Сохранить
                </Button>
                
                <Button 
                  variant="outline" 
                  onClick={handleReset}
                  disabled={!hasChanges}
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Сбросить
                </Button>
              </div>

              {/* Import/Export */}
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={exportSettings}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Экспорт
                </Button>
                
                <Button variant="outline" size="sm" asChild>
                  <label className="cursor-pointer">
                    <Download className="w-4 h-4 mr-2" />
                    Импорт
                    <input 
                      type="file" 
                      accept=".json"
                      onChange={importSettings}
                      className="hidden"
                    />
                  </label>
                </Button>
              </div>
            </div>

            {/* Quick Presets (Mobile) */}
            {isMobile && (
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    // Apply battery saver preset
                    setCurrentSettings(prev => ({
                      ...prev,
                      display: { ...prev.display, animationsEnabled: false },
                      performance: { 
                        ...prev.performance, 
                        lazyLoadingEnabled: true,
                        imageOptimization: true,
                        cacheStrategy: 'aggressive'
                      },
                      network: { ...prev.network, dataCompression: true }
                    }));
                    setHasChanges(true);
                  }}
                >
                  <Battery className="w-4 h-4 mr-2" />
                  Экономия
                </Button>
                
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    // Apply performance preset
                    setCurrentSettings(prev => ({
                      ...prev,
                      display: { ...prev.display, animationsEnabled: true },
                      performance: { 
                        ...prev.performance, 
                        lazyLoadingEnabled: true,
                        imageOptimization: true,
                        serviceWorkerEnabled: true
                      }
                    }));
                    setHasChanges(true);
                  }}
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Производит.
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};