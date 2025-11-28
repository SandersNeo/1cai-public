/**
 * Suggestion Panel Component
 * Панель для отображения и управления AI подсказками
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
import {
  Lightbulb,
  Code,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Filter,
  Search,
  Star,
  Zap,
  Target,
  AlertTriangle,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  RefreshCw
} from 'lucide-react';

// Типы подсказок
interface Suggestion {
  id: string;
  type: 'code' | 'task' | 'optimization' | 'documentation' | 'testing' | 'refactor' | 'integration';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  code?: string;
  impact: string;
  confidence: number;
  relatedFiles: string[];
  metadata?: {
    agentType?: string;
    complexity?: 'low' | 'medium' | 'high';
    estimatedTime?: string;
    performanceGain?: string;
  };
  createdAt: Date;
  applied?: boolean;
  rejected?: boolean;
}

interface SuggestionRule {
  id: string;
  name: string;
  enabled: boolean;
  condition: string;
  weight: number;
}

const SuggestionPanel: React.FC<{
  conversationId?: string;
  onApplySuggestion?: (suggestion: Suggestion) => void;
  onRejectSuggestion?: (suggestion: Suggestion, reason?: string) => void;
}> = ({ 
  conversationId, 
  onApplySuggestion, 
  onRejectSuggestion 
}) => {
  // Состояние
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [filteredSuggestions, setFilteredSuggestions] = useState<Suggestion[]>([]);
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'priority' | 'confidence' | 'date'>('priority');
  const [showDetails, setShowDetails] = useState<string | null>(null);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState('suggestions');
  const [rules, setRules] = useState<SuggestionRule[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadSuggestions();
    loadRules();
  }, [conversationId]);

  // Фильтрация и сортировка
  useEffect(() => {
    let filtered = [...suggestions];

    // Фильтр по типу
    if (activeFilter !== 'all') {
      filtered = filtered.filter(s => s.type === activeFilter);
    }

    // Поиск
    if (searchTerm) {
      filtered = filtered.filter(s => 
        s.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Сортировка
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          const priorityOrder = { high: 3, medium: 2, low: 1 };
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        case 'confidence':
          return b.confidence - a.confidence;
        case 'date':
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        default:
          return 0;
      }
    });

    setFilteredSuggestions(filtered);
  }, [suggestions, activeFilter, searchTerm, sortBy]);

  /**
   * Загрузка подсказок
   */
  const loadSuggestions = async () => {
    setIsLoading(true);
    try {
      // Имитация загрузки подсказок
      const mockSuggestions: Suggestion[] = [
        {
          id: '1',
          type: 'code',
          priority: 'high',
          title: 'Оптимизация запроса к базе данных',
          description: 'Обнаружен медленный запрос в модуле обработки документов. Рекомендуется добавить индексы и переписать условия.',
          code: `// Текущий запрос
Запрос = Новый Запрос;
Запрос.Текст = "ВЫБРАТЬ * ИЗ Документ.Продажа";
Результат = Запрос.Выполнить();

// Оптимизированный запрос
Запрос = Новый Запрос;
Запрос.Текст = "ВЫБРАТЬ Ссылка, Дата, Сумма ИЗ Документ.Продажа ГДЕ Проведен = ИСТИНА";`,
          impact: 'Увеличение производительности на 60-80%',
          confidence: 0.9,
          relatedFiles: ['МодульДокумента.bsl', 'ФормаСписка.Форма'],
          metadata: {
            complexity: 'medium',
            estimatedTime: '2-3 часа',
            performanceGain: '60-80%'
          },
          createdAt: new Date(Date.now() - 1000 * 60 * 30) // 30 минут назад
        },
        {
          id: '2',
          type: 'task',
          priority: 'medium',
          title: 'Добавление валидации данных',
          description: 'Рекомендуется добавить проверку корректности вводимых данных в форме создания контрагента.',
          impact: 'Повышение качества данных и уменьшение ошибок',
          confidence: 0.8,
          relatedFiles: ['ФормаКонтрагента.Форма', 'МодульФормы.Модуль'],
          metadata: {
            complexity: 'low',
            estimatedTime: '1-2 часа'
          },
          createdAt: new Date(Date.now() - 1000 * 60 * 60) // 1 час назад
        },
        {
          id: '3',
          type: 'documentation',
          priority: 'low',
          title: 'Обновление технической документации',
          description: 'Некоторые части кода не имеют комментариев. Рекомендуется добавить документацию для лучшего понимания.',
          impact: 'Улучшение поддерживаемости кода',
          confidence: 0.7,
          relatedFiles: ['МодульОбработки.Модуль', 'ОбщийМодуль.Модуль'],
          metadata: {
            complexity: 'low',
            estimatedTime: '30 минут'
          },
          createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2) // 2 часа назад
        },
        {
          id: '4',
          type: 'optimization',
          priority: 'high',
          title: 'Кэширование результатов вычислений',
          description: 'Повторяющиеся вычисления можно кэшировать для ускорения работы системы.',
          impact: 'Сокращение времени обработки в 3-5 раз',
          confidence: 0.85,
          relatedFiles: ['МодульРасчетов.Модуль'],
          metadata: {
            complexity: 'high',
            estimatedTime: '4-6 часов',
            performanceGain: '300-500%'
          },
          createdAt: new Date(Date.now() - 1000 * 60 * 90) // 1.5 часа назад
        }
      ];

      setSuggestions(mockSuggestions);
    } catch (error) {
      console.error('Ошибка загрузки подсказок:', error);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Загрузка правил
   */
  const loadRules = async () => {
    const mockRules: SuggestionRule[] = [
      {
        id: '1',
        name: '1C лучшие практики',
        enabled: true,
        condition: 'projectType == "1c" AND agentType == "developer"',
        weight: 0.8
      },
      {
        id: '2',
        name: 'Большой проект',
        enabled: true,
        condition: 'currentTasks.length > 10',
        weight: 0.6
      },
      {
        id: '3',
        name: 'Начинающий разработчик',
        enabled: true,
        condition: 'userLevel == "beginner"',
        weight: 0.5
      }
    ];

    setRules(mockRules);
  };

  /**
   * Применение подсказки
   */
  const handleApplySuggestion = (suggestion: Suggestion) => {
    setSuggestions(prev => 
      prev.map(s => 
        s.id === suggestion.id 
          ? { ...s, applied: true, rejected: false }
          : s
      )
    );

    onApplySuggestion?.(suggestion);
  };

  /**
   * Отклонение подсказки
   */
  const handleRejectSuggestion = (suggestion: Suggestion, reason?: string) => {
    setSuggestions(prev => 
      prev.map(s => 
        s.id === suggestion.id 
          ? { ...s, rejected: true, applied: false }
          : s
      )
    );

    onRejectSuggestion?.(suggestion, reason);
  };

  /**
   * Переключение деталей подсказки
   */
  const toggleDetails = (suggestionId: string) => {
    setShowDetails(showDetails === suggestionId ? null : suggestionId);
  };

  /**
   * Копирование кода
   */
  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    // Можно добавить уведомление об успешном копировании
  };

  /**
   * Получение иконки для типа подсказки
   */
  const getTypeIcon = (type: Suggestion['type']) => {
    const icons = {
      code: Code,
      task: Target,
      optimization: TrendingUp,
      documentation: BookOpen,
      testing: CheckCircle,
      refactor: RefreshCw,
      integration: ExternalLink
    };
    
    const Icon = icons[type] || Lightbulb;
    return <Icon className="h-4 w-4" />;
  };

  /**
   * Получение цвета для приоритета
   */
  const getPriorityColor = (priority: Suggestion['priority']) => {
    const colors = {
      high: 'bg-red-100 text-red-800 border-red-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-green-100 text-green-800 border-green-200'
    };
    
    return colors[priority];
  };

  /**
   * Получение цвета для типа
   */
  const getTypeColor = (type: Suggestion['type']) => {
    const colors = {
      code: 'bg-blue-100 text-blue-800',
      task: 'bg-purple-100 text-purple-800',
      optimization: 'bg-green-100 text-green-800',
      documentation: 'bg-gray-100 text-gray-800',
      testing: 'bg-indigo-100 text-indigo-800',
      refactor: 'bg-orange-100 text-orange-800',
      integration: 'bg-pink-100 text-pink-800'
    };
    
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Заголовок */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-600" />
            AI Подсказки
          </h2>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={loadSuggestions}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Badge variant="outline">
              {filteredSuggestions.length} из {suggestions.length}
            </Badge>
          </div>
        </div>

        {/* Фильтры и поиск */}
        <div className="flex flex-wrap gap-2 mb-4">
          <Select value={activeFilter} onValueChange={setActiveFilter}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все типы</SelectItem>
              <SelectItem value="code">Код</SelectItem>
              <SelectItem value="task">Задачи</SelectItem>
              <SelectItem value="optimization">Оптимизация</SelectItem>
              <SelectItem value="documentation">Документация</SelectItem>
              <SelectItem value="testing">Тестирование</SelectItem>
              <SelectItem value="refactor">Рефакторинг</SelectItem>
              <SelectItem value="integration">Интеграция</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={(value) => setSortBy(value as any)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="priority">По приоритету</SelectItem>
              <SelectItem value="confidence">По уверенности</SelectItem>
              <SelectItem value="date">По дате</SelectItem>
            </SelectContent>
          </Select>

          <div className="flex-1 min-w-48">
            <Input
              placeholder="Поиск подсказок..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
            <Search className="h-4 w-4 absolute left-2 top-2.5 text-gray-400" />
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="suggestions">
              Подсказки ({filteredSuggestions.length})
            </TabsTrigger>
            <TabsTrigger value="rules">
              Правила ({rules.length})
            </TabsTrigger>
            <TabsTrigger value="stats">
              Статистика
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Контент */}
      <div className="flex-1 overflow-hidden">
        <TabsContent value="suggestions" className="h-full m-0">
          <ScrollArea className="h-full p-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="text-center">
                  <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600">Загрузка подсказок...</p>
                </div>
              </div>
            ) : filteredSuggestions.length === 0 ? (
              <div className="text-center py-8">
                <Lightbulb className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">
                  {suggestions.length === 0 
                    ? 'Подсказки пока не доступны' 
                    : 'Нет подсказок, соответствующих фильтрам'
                  }
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredSuggestions.map((suggestion) => (
                  <Card 
                    key={suggestion.id} 
                    className={`transition-all ${
                      suggestion.applied 
                        ? 'bg-green-50 border-green-200' 
                        : suggestion.rejected 
                          ? 'bg-red-50 border-red-200' 
                          : 'bg-white hover:shadow-md'
                    }`}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <div className="mt-1">
                            {getTypeIcon(suggestion.type)}
                          </div>
                          
                          <div className="flex-1">
                            <CardTitle className="text-base mb-2">
                              {suggestion.title}
                            </CardTitle>
                            
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={getTypeColor(suggestion.type)}>
                                {suggestion.type}
                              </Badge>
                              
                              <Badge className={getPriorityColor(suggestion.priority)}>
                                {suggestion.priority}
                              </Badge>
                              
                              <Badge variant="outline">
                                {Math.round(suggestion.confidence * 100)}%
                              </Badge>
                              
                              {suggestion.applied && (
                                <Badge className="bg-green-100 text-green-800">
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  Применено
                                </Badge>
                              )}
                              
                              {suggestion.rejected && (
                                <Badge className="bg-red-100 text-red-800">
                                  <XCircle className="h-3 w-3 mr-1" />
                                  Отклонено
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleDetails(suggestion.id)}
                          >
                            {showDetails === suggestion.id ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                    </CardHeader>

                    <CardContent className="pt-0">
                      <p className="text-sm text-gray-700 mb-3">
                        {suggestion.description}
                      </p>

                      {showDetails === suggestion.id && (
                        <div className="mt-4 space-y-4">
                          {/* Метаданные */}
                          {suggestion.metadata && (
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              {suggestion.metadata.estimatedTime && (
                                <div className="flex items-center gap-2">
                                  <Clock className="h-4 w-4 text-gray-400" />
                                  <span>Время: {suggestion.metadata.estimatedTime}</span>
                                </div>
                              )}
                              {suggestion.metadata.complexity && (
                                <div className="flex items-center gap-2">
                                  <AlertTriangle className="h-4 w-4 text-gray-400" />
                                  <span>Сложность: {suggestion.metadata.complexity}</span>
                                </div>
                              )}
                              {suggestion.metadata.performanceGain && (
                                <div className="flex items-center gap-2 col-span-2">
                                  <TrendingUp className="h-4 w-4 text-gray-400" />
                                  <span>Улучшение: {suggestion.metadata.performanceGain}</span>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Код */}
                          {suggestion.code && (
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-medium">Пример кода:</h4>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => copyCode(suggestion.code!)}
                                >
                                  <Copy className="h-4 w-4" />
                                </Button>
                              </div>
                              <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                                <code>{suggestion.code}</code>
                              </pre>
                            </div>
                          )}

                          {/* Связанные файлы */}
                          {suggestion.relatedFiles.length > 0 && (
                            <div>
                              <h4 className="text-sm font-medium mb-2">Связанные файлы:</h4>
                              <div className="flex flex-wrap gap-2">
                                {suggestion.relatedFiles.map((file) => (
                                  <Badge key={file} variant="outline" className="text-xs">
                                    {file}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Воздействие */}
                          <div>
                            <h4 className="text-sm font-medium mb-1">Ожидаемый результат:</h4>
                            <p className="text-sm text-gray-600">{suggestion.impact}</p>
                          </div>

                          {/* Время создания */}
                          <div className="text-xs text-gray-500">
                            Создано: {suggestion.createdAt.toLocaleString('ru-RU')}
                          </div>
                        </div>
                      )}

                      {/* Действия */}
                      <div className="flex items-center justify-between mt-4 pt-3 border-t">
                        <div className="flex gap-2">
                          {!suggestion.applied && !suggestion.rejected && (
                            <>
                              <Button
                                size="sm"
                                onClick={() => handleApplySuggestion(suggestion)}
                                className="text-xs"
                              >
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Применить
                              </Button>
                              
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRejectSuggestion(suggestion)}
                                className="text-xs"
                              >
                                <XCircle className="h-3 w-3 mr-1" />
                                Отклонить
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="rules" className="h-full m-0 p-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">Правила генерации подсказок</h3>
              <Button variant="outline" size="sm">
                Добавить правило
              </Button>
            </div>

            {rules.map((rule) => (
              <Card key={rule.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{rule.name}</h4>
                      <p className="text-sm text-gray-600">{rule.condition}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline">Вес: {rule.weight}</Badge>
                        <Badge variant={rule.enabled ? 'default' : 'secondary'}>
                          {rule.enabled ? 'Включено' : 'Отключено'}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm">
                        Редактировать
                      </Button>
                      <Button variant="ghost" size="sm">
                        {rule.enabled ? 'Отключить' : 'Включить'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="stats" className="h-full m-0 p-4">
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {suggestions.length}
                  </div>
                  <div className="text-sm text-gray-600">Всего подсказок</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {suggestions.filter(s => s.applied).length}
                  </div>
                  <div className="text-sm text-gray-600">Применено</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {suggestions.filter(s => s.rejected).length}
                  </div>
                  <div className="text-sm text-gray-600">Отклонено</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {suggestions.length > 0 
                      ? Math.round((suggestions.filter(s => s.applied).length / suggestions.length) * 100)
                      : 0}%
                  </div>
                  <div className="text-sm text-gray-600">Эффективность</div>
                </CardContent>
              </Card>
            </div>

            <div>
              <h3 className="font-medium mb-4">Распределение по типам</h3>
              <div className="space-y-2">
                {Object.entries(
                  suggestions.reduce((acc, s) => {
                    acc[s.type] = (acc[s.type] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>)
                ).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{type}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ 
                            width: `${suggestions.length > 0 ? (count / suggestions.length) * 100 : 0}%` 
                          }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>
      </div>
    </div>
  );
};

export default SuggestionPanel;