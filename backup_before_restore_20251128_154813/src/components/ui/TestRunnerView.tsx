import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  FileText, 
  Terminal,
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  RefreshCw,
  Download,
  Upload,
  Copy,
  Minimize2,
  Maximize2
} from 'lucide-react';

interface TestStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped';
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  output?: string;
  error?: string;
  screenshot?: string;
}

interface RunningTest {
  id: string;
  name: string;
  type: 'unit' | 'integration' | 'e2e' | 'performance' | 'mobile';
  status: 'initializing' | 'running' | 'passed' | 'failed' | 'stopped';
  currentStep?: string;
  steps: TestStep[];
  startTime: Date;
  progress: number;
  totalSteps: number;
  completedSteps: number;
  output: string[];
  config: any;
}

const TestRunnerView: React.FC = () => {
  const [runningTests, setRunningTests] = useState<RunningTest[]>([]);
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState<string[]>([
    'Test Runner инициализирован...',
    'Ожидание команд...',
    'Система готова к тестированию'
  ]);

  const consoleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [consoleOutput]);

  const addConsoleMessage = (message: string) => {
    setConsoleOutput(prev => [...prev, `[${new Date().toLocaleTimeString('ru-RU')}] ${message}`]);
  };

  const startTest = (type: string) => {
    const testId = `${type}-${Date.now()}`;
    const test: RunningTest = {
      id: testId,
      name: `${type.charAt(0).toUpperCase() + type.slice(1)} Test Suite`,
      type: type as any,
      status: 'initializing',
      steps: generateTestSteps(type),
      startTime: new Date(),
      progress: 0,
      totalSteps: 0,
      completedSteps: 0,
      output: [],
      config: getTestConfig(type)
    };

    setRunningTests(prev => [...prev, test]);
    setSelectedTest(testId);
    addConsoleMessage(`Запуск ${test.name}`);

    executeTest(test);
  };

  const generateTestSteps = (type: string): TestStep[] => {
    const stepTemplates = {
      unit: [
        { name: 'Инициализация тестового окружения', description: 'Подготовка изоляции и моков' },
        { name: 'Компиляция тестов', description: 'Анализ и подготовка тест-кейсов' },
        { name: 'Выполнение модульных тестов', description: 'Запуск отдельных компонентов' },
        { name: 'Проверка утверждений', description: 'Валидация результатов' },
        { name: 'Генерация отчета покрытия', description: 'Создание метрик покрытия кода' },
        { name: 'Очистка ресурсов', description: 'Удаление временных данных' }
      ],
      integration: [
        { name: 'Настройка внешних зависимостей', description: 'Инициализация API и баз данных' },
        { name: 'Валидация контрактов', description: 'Проверка форматов API' },
        { name: 'Тестирование интеграций', description: 'Взаимодействие между сервисами' },
        { name: 'Проверка транзакций', description: 'Тестирование целостности данных' },
        { name: 'Валидация производительности', description: 'Проверка времени отклика' }
      ],
      e2e: [
        { name: 'Инициализация браузера', description: 'Запуск селенума/плейврайта' },
        { name: 'Навигация по страницам', description: 'Проверка маршрутизации' },
        { name: 'Взаимодействие с UI', description: 'Тестирование пользовательского интерфейса' },
        { name: 'Валидация данных форм', description: 'Проверка валидации ввода' },
        { name: 'Проверка визуального состояния', description: 'Скриншоты и сравнения' },
        { name: 'Очистка сессии браузера', description: 'Закрытие всех вкладок' }
      ],
      performance: [
        { name: 'Калибровка нагрузочного профиля', description: 'Настройка параметров нагрузки' },
        { name: 'Подготовка метрик', description: 'Инициализация систем мониторинга' },
        { name: 'Постепенное увеличение нагрузки', description: 'Ramp-up профиль' },
        { name: 'Измерение производительности', description: 'Сбор метрик отклика' },
        { name: 'Анализ узких мест', description: 'Идентификация проблем' },
        { name: 'Генерация отчета производительности', description: 'Создание итогового отчета' }
      ],
      mobile: [
        { name: 'Инициализация эмулятора устройства', description: 'Запуск мобильного симулятора' },
        { name: 'Настройка сенсорных жестов', description: 'Подготовка обработчиков касаний' },
        { name: 'Тестирование адаптивного дизайна', description: 'Проверка отзывчивости' },
        { name: 'Проверка жестов навигации', description: 'Swipe, pinch, scroll' },
        { name: 'Тестирование ориентации', description: 'Портретный/альбомный режим' },
        { name: 'Валидация мобильной производительности', description: 'Проверка FPS и памяти' }
      ]
    };

    return stepTemplates[type as keyof typeof stepTemplates]?.map((template, index) => ({
      id: `step-${index}`,
      name: template.name,
      description: template.description,
      status: 'pending'
    })) || [];
  };

  const getTestConfig = (type: string) => {
    const configs = {
      unit: { parallel: true, timeout: 30000, coverage: true },
      integration: { timeout: 60000, retries: 2, databases: true },
      e2e: { browser: 'chromium', headless: false, screenshot: true },
      performance: { users: 100, duration: 300, rampUp: 60 },
      mobile: { devices: ['iPhone 14', 'Pixel 7'], orientations: ['portrait', 'landscape'] }
    };
    return configs[type as keyof typeof configs];
  };

  const executeTest = async (test: RunningTest) => {
    const testIndex = runningTests.findIndex(t => t.id === test.id);
    
    // Обновляем статус на 'running'
    setRunningTests(prev => prev.map((t, index) => 
      index === testIndex ? { ...t, status: 'running' as const } : t
    ));

    for (let i = 0; i < test.steps.length; i++) {
      const step = test.steps[i];
      
      // Обновляем текущий шаг
      setRunningTests(prev => prev.map((t, index) => 
        index === testIndex ? { 
          ...t, 
          currentStep: step.name,
          completedSteps: i 
        } : t
      ));

      addConsoleMessage(`Выполняется: ${step.name}`);

      // Симуляция выполнения шага
      await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));

      // Обновляем статус шага
      const stepSuccess = Math.random() > 0.1; // 90% успешность
      const stepResult: TestStep = {
        ...step,
        status: stepSuccess ? 'passed' : 'failed',
        startTime: new Date(),
        endTime: new Date(),
        duration: 2000 + Math.random() * 3000,
        output: stepSuccess ? `Шаг "${step.name}" выполнен успешно` : `Ошибка в "${step.name}"`,
        error: stepSuccess ? undefined : 'Имитированная ошибка для тестирования'
      };

      setRunningTests(prev => prev.map((t, index) => 
        index === testIndex ? { 
          ...t, 
          steps: t.steps.map((s, sIndex) => sIndex === i ? stepResult : s),
          progress: ((i + 1) / t.steps.length) * 100 
        } : t
      ));

      addConsoleMessage(stepSuccess ? `✓ ${step.name}` : `✗ ${step.name}`);

      if (!stepSuccess) {
        setRunningTests(prev => prev.map((t, index) => 
          index === testIndex ? { ...t, status: 'failed' as const } : t
        ));
        addConsoleMessage(`Тест ${test.name} завершен с ошибками`);
        break;
      }
    }

    // Завершение теста
    if (test.steps.every(step => step.status === 'passed')) {
      setRunningTests(prev => prev.map((t, index) => 
        index === testIndex ? { ...t, status: 'passed' as const, progress: 100 } : t
      ));
      addConsoleMessage(`✓ Тест ${test.name} успешно завершен`);
    }
  };

  const stopTest = (testId: string) => {
    setRunningTests(prev => prev.map(t => 
      t.id === testId ? { ...t, status: 'stopped' as const } : t
    ));
    addConsoleMessage(`Тест остановлен пользователем`);
  };

  const stopAllTests = () => {
    runningTests.forEach(test => {
      if (test.status === 'running') {
        stopTest(test.id);
      }
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'running': return 'text-blue-600';
      case 'stopped': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-600" />;
      case 'running': return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'stopped': return <Square className="h-4 w-4 text-yellow-600" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-400" />;
    }
  };

  const copyOutput = () => {
    const output = consoleOutput.join('\n');
    navigator.clipboard.writeText(output);
  };

  const exportLogs = () => {
    const logs = consoleOutput.join('\n');
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test-runner-logs-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const selectedTestData = runningTests.find(t => t.id === selectedTest);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Исполнитель тестов</h2>
            <p className="text-sm text-gray-600">Пошаговое выполнение и мониторинг</p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsMinimized(!isMinimized)}
            >
              {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={copyOutput}
            >
              <Copy className="h-4 w-4 mr-1" />
              Копировать
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={exportLogs}
            >
              <Download className="h-4 w-4 mr-1" />
              Экспорт
            </Button>
          </div>
        </div>
      </div>

      {!isMinimized && (
        <div className="flex-1 flex overflow-hidden">
          {/* Левая панель - список тестов */}
          <div className="w-1/3 bg-white border-r flex flex-col">
            <div className="p-4 border-b">
              <h3 className="font-medium mb-3">Быстрый запуск</h3>
              <div className="grid grid-cols-2 gap-2">
                <Button size="sm" onClick={() => startTest('unit')}>
                  Модульные
                </Button>
                <Button size="sm" onClick={() => startTest('integration')}>
                  Интеграция
                </Button>
                <Button size="sm" onClick={() => startTest('e2e')}>
                  E2E
                </Button>
                <Button size="sm" onClick={() => startTest('performance')}>
                  Производительность
                </Button>
                <Button size="sm" onClick={() => startTest('mobile')} className="col-span-2">
                  Мобильные
                </Button>
              </div>
              
              {runningTests.some(t => t.status === 'running') && (
                <Button 
                  variant="destructive" 
                  size="sm" 
                  className="w-full mt-3"
                  onClick={stopAllTests}
                >
                  <Square className="h-4 w-4 mr-1" />
                  Остановить все
                </Button>
              )}
            </div>

            <div className="flex-1 overflow-auto p-4">
              <h3 className="font-medium mb-3">Активные тесты</h3>
              <div className="space-y-3">
                {runningTests.map((test) => (
                  <Card 
                    key={test.id} 
                    className={`cursor-pointer transition-colors ${
                      selectedTest === test.id ? 'ring-2 ring-blue-500' : ''
                    }`}
                    onClick={() => setSelectedTest(test.id)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-sm">{test.name}</h4>
                        {getStatusIcon(test.status)}
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          <span>Прогресс</span>
                          <span>{Math.round(test.progress)}%</span>
                        </div>
                        <Progress value={test.progress} className="h-2" />
                        
                        {test.currentStep && (
                          <p className="text-xs text-blue-600 truncate">
                            {test.currentStep}
                          </p>
                        )}
                        
                        <div className="flex items-center justify-between">
                          <Badge variant="outline" className="text-xs">
                            {test.type}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {test.completedSteps}/{test.steps.length}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {runningTests.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    Нет активных тестов
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Правая панель - детали теста */}
          <div className="flex-1 flex flex-col">
            {selectedTestData ? (
              <Tabs defaultValue="steps" className="flex-1 flex flex-col">
                <div className="border-b bg-white p-4">
                  <TabsList>
                    <TabsTrigger value="steps">Шаги выполнения</TabsTrigger>
                    <TabsTrigger value="config">Конфигурация</TabsTrigger>
                    <TabsTrigger value="logs">Логи</TabsTrigger>
                  </TabsList>
                </div>

                <TabsContent value="steps" className="flex-1 p-4 overflow-auto">
                  <div className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">{selectedTestData.name}</CardTitle>
                        <CardDescription>
                          {selectedTestData.steps.length} шагов • Начат: {selectedTestData.startTime.toLocaleTimeString('ru-RU')}
                        </CardDescription>
                      </CardHeader>
                    </Card>

                    <div className="space-y-3">
                      {selectedTestData.steps.map((step, index) => (
                        <Card key={step.id} className="relative">
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-3 mb-2">
                                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-xs font-medium">
                                    {index + 1}
                                  </span>
                                  <h4 className="font-medium">{step.name}</h4>
                                  {getStatusIcon(step.status)}
                                </div>
                                
                                <p className="text-sm text-gray-600 mb-2">{step.description}</p>
                                
                                {step.output && (
                                  <div className="bg-gray-50 p-2 rounded text-sm">
                                    <strong>Вывод:</strong> {step.output}
                                  </div>
                                )}
                                
                                {step.error && (
                                  <div className="bg-red-50 p-2 rounded text-sm text-red-600">
                                    <strong>Ошибка:</strong> {step.error}
                                  </div>
                                )}
                              </div>
                              
                              <div className="text-right text-sm text-gray-500">
                                {step.duration && (
                                  <div>{(step.duration / 1000).toFixed(1)}с</div>
                                )}
                                {step.startTime && (
                                  <div>{step.startTime.toLocaleTimeString('ru-RU')}</div>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="config" className="flex-1 p-4 overflow-auto">
                  <Card>
                    <CardHeader>
                      <CardTitle>Конфигурация теста</CardTitle>
                      <CardDescription>
                        Параметры выполнения для {selectedTestData.type} тестов
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {Object.entries(selectedTestData.config).map(([key, value]) => (
                        <div key={key} className="grid grid-cols-2 gap-4">
                          <Label>{key}</Label>
                          <Input value={String(value)} readOnly />
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="logs" className="flex-1 flex flex-col">
                  <Card className="flex-1 flex flex-col">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle>Логи выполнения</CardTitle>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={copyOutput}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="flex-1 p-0">
                      <div 
                        ref={consoleRef}
                        className="h-96 overflow-auto bg-black text-green-400 p-4 font-mono text-sm"
                      >
                        {consoleOutput.map((message, index) => (
                          <div key={index} className="mb-1">
                            {message}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            ) : (
              <div className="flex-1 flex items-center justify-center bg-gray-50">
                <div className="text-center text-gray-500">
                  <Terminal className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Выберите тест для просмотра деталей</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TestRunnerView;