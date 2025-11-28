/**
 * Context Viewer Component
 * Компонент для просмотра и управления контекстом разговора
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Database,
  MessageSquare,
  Clock,
  User,
  Bot,
  Settings,
  Download,
  Upload,
  Trash2,
  RefreshCw,
  Search,
  Filter,
  Calendar,
  FileText,
  Brain,
  Activity,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  Info
} from 'lucide-react';

// Типы для контекста
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
    contextData?: Record<string, any>;
  };
}

interface TaskContext {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'paused' | 'cancelled';
  progress: number;
  relatedFiles: string[];
  dependencies: string[];
  createdAt: Date;
  completedAt?: Date;
}

interface SessionData {
  currentProject?: string;
  workingDirectory?: string;
  selectedFiles?: string[];
  recentActions?: string[];
  userPreferences?: Record<string, any>;
  knowledgeBase?: string[];
  taskHistory?: TaskContext[];
}

interface ConversationContext {
  id: string;
  userId: string;
  agentType: string;
  messages: Message[];
  sessionData: SessionData;
  createdAt: Date;
  updatedAt: Date;
}

interface ContextFilter {
  agentType?: string;
  timeRange?: {
    start: Date;
    end: Date;
  };
  keywords?: string[];
  project?: string;
}

const ContextViewer: React.FC<{
  conversationId?: string;
  currentContext?: ConversationContext;
  onContextUpdate?: (context: ConversationContext) => void;
}> = ({ 
  conversationId, 
  currentContext, 
  onContextUpdate 
}) => {
  // Состояние
  const [context, setContext] = useState<ConversationContext | null>(currentContext || null);
  const [contexts, setContexts] = useState<ConversationContext[]>([]);
  const [activeTab, setActiveTab] = useState('current');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMessage, setSelectedMessage] = useState<string | null>(null);
  const [filter, setFilter] = useState<ContextFilter>({});
  const [showFilters, setShowFilters] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadContexts();
    if (conversationId) {
      loadContext(conversationId);
    }
  }, [conversationId]);

  /**
   * Загрузка всех контекстов
   */
  const loadContexts = async () => {
    setIsLoading(true);
    try {
      // Имитация загрузки контекстов
      const mockContexts: ConversationContext[] = [
        {
          id: 'context_1',
          userId: 'user_1',
          agentType: 'developer',
          messages: [
            {
              id: 'msg_1',
              role: 'user',
              content: 'Помогите оптимизировать запрос к базе данных',
              timestamp: new Date(Date.now() - 1000 * 60 * 60),
              metadata: { agentType: 'developer' }
            },
            {
              id: 'msg_2',
              role: 'assistant',
              content: 'Для оптимизации запроса рекомендую:\n1. Добавить индексы\n2. Использовать конкретные поля вместо *\n3. Добавить условия WHERE',
              timestamp: new Date(Date.now() - 1000 * 60 * 55),
              metadata: { agentType: 'developer', tokens: 85, confidence: 0.9 }
            }
          ],
          sessionData: {
            currentProject: 'ERP_Sales',
            workingDirectory: '/src/modules/sales',
            selectedFiles: ['DocumentSales.bsl', 'QueryOptimize.bsl'],
            recentActions: ['Создан документ Продажа', 'Оптимизирован запрос', 'Добавлены индексы'],
            taskHistory: [
              {
                id: 'task_1',
                name: 'Оптимизация базы данных',
                status: 'completed',
                progress: 100,
                relatedFiles: ['Database.1CDB'],
                dependencies: [],
                createdAt: new Date(Date.now() - 1000 * 60 * 120),
                completedAt: new Date(Date.now() - 1000 * 60 * 60)
              }
            ]
          },
          createdAt: new Date(Date.now() - 1000 * 60 * 120),
          updatedAt: new Date(Date.now() - 1000 * 60 * 55)
        },
        {
          id: 'context_2',
          userId: 'user_1',
          agentType: 'architect',
          messages: [
            {
              id: 'msg_3',
              role: 'user',
              content: 'Нужно спроектировать архитектуру нового модуля',
              timestamp: new Date(Date.now() - 1000 * 60 * 30),
              metadata: { agentType: 'architect' }
            }
          ],
          sessionData: {
            currentProject: 'CRM_Customers',
            workingDirectory: '/architecture/modules',
            selectedFiles: ['ModuleStructure.md', 'API_Design.md'],
            taskHistory: []
          },
          createdAt: new Date(Date.now() - 1000 * 60 * 30),
          updatedAt: new Date(Date.now() - 1000 * 60 * 30)
        }
      ];

      setContexts(mockContexts);
      
      // Если не указан текущий контекст, берем первый
      if (!currentContext && mockContexts.length > 0) {
        setContext(mockContexts[0]);
      }
      
    } catch (error) {
      console.error('Ошибка загрузки контекстов:', error);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Загрузка конкретного контекста
   */
  const loadContext = async (id: string) => {
    const foundContext = contexts.find(c => c.id === id);
    if (foundContext) {
      setContext(foundContext);
      onContextUpdate?.(foundContext);
    }
  };

  /**
   * Фильтрация сообщений
   */
  const filteredMessages = context?.messages.filter(message => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      message.content.toLowerCase().includes(searchLower) ||
      message.role.toLowerCase().includes(searchLower)
    );
  }) || [];

  /**
   * Форматирование времени
   */
  const formatTime = (date: Date) => {
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  /**
   * Копирование содержимого
   */
  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
    // Можно добавить уведомление об успешном копировании
  };

  /**
   * Экспорт контекста
   */
  const exportContext = (ctx: ConversationContext) => {
    const data = {
      ...ctx,
      exportDate: new Date().toISOString(),
      exportVersion: '1.0'
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `context_${ctx.agentType}_${ctx.id}_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  /**
   * Получение статистики контекста
   */
  const getContextStats = (ctx: ConversationContext) => {
    const messages = ctx.messages;
    const userMessages = messages.filter(m => m.role === 'user').length;
    const assistantMessages = messages.filter(m => m.role === 'assistant').length;
    const systemMessages = messages.filter(m => m.role === 'system').length;
    const tasksCompleted = ctx.sessionData.taskHistory?.filter(t => t.status === 'completed').length || 0;
    const tasksActive = ctx.sessionData.taskHistory?.filter(t => t.status === 'active').length || 0;

    return {
      totalMessages: messages.length,
      userMessages,
      assistantMessages,
      systemMessages,
      tasksCompleted,
      tasksActive,
      duration: Math.round((ctx.updatedAt.getTime() - ctx.createdAt.getTime()) / (1000 * 60)) // минуты
    };
  };

  /**
   * Генерация контекстного резюме
   */
  const generateSummary = (ctx: ConversationContext) => {
    const stats = getContextStats(ctx);
    const recentActions = ctx.sessionData.recentActions?.slice(-5) || [];
    const activeTasks = ctx.sessionData.taskHistory?.filter(t => t.status === 'active') || [];

    return `
Контекст сессии:
• Агент: ${ctx.agentType}
• Сообщений: ${stats.totalMessages} (пользователь: ${stats.userMessages}, AI: ${stats.assistantMessages})
• Завершенных задач: ${stats.tasksCompleted}
• Активных задач: ${stats.tasksActive}
• Длительность: ${stats.duration} минут
• Проект: ${ctx.sessionData.currentProject || 'не указан'}
• Рабочая директория: ${ctx.sessionData.workingDirectory || 'не указана'}

Последние действия:
${recentActions.map(action => `• ${action}`).join('\n')}

${activeTasks.length > 0 ? `Активные задачи:\n${activeTasks.map(task => `• ${task.name} (${task.progress}%)`).join('\n')}` : ''}
    `.trim();
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Database className="h-5 w-5 text-blue-600" />
            Context Manager
          </h2>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowFilters(!showFilters)}>
              <Filter className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={loadContexts}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Панель поиска и фильтров */}
        <div className="flex gap-2 mb-4">
          <div className="flex-1">
            <Input
              placeholder="Поиск в контексте..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
            <Search className="h-4 w-4 absolute left-2 top-2.5 text-gray-400" />
          </div>
          
          <Select value={context?.agentType || 'all'} onValueChange={(value) => {
            if (value !== 'all') {
              const filtered = contexts.filter(c => c.agentType === value);
              setContexts(filtered);
            } else {
              loadContexts();
            }
          }}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все агенты</SelectItem>
              <SelectItem value="architect">Архитектор</SelectItem>
              <SelectItem value="developer">Разработчик</SelectItem>
              <SelectItem value="project_manager">Project Manager</SelectItem>
              <SelectItem value="business_analyst">Business Analyst</SelectItem>
              <SelectItem value="data_analyst">Data Analyst</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Фильтры */}
        {showFilters && (
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm font-medium">Проект</label>
                  <Input
                    placeholder="Название проекта"
                    value={filter.project || ''}
                    onChange={(e) => setFilter(prev => ({ ...prev, project: e.target.value }))}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">Дата начала</label>
                  <Input
                    type="date"
                    value={filter.timeRange?.start?.toISOString().split('T')[0] || ''}
                    onChange={(e) => setFilter(prev => ({
                      ...prev,
                      timeRange: {
                        start: new Date(e.target.value),
                        end: prev.timeRange?.end || new Date()
                      }
                    }))}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">Дата окончания</label>
                  <Input
                    type="date"
                    value={filter.timeRange?.end?.toISOString().split('T')[0] || ''}
                    onChange={(e) => setFilter(prev => ({
                      ...prev,
                      timeRange: {
                        start: prev.timeRange?.start || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
                        end: new Date(e.target.value)
                      }
                    }))}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">Ключевые слова</label>
                  <Input
                    placeholder="Через запятую"
                    value={filter.keywords?.join(', ') || ''}
                    onChange={(e) => setFilter(prev => ({
                      ...prev,
                      keywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean)
                    }))}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="current">Текущий контекст</TabsTrigger>
            <TabsTrigger value="all">Все контексты</TabsTrigger>
            <TabsTrigger value="stats">Статистика</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Контент */}
      <div className="flex-1 overflow-hidden">
        <TabsContent value="current" className="h-full m-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-gray-400" />
                <p className="text-sm text-gray-600">Загрузка контекста...</p>
              </div>
            </div>
          ) : context ? (
            <div className="h-full flex">
              {/* Левая панель - информация о контексте */}
              <div className="w-80 bg-white border-r p-4 overflow-y-auto">
                <div className="space-y-4">
                  {/* Основная информация */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Информация о сессии</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div>
                        <label className="text-xs text-gray-600">ID сессии</label>
                        <p className="text-sm font-mono">{context.id}</p>
                      </div>
                      
                      <div>
                        <label className="text-xs text-gray-600">Агент</label>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline">{context.agentType}</Badge>
                        </div>
                      </div>
                      
                      <div>
                        <label className="text-xs text-gray-600">Проект</label>
                        <p className="text-sm">{context.sessionData.currentProject || 'не указан'}</p>
                      </div>
                      
                      <div>
                        <label className="text-xs text-gray-600">Директория</label>
                        <p className="text-sm">{context.sessionData.workingDirectory || 'не указана'}</p>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Статистика */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Статистика</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {(() => {
                        const stats = getContextStats(context);
                        return (
                          <>
                            <div className="flex justify-between">
                              <span className="text-xs text-gray-600">Сообщений</span>
                              <span className="text-sm">{stats.totalMessages}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-xs text-gray-600">Пользователь</span>
                              <span className="text-sm">{stats.userMessages}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-xs text-gray-600">AI помощник</span>
                              <span className="text-sm">{stats.assistantMessages}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-xs text-gray-600">Задач завершено</span>
                              <span className="text-sm">{stats.tasksCompleted}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-xs text-gray-600">Задач активно</span>
                              <span className="text-sm">{stats.tasksActive}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-xs text-gray-600">Длительность</span>
                              <span className="text-sm">{stats.duration} мин</span>
                            </div>
                          </>
                        );
                      })()}
                    </CardContent>
                  </Card>

                  {/* Задачи */}
                  {context.sessionData.taskHistory && context.sessionData.taskHistory.length > 0 && (
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">История задач</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {context.sessionData.taskHistory.map((task) => (
                          <div key={task.id} className="border rounded p-2">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium">{task.name}</span>
                              <Badge 
                                variant={task.status === 'completed' ? 'default' : 'outline'}
                                className="text-xs"
                              >
                                {task.status}
                              </Badge>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-1 mb-1">
                              <div 
                                className="bg-blue-600 h-1 rounded-full"
                                style={{ width: `${task.progress}%` }}
                              />
                            </div>
                            <div className="text-xs text-gray-600">
                              {task.progress}% • {task.relatedFiles.length} файлов
                            </div>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}

                  {/* Действия */}
                  <div className="space-y-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={() => exportContext(context)}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Экспорт контекста
                    </Button>
                  </div>
                </div>
              </div>

              {/* Правая панель - сообщения */}
              <div className="flex-1 flex flex-col">
                <div className="bg-white border-b p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Сообщения ({filteredMessages.length})</h3>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => copyToClipboard(generateSummary(context))}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Копировать резюме
                    </Button>
                  </div>
                </div>

                <ScrollArea className="flex-1 p-4">
                  <div className="space-y-4">
                    {filteredMessages.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                        <p>Нет сообщений для отображения</p>
                        {searchTerm && <p className="text-sm">Попробуйте изменить поисковый запрос</p>}
                      </div>
                    ) : (
                      filteredMessages.map((message) => (
                        <Card 
                          key={message.id}
                          className={`cursor-pointer transition-all ${
                            selectedMessage === message.id 
                              ? 'ring-2 ring-blue-500 bg-blue-50' 
                              : 'hover:shadow-sm'
                          }`}
                          onClick={() => setSelectedMessage(
                            selectedMessage === message.id ? null : message.id
                          )}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-start gap-3">
                              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0">
                                {message.role === 'user' ? (
                                  <User className="h-4 w-4 text-blue-600" />
                                ) : message.role === 'assistant' ? (
                                  <Bot className="h-4 w-4 text-green-600" />
                                ) : (
                                  <Settings className="h-4 w-4 text-gray-600" />
                                )}
                              </div>
                              
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <Badge variant="outline" className="text-xs">
                                    {message.role}
                                  </Badge>
                                  <span className="text-xs text-gray-500">
                                    {formatTime(message.timestamp)}
                                  </span>
                                  {message.metadata?.agentType && (
                                    <Badge variant="secondary" className="text-xs">
                                      {message.metadata.agentType}
                                    </Badge>
                                  )}
                                  {message.metadata?.confidence && (
                                    <Badge 
                                      variant={message.metadata.confidence > 0.7 ? 'default' : 'outline'}
                                      className="text-xs"
                                    >
                                      {Math.round(message.metadata.confidence * 100)}%
                                    </Badge>
                                  )}
                                </div>
                                
                                <p className="text-sm whitespace-pre-wrap">
                                  {message.content}
                                </p>
                                
                                {selectedMessage === message.id && message.metadata && (
                                  <div className="mt-3 pt-3 border-t space-y-2">
                                    {message.metadata.tokens && (
                                      <div className="text-xs text-gray-600">
                                        Токенов использовано: {message.metadata.tokens}
                                      </div>
                                    )}
                                    
                                    {message.metadata.contextData && Object.keys(message.metadata.contextData).length > 0 && (
                                      <div className="text-xs">
                                        <span className="font-medium">Дополнительные данные:</span>
                                        <pre className="mt-1 bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                                          {JSON.stringify(message.metadata.contextData, null, 2)}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                <Database className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Контекст не выбран</p>
                <p className="text-sm">Выберите контекст для просмотра</p>
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="all" className="h-full m-0 p-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">Все контексты ({contexts.length})</h3>
              <Button variant="outline" size="sm">
                <Upload className="h-4 w-4 mr-2" />
                Импорт
              </Button>
            </div>

            <div className="grid gap-4">
              {contexts.map((ctx) => (
                <Card 
                  key={ctx.id} 
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => {
                    setContext(ctx);
                    setActiveTab('current');
                  }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline">{ctx.agentType}</Badge>
                          <span className="text-xs text-gray-500">
                            {formatTime(ctx.updatedAt)}
                          </span>
                        </div>
                        
                        <h4 className="font-medium mb-1">
                          {ctx.sessionData.currentProject || 'Без проекта'}
                        </h4>
                        
                        <p className="text-sm text-gray-600 mb-2">
                          Сообщений: {ctx.messages.length} • 
                          Задач: {ctx.sessionData.taskHistory?.length || 0}
                        </p>
                        
                        <div className="text-xs text-gray-500">
                          {ctx.sessionData.workingDirectory}
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            exportContext(ctx);
                          }}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="stats" className="h-full m-0 p-4">
          <div className="space-y-6">
            <h3 className="font-medium">Общая статистика</h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {contexts.length}
                  </div>
                  <div className="text-sm text-gray-600">Контекстов</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {contexts.reduce((sum, ctx) => sum + ctx.messages.length, 0)}
                  </div>
                  <div className="text-sm text-gray-600">Сообщений</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {[...new Set(contexts.map(ctx => ctx.agentType))].length}
                  </div>
                  <div className="text-sm text-gray-600">Агентов</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {contexts.filter(ctx => ctx.sessionData.currentProject).length}
                  </div>
                  <div className="text-sm text-gray-600">С проектами</div>
                </CardContent>
              </Card>
            </div>

            <div>
              <h4 className="font-medium mb-4">Распределение по агентам</h4>
              <div className="space-y-2">
                {[...new Set(contexts.map(ctx => ctx.agentType))].map((agentType) => {
                  const count = contexts.filter(ctx => ctx.agentType === agentType).length;
                  const percentage = contexts.length > 0 ? (count / contexts.length) * 100 : 0;
                  
                  return (
                    <div key={agentType} className="flex items-center justify-between">
                      <span className="text-sm capitalize">{agentType}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">{count} ({Math.round(percentage)}%)</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </TabsContent>
      </div>
    </div>
  );
};

export default ContextViewer;