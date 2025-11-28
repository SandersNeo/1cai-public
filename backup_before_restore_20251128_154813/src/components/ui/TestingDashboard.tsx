import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  PlayCircle, 
  PauseCircle, 
  StopCircle, 
  BarChart3, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Settings,
  Download,
  Upload,
  RefreshCw,
  Activity,
  Clock,
  Users,
  Server
} from 'lucide-react';

interface TestSuite {
  id: string;
  name: string;
  type: 'unit' | 'integration' | 'e2e' | 'performance' | 'mobile';
  status: 'idle' | 'running' | 'passed' | 'failed' | 'stopped';
  totalTests: number;
  passedTests: number;
  failedTests: number;
  lastRun?: Date;
  duration?: number;
}

interface SystemResource {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

const TestingDashboard: React.FC = () => {
  const [testSuites, setTestSuites] = useState<TestSuite[]>([
    {
      id: 'unit-tests',
      name: 'Модульные тесты',
      type: 'unit',
      status: 'idle',
      totalTests: 245,
      passedTests: 0,
      failedTests: 0,
      lastRun: new Date('2025-10-31T20:00:00Z')
    },
    {
      id: 'integration-tests',
      name: 'Интеграционные тесты',
      type: 'integration',
      status: 'idle',
      totalTests: 89,
      passedTests: 0,
      failedTests: 0,
      lastRun: new Date('2025-10-31T19:30:00Z')
    },
    {
      id: 'e2e-tests',
      name: 'E2E тесты',
      type: 'e2e',
      status: 'idle',
      totalTests: 34,
      passedTests: 0,
      failedTests: 0,
      lastRun: new Date('2025-10-31T19:00:00Z')
    },
    {
      id: 'performance-tests',
      name: 'Производительность',
      type: 'performance',
      status: 'idle',
      totalTests: 12,
      passedTests: 0,
      failedTests: 0,
      lastRun: new Date('2025-10-31T18:45:00Z')
    },
    {
      id: 'mobile-tests',
      name: 'Мобильное тестирование',
      type: 'mobile',
      status: 'idle',
      totalTests: 67,
      passedTests: 0,
      failedTests: 0,
      lastRun: new Date('2025-10-31T18:30:00Z')
    }
  ]);

  const [systemResources, setSystemResources] = useState<SystemResource>({
    cpu: 12,
    memory: 45,
    disk: 68,
    network: 23
  });

  const [activeTests, setActiveTests] = useState<string[]>([]);
  const [overallProgress, setOverallProgress] = useState(0);
  const [testHistory, setTestHistory] = useState<any[]>([]);

  useEffect(() => {
    // Симуляция обновления ресурсов системы
    const interval = setInterval(() => {
      setSystemResources(prev => ({
        cpu: Math.max(0, Math.min(100, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(0, Math.min(100, prev.memory + (Math.random() - 0.5) * 5)),
        disk: Math.max(0, Math.min(100, prev.disk + (Math.random() - 0.5) * 2)),
        network: Math.max(0, Math.min(100, prev.network + (Math.random() - 0.5) * 15))
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const runTestSuite = async (suiteId: string) => {
    setTestSuites(prev => prev.map(suite => 
      suite.id === suiteId 
        ? { ...suite, status: 'running' as const }
        : suite
    ));

    setActiveTests(prev => [...prev, suiteId]);

    // Симуляция выполнения тестов
    const suite = testSuites.find(s => s.id === suiteId);
    if (!suite) return;

    // Симуляция выполнения с прогрессом
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200));
      setOverallProgress(i);
    }

    // Симуляция результатов
    const passed = Math.floor(suite.totalTests * (0.85 + Math.random() * 0.1));
    const failed = suite.totalTests - passed;

    setTestSuites(prev => prev.map(s => 
      s.id === suiteId 
        ? { 
            ...s, 
            status: failed === 0 ? 'passed' : 'failed',
            passedTests: passed,
            failedTests: failed,
            duration: Math.floor(Math.random() * 300) + 60,
            lastRun: new Date()
          }
        : s
    ));

    setActiveTests(prev => prev.filter(id => id !== suiteId));
    setOverallProgress(0);
  };

  const stopTestSuite = (suiteId: string) => {
    setTestSuites(prev => prev.map(suite => 
      suite.id === suiteId 
        ? { ...suite, status: 'stopped' as const }
        : suite
    ));

    setActiveTests(prev => prev.filter(id => id !== suiteId));
  };

  const runAllTests = async () => {
    const idleSuites = testSuites.filter(s => s.status === 'idle');
    
    for (const suite of idleSuites) {
      await runTestSuite(suite.id);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  };

  const stopAllTests = () => {
    testSuites.forEach(suite => {
      if (suite.status === 'running') {
        stopTestSuite(suite.id);
      }
    });
  };

  const getStatusIcon = (status: TestSuite['status']) => {
    switch (status) {
      case 'running': return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />;
      case 'passed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'stopped': return <PauseCircle className="h-4 w-4 text-yellow-500" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTypeColor = (type: TestSuite['type']) => {
    switch (type) {
      case 'unit': return 'bg-blue-100 text-blue-800';
      case 'integration': return 'bg-green-100 text-green-800';
      case 'e2e': return 'bg-purple-100 text-purple-800';
      case 'performance': return 'bg-orange-100 text-orange-800';
      case 'mobile': return 'bg-pink-100 text-pink-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Панель тестирования</h1>
              <p className="text-gray-600 mt-1">Центральный контроль всех тестов</p>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Настройки
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Экспорт
              </Button>
              <Button variant="outline" size="sm">
                <Upload className="h-4 w-4 mr-2" />
                Импорт
              </Button>
            </div>
          </div>
        </div>

        {/* Метрики в реальном времени */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Активные тесты</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeTests.length}</div>
              <p className="text-xs text-muted-foreground">
                Выполняются сейчас
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CPU</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemResources.cpu.toFixed(1)}%</div>
              <Progress value={systemResources.cpu} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Память</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemResources.memory.toFixed(1)}%</div>
              <Progress value={systemResources.memory} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Пользователи</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1</div>
              <p className="text-xs text-muted-foreground">
                Активный сеанс
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Глобальные элементы управления */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Глобальное управление</CardTitle>
            <CardDescription>
              Запуск и остановка всех тестов
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4">
              <Button 
                onClick={runAllTests}
                disabled={activeTests.length > 0}
                className="flex items-center space-x-2"
              >
                <PlayCircle className="h-4 w-4" />
                <span>Запустить все</span>
              </Button>
              
              <Button 
                variant="destructive"
                onClick={stopAllTests}
                disabled={activeTests.length === 0}
                className="flex items-center space-x-2"
              >
                <StopCircle className="h-4 w-4" />
                <span>Остановить все</span>
              </Button>

              {overallProgress > 0 && overallProgress < 100 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">Общий прогресс:</span>
                  <Progress value={overallProgress} className="w-32" />
                  <span className="text-sm font-medium">{overallProgress}%</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Наборы тестов */}
        <Tabs defaultValue="suites" className="space-y-6">
          <TabsList>
            <TabsTrigger value="suites">Наборы тестов</TabsTrigger>
            <TabsTrigger value="history">История</TabsTrigger>
            <TabsTrigger value="analytics">Аналитика</TabsTrigger>
          </TabsList>

          <TabsContent value="suites" className="space-y-6">
            <div className="grid gap-6">
              {testSuites.map((suite) => (
                <Card key={suite.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(suite.status)}
                        <div>
                          <CardTitle className="text-lg">{suite.name}</CardTitle>
                          <CardDescription>
                            {suite.totalTests} тестов
                          </CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={getTypeColor(suite.type)}>
                          {suite.type.toUpperCase()}
                        </Badge>
                        {suite.lastRun && (
                          <span className="text-sm text-gray-500">
                            Последний запуск: {suite.lastRun.toLocaleString('ru-RU')}
                          </span>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="space-y-4">
                      {suite.status === 'running' && (
                        <Alert>
                          <RefreshCw className="h-4 w-4 animate-spin" />
                          <AlertDescription>
                            Выполняется... {suite.passedTests} пройдено, {suite.failedTests} не пройдено
                          </AlertDescription>
                        </Alert>
                      )}

                      {suite.passedTests > 0 || suite.failedTests > 0 ? (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Результаты последнего запуска:</span>
                            <div className="flex items-center space-x-4">
                              <span className="flex items-center text-green-600">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                {suite.passedTests}
                              </span>
                              <span className="flex items-center text-red-600">
                                <XCircle className="h-3 w-3 mr-1" />
                                {suite.failedTests}
                              </span>
                              {suite.duration && (
                                <span className="text-gray-500">
                                  {Math.floor(suite.duration / 60)}:{(suite.duration % 60).toString().padStart(2, '0')}
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <Progress 
                            value={suite.totalTests > 0 ? (suite.passedTests / suite.totalTests) * 100 : 0} 
                            className="h-2"
                          />
                        </div>
                      ) : null}

                      <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-600">
                          {suite.status === 'idle' && 'Готов к запуску'}
                          {suite.status === 'running' && 'Выполняется...'}
                          {suite.status === 'passed' && 'Все тесты пройдены'}
                          {suite.status === 'failed' && 'Обнаружены проблемы'}
                          {suite.status === 'stopped' && 'Остановлено пользователем'}
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {suite.status === 'idle' ? (
                            <Button 
                              size="sm" 
                              onClick={() => runTestSuite(suite.id)}
                              disabled={activeTests.includes(suite.id)}
                            >
                              <PlayCircle className="h-3 w-3 mr-1" />
                              Запустить
                            </Button>
                          ) : suite.status === 'running' ? (
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => stopTestSuite(suite.id)}
                            >
                              <StopCircle className="h-3 w-3 mr-1" />
                              Остановить
                            </Button>
                          ) : (
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => runTestSuite(suite.id)}
                            >
                              <RefreshCw className="h-3 w-3 mr-1" />
                              Перезапустить
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>История тестов</CardTitle>
                <CardDescription>
                  Последние запуски и результаты
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  История тестов будет отображаться здесь
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Аналитика</CardTitle>
                <CardDescription>
                  Статистика и тренды
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  Аналитические графики будут отображаться здесь
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default TestingDashboard;