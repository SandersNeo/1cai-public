import React, { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  Filter,
  Search,
  Download,
  FileText,
  BarChart3,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Calendar,
  User,
  Tag,
  ChevronRight
} from 'lucide-react';

interface TestResult {
  id: string;
  testSuite: string;
  testType: 'unit' | 'integration' | 'e2e' | 'performance' | 'mobile';
  status: 'passed' | 'failed' | 'skipped';
  totalTests: number;
  passedTests: number;
  failedTests: number;
  skippedTests: number;
  duration: number;
  startTime: Date;
  endTime: Date;
  environment: string;
  branch: string;
  commitHash: string;
  executedBy: string;
  coverage?: {
    statement: number;
    branch: number;
    function: number;
    line: number;
  };
  errors: Array<{
    testName: string;
    message: string;
    stackTrace: string;
    screenshot?: string;
  }>;
  metrics?: {
    performance?: any;
    memory?: any;
    cpu?: any;
  };
  artifacts: Array<{
    type: 'screenshot' | 'video' | 'log' | 'report';
    name: string;
    url: string;
    size: number;
  }>;
}

const TestResultsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedResult, setSelectedResult] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<string>('7days');

  // Генерируем тестовые данные результатов
  const testResults: TestResult[] = useMemo(() => {
    const suites = [
      { name: 'Authentication Service', type: 'unit' as const },
      { name: 'Database Integration', type: 'integration' as const },
      { name: 'User Journey Flow', type: 'e2e' as const },
      { name: 'Load Testing Suite', type: 'performance' as const },
      { name: 'Mobile App Testing', type: 'mobile' as const },
      { name: 'Payment Gateway', type: 'unit' as const },
      { name: 'API Contract Tests', type: 'integration' as const },
      { name: 'Checkout Process', type: 'e2e' as const },
      { name: 'Stress Testing', type: 'performance' as const },
      { name: 'Device Compatibility', type: 'mobile' as const }
    ];

    return suites.map((suite, index) => {
      const totalTests = Math.floor(Math.random() * 100) + 20;
      const passedTests = Math.floor(totalTests * (0.85 + Math.random() * 0.1));
      const failedTests = Math.floor(totalTests * 0.05);
      const skippedTests = totalTests - passedTests - failedTests;
      
      const startTime = new Date(Date.now() - (index * 86400000) - Math.random() * 86400000);
      const duration = Math.floor(Math.random() * 600) + 60; // 1-11 минут

      return {
        id: `result-${index}`,
        testSuite: suite.name,
        testType: suite.type,
        status: failedTests > 0 ? 'failed' : 'passed',
        totalTests,
        passedTests,
        failedTests,
        skippedTests,
        duration,
        startTime,
        endTime: new Date(startTime.getTime() + duration * 1000),
        environment: ['dev', 'staging', 'prod'][Math.floor(Math.random() * 3)],
        branch: ['main', 'feature/auth', 'hotfix/db'][Math.floor(Math.random() * 3)],
        commitHash: Math.random().toString(36).substring(2, 9),
        executedBy: ['Алексей', 'Мария', 'Дмитрий', 'Елена'][Math.floor(Math.random() * 4)],
        coverage: {
          statement: Math.floor(Math.random() * 30) + 70,
          branch: Math.floor(Math.random() * 25) + 60,
          function: Math.floor(Math.random() * 20) + 75,
          line: Math.floor(Math.random() * 25) + 65
        },
        errors: failedTests > 0 ? [
          {
            testName: 'testInvalidCredentials',
            message: 'Expected "valid token" but received "invalid token"',
            stackTrace: `Error: Test assertion failed
    at Object.test (auth.test.js:45:15)
    at processTicksAndRejections (node:internal/process/task_queues:95:5)`,
            screenshot: './screenshots/auth-error.png'
          }
        ] : [],
        metrics: {
          performance: {
            avgResponseTime: Math.floor(Math.random() * 500) + 100,
            p95ResponseTime: Math.floor(Math.random() * 800) + 200
          },
          memory: {
            avgUsage: Math.floor(Math.random() * 50) + 30,
            peakUsage: Math.floor(Math.random() * 70) + 40
          }
        },
        artifacts: [
          {
            type: 'report',
            name: 'coverage-report.html',
            url: './reports/coverage-report.html',
            size: 245760
          },
          {
            type: 'screenshot',
            name: 'failure-screenshot.png',
            url: './screenshots/failure.png',
            size: 102400
          },
          {
            type: 'log',
            name: 'test-output.log',
            url: './logs/test-output.log',
            size: 51200
          }
        ]
      };
    });
  }, []);

  // Фильтрация результатов
  const filteredResults = useMemo(() => {
    return testResults.filter(result => {
      const matchesType = filterType === 'all' || result.testType === filterType;
      const matchesStatus = filterStatus === 'all' || result.status === filterStatus;
      const matchesSearch = result.testSuite.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           result.executedBy.toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesType && matchesStatus && matchesSearch;
    });
  }, [testResults, filterType, filterStatus, searchTerm]);

  // Статистика
  const stats = useMemo(() => {
    const total = filteredResults.length;
    const passed = filteredResults.filter(r => r.status === 'passed').length;
    const failed = filteredResults.filter(r => r.status === 'failed').length;
    const avgDuration = filteredResults.reduce((sum, r) => sum + r.duration, 0) / total || 0;
    const avgCoverage = filteredResults.reduce((sum, r) => 
      sum + (r.coverage?.statement || 0), 0) / total || 0;

    return {
      total,
      passed,
      failed,
      passRate: total > 0 ? (passed / total) * 100 : 0,
      avgDuration,
      avgCoverage
    };
  }, [filteredResults]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'skipped': return <Clock className="h-4 w-4 text-yellow-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'unit': return 'bg-blue-100 text-blue-800';
      case 'integration': return 'bg-green-100 text-green-800';
      case 'e2e': return 'bg-purple-100 text-purple-800';
      case 'performance': return 'bg-orange-100 text-orange-800';
      case 'mobile': return 'bg-pink-100 text-pink-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return minutes > 0 ? `${minutes}м ${remainingSeconds}с` : `${remainingSeconds}с`;
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const exportResults = (format: 'csv' | 'json' | 'pdf') => {
    console.log(`Экспорт результатов в формате ${format}`);
    // Здесь будет логика экспорта
  };

  const selectedResultData = testResults.find(r => r.id === selectedResult);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Результаты тестирования</h1>
              <p className="text-gray-600 mt-1">Детальный анализ выполненных тестов</p>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm" onClick={() => exportResults('csv')}>
                <Download className="h-4 w-4 mr-2" />
                CSV
              </Button>
              <Button variant="outline" size="sm" onClick={() => exportResults('pdf')}>
                <FileText className="h-4 w-4 mr-2" />
                PDF
              </Button>
            </div>
          </div>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Всего тестов</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground">
                {filteredResults.length} из {testResults.length}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Пройдено</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.passed}</div>
              <p className="text-xs text-muted-foreground">
                {stats.passRate.toFixed(1)}% успешности
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Ошибки</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
              <p className="text-xs text-muted-foreground">
                Требуют внимания
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Время выполнения</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatDuration(stats.avgDuration)}</div>
              <p className="text-xs text-muted-foreground">
                Среднее время
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Покрытие кода</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.avgCoverage.toFixed(1)}%</div>
              <Progress value={stats.avgCoverage} className="mt-2" />
            </CardContent>
          </Card>
        </div>

        {/* Фильтры */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Search className="h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Поиск по названию или исполнителю..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-64"
                />
              </div>

              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Тип теста" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все типы</SelectItem>
                  <SelectItem value="unit">Модульные</SelectItem>
                  <SelectItem value="integration">Интеграционные</SelectItem>
                  <SelectItem value="e2e">E2E</SelectItem>
                  <SelectItem value="performance">Производительность</SelectItem>
                  <SelectItem value="mobile">Мобильные</SelectItem>
                </SelectContent>
              </Select>

              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Статус" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все статусы</SelectItem>
                  <SelectItem value="passed">Пройдено</SelectItem>
                  <SelectItem value="failed">Ошибки</SelectItem>
                  <SelectItem value="skipped">Пропущено</SelectItem>
                </SelectContent>
              </Select>

              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Период" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1day">1 день</SelectItem>
                  <SelectItem value="7days">7 дней</SelectItem>
                  <SelectItem value="30days">30 дней</SelectItem>
                  <SelectItem value="90days">90 дней</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Основное содержимое */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Таблица результатов */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>История выполнения</CardTitle>
                <CardDescription>
                  Последние результаты тестирования ({filteredResults.length} из {testResults.length})
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Набор тестов</TableHead>
                      <TableHead>Тип</TableHead>
                      <TableHead>Статус</TableHead>
                      <TableHead>Результат</TableHead>
                      <TableHead>Время</TableHead>
                      <TableHead>Исполнитель</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredResults.map((result) => (
                      <TableRow 
                        key={result.id}
                        className={`cursor-pointer hover:bg-gray-50 ${selectedResult === result.id ? 'bg-blue-50' : ''}`}
                        onClick={() => setSelectedResult(result.id)}
                      >
                        <TableCell className="font-medium">
                          <div>
                            <div className="font-medium">{result.testSuite}</div>
                            <div className="text-sm text-gray-500">
                              {result.environment} • {result.branch}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getTypeColor(result.testType)}>
                            {result.testType.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(result.status)}
                            <span className="capitalize">{result.status}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div className="flex items-center space-x-2">
                              <span className="text-green-600">{result.passedTests}</span>
                              <span className="text-gray-400">/</span>
                              <span className="text-red-600">{result.failedTests}</span>
                              <span className="text-gray-400">/</span>
                              <span className="text-gray-600">{result.totalTests}</span>
                            </div>
                            <Progress 
                              value={result.totalTests > 0 ? (result.passedTests / result.totalTests) * 100 : 0} 
                              className="mt-1 h-1"
                            />
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div>{formatDuration(result.duration)}</div>
                            <div className="text-gray-500">
                              {result.startTime.toLocaleDateString('ru-RU')}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <User className="h-3 w-3 text-gray-400" />
                            <span className="text-sm">{result.executedBy}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <ChevronRight className="h-4 w-4 text-gray-400" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>

          {/* Панель деталей */}
          <div className="lg:col-span-1">
            {selectedResultData ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Детали результата</CardTitle>
                  <CardDescription>
                    {selectedResultData.testSuite}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Tabs defaultValue="overview" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="overview">Обзор</TabsTrigger>
                      <TabsTrigger value="errors">Ошибки</TabsTrigger>
                      <TabsTrigger value="artifacts">Файлы</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4">
                      <div>
                        <h4 className="font-medium mb-2">Информация о запуске</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Статус:</span>
                            <div className="flex items-center space-x-1">
                              {getStatusIcon(selectedResultData.status)}
                              <span>{selectedResultData.status}</span>
                            </div>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Время:</span>
                            <span>{formatDuration(selectedResultData.duration)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Окружение:</span>
                            <span>{selectedResultData.environment}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Ветка:</span>
                            <span>{selectedResultData.branch}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Коммит:</span>
                            <span className="font-mono text-xs">{selectedResultData.commitHash}</span>
                          </div>
                        </div>
                      </div>

                      {selectedResultData.coverage && (
                        <div>
                          <h4 className="font-medium mb-2">Покрытие кода</h4>
                          <div className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm">Операторы</span>
                              <div className="flex items-center space-x-2">
                                <Progress value={selectedResultData.coverage.statement} className="w-16 h-2" />
                                <span className="text-sm font-medium">{selectedResultData.coverage.statement}%</span>
                              </div>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm">Ветки</span>
                              <div className="flex items-center space-x-2">
                                <Progress value={selectedResultData.coverage.branch} className="w-16 h-2" />
                                <span className="text-sm font-medium">{selectedResultData.coverage.branch}%</span>
                              </div>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm">Функции</span>
                              <div className="flex items-center space-x-2">
                                <Progress value={selectedResultData.coverage.function} className="w-16 h-2" />
                                <span className="text-sm font-medium">{selectedResultData.coverage.function}%</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {selectedResultData.metrics?.performance && (
                        <div>
                          <h4 className="font-medium mb-2">Производительность</h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Среднее время отклика:</span>
                              <span>{selectedResultData.metrics.performance.avgResponseTime}мс</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">P95 время:</span>
                              <span>{selectedResultData.metrics.performance.p95ResponseTime}мс</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="errors" className="space-y-4">
                      {selectedResultData.errors.length > 0 ? (
                        <div className="space-y-3">
                          {selectedResultData.errors.map((error, index) => (
                            <Card key={index}>
                              <CardContent className="p-3">
                                <div className="space-y-2">
                                  <div className="flex items-center space-x-2">
                                    <XCircle className="h-4 w-4 text-red-500" />
                                    <span className="font-medium text-sm">{error.testName}</span>
                                  </div>
                                  <p className="text-sm text-red-600">{error.message}</p>
                                  <details className="text-xs">
                                    <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                                      Stack trace
                                    </summary>
                                    <pre className="mt-2 p-2 bg-gray-100 rounded overflow-auto">
                                      {error.stackTrace}
                                    </pre>
                                  </details>
                                  {error.screenshot && (
                                    <div className="text-xs">
                                      <strong>Скриншот:</strong> {error.screenshot}
                                    </div>
                                  )}
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center text-gray-500 py-8">
                          <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                          <p>Ошибок не найдено</p>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="artifacts" className="space-y-4">
                      <div className="space-y-3">
                        {selectedResultData.artifacts.map((artifact, index) => (
                          <Card key={index}>
                            <CardContent className="p-3">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                  {artifact.type === 'screenshot' && <FileText className="h-4 w-4 text-blue-500" />}
                                  {artifact.type === 'video' && <RefreshCw className="h-4 w-4 text-purple-500" />}
                                  {artifact.type === 'log' && <AlertTriangle className="h-4 w-4 text-orange-500" />}
                                  {artifact.type === 'report' && <BarChart3 className="h-4 w-4 text-green-500" />}
                                  <div>
                                    <div className="font-medium text-sm">{artifact.name}</div>
                                    <div className="text-xs text-gray-500">{formatFileSize(artifact.size)}</div>
                                  </div>
                                </div>
                                <Button variant="outline" size="sm">
                                  <Download className="h-3 w-3" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="flex items-center justify-center h-64">
                  <div className="text-center text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Выберите результат для просмотра деталей</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestResultsView;