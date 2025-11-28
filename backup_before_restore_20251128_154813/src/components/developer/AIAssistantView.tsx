/**
 * AI Assistant View Component
 * Основной интерфейс AI помощника
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  MessageCircle,
  Send,
  Settings,
  Brain,
  Lightbulb,
  BarChart3,
  Clock,
  User,
  Bot,
  Zap,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Trash2,
  Download,
  Upload
} from 'lucide-react';

// Импортируем сервисы (заглушки для TypeScript)
interface AIService {
  createChatSession: (userId: string, agentType: string, preferences?: any) => Promise<string>;
  sendMessage: (sessionId: string, message: string, options?: any) => Promise<any>;
  getChatSession: (sessionId: string) => any;
  getUserSessions: (userId: string) => any[];
  updateSessionPreferences: (sessionId: string, preferences: any) => boolean;
  closeSession: (sessionId: string) => boolean;
  healthCheck: () => Promise<any>;
  getServiceStats: () => any;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    agentType?: string;
    tokens?: number;
    confidence?: number;
    suggestions?: any[];
  };
}

interface ChatSession {
  id: string;
  status: 'active' | 'paused' | 'closed';
  preferences: {
    language: 'ru' | 'en';
    verbosity: 'brief' | 'normal' | 'detailed';
    includeCode: boolean;
    includeSuggestions: boolean;
  };
  createdAt: Date;
  lastActivity: Date;
}

const AIAssistantView: React.FC = () => {
  // Состояние
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState('developer');
  const [activeTab, setActiveTab] = useState('chat');
  const [serviceStatus, setServiceStatus] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [showSettings, setShowSettings] = useState(false);
  
  // Ссылки
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Загрузка при монтировании
  useEffect(() => {
    initializeAI();
    loadStats();
  }, []);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Инициализация AI сервиса
   */
  const initializeAI = async () => {
    try {
      // Имитация инициализации AI сервиса
      console.log('Инициализация AI Assistant...');
      
      // Создаем тестовую сессию
      const sessionId = await createTestSession();
      console.log('AI Assistant инициализирован успешно');
      
    } catch (error) {
      console.error('Ошибка инициализации AI:', error);
    }
  };

  /**
   * Создание тестовой сессии
   */
  const createTestSession = async (): Promise<string> => {
    // Имитация создания сессии
    const sessionId = `session_${Date.now()}`;
    const session: ChatSession = {
      id: sessionId,
      status: 'active',
      preferences: {
        language: 'ru',
        verbosity: 'normal',
        includeCode: true,
        includeSuggestions: true
      },
      createdAt: new Date(),
      lastActivity: new Date()
    };

    setCurrentSession(session);

    // Добавляем приветственное сообщение
    const welcomeMessage: Message = {
      id: 'welcome',
      role: 'assistant',
      content: `Привет! Я ваш AI помощник для 1C разработки. Я специализируюсь на:\n\n• Разработке конфигураций 1C\n• Оптимизации запросов\n• Архитектурных решениях\n• Лучших практиках разработки\n\nКак я могу вам помочь?`,
      timestamp: new Date(),
      metadata: {
        agentType: selectedAgent,
        confidence: 0.9
      }
    };

    setMessages([welcomeMessage]);
    return sessionId;
  };

  /**
   * Загрузка статистики
   */
  const loadStats = async () => {
    try {
      // Имитация загрузки статистики
      const mockStats = {
        sessions: {
          total: 1,
          active: 1,
          closed: 0
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
          configured: false,
          healthy: false
        },
        features: {
          suggestions: true,
          streaming: false,
          embeddings: false
        }
      };

      setStats(mockStats);
      setServiceStatus({
        service: 'healthy',
        openai: 'unavailable',
        contextManager: 'healthy',
        suggestionEngine: 'healthy',
        uptime: 300000
      });

    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
    }
  };

  /**
   * Отправка сообщения
   */
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Имитация ответа AI
      await new Promise(resolve => setTimeout(resolve, 1500));

      const aiResponse: Message = {
        id: `ai_${Date.now()}`,
        role: 'assistant',
        content: generateMockResponse(inputMessage),
        timestamp: new Date(),
        metadata: {
          agentType: selectedAgent,
          confidence: 0.8,
          tokens: 150
        }
      };

      setMessages(prev => [...prev, aiResponse]);

    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
      
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: 'Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз.',
        timestamp: new Date(),
        metadata: {
          agentType: selectedAgent,
          confidence: 0
        }
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Генерация мок ответа
   */
  const generateMockResponse = (userMessage: string): string => {
    const responses = [
      `Я понимаю ваш вопрос о "${userMessage}". В контексте 1C разработки рекомендую следующий подход:\n\n1. Проанализируйте текущую структуру данных\n2. Определите оптимальные алгоритмы обработки\n3. Реализуйте решение с учетом производительности\n\nНужна ли дополнительная помощь с конкретной реализацией?`,
      
      `Отличный вопрос! Для решения задачи "${userMessage}" в 1C можно использовать несколько подходов:\n\n• Стандартные механизмы платформы\n• Собственные алгоритмы обработки\n• Интеграцию с внешними системами\n\nРекомендую начать с анализа требований и выбора наиболее подходящего решения.`,
      
      `Ваш запрос требует комплексного подхода. Предлагаю следующую стратегию:\n\n1. **Анализ**: Изучите текущую реализацию\n2. **Планирование**: Определите этапы работ\n3. **Реализация**: Выполните разработку по этапам\n4. **Тестирование**: Проверьте корректность работы\n\nГотов помочь с любым из этапов!`
    ];

    return responses[Math.floor(Math.random() * responses.length)];
  };

  /**
   * Обработка нажатия Enter
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  /**
   * Смена агента
   */
  const handleAgentChange = async (agentType: string) => {
    setSelectedAgent(agentType);
    
    // Создаем новую сессию для другого агента
    const newSessionId = await createTestSession();
    console.log(`Переключен на агента: ${agentType}`);
  };

  /**
   * Очистка чата
   */
  const handleClearChat = () => {
    setMessages([]);
    createTestSession();
  };

  /**
   * Экспорт истории чата
   */
  const handleExportChat = () => {
    const chatData = {
      session: currentSession,
      messages: messages,
      exportDate: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai_chat_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-semibold">AI Помощник</h1>
            <Badge variant={serviceStatus?.service === 'healthy' ? 'default' : 'destructive'}>
              {serviceStatus?.service === 'healthy' ? 'Онлайн' : 'Офлайн'}
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <Select value={selectedAgent} onValueChange={handleAgentChange}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="architect">Архитектор</SelectItem>
                <SelectItem value="developer">Разработчик</SelectItem>
                <SelectItem value="project_manager">Project Manager</SelectItem>
                <SelectItem value="business_analyst">Business Analyst</SelectItem>
                <SelectItem value="data_analyst">Data Analyst</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" size="sm" onClick={() => setShowSettings(!showSettings)}>
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Основной контент */}
      <div className="flex-1 flex overflow-hidden">
        {/* Левая панель - статистика */}
        <div className="w-64 bg-white border-r p-4 overflow-y-auto">
          <h3 className="font-medium mb-4">Статистика</h3>
          
          {stats && (
            <div className="space-y-4">
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageCircle className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium">Сессии</span>
                  </div>
                  <div className="space-y-1">
                    <div className="text-xs text-gray-600">Активных: {stats.sessions.active}</div>
                    <div className="text-xs text-gray-600">Всего: {stats.sessions.total}</div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="h-4 w-4 text-yellow-600" />
                    <span className="text-sm font-medium">OpenAI</span>
                  </div>
                  <Badge variant={stats.openai.configured ? 'default' : 'secondary'}>
                    {stats.openai.configured ? 'Настроен' : 'Не настроен'}
                  </Badge>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium">Подсказки</span>
                  </div>
                  <Badge variant={stats.features.suggestions ? 'default' : 'secondary'}>
                    {stats.features.suggestions ? 'Включены' : 'Отключены'}
                  </Badge>
                </CardContent>
              </Card>

              {/* Статус системы */}
              <div className="mt-6">
                <h4 className="text-sm font-medium mb-2">Статус системы</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    <span className="text-xs">Context Manager</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    <span className="text-xs">Suggestion Engine</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {serviceStatus?.openai === 'available' ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-3 w-3 text-yellow-600" />
                    )}
                    <span className="text-xs">OpenAI API</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Основная область чата */}
        <div className="flex-1 flex flex-col">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
            <TabsList className="mx-4 mt-4">
              <TabsTrigger value="chat">Чат</TabsTrigger>
              <TabsTrigger value="suggestions">Подсказки</TabsTrigger>
              <TabsTrigger value="commands">Команды</TabsTrigger>
            </TabsList>

            <TabsContent value="chat" className="flex-1 flex flex-col m-0">
              {/* Сообщения */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.role !== 'user' && (
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <Bot className="h-4 w-4 text-blue-600" />
                        </div>
                      )}
                      
                      <Card className={`max-w-[80%] ${
                        message.role === 'user' 
                          ? 'bg-blue-50 border-blue-200' 
                          : 'bg-white'
                      }`}>
                        <CardContent className="p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-medium">
                              {message.role === 'user' ? 'Вы' : 'AI Помощник'}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {message.metadata?.agentType}
                            </Badge>
                            {message.metadata?.confidence && (
                              <Badge 
                                variant={message.metadata.confidence > 0.7 ? 'default' : 'secondary'}
                                className="text-xs"
                              >
                                {Math.round(message.metadata.confidence * 100)}%
                              </Badge>
                            )}
                          </div>
                          
                          <div className="text-sm whitespace-pre-wrap">
                            {message.content}
                          </div>
                          
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span>{message.timestamp.toLocaleTimeString('ru-RU')}</span>
                            {message.metadata?.tokens && (
                              <span>{message.metadata.tokens} токенов</span>
                            )}
                          </div>
                        </CardContent>
                      </Card>

                      {message.role === 'user' && (
                        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <User className="h-4 w-4 text-gray-600" />
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="flex gap-3 justify-start">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <Bot className="h-4 w-4 text-blue-600" />
                      </div>
                      <Card className="bg-white">
                        <CardContent className="p-3">
                          <div className="flex items-center gap-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span className="text-sm">Думаю...</span>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Панель ввода */}
              <div className="border-t bg-white p-4">
                <div className="flex gap-2">
                  <div className="flex-1">
                    <Textarea
                      ref={textareaRef}
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyDown={handleKeyPress}
                      placeholder="Напишите ваш вопрос или задачу..."
                      className="min-h-[60px] resize-none"
                      disabled={isLoading}
                    />
                  </div>
                  
                  <div className="flex flex-col gap-2">
                    <Button 
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim() || isLoading}
                      size="sm"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                    
                    <Button variant="outline" size="sm" onClick={handleClearChat}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                    
                    <Button variant="outline" size="sm" onClick={handleExportChat}>
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                  <span>Enter для отправки, Shift+Enter для новой строки</span>
                  <span>{inputMessage.length} символов</span>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="suggestions" className="flex-1 m-0 p-4">
              <div className="text-center text-gray-500 py-8">
                <Lightbulb className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Подсказки будут отображаться здесь</p>
                <p className="text-sm">Начните разговор, чтобы получить умные предложения</p>
              </div>
            </TabsContent>

            <TabsContent value="commands" className="flex-1 m-0 p-4">
              <div className="text-center text-gray-500 py-8">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Команды будут отображаться здесь</p>
                <p className="text-sm">Используйте /help для просмотра доступных команд</p>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Настройки */}
      {showSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Настройки AI Помощника</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Язык</label>
                <Select value="ru">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ru">Русский</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium">Подробность ответов</label>
                <Select value="normal">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="brief">Краткие</SelectItem>
                    <SelectItem value="normal">Обычные</SelectItem>
                    <SelectItem value="detailed">Подробные</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm">Включать примеры кода</span>
                <input type="checkbox" defaultChecked />
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm">Показывать подсказки</span>
                <input type="checkbox" defaultChecked />
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowSettings(false)}>
                  Отмена
                </Button>
                <Button onClick={() => setShowSettings(false)}>
                  Сохранить
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AIAssistantView;