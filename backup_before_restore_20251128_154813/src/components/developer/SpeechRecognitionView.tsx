import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Activity,
  Settings,
  Waves,
  Keyboard,
  RotateCcw
} from 'lucide-react';
import { SpeechRecognitionService, SpeechRecognitionEvent, SpeechCommand } from '@/services/speech-recognition-service';

interface SpeechRecognitionViewProps {
  speechService: SpeechRecognitionService;
  onCommandProcessed?: (command: SpeechCommand) => void;
}

interface RecognitionStats {
  totalRecognitions: number;
  successfulCommands: number;
  averageConfidence: number;
  lastRecognition: Date | null;
  errorsCount: number;
}

const SpeechRecognitionView: React.FC<SpeechRecognitionViewProps> = ({
  speechService,
  onCommandProcessed
}) => {
  const [isListening, setIsListening] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [recentCommands, setRecentCommands] = useState<SpeechCommand[]>([]);
  const [stats, setStats] = useState<RecognitionStats>({
    totalRecognitions: 0,
    successfulCommands: 0,
    averageConfidence: 0,
    lastRecognition: null,
    errorsCount: 0
  });

  const [config, setConfig] = useState({
    language: 'ru-RU',
    continuous: true,
    interimResults: true,
    maxAlternatives: 3
  });

  const [audioLevel, setAudioLevel] = useState(0);
  const [isSupported, setIsSupported] = useState(false);
  const levelTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Проверка поддержки API
    const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);

    // Подписка на события
    const speechEventSubscription = speechService.speechEvent$.subscribe(event => {
      if (event) {
        handleSpeechEvent(event);
      }
    });

    const commandSubscription = speechService.command$.subscribe(command => {
      if (command) {
        handleCommand(command);
      }
    });

    const listeningStateSubscription = speechService.listeningState$.subscribe(listening => {
      setIsListening(listening);
    });

    // Загрузка конфигурации
    const currentConfig = speechService.getCurrentConfig();
    setConfig(currentConfig);

    return () => {
      speechEventSubscription.unsubscribe();
      commandSubscription.unsubscribe();
      listeningStateSubscription.unsubscribe();
      if (levelTimerRef.current) {
        clearInterval(levelTimerRef.current);
      }
    };
  }, [speechService]);

  const handleSpeechEvent = (event: SpeechRecognitionEvent) => {
    switch (event.type) {
      case 'result':
        if (event.transcript) {
          if (event.transcript.includes('[промежуточный]')) {
            setInterimTranscript(event.transcript.replace('[промежуточный] ', ''));
          } else {
            setCurrentTranscript(event.transcript);
            setInterimTranscript('');
          }
        }
        break;
      
      case 'start':
        startAudioLevelMonitoring();
        break;
      
      case 'end':
        stopAudioLevelMonitoring();
        setInterimTranscript('');
        break;
      
      case 'error':
        setStats(prev => ({
          ...prev,
          errorsCount: prev.errorsCount + 1
        }));
        setCurrentTranscript('');
        setInterimTranscript('');
        break;
      
      case 'nomatch':
        console.log('Речь не распознана');
        break;
    }
  };

  const handleCommand = (command: SpeechCommand) => {
    setRecentCommands(prev => {
      const updated = [command, ...prev];
      return updated.slice(0, 10); // Оставляем только последние 10 команд
    });

    setStats(prev => ({
      totalRecognitions: prev.totalRecognitions + 1,
      successfulCommands: prev.successfulCommands + 1,
      averageConfidence: prev.averageConfidence > 0 
        ? (prev.averageConfidence + command.confidence) / 2 
        : command.confidence,
      lastRecognition: command.timestamp,
      errorsCount: prev.errorsCount
    }));

    if (onCommandProcessed) {
      onCommandProcessed(command);
    }
  };

  const startListening = async () => {
    try {
      await speechService.startListening();
    } catch (error) {
      console.error('Ошибка запуска распознавания речи:', error);
    }
  };

  const stopListening = () => {
    speechService.stopListening();
  };

  const startAudioLevelMonitoring = () => {
    levelTimerRef.current = setInterval(() => {
      // Симуляция уровня аудио (в реальном приложении здесь был бы анализ аудио потока)
      setAudioLevel(Math.random() * 100);
    }, 100);
  };

  const stopAudioLevelMonitoring = () => {
    if (levelTimerRef.current) {
      clearInterval(levelTimerRef.current);
      levelTimerRef.current = null;
    }
    setAudioLevel(0);
  };

  const updateConfig = (newConfig: Partial<typeof config>) => {
    const updated = { ...config, ...newConfig };
    setConfig(updated);
    speechService.updateConfig(updated);
  };

  const clearTranscripts = () => {
    setCurrentTranscript('');
    setInterimTranscript('');
  };

  const resetStats = () => {
    setStats({
      totalRecognitions: 0,
      successfulCommands: 0,
      averageConfidence: 0,
      lastRecognition: null,
      errorsCount: 0
    });
    setRecentCommands([]);
  };

  const availableLanguages = speechService.getSupportedLanguages();

  if (!isSupported) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <MicOff className="h-5 w-5" />
            Распознавание речи недоступно
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Ваш браузер не поддерживает Web Speech API. Попробуйте использовать Chrome, Edge или Safari.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="speech-recognition-container space-y-6">
      {/* Основное управление */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5" />
            Распознавание речи
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Кнопки управления */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              {isListening ? (
                <Button onClick={stopListening} variant="destructive">
                  <MicOff className="h-4 w-4 mr-2" />
                  Остановить
                </Button>
              ) : (
                <Button onClick={startListening}>
                  <Mic className="h-4 w-4 mr-2" />
                  Начать прослушивание
                </Button>
              )}
              
              <Button variant="outline" onClick={clearTranscripts}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Очистить
              </Button>
            </div>

            <Badge variant={isListening ? "default" : "secondary"} className="animate-pulse">
              <Activity className="h-3 w-3 mr-1" />
              {isListening ? 'Активно' : 'Неактивно'}
            </Badge>
          </div>

          {/* Визуализация аудио уровня */}
          {isListening && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Volume2 className="h-4 w-4" />
                <span className="text-sm">Уровень звука</span>
              </div>
              <Progress value={audioLevel} className="w-full" />
            </div>
          )}

          {/* Текущий транскрипт */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Текущий текст:</label>
            <div className="min-h-[3rem] p-3 border rounded-lg bg-muted">
              {currentTranscript ? (
                <p className="text-sm">{currentTranscript}</p>
              ) : interimTranscript ? (
                <p className="text-sm text-muted-foreground italic">{interimTranscript}</p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {isListening ? 'Слушаю...' : 'Нажмите "Начать прослушивание" для начала записи'}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Настройки распознавания */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Настройки распознавания
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Язык */}
          <div>
            <label className="text-sm font-medium mb-2 block">Язык распознавания</label>
            <Select
              value={config.language}
              onValueChange={(value) => updateConfig({ language: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableLanguages.map(lang => (
                  <SelectItem key={lang} value={lang}>{lang}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Непрерывное распознавание */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">Непрерывное распознавание</label>
              <p className="text-xs text-muted-foreground">
                Продолжать распознавание после завершения фразы
              </p>
            </div>
            <Button
              variant={config.continuous ? "default" : "outline"}
              size="sm"
              onClick={() => updateConfig({ continuous: !config.continuous })}
            >
              {config.continuous ? 'Включено' : 'Выключено'}
            </Button>
          </div>

          {/* Промежуточные результаты */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">Промежуточные результаты</label>
              <p className="text-xs text-muted-foreground">
                Показывать результаты во время речи
              </p>
            </div>
            <Button
              variant={config.interimResults ? "default" : "outline"}
              size="sm"
              onClick={() => updateConfig({ interimResults: !config.interimResults })}
            >
              {config.interimResults ? 'Включено' : 'Выключено'}
            </Button>
          </div>

          {/* Количество альтернатив */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Количество альтернатив: {config.maxAlternatives}
            </label>
            <Slider
              value={[config.maxAlternatives]}
              onValueChange={([value]) => updateConfig({ maxAlternatives: value })}
              min={1}
              max={5}
              step={1}
              className="w-full"
            />
          </div>
        </CardContent>
      </Card>

      {/* Статистика */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Waves className="h-5 w-5" />
              Статистика распознавания
            </CardTitle>
            <Button variant="outline" size="sm" onClick={resetStats}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Сброс
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.totalRecognitions}</div>
              <div className="text-xs text-muted-foreground">Всего распознано</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.successfulCommands}</div>
              <div className="text-xs text-muted-foreground">Команды</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {stats.averageConfidence > 0 ? `${Math.round(stats.averageConfidence * 100)}%` : '0%'}
              </div>
              <div className="text-xs text-muted-foreground">Средняя точность</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.errorsCount}</div>
              <div className="text-xs text-muted-foreground">Ошибки</div>
            </div>
          </div>
          
          {stats.lastRecognition && (
            <div className="mt-4 text-center">
              <p className="text-sm text-muted-foreground">
                Последнее распознавание: {stats.lastRecognition.toLocaleTimeString()}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Последние команды */}
      {recentCommands.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Последние команды</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentCommands.map((command, index) => (
                <div key={`${command.timestamp.getTime()}-${index}`} className="flex items-center justify-between p-2 border rounded">
                  <div className="flex-1">
                    <p className="text-sm font-medium">{command.text}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        Точность: {Math.round(command.confidence * 100)}%
                      </Badge>
                      {command.agent && (
                        <Badge variant="secondary" className="text-xs">
                          {command.agent}
                        </Badge>
                      )}
                      {command.command && (
                        <Badge variant="default" className="text-xs">
                          {command.command}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {command.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SpeechRecognitionView;