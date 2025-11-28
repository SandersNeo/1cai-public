import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Mic, MicOff, Volume2, VolumeX, Settings, Play, Pause, Square } from 'lucide-react';
import { VoiceIntegrationService, VoiceSession } from '@/services/voice-integration-service';
import { SpeechRecognitionService } from '@/services/speech-recognition-service';
import { TextToSpeechService } from '@/services/text-to-speech-service';

interface VoiceControlViewProps {
  agentType: string;
  userId: string;
  voiceService: VoiceIntegrationService;
  speechService: SpeechRecognitionService;
  ttsService: TextToSpeechService;
}

interface VoiceSettings {
  language: string;
  rate: number;
  pitch: number;
  volume: number;
  autoExecute: boolean;
  voiceFeedback: boolean;
}

const VoiceControlView: React.FC<VoiceControlViewProps> = ({
  agentType,
  userId,
  voiceService,
  speechService,
  ttsService
}) => {
  const [currentSession, setCurrentSession] = useState<VoiceSession | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [settings, setSettings] = useState<VoiceSettings>({
    language: 'ru-RU',
    rate: 1.0,
    pitch: 1.0,
    volume: 1.0,
    autoExecute: false,
    voiceFeedback: true
  });

  const [lastCommand, setLastCommand] = useState<string>('');
  const [sessionStats, setSessionStats] = useState({
    commandsProcessed: 0,
    sessionDuration: 0,
    errorCount: 0
  });

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Подписка на сессию
    const sessionSubscription = voiceService.session$.subscribe(session => {
      setCurrentSession(session);
    });

    // Подписка на состояние прослушивания
    const listeningSubscription = speechService.listeningState$.subscribe(listening => {
      setIsListening(listening);
    });

    // Подписка на состояние синтеза речи
    const speakingSubscription = ttsService.processingState$.subscribe(processing => {
      setIsSpeaking(processing);
    });

    return () => {
      sessionSubscription.unsubscribe();
      listeningSubscription.unsubscribe();
      speakingSubscription.unsubscribe();
    };
  }, [voiceService, speechService, ttsService]);

  useEffect(() => {
    // Обновление статистики сессии
    if (currentSession) {
      timerRef.current = setInterval(() => {
        setSessionStats({
          commandsProcessed: currentSession.commandsProcessed,
          sessionDuration: Date.now() - currentSession.startTime.getTime(),
          errorCount: 0 // Можно добавить счетчик ошибок
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [currentSession]);

  const startVoiceSession = async () => {
    try {
      await voiceService.startVoiceSession(agentType, userId);
    } catch (error) {
      console.error('Ошибка запуска голосовой сессии:', error);
    }
  };

  const endVoiceSession = async () => {
    if (currentSession) {
      try {
        await voiceService.endVoiceSession(currentSession.id);
      } catch (error) {
        console.error('Ошибка завершения голосовой сессии:', error);
      }
    }
  };

  const toggleListening = async () => {
    if (isListening) {
      speechService.stopListening();
    } else {
      try {
        await speechService.startListening();
      } catch (error) {
        console.error('Ошибка запуска распознавания речи:', error);
      }
    }
  };

  const testVoice = async () => {
    const testText = `Тестирование голосового управления для ${getAgentDisplayName(agentType)}`;
    try {
      await ttsService.speak(testText, {
        lang: settings.language,
        rate: settings.rate,
        pitch: settings.pitch,
        volume: settings.volume
      });
    } catch (error) {
      console.error('Ошибка тестирования голоса:', error);
    }
  };

  const updateSettings = (newSettings: Partial<VoiceSettings>) => {
    const updated = { ...settings, ...newSettings };
    setSettings(updated);

    // Применяем настройки к сервисам
    speechService.updateConfig({ language: updated.language });
    ttsService.updateConfig({
      rate: updated.rate,
      pitch: updated.pitch,
      volume: updated.volume,
      lang: updated.language
    });

    // Обновляем конфигурацию voice service
    voiceService.updateConfig({
      enableTextToSpeech: updated.voiceFeedback,
      autoExecuteCommands: updated.autoExecute,
      defaultLanguage: updated.language
    });
  };

  const formatDuration = (milliseconds: number): string => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
    }
    return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
  };

  const getAgentDisplayName = (agentType: string): string => {
    const names: { [key: string]: string } = {
      'architect': 'Архитектора',
      'developer': 'Разработчика',
      'pm': 'Менеджера проектов',
      'ba': 'Бизнес-аналитика',
      'data_analyst': 'Аналитика данных'
    };
    return names[agentType] || agentType;
  };

  return (
    <div className="voice-control-container space-y-6">
      {/* Основное управление */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="h-5 w-5" />
            Голосовое управление: {getAgentDisplayName(agentType)}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Статус сессии */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant={currentSession?.isActive ? "default" : "secondary"}>
                {currentSession?.isActive ? "Активна" : "Неактивна"}
              </Badge>
              {isListening && (
                <Badge variant="destructive" className="animate-pulse">
                  <Mic className="h-3 w-3 mr-1" />
                  Слушаю
                </Badge>
              )}
              {isSpeaking && (
                <Badge variant="default" className="animate-pulse">
                  <Volume2 className="h-3 w-3 mr-1" />
                  Говорю
                </Badge>
              )}
            </div>
            
            <div className="flex gap-2">
              {currentSession?.isActive ? (
                <Button onClick={endVoiceSession} variant="destructive">
                  <Square className="h-4 w-4 mr-2" />
                  Завершить
                </Button>
              ) : (
                <Button onClick={startVoiceSession} variant="default">
                  <Play className="h-4 w-4 mr-2" />
                  Начать
                </Button>
              )}
            </div>
          </div>

          {/* Управление прослушиванием */}
          {currentSession?.isActive && (
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Распознавание речи:</span>
                <Switch
                  checked={isListening}
                  onCheckedChange={toggleListening}
                />
              </div>
              <Button
                size="sm"
                variant={isListening ? "destructive" : "default"}
                onClick={toggleListening}
              >
                {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
            </div>
          )}

          {/* Статистика сессии */}
          {currentSession?.isActive && (
            <div className="grid grid-cols-3 gap-4 p-3 bg-muted rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold">{sessionStats.commandsProcessed}</div>
                <div className="text-xs text-muted-foreground">Команды</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{formatDuration(sessionStats.sessionDuration)}</div>
                <div className="text-xs text-muted-foreground">Время сессии</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{sessionStats.errorCount}</div>
                <div className="text-xs text-muted-foreground">Ошибки</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Настройки голоса */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Настройки голоса
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Язык */}
          <div>
            <label className="text-sm font-medium mb-2 block">Язык распознавания</label>
            <Select
              value={settings.language}
              onValueChange={(value) => updateSettings({ language: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ru-RU">Русский (ru-RU)</SelectItem>
                <SelectItem value="en-US">English (US)</SelectItem>
                <SelectItem value="en-GB">English (UK)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Скорость речи */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Скорость речи: {settings.rate.toFixed(1)}
            </label>
            <Slider
              value={[settings.rate]}
              onValueChange={([value]) => updateSettings({ rate: value })}
              min={0.5}
              max={2.0}
              step={0.1}
              className="w-full"
            />
          </div>

          {/* Высота тона */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Высота тона: {settings.pitch.toFixed(1)}
            </label>
            <Slider
              value={[settings.pitch]}
              onValueChange={([value]) => updateSettings({ pitch: value })}
              min={0.5}
              max={2.0}
              step={0.1}
              className="w-full"
            />
          </div>

          {/* Громкость */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Громкость: {Math.round(settings.volume * 100)}%
            </label>
            <Slider
              value={[settings.volume]}
              onValueChange={([value]) => updateSettings({ volume: value })}
              min={0.0}
              max={1.0}
              step={0.1}
              className="w-full"
            />
          </div>

          {/* Автоматическое выполнение команд */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">Автоматическое выполнение команд</label>
              <p className="text-xs text-muted-foreground">
                Выполнять команды без подтверждения
              </p>
            </div>
            <Switch
              checked={settings.autoExecute}
              onCheckedChange={(checked) => updateSettings({ autoExecute: checked })}
            />
          </div>

          {/* Голосовая обратная связь */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">Голосовая обратная связь</label>
              <p className="text-xs text-muted-foreground">
                Озвучивать результаты команд
              </p>
            </div>
            <Switch
              checked={settings.voiceFeedback}
              onCheckedChange={(checked) => updateSettings({ voiceFeedback: checked })}
            />
          </div>

          {/* Тест голоса */}
          <Button onClick={testVoice} variant="outline" className="w-full">
            <Volume2 className="h-4 w-4 mr-2" />
            Тестировать голос
          </Button>
        </CardContent>
      </Card>

      {/* Последняя команда */}
      {lastCommand && (
        <Card>
          <CardHeader>
            <CardTitle>Последняя команда</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm">{lastCommand}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {new Date().toLocaleTimeString()}
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default VoiceControlView;