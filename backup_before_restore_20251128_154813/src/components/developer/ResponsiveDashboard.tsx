import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { ResponsiveGrid } from '../responsive/ResponsiveGrid';
import { AdaptiveChart } from '../responsive/AdaptiveChart';
import { MobileCardsLayout } from '../responsive/MobileCardsLayout';
import { BreakpointManager } from '../../services/responsive-ui-service';
import { 
  BarChart3, 
  TrendingUp, 
  Smartphone, 
  Tablet, 
  Monitor,
  Battery,
  Network,
  Users,
  Code,
  Activity,
  Wifi,
  Zap
} from 'lucide-react';

interface DashboardMetrics {
  performance: {
    fps: number;
    memoryUsage: number;
    cpuUsage: number;
  };
  device: {
    type: 'mobile' | 'tablet' | 'desktop';
    orientation: 'portrait' | 'landscape';
    batteryLevel?: number;
    networkSpeed: 'slow' | 'fast' | 'gps';
  };
  user: {
    activeUsers: number;
    sessionDuration: number;
    bounceRate: number;
  };
  code: {
    componentsCount: number;
    servicesCount: number;
    apiCalls: number;
    errorRate: number;
  };
}

interface ResponsiveDashboardProps {
  className?: string;
  deviceType?: 'mobile' | 'tablet' | 'desktop';
  onDeviceChange?: (deviceType: string) => void;
}

export const ResponsiveDashboard: React.FC<ResponsiveDashboardProps> = ({
  className = '',
  deviceType,
  onDeviceChange
}) => {
  const [activeBreakpoint, setActiveBreakpoint] = useState<string>('desktop');
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('landscape');
  const [dashboardMetrics, setDashboardMetrics] = useState<DashboardMetrics>({
    performance: {
      fps: 60,
      memoryUsage: 45,
      cpuUsage: 25
    },
    device: {
      type: deviceType || 'desktop',
      orientation: 'landscape',
      batteryLevel: 85,
      networkSpeed: 'fast'
    },
    user: {
      activeUsers: 1247,
      sessionDuration: 245,
      bounceRate: 15.2
    },
    code: {
      componentsCount: 156,
      servicesCount: 89,
      apiCalls: 12500,
      errorRate: 0.8
    }
  });

  const breakpointManager = new BreakpointManager();

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth;
      let breakpoint = 'desktop';
      
      if (width < 768) {
        breakpoint = 'mobile';
      } else if (width < 1024) {
        breakpoint = 'tablet';
      }
      
      setActiveBreakpoint(breakpoint);
      setOrientation(width > height ? 'landscape' : 'portrait');
      
      // Update device type
      const newDeviceType = breakpoint as 'mobile' | 'tablet' | 'desktop';
      setDashboardMetrics(prev => ({
        ...prev,
        device: {
          ...prev.device,
          type: newDeviceType,
          orientation: width > height ? 'landscape' : 'portrait'
        }
      }));
      
      if (onDeviceChange) {
        onDeviceChange(newDeviceType);
      }
    };

    const height = window.innerHeight;
    updateBreakpoint();
    
    window.addEventListener('resize', updateBreakpoint);
    window.addEventListener('orientationchange', updateBreakpoint);

    return () => {
      window.removeEventListener('resize', updateBreakpoint);
      window.removeEventListener('orientationchange', updateBreakpoint);
    };
  }, [onDeviceChange]);

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'mobile': return <Smartphone className="w-4 h-4" />;
      case 'tablet': return <Tablet className="w-4 h-4" />;
      default: return <Monitor className="w-4 h-4" />;
    }
  };

  const getDeviceColor = (type: string) => {
    switch (type) {
      case 'mobile': return 'bg-blue-500';
      case 'tablet': return 'bg-green-500';
      default: return 'bg-purple-500';
    }
  };

  const getNetworkColor = (speed: string) => {
    switch (speed) {
      case 'slow': return 'bg-red-500';
      case 'fast': return 'bg-green-500';
      default: return 'bg-yellow-500';
    }
  };

  const isMobile = activeBreakpoint === 'mobile';
  const isTablet = activeBreakpoint === 'tablet';

  return (
    <div className={`responsive-dashboard ${className}`}>
      {/* Dashboard Header */}
      <div className="dashboard-header mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Адаптивный Дашборд</h2>
            <p className="text-gray-600 mt-1">
              Оптимизирован для {dashboardMetrics.device.type} • {orientation === 'portrait' ? 'Вертикальный' : 'Горизонтальный'} режим
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge className={`${getDeviceColor(dashboardMetrics.device.type)} text-white`}>
              {getDeviceIcon(dashboardMetrics.device.type)}
              {dashboardMetrics.device.type}
            </Badge>
            
            <Badge variant={orientation === 'portrait' ? 'default' : 'outline'}>
              {orientation === 'portrait' ? '📱' : '🖥️'}
              {orientation === 'portrait' ? 'Вертикальный' : 'Горизонтальный'}
            </Badge>
          </div>
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">FPS</p>
                <p className="text-2xl font-bold text-green-600">
                  {dashboardMetrics.performance.fps}
                </p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Память</p>
                <p className="text-2xl font-bold text-blue-600">
                  {dashboardMetrics.performance.memoryUsage}%
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Пользователи</p>
                <p className="text-2xl font-bold text-purple-600">
                  {dashboardMetrics.user.activeUsers}
                </p>
              </div>
              <Users className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Сетевой</p>
                <Badge className={`${getNetworkColor(dashboardMetrics.device.networkSpeed)} text-white`}>
                  <Wifi className="w-3 h-3 mr-1" />
                  {dashboardMetrics.device.networkSpeed}
                </Badge>
              </div>
              <Network className="w-8 h-8 text-gray-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Content */}
      <Tabs defaultValue="performance" className="dashboard-tabs">
        <TabsList className={`grid w-full ${isMobile ? 'grid-cols-2' : 'grid-cols-4'}`}>
          <TabsTrigger value="performance">
            <Zap className="w-4 h-4 mr-2" />
            {isMobile ? 'Производительность' : 'Performance'}
          </TabsTrigger>
          <TabsTrigger value="device">
            <Smartphone className="w-4 h-4 mr-2" />
            {isMobile ? 'Устройство' : 'Device'}
          </TabsTrigger>
          <TabsTrigger value="users">
            <Users className="w-4 h-4 mr-2" />
            {isMobile ? 'Пользователи' : 'Users'}
          </TabsTrigger>
          <TabsTrigger value="code">
            <Code className="w-4 h-4 mr-2" />
            {isMobile ? 'Код' : 'Code'}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Chart */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Производительность</h3>
              </CardHeader>
              <CardContent>
                <AdaptiveChart
                  type="line"
                  data={[
                    { name: 'FPS', value: dashboardMetrics.performance.fps },
                    { name: 'CPU', value: dashboardMetrics.performance.cpuUsage },
                    { name: 'Память', value: dashboardMetrics.performance.memoryUsage }
                  ]}
                  height={isMobile ? 200 : 300}
                  responsive={true}
                />
              </CardContent>
            </Card>

            {/* Battery Info (Mobile) */}
            {dashboardMetrics.device.batteryLevel && (
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Батарея</h3>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center h-32">
                    <div className="text-center">
                      <Battery className="w-16 h-16 mx-auto mb-4 text-green-500" />
                      <p className="text-3xl font-bold text-green-600">
                        {dashboardMetrics.device.batteryLevel}%
                      </p>
                      <p className="text-sm text-gray-600">Заряд батареи</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="device" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Тип устройства</h3>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center h-32">
                  {getDeviceIcon(dashboardMetrics.device.type)}
                  <span className="ml-3 text-xl font-medium capitalize">
                    {dashboardMetrics.device.type}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Ориентация</h3>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center h-32">
                  <div className="text-center">
                    <div className={`w-16 h-20 mx-auto mb-2 border-2 border-gray-300 rounded ${orientation === 'portrait' ? 'rotate-0' : 'rotate-90'}`}>
                      <div className="w-full h-full bg-blue-200 rounded"></div>
                    </div>
                    <p className="text-sm font-medium">
                      {orientation === 'portrait' ? 'Вертикальный' : 'Горизонтальный'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Сеть</h3>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center h-32">
                  <div className="text-center">
                    <Wifi className="w-16 h-16 mx-auto mb-2 text-blue-500" />
                    <Badge className={`${getNetworkColor(dashboardMetrics.device.networkSpeed)} text-white`}>
                      {dashboardMetrics.device.networkSpeed}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Активные пользователи</h3>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600 mb-2">
                    {dashboardMetrics.user.activeUsers}
                  </p>
                  <TrendingUp className="w-8 h-8 mx-auto text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Время сессии</h3>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600 mb-2">
                    {Math.floor(dashboardMetrics.user.sessionDuration / 60)}:
                    {(dashboardMetrics.user.sessionDuration % 60).toString().padStart(2, '0')}
                  </p>
                  <p className="text-sm text-gray-600">минут</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Показатель отказов</h3>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-orange-600 mb-2">
                    {dashboardMetrics.user.bounceRate}%
                  </p>
                  <p className="text-sm text-gray-600">от общего трафика</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="code" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Компоненты</h3>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600 mb-2">
                    {dashboardMetrics.code.componentsCount}
                  </p>
                  <Code className="w-8 h-8 mx-auto text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Сервисы</h3>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600 mb-2">
                    {dashboardMetrics.code.servicesCount}
                  </p>
                  <Activity className="w-8 h-8 mx-auto text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">API Вызовы</h3>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-purple-600 mb-2">
                    {(dashboardMetrics.code.apiCalls / 1000).toFixed(1)}k
                  </p>
                  <Network className="w-8 h-8 mx-auto text-purple-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Ошибки</h3>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-red-600 mb-2">
                    {dashboardMetrics.code.errorRate}%
                  </p>
                  <div className="w-8 h-8 mx-auto bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-red-600 text-sm">!</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Responsive Controls (Mobile) */}
      {isMobile && (
        <Card className="mt-6">
          <CardHeader>
            <h3 className="text-lg font-semibold">Быстрые действия</h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => {
                  setDashboardMetrics(prev => ({
                    ...prev,
                    performance: {
                      ...prev.performance,
                      fps: Math.max(30, prev.performance.fps - 5)
                    }
                  }));
                }}
              >
                <Zap className="w-4 h-4 mr-2" />
                Оптимизировать
              </Button>
              
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => {
                  window.location.reload();
                }}
              >
                <Activity className="w-4 h-4 mr-2" />
                Обновить
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};