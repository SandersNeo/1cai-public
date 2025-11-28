import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Mic, 
  Volume2, 
  Command, 
  Settings, 
  Activity, 
  Users, 
  BarChart3,
  Headphones,
  Keyboard,
  Play,
  Pause,
  Square
} from 'lucide-react';

// Импорт сервисов
import { VoiceIntegrationService } from '@/services/voice-integration-service';
import { SpeechRecognitionService } from '@/services/speech-recognition-service';
import { TextToSpeechService } from '@/services/text-to-speech-service';
import { VoiceCommandProcessorService } from '@/services/voice-command-processor-service';

// Импорт компонентов
import VoiceControlView from './VoiceControlView';
import VoiceCommandPanel from './VoiceCommandPanel';
import SpeechRecognitionView from './SpeechRecognitionView';

const VoiceCommandsPage: React.FC = () => {
  // Инициализация сервисов
  const [voiceService] = useState(() => new VoiceIntegrationService());
  const [speechService] = useState(() => new SpeechRecognitionService());
  const [ttsService] = useState(() => new TextToSpeechService());
  const [commandService] = useState(() => new VoiceCommandProcessorService());

  const [activeTab, setActiveTab] = useState('overview');
  const [currentAgent, setCurrentAgent] = useState('architect');
  const [userId] = useState('user_' + Date.now());
  const [isActive, setIsActive] = useState(false);

  // Состояние для статистики и мониторинга
  const [voiceStats, setVoiceStats] = useState({
    totalSessions: 0,
    activeSessions: 0,
    commandsExecuted: 0,
    mostActiveAgent: '',
    averageSessionDuration: 0
  });

  const [sessionStats, setSessionStats] = useState({
    commandsProcessed: 0,
    sessionDuration: 0,
    errorCount: 0
  });

  const [availableAgents] = useState([
    { id: 'architect', name: 'Архитектор', icon: '🏗️', description: 'Архитектурное планирование и дизайн' },
    { id: 'developer', name: 'Разработчик', icon: '💻', description: 'Разработка и кодирование' },
    { id: 'pm', name: 'Менеджер проектов', icon: '📋', description: 'Управление проектами' },
    { id: 'ba', name: 'Бизнес-аналитик', icon: '📊', description: 'Бизнес-анализ и требования' },
    { id: 'data_analyst', name: 'Аналитик данных', icon: '📈', description: 'Анализ данных и отчеты' }
  ]);

  const [recentEvents, setRecentEvents] = useState<Array<{
    id: string;
    type: string;
    message: string;
    timestamp: Date;
    agent?: string;
  }>>([]);

  useEffect(() => {
    // Подписка на события голосового сервиса
    const eventSubscription = voiceService.voiceEvent$.subscribe(event => {
      if (event) {
        addVoiceEvent(event);
      }
    });

    // Подписка на сессии
    const sessionSubscription = voiceService.session$.subscribe(session => {
      setIsActive(!!session);
      if (session) {
        setSessionStats({
          commandsProcessed: session.commandsProcessed,
          sessionDuration: Date.now() - session.startTime.getTime(),
          errorCount: 0
        });
      }
    });

    // Подписка на команды
    const commandSubscription = commandService.commandExecuted$.subscribe(command => {
      if (command) {
        addVoiceEvent({
          type: 'command_executed',
          sessionId: 'current',
          agentType: command.agent,
          data: command,
          timestamp: new Date()
        });
      }
    });

    // Обновление статистики
    const statsInterval = setInterval(() => {
      setVoiceStats(voiceService.getVoiceStatistics());
    }, 5000);

    return () => {
      eventSubscription.unsubscribe();
      sessionSubscription.unsubscribe();
      commandSubscription.unsubscribe();
      clearInterval(statsInterval);
    };
  }, [voiceService, commandService]);

  const addVoiceEvent = (event: any) => {
    const newEvent = {
      id: `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: event.type,
      message: getEventMessage(event),
      timestamp: event.timestamp,
      agent: event.agentType
    };

    setRecentEvents(prev => {
      const updated = [newEvent, ...prev];
      return updated.slice(0, 20); // Оставляем только последние 20 событий
    });
  };

  const getEventMessage = (event: any): string => {
    switch (event.type) {
      case 'session_started':
        return `Начата голосовая сессия для ${getAgentDisplayName(event.agentType)}`;
      case 'session_ended':
        return `Завершена голосовая сессия для ${getAgentDisplayName(event.agentType)}`;
      case 'command_received':
        return `Получена команда: ${event.data?.text || 'Неизвестная команда'}`;
      case 'command_executed':
        return `Выполнена команда: ${event.data?.command || 'Неизвестная команда'}`;
      case 'speech_recognized':
        return `Распознана речь: ${event.data?.transcript || 'Неизвестный текст'}`;
      case 'tts_started':
        return 'Начат синтез речи';
      case 'tts_completed':
        return 'Завершен синтез речи';
      case 'error':
        return `Ошибка: ${event.data?.error || 'Неизвестная ошибка'}`;
      default:
        return `Событие: ${event.type}`;
    }
  };

  const getAgentDisplayName = (agentType: string): string => {
    const agent = availableAgents.find(a => a.id === agentType);
    return agent ? agent.name : agentType;
  };

  const formatDuration = (milliseconds: number): string => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}ч ${minutes % 60}м`;
    }
    return `${minutes}м ${seconds % 60}с`;
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'session_started':
      case 'session_ended':
        return <Mic className="h-4 w-4" />;
      case 'command_received':
      case 'command_executed':
        return <Command className="h-4 w-4" />;
      case 'speech_recognized':
        return <Keyboard className="h-4 w-4" />;
      case 'tts_started':
      case 'tts_completed':
        return <Volume2 className="h-4 w-4" />;
      case 'error':
        return <Activity className="h-4 w-4 text-destructive" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getEventColor = (type: string): string => {
    switch (type) {
      case 'session_started':
        return 'bg-green-500';
      case 'session_ended':
        return 'bg-gray-500';
      case 'command_received':
        return 'bg-blue-500';
      case 'command_executed':
        return 'bg-green-600';
      case 'speech_recognized':
        return 'bg-purple-500';
      case 'tts_started':
      case 'tts_completed':
        return 'bg-orange-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div className="voice-commands-page space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Mic className="h-8 w-8" />
            Голосовые команды
          </h1>
          <p className="text-muted-foreground mt-2">
            Полное управление агентной системой с помощью голосовых команд
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isActive ? "default" : "secondary"} className="text-sm">
            <Activity className="h-3 w-3 mr-1" />
            {isActive ? 'Система активна' : 'Система неактивна'}
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Обзор</TabsTrigger>
          <TabsTrigger value="control">Управление</TabsTrigger>
          <TabsTrigger value="commands">Команды</TabsTrigger>
          <TabsTrigger value="recognition">Распознавание</TabsTrigger>
          <TabsTrigger value="settings">Настройки</TabsTrigger>
        </TabsList>

        {/* Обзор */}
        <TabsContent value="overview" className="space-y-6">
          {/* Статистика */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-muted-foreground" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Всего сессий</p>
                    <p className="text-2xl font-bold">{voiceStats.totalSessions}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Activity className="h-8 w-8 text-muted-foreground" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Активных сессий</p>
                    <p className="text-2xl font-bold">{voiceStats.activeSessions}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Command className="h-8 w-8 text-muted-foreground" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Выполнено команд</p>
                    <p className="text-2xl font-bold">{voiceStats.commandsExecuted}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <BarChart3 className="h-8 w-8 text-muted-foreground" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Средняя длительность</p>
                    <p className="text-2xl font-bold">
                      {formatDuration(voiceStats.averageSessionDuration)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Агенты */}
          <Card>
            <CardHeader>
              <CardTitle>Доступные агенты</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {availableAgents.map(agent => (
                  <Card 
                    key={agent.id} 
                    className={`cursor-pointer transition-colors ${
                      currentAgent === agent.id ? 'ring-2 ring-primary' : ''
                    }`}
                    onClick={() => setCurrentAgent(agent.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{agent.icon}</span>
                        <div className="flex-1">
                          <h3 className="font-semibold">{agent.name}</h3>
                          <p className="text-sm text-muted-foreground">{agent.description}</p>
                        </div>
                        <Badge variant={currentAgent === agent.id ? "default" : "outline"}>
                          {currentAgent === agent.id ? 'Выбран' : 'Доступен'}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Последние события */}
          <Card>
            <CardHeader>
              <CardTitle>Последние события</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentEvents.length > 0 ? (
                  recentEvents.map(event => (
                    <div key={event.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getEventColor(event.type)}`}>
                        {getEventIcon(event.type)}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">{event.message}</p>
                        <div className="flex items-center gap-2 mt-1">
                          {event.agent && (
                            <Badge variant="outline" className="text-xs">
                              {getAgentDisplayName(event.agent)}
                            </Badge>
                          )}
                          <span className="text-xs text-muted-foreground">
                            {event.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-4">
                    Нет событий для отображения
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Управление */}
        <TabsContent value="control">
          <VoiceControlView
            agentType={currentAgent}
            userId={userId}
            voiceService={voiceService}
            speechService={speechService}
            ttsService={ttsService}
          />
        </TabsContent>

        {/* Команды */}
        <TabsContent value="commands">
          <VoiceCommandPanel commandService={commandService} agentFilter={currentAgent} />
        </TabsContent>

        {/* Распознавание */}
        <TabsContent value="recognition">
          <SpeechRecognitionView
            speechService={speechService}
            onCommandProcessed={(command) => {
              console.log('Команда обработана:', command);
            }}
          />
        </TabsContent>

        {/* Настройки */}
        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Общие настройки
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Голосовая обратная связь</label>
                  <p className="text-xs text-muted-foreground">
                    Озвучивать результаты и статусы
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => voiceService.updateConfig({ voiceFeedback: true })}
                >
                  Включено
                </Button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Автоматическое выполнение</label>
                  <p className="text-xs text-muted-foreground">
                    Выполнять команды без подтверждения
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => voiceService.updateConfig({ autoExecuteCommands: false })}
                >
                  Отключено
                </Button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Непрерывное прослушивание</label>
                  <p className="text-xs text-muted-foreground">
                    Постоянное ожидание команд
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => voiceService.updateConfig({ continuousListening: true })}
                >
                  Включено
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Информация о системе</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Поддержка распознавания речи</p>
                  <Badge variant="default">Доступно</Badge>
                </div>
                <div>
                  <p className="text-sm font-medium">Поддержка синтеза речи</p>
                  <Badge variant="default">Доступно</Badge>
                </div>
                <div>
                  <p className="text-sm font-medium">Язык по умолчанию</p>
                  <Badge variant="outline">ru-RU</Badge>
                </div>
                <div>
                  <p className="text-sm font-medium">Версия API</p>
                  <Badge variant="outline">Web Speech API</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VoiceCommandsPage;