import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import TestingDashboard from './TestingDashboard';
import TestRunnerView from './TestRunnerView';
import TestResultsView from './TestResultsView';
import CoverageReportsView from './CoverageReportsView';
import { 
  Play, 
  Pause, 
  Square, 
  BarChart3, 
  FileText, 
  Settings,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Activity,
  Zap,
  Shield,
  Target,
  Layers,
  Code,
  TestTube
} from 'lucide-react';

interface TestingSummary {
  totalSuites: number;
  activeSuites: number;
  completedToday: number;
  successRate: number;
  avgExecutionTime: number;
  coveragePercentage: number;
  criticalIssues: number;
  lastUpdate: Date;
}

interface TestQueueItem {
  id: string;
  name: string;
  type: 'unit' | 'integration' | 'e2e' | 'performance' | 'mobile';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'queued' | 'running' | 'completed' | 'failed';
  estimatedDuration: number;
  submittedBy: string;
  submittedAt: Date;
  dependencies?: string[];
}

const ComprehensiveTestingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [testingSummary, setTestingSummary] = useState<TestingSummary>({
    totalSuites: 5,
    activeSuites: 2,
    completedToday: 12,
    successRate: 87.5,
    avgExecutionTime: 145,
    coveragePercentage: 78.3,
    criticalIssues: 3,
    lastUpdate: new Date()
  });

  const [testQueue, setTestQueue] = useState<TestQueueItem[]>([
    {
      id: 'queue-1',
      name: 'Модульные тесты - Authentication',
      type: 'unit',
      priority: 'high',
      status: 'queued',
      estimatedDuration: 300,
      submittedBy: 'Алексей',
      submittedAt: new Date(Date.now() - 300000)
    },
    {
      id: 'queue-2',
      name: 'E2E тесты - User Journey',
      type: 'e2e',
      priority: 'medium',
      status: 'running',
      estimatedDuration: 600,
      submittedBy: 'Мария',
      submittedAt: new Date(Date.now() - 600000),
      dependencies: ['queue-1']
    },
    {
      id: 'queue-3',
      name: 'Нагрузочное тестирование',
      type: 'performance',
      priority: 'critical',
      status: 'completed',
      estimatedDuration: 1800,
      submittedBy: 'Дмитрий',
      submittedAt: new Date(Date.now() - 7200000)
    },
    {
      id: 'queue-4',
      name: 'Мобильное тестирование',
      type: 'mobile',
      priority: 'low',
      status: 'failed',
      estimatedDuration: 900,
      submittedBy: 'Елена',
      submittedAt: new Date(Date.now() - 3600000)
    }
  ]);

  const [quickStats, setQuickStats] = useState({
    queuedTests: 0,
    runningTests: 0,
    completedTests: 0,
    failedTests: 0
  });

  useEffect(() => {
    // Обновляем статистику очереди тестов
    const stats = testQueue.reduce((acc, test) => {
      switch (test.status) {
        case 'queued': acc.queuedTests++; break;
        case 'running': acc.runningTests++; break;
        case 'completed': acc.completedTests++; break;
        case 'failed': acc.failedTests++; break;
      }
      return acc;
    }, { queuedTests: 0, runningTests: 0, completedTests: 0, failedTests: 0 });

    setQuickStats(stats);
  }, [testQueue]);

  const executeQuickTest = (type: string) => {
    console.log(`Запуск быстрого ${type} теста`);
    // Логика выполнения быстрого теста
  };

  const cancelQueuedTest = (queueId: string) => {
    setTestQueue(prev => prev.filter(test => test.id !== queueId));
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'running': return 'text-blue-600';
      case 'queued': return 'text-yellow-600';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'running': return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'queued': return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-600" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'unit': return <TestTube className="h-4 w-4" />;
      case 'integration': return <Layers className="h-4 w-4" />;
      case 'e2e': return <Zap className="h-4 w-4" />;
      case 'performance': return <Activity className="h-4 w-4" />;
      case 'mobile': return <Shield className="h-4 w-4" />;
      default: return <Code className="h-4 w-4" />;
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Быстрые действия */}
      <Card>
        <CardHeader>
          <CardTitle>Быстрое тестирование</CardTitle>
          <CardDescription>
            Запуск основных типов тестов с предустановленными параметрами
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Button 
              variant="outline" 
              className="h-20 flex flex-col space-y-2"
              onClick={() => executeQuickTest('unit')}
            >
              <TestTube className="h-6 w-6 text-blue-600" />
              <span>Модульные</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex flex-col space-y-2"
              onClick={() => executeQuickTest('integration')}
            >
              <Layers className="h-6 w-6 text-green-600" />
              <span>Интеграция</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex flex-col space-y-2"
              onClick={() => executeQuickTest('e2e')}
            >
              <Zap className="h-6 w-6 text-purple-600" />
              <span>E2E</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex flex-col space-y-2"
              onClick={() => executeQuickTest('performance')}
            >
              <Activity className="h-6 w-6 text-orange-600" />
              <span>Производ.</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex flex-col space-y-2"
              onClick={() => executeQuickTest('mobile')}
            >
              <Shield className="h-6 w-6 text-pink-600" />
              <span>Мобильные</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Краткая статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Очередь тестов</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{quickStats.queuedTests}</div>
            <p className="text-xs text-muted-foreground">
              Ожидают выполнения
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Выполняются</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{quickStats.runningTests}</div>
            <p className="text-xs text-muted-foreground">
              Активных тестов
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Успешность</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{testingSummary.successRate}%</div>
            <p className="text-xs text-muted-foreground">
              За последние 24ч
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Покрытие кода</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{testingSummary.coveragePercentage}%</div>
            <Progress value={testingSummary.coveragePercentage} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Очередь тестов */}
      <Card>
        <CardHeader>
          <CardTitle>Очередь тестов</CardTitle>
          <CardDescription>
            Управление приоритетами и статусом тестов
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {testQueue.map((test) => (
              <div key={test.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(test.status)}
                  <div>
                    <div className="font-medium flex items-center space-x-2">
                      <span>{test.name}</span>
                      <Badge className={getPriorityColor(test.priority)}>
                        {test.priority.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="text-sm text-gray-500 flex items-center space-x-4">
                      <span>Тип: {test.type}</span>
                      <span>Исполнитель: {test.submittedBy}</span>
                      <span>Время: {Math.floor(test.estimatedDuration / 60)}м</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-medium ${getStatusColor(test.status)}`}>
                    {test.status}
                  </span>
                  {test.status === 'queued' && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => cancelQueuedTest(test.id)}
                    >
                      Отменить
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Интеграция с TestingDashboard */}
      <Card>
        <CardHeader>
          <CardTitle>Панель управления тестированием</CardTitle>
          <CardDescription>
            Детальное управление и мониторинг всех тестовых процессов
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-96 border rounded-lg overflow-hidden">
            <TestingDashboard />
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Заголовок страницы */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Комплексное тестирование
              </h1>
              <p className="text-gray-600 mt-1">
                Центральная платформа для всех видов тестирования
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Badge variant="outline" className="flex items-center space-x-1">
                <Activity className="h-3 w-3" />
                <span>В реальном времени</span>
              </Badge>
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Настройки
              </Button>
            </div>
          </div>
        </div>

        {/* Системные уведомления */}
        {testingSummary.criticalIssues > 0 && (
          <Alert className="mb-6">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Обнаружено {testingSummary.criticalIssues} критических проблем в тестах. 
              Требуется немедленное внимание.
            </AlertDescription>
          </Alert>
        )}

        {/* Основная навигация */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="dashboard" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Панель</span>
            </TabsTrigger>
            <TabsTrigger value="runner" className="flex items-center space-x-2">
              <Play className="h-4 w-4" />
              <span>Исполнитель</span>
            </TabsTrigger>
            <TabsTrigger value="results" className="flex items-center space-x-2">
              <FileText className="h-4 w-4" />
              <span>Результаты</span>
            </TabsTrigger>
            <TabsTrigger value="coverage" className="flex items-center space-x-2">
              <Target className="h-4 w-4" />
              <span>Покрытие</span>
            </TabsTrigger>
            <TabsTrigger value="reports" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Отчеты</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            {renderDashboard()}
          </TabsContent>

          <TabsContent value="runner">
            <Card>
              <CardContent className="p-0">
                <TestRunnerView />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="results">
            <Card>
              <CardContent className="p-0">
                <TestResultsView />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="coverage">
            <Card>
              <CardContent className="p-0">
                <CoverageReportsView />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reports">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Генерация отчетов</CardTitle>
                  <CardDescription>
                    Создание и экспорт детальных отчетов по тестированию
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Еженедельный отчет</CardTitle>
                        <CardDescription>
                          Сводка результатов за неделю
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Button className="w-full">
                          <FileText className="h-4 w-4 mr-2" />
                          Генерировать
                        </Button>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Отчет покрытия</CardTitle>
                        <CardDescription>
                          Детальный анализ покрытия кода
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Button className="w-full">
                          <Target className="h-4 w-4 mr-2" />
                          Генерировать
                        </Button>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Performance отчет</CardTitle>
                        <CardDescription>
                          Анализ производительности тестов
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Button className="w-full">
                          <Activity className="h-4 w-4 mr-2" />
                          Генерировать
                        </Button>
                      </CardContent>
                    </Card>
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

export default ComprehensiveTestingPage;