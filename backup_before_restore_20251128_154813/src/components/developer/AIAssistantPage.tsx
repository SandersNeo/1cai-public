/**
 * AI Assistant Page Component
 * Интеграционная страница для AI помощника
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Brain,
  MessageCircle,
  Lightbulb,
  Database,
  Settings,
  Activity,
  CheckCircle,
  AlertTriangle,
  Zap,
  TrendingUp,
  Clock,
  Users,
  Code,
  FileText,
  BarChart3,
  Shield,
  Globe,
  Cpu,
  RefreshCw,
  Play,
  Pause,
  Square,
  Info
} from 'lucide-react';

// Импортируем компоненты
import AIAssistantView from './AIAssistantView';
import SuggestionPanel from './SuggestionPanel';
import ContextViewer from './ContextViewer';

// Типы для состояния AI Assistant
interface AIAssistantState {
  isInitialized: boolean;
  isRunning: boolean;
  configuration: {
    openai: {
      apiKey: string;
      baseURL: string;
      model: string;
      maxTokens: number;
      temperature: number;
      configured: boolean;
    };
    suggestions: {
      enabled: boolean;
      maxSuggestions: number;
      autoSuggest: boolean;
    };
    context: {
      maxHistoryLength: number;
      autoCleanup: boolean;
      retentionDays: number;
    };
    features: {
      streaming: boolean;
      embeddings: boolean;
      moderation: boolean;
    };
  };
  health: {
    service: 'healthy' | 'degraded' | 'unhealthy';
    openai: 'available' | 'unavailable' | 'error';
    contextManager: 'healthy' | 'unhealthy';
    suggestionEngine: 'healthy' | 'unhealthy';
    uptime: number;
  };
  stats: {
    sessions: {
      total: number;
      active: number;
      closed: number;
    };
    commands: {
      total: number;
      byCategory: Record<string, number>;
    };
    openai: {
      configured: boolean;
      healthy: boolean;
    };
    features: {
      suggestions: boolean;
      streaming: boolean;
      embeddings: boolean;
    };
  };
}

const AIAssistantPage: React.FC = () => {
  // Состояние
  const [state, setState] = useState<AIAssistantState>({
    isInitialized: false,
    isRunning: false,
    configuration: {
      openai: {
        apiKey: '',
        baseURL: 'https://api.openai.com/v1',
        model: 'gpt-3.5-turbo',
        maxTokens: 2000,
        temperature: 0.7,
        configured: false
      },
      suggestions: {
        enabled: true,
        maxSuggestions: 10,
        autoSuggest: true
      },
      context: {
        maxHistoryLength: 100,
        autoCleanup: true,
        retentionDays: 30
      },
      features: {
        streaming: false,
        embeddings: false,
        moderation: false
      }
    },
    health: {
      service: 'unhealthy',
      openai: 'unavailable',
      contextManager: 'unhealthy',
      suggestionEngine: 'unhealthy',
      uptime: 0
    },
    stats: {
      sessions: {
        total: 0,
        active: 0,
        closed: 0
      },
      commands: {
        total: 0,
        byCategory: {}
      },
      openai: {
        configured: false,
        healthy: false
      },
      features: {
        suggestions: true,
        streaming: false,
        embeddings: false
      }
    }
  });

  const [activeTab, setActiveTab] = useState('overview');
  const [showConfiguration, setShowConfiguration] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Загрузка при монтировании
  useEffect(() => {
    initializeAIAssistant();
    loadConfiguration();
  }, []);

  /**
   * Инициализация AI Assistant
   */
  const initializeAIAssistant = async () => {
    setIsLoading(true);
    try {
      // Имитация инициализации AI Assistant
      await new Promise(resolve => setTimeout(resolve, 1500));

      setState(prev => ({
        ...prev,
        isInitialized: true,
        isRunning: true,
        health: {
          service: 'healthy',
          openai: 'available',
          contextManager: 'healthy',
          suggestionEngine: 'healthy',
          uptime: 300000
        },
        stats: {
          sessions: {
            total: 3,
            active: 2,
            closed: 1
          },
          commands: {
            total: 15,
            byCategory: {
              system: 4,
              analysis: 5,
              generation: 4,
              navigation: 2
            }
          },
          openai: {
            configured: true,
            healthy: true
          },
          features: {
            suggestions: true,
            streaming: false,
            embeddings: false
          }
        }
      }));

      console.log('AI Assistant успешно инициализирован');

    } catch (error) {
      console.error('Ошибка инициализации AI Assistant:', error);
      
      setState(prev => ({
        ...prev,
        isInitialized: false,
        isRunning: false,
        health: {
          ...prev.health,
          service: 'unhealthy'
        }
      }));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Загрузка конфигурации
   */
  const loadConfiguration = async () => {
    // Имитация загрузки конфигурации
    const savedConfig = localStorage.getItem('ai-assistant-config');
    if (savedConfig) {
      try {
        const config = JSON.parse(savedConfig);
        setState(prev => ({
          ...prev,
          configuration: { ...prev.configuration, ...config }
        }));
      } catch (error) {
        console.warn('Ошибка загрузки конфигурации:', error);
      }
    }
  };

  /**
   * Сохранение конфигурации
   */
  const saveConfiguration = (newConfig: Partial<AIAssistantState['configuration']>) => {
    const updatedConfig = { ...state.configuration, ...newConfig };
    setState(prev => ({
      ...prev,
      configuration: updatedConfig
    }));

    // Сохраняем в localStorage
    localStorage.setItem('ai-assistant-config', JSON.stringify(updatedConfig));
  };

  /**
   * Управление состоянием AI Assistant
   */
  const toggleRunning = async () => {
    if (state.isRunning) {
      // Остановка
      setState(prev => ({
        ...prev,
        isRunning: false,
        health: { ...prev.health, service: 'degraded' }
      }));
    } else {
      // Запуск
      await initializeAIAssistant();
    }
  };

  /**
   * Получение цвета статуса
   */
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'available':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'unhealthy':
      case 'unavailable':
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  /**
   * Получение иконки статуса
   */
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'available':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'unhealthy':
      case 'unavailable':
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Info className="h-4 w-4 text-gray-600" />;
    }
  };

  /**
   * Форматирование времени работы
   */
  const formatUptime = (uptime: number) => {
    const hours = Math.floor(uptime / (1000 * 60 * 60));
    const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}ч ${minutes}м`;
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Brain className="h-8 w-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">AI Assistant Integration</h1>
              <p className="text-gray-600">Интегрированный AI помощник для 1C разработки</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Индикатор состояния */}
            <div className="flex items-center gap-2">
              {getStatusIcon(state.health.service)}
              <Badge variant={state.isRunning ? 'default' : 'secondary'}>
                {state.isRunning ? 'Активен' : 'Неактивен'}
              </Badge>
            </div>

            {/* Кнопка управления */}
            <Button
              onClick={toggleRunning}
              disabled={isLoading}
              variant={state.isRunning ? 'outline' : 'default'}
            >
              {isLoading ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : state.isRunning ? (
                <Pause className="h-4 w-4 mr-2" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              {state.isRunning ? 'Остановить' : 'Запустить'}
            </Button>

            <Button
              variant="outline"
              onClick={() => setShowConfiguration(!showConfiguration)}
            >
              <Settings className="h-4 w-4 mr-2" />
              Настройки
            </Button>
          </div>
        </div>

        {/* Быстрая статистика */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-blue-600" />
            <div>
              <div className="text-sm font-medium">{state.stats.sessions.active}</div>
              <div className="text-xs text-gray-600">Активных сессий</div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-green-600" />
            <div>
              <div className="text-sm font-medium">{state.stats.openai.healthy ? 'OK' : 'Ошибка'}</div>
              <div className="text-xs text-gray-600">OpenAI API</div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-yellow-600" />
            <div>
              <div className="text-sm font-medium">{state.stats.features.suggestions ? 'ON' : 'OFF'}</div>
              <div className="text-xs text-gray-600">Подсказки</div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-purple-600" />
            <div>
              <div className="text-sm font-medium">{formatUptime(state.health.uptime)}</div>
              <div className="text-xs text-gray-600">Время работы</div>
            </div>
          </div>
        </div>

        {/* Предупреждения */}
        {!state.isInitialized && (
          <Alert className="mt-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              AI Assistant не инициализирован. Настройте конфигурацию и запустите сервис.
            </AlertDescription>
          </Alert>
        )}

        {state.isRunning && state.health.openai === 'error' && (
          <Alert className="mt-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Ошибка подключения к OpenAI API. Проверьте настройки.
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* Основной контент */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="bg-white border-b px-6">
            <TabsList>
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Обзор
              </TabsTrigger>
              <TabsTrigger value="chat" className="flex items-center gap-2">
                <MessageCircle className="h-4 w-4" />
                Чат
              </TabsTrigger>
              <TabsTrigger value="suggestions" className="flex items-center gap-2">
                <Lightbulb className="h-4 w-4" />
                Подсказки
              </TabsTrigger>
              <TabsTrigger value="context" className="flex items-center gap-2">
                <Database className="h-4 w-4" />
                Контекст
              </TabsTrigger>
              <TabsTrigger value="system" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Система
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-hidden">
            {/* Обзор */}
            <TabsContent value="overview" className="h-full m-0 p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 h-full overflow-y-auto">
                {/* Статус системы */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="h-5 w-5" />
                      Статус системы
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">AI Assistant</span>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(state.health.service)}
                          <span className={`text-sm ${getStatusColor(state.health.service)}`}>
                            {state.health.service}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Context Manager</span>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(state.health.contextManager)}
                          <span className={`text-sm ${getStatusColor(state.health.contextManager)}`}>
                            {state.health.contextManager}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Suggestion Engine</span>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(state.health.suggestionEngine)}
                          <span className={`text-sm ${getStatusColor(state.health.suggestionEngine)}`}>
                            {state.health.suggestionEngine}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">OpenAI API</span>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(state.health.openai)}
                          <span className={`text-sm ${getStatusColor(state.health.openai)}`}>
                            {state.health.openai}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="pt-3 border-t">
                      <div className="flex items-center justify-between text-sm">
                        <span>Время работы</span>
                        <span>{formatUptime(state.health.uptime)}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Статистика использования */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Использование
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Всего сессий</span>
                        <Badge variant="outline">{state.stats.sessions.total}</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Активных</span>
                        <Badge className="bg-green-100 text-green-800">
                          {state.stats.sessions.active}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Завершенных</span>
                        <Badge variant="secondary">{state.stats.sessions.closed}</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Доступных команд</span>
                        <Badge variant="outline">{state.stats.commands.total}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Функции */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-5 w-5" />
                      Возможности
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">AI Подсказки</span>
                      <div className="flex items-center gap-2">
                        {state.stats.features.suggestions ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <Square className="h-4 w-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Streaming ответы</span>
                      <div className="flex items-center gap-2">
                        {state.stats.features.streaming ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <Square className="h-4 w-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Embeddings</span>
                      <div className="flex items-center gap-2">
                        {state.stats.features.embeddings ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <Square className="h-4 w-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm">OpenAI интеграция</span>
                      <div className="flex items-center gap-2">
                        {state.stats.openai.configured ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Компоненты */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Cpu className="h-5 w-5" />
                      Компоненты
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Code className="h-4 w-4 text-blue-600" />
                        <span className="text-sm">Context Manager</span>
                      </div>
                      <Badge variant="outline">463 строки</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Lightbulb className="h-4 w-4 text-yellow-600" />
                        <span className="text-sm">Suggestion Engine</span>
                      </div>
                      <Badge variant="outline">626 строк</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Globe className="h-4 w-4 text-green-600" />
                        <span className="text-sm">OpenAI Integration</span>
                      </div>
                      <Badge variant="outline">588 строк</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4 text-purple-600" />
                        <span className="text-sm">AI Assistant Service</span>
                      </div>
                      <Badge variant="outline">670 строк</Badge>
                    </div>
                  </CardContent>
                </Card>

                {/* Архитектура */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Архитектура
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <span>Context Manager - Управление контекстом</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-yellow-600 rounded-full"></div>
                        <span>Suggestion Engine - Генерация подсказок</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <span>OpenAI Integration - API клиент</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <span>AI Assistant - Основной сервис</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Быстрые действия */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-5 w-5" />
                      Быстрые действия
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('chat')}
                    >
                      <MessageCircle className="h-4 w-4 mr-2" />
                      Начать чат
                    </Button>
                    
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('suggestions')}
                    >
                      <Lightbulb className="h-4 w-4 mr-2" />
                      Посмотреть подсказки
                    </Button>
                    
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('system')}
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Настройки
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Чат */}
            <TabsContent value="chat" className="h-full m-0">
              <AIAssistantView />
            </TabsContent>

            {/* Подсказки */}
            <TabsContent value="suggestions" className="h-full m-0">
              <SuggestionPanel />
            </TabsContent>

            {/* Контекст */}
            <TabsContent value="context" className="h-full m-0">
              <ContextViewer />
            </TabsContent>

            {/* Система */}
            <TabsContent value="system" className="h-full m-0 p-6">
              <div className="space-y-6">
                <h2 className="text-xl font-semibold">Настройки системы</h2>
                
                {/* Конфигурация OpenAI */}
                <Card>
                  <CardHeader>
                    <CardTitle>OpenAI API</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium">API Key</label>
                        <input 
                          type="password"
                          className="w-full mt-1 p-2 border rounded"
                          placeholder="sk-..."
                          value={state.configuration.openai.apiKey}
                          onChange={(e) => saveConfiguration({
                            openai: { ...state.configuration.openai, apiKey: e.target.value }
                          })}
                        />
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium">Base URL</label>
                        <input 
                          className="w-full mt-1 p-2 border rounded"
                          value={state.configuration.openai.baseURL}
                          onChange={(e) => saveConfiguration({
                            openai: { ...state.configuration.openai, baseURL: e.target.value }
                          })}
                        />
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium">Model</label>
                        <Select 
                          value={state.configuration.openai.model}
                          onValueChange={(value) => saveConfiguration({
                            openai: { ...state.configuration.openai, model: value }
                          })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                            <SelectItem value="gpt-4">GPT-4</SelectItem>
                            <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium">Max Tokens</label>
                        <input 
                          type="number"
                          className="w-full mt-1 p-2 border rounded"
                          value={state.configuration.openai.maxTokens}
                          onChange={(e) => saveConfiguration({
                            openai: { ...state.configuration.openai, maxTokens: parseInt(e.target.value) }
                          })}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Настройки подсказок */}
                <Card>
                  <CardHeader>
                    <CardTitle>Система подсказок</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Включить подсказки</label>
                      <input 
                        type="checkbox"
                        checked={state.configuration.suggestions.enabled}
                        onChange={(e) => saveConfiguration({
                          suggestions: { ...state.configuration.suggestions, enabled: e.target.checked }
                        })}
                      />
                    </div>
                    
                    <div>
                      <label className="text-sm font-medium">Максимум подсказок</label>
                      <input 
                        type="number"
                        className="w-full mt-1 p-2 border rounded"
                        value={state.configuration.suggestions.maxSuggestions}
                        onChange={(e) => saveConfiguration({
                          suggestions: { ...state.configuration.suggestions, maxSuggestions: parseInt(e.target.value) }
                        })}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Автоматические подсказки</label>
                      <input 
                        type="checkbox"
                        checked={state.configuration.suggestions.autoSuggest}
                        onChange={(e) => saveConfiguration({
                          suggestions: { ...state.configuration.suggestions, autoSuggest: e.target.checked }
                        })}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Дополнительные функции */}
                <Card>
                  <CardHeader>
                    <CardTitle>Дополнительные функции</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Streaming ответы</label>
                      <input 
                        type="checkbox"
                        checked={state.configuration.features.streaming}
                        onChange={(e) => saveConfiguration({
                          features: { ...state.configuration.features, streaming: e.target.checked }
                        })}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Embeddings поиск</label>
                      <input 
                        type="checkbox"
                        checked={state.configuration.features.embeddings}
                        onChange={(e) => saveConfiguration({
                          features: { ...state.configuration.features, embeddings: e.target.checked }
                        })}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">Модерация контента</label>
                      <input 
                        type="checkbox"
                        checked={state.configuration.features.moderation}
                        onChange={(e) => saveConfiguration({
                          features: { ...state.configuration.features, moderation: e.target.checked }
                        })}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
};

export default AIAssistantPage;