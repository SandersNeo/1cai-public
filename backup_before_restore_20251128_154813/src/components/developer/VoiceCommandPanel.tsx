import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Command, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Mic, 
  Volume2, 
  Settings,
  HelpCircle,
  Zap
} from 'lucide-react';
import { VoiceCommandProcessorService, VoiceCommandRule, ProcessedCommand } from '@/services/voice-command-processor-service';

interface VoiceCommandPanelProps {
  commandService: VoiceCommandProcessorService;
  agentFilter?: string;
}

const VoiceCommandPanel: React.FC<VoiceCommandPanelProps> = ({
  commandService,
  agentFilter
}) => {
  const [rules, setRules] = useState<VoiceCommandRule[]>([]);
  const [commandHistory, setCommandHistory] = useState<ProcessedCommand[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>(agentFilter || 'all');
  const [searchTerm, setSearchTerm] = useState('');
  const [editingRule, setEditingRule] = useState<VoiceCommandRule | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

  // Новые правила
  const [newRule, setNewRule] = useState<Partial<VoiceCommandRule>>({
    trigger: '',
    command: '',
    agent: selectedAgent !== 'all' ? selectedAgent : undefined,
    parameters: [],
    priority: 1,
    enabled: true,
    description: '',
    examples: []
  });

  useEffect(() => {
    // Загрузка правил
    const rulesSubscription = commandService.history$.subscribe(() => {
      loadRules();
      loadHistory();
    });

    // Первоначальная загрузка
    loadRules();
    loadHistory();

    return () => {
      rulesSubscription.unsubscribe();
    };
  }, [commandService, selectedAgent]);

  const loadRules = () => {
    const allRules = commandService.getRules();
    const filtered = selectedAgent === 'all' 
      ? allRules 
      : allRules.filter(rule => rule.agent === selectedAgent || !rule.agent);
    setRules(filtered);
  };

  const loadHistory = () => {
    const history = commandService.getCommandHistory(50);
    const filtered = selectedAgent === 'all'
      ? history
      : history.filter(cmd => cmd.agent === selectedAgent);
    setCommandHistory(filtered);
  };

  const filteredRules = rules.filter(rule => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return rule.command.toLowerCase().includes(search) ||
             rule.description?.toLowerCase().includes(search) ||
             rule.trigger.toString().toLowerCase().includes(search);
    }
    return true;
  });

  const addRule = () => {
    if (!newRule.trigger || !newRule.command) {
      alert('Заполните обязательные поля');
      return;
    }

    try {
      const rule: VoiceCommandRule = {
        id: `rule_${Date.now()}`,
        trigger: new RegExp(newRule.trigger!, 'i'),
        command: newRule.command!,
        agent: newRule.agent,
        parameters: newRule.parameters || [],
        priority: newRule.priority || 1,
        enabled: newRule.enabled ?? true,
        description: newRule.description,
        examples: newRule.examples || []
      };

      commandService.addRule(rule);
      setNewRule({
        trigger: '',
        command: '',
        agent: selectedAgent !== 'all' ? selectedAgent : undefined,
        parameters: [],
        priority: 1,
        enabled: true,
        description: '',
        examples: []
      });
      setIsAddDialogOpen(false);
      loadRules();
    } catch (error) {
      alert(`Ошибка добавления правила: ${error}`);
    }
  };

  const updateRule = (ruleId: string, updates: Partial<VoiceCommandRule>) => {
    try {
      commandService.updateRule(ruleId, updates);
      loadRules();
      setEditingRule(null);
    } catch (error) {
      alert(`Ошибка обновления правила: ${error}`);
    }
  };

  const removeRule = (ruleId: string) => {
    if (confirm('Удалить это правило?')) {
      commandService.removeRule(ruleId);
      loadRules();
    }
  };

  const toggleRule = (ruleId: string, enabled: boolean) => {
    updateRule(ruleId, { enabled });
  };

  const testCommand = async (rule: VoiceCommandRule) => {
    // Симуляция тестовой команды
    const testText = rule.examples?.[0] || 'тестовая команда';
    alert(`Тестирование команды: "${testText}"`);
  };

  const getAgentDisplayName = (agentType?: string): string => {
    if (!agentType) return 'Универсальная';
    
    const names: { [key: string]: string } = {
      'architect': 'Архитектор',
      'developer': 'Разработчик',
      'pm': 'Менеджер проектов',
      'ba': 'Бизнес-аналитик',
      'data_analyst': 'Аналитик данных'
    };
    return names[agentType] || agentType;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      case 'executing': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="voice-command-panel space-y-6">
      {/* Заголовок с управлением */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Command className="h-5 w-5" />
              Панель голосовых команд
            </CardTitle>
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Добавить команду
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Новая голосовая команда</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Регулярное выражение (обязательно)
                    </label>
                    <Input
                      placeholder="например: создай задачу (.*)"
                      value={newRule.trigger}
                      onChange={(e) => setNewRule({...newRule, trigger: e.target.value})}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Команда (обязательно)
                    </label>
                    <Input
                      placeholder="например: create_task"
                      value={newRule.command}
                      onChange={(e) => setNewRule({...newRule, command: e.target.value})}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Агент</label>
                    <Select
                      value={newRule.agent || 'all'}
                      onValueChange={(value) => setNewRule({...newRule, agent: value === 'all' ? undefined : value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Универсальная</SelectItem>
                        <SelectItem value="architect">Архитектор</SelectItem>
                        <SelectItem value="developer">Разработчик</SelectItem>
                        <SelectItem value="pm">Менеджер проектов</SelectItem>
                        <SelectItem value="ba">Бизнес-аналитик</SelectItem>
                        <SelectItem value="data_analyst">Аналитик данных</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Описание</label>
                    <Textarea
                      placeholder="Описание команды"
                      value={newRule.description}
                      onChange={(e) => setNewRule({...newRule, description: e.target.value})}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Примеры (через запятую)</label>
                    <Input
                      placeholder="создай задачу, добавь задание"
                      value={(newRule.examples || []).join(', ')}
                      onChange={(e) => setNewRule({
                        ...newRule, 
                        examples: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                      })}
                    />
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                      Отмена
                    </Button>
                    <Button onClick={addRule}>
                      Добавить
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Input
                placeholder="Поиск команд..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={selectedAgent} onValueChange={setSelectedAgent}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все агенты</SelectItem>
                <SelectItem value="architect">Архитектор</SelectItem>
                <SelectItem value="developer">Разработчик</SelectItem>
                <SelectItem value="pm">Менеджер проектов</SelectItem>
                <SelectItem value="ba">Бизнес-аналитик</SelectItem>
                <SelectItem value="data_analyst">Аналитик данных</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Список команд */}
      <Card>
        <CardHeader>
          <CardTitle>Доступные команды ({filteredRules.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredRules.map(rule => (
              <div key={rule.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline">{getAgentDisplayName(rule.agent)}</Badge>
                    <Badge variant={rule.enabled ? "default" : "secondary"}>
                      {rule.enabled ? 'Активна' : 'Отключена'}
                    </Badge>
                    <Badge variant="outline">
                      Приоритет: {rule.priority}
                    </Badge>
                  </div>
                  <div className="font-mono text-sm text-muted-foreground mb-1">
                    {rule.trigger.toString()}
                  </div>
                  <div className="text-sm">{rule.description}</div>
                  {rule.examples && rule.examples.length > 0 && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Примеры: {rule.examples.join(', ')}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => testCommand(rule)}
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingRule(rule)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toggleRule(rule.id, !rule.enabled)}
                  >
                    <Switch checked={rule.enabled} />
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => removeRule(rule.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* История команд */}
      <Card>
        <CardHeader>
          <CardTitle>Последние команды ({commandHistory.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {commandHistory.map(command => (
              <div key={command.id} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(command.status)}`} />
                  <span className="text-sm font-medium">{command.command}</span>
                  {command.agent && (
                    <Badge variant="outline" className="text-xs">
                      {getAgentDisplayName(command.agent)}
                    </Badge>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  {command.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Диалог редактирования */}
      {editingRule && (
        <Dialog open={!!editingRule} onOpenChange={() => setEditingRule(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Редактирование команды</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Описание</label>
                <Textarea
                  value={editingRule.description || ''}
                  onChange={(e) => setEditingRule({
                    ...editingRule,
                    description: e.target.value
                  })}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Приоритет</label>
                <Input
                  type="number"
                  value={editingRule.priority}
                  onChange={(e) => setEditingRule({
                    ...editingRule,
                    priority: parseInt(e.target.value) || 1
                  })}
                  min="1"
                  max="10"
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Включена</label>
                <Switch
                  checked={editingRule.enabled}
                  onCheckedChange={(checked) => setEditingRule({
                    ...editingRule,
                    enabled: checked
                  })}
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingRule(null)}>
                  Отмена
                </Button>
                <Button onClick={() => updateRule(editingRule.id, editingRule)}>
                  Сохранить
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default VoiceCommandPanel;