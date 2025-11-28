/**
 * Компонент интеграции с системами управления задачами
 * Обеспечивает подключение, настройку и мониторинг интеграций
 * с Jira, Trello, GitHub, Azure DevOps и другими системами
 */

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Link, 
  Settings, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Clock,
  GitBranch,
  ExternalLink,
  Plus,
  Edit,
  Trash2,
  Play,
  Pause,
  Download,
  Upload,
  Eye,
  EyeOff,
  Filter,
  Search
} from 'lucide-react';
import { 
  TaskManagementSystem,
  ExternalTask,
  SyncResult,
  IntegrationMetrics,
  SystemStatus,
  ConflictResolution
} from '../../services/task-management-integration-service';

interface ProjectIntegrationProps {
  projectId: string;
  systems: TaskManagementSystem[];
  metrics: IntegrationMetrics | null;
  onSystemConnect?: (config: TaskManagementSystem) => void;
  onSystemDisconnect?: (systemId: string) => void;
  onSystemUpdate?: (systemId: string, updates: Partial<TaskManagementSystem>) => void;
  onSyncTasks?: (localSystemId: string, externalSystemId: string) => void;
  readOnly?: boolean;
  height?: number;
}

interface SystemCardProps {
  system: TaskManagementSystem;
  metrics: SystemStatus | null;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onEdit?: () => void;
  onSync?: () => void;
  onTestConnection?: () => void;
  readOnly?: boolean;
}

interface SyncModalProps {
  isOpen: boolean;
  systems: TaskManagementSystem[];
  onClose: () => void;
  onSync: (localSystemId: string, externalSystemId: string) => void;
}

const ProjectIntegrations: React.FC<ProjectIntegrationProps> = ({
  projectId,
  systems,
  metrics,
  onSystemConnect,
  onSystemDisconnect,
  onSystemUpdate,
  onSyncTasks,
  readOnly = false,
  height = 800
}) => {
  const [selectedSystemId, setSelectedSystemId] = useState<string | null>(null);
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [editingSystem, setEditingSystem] = useState<TaskManagementSystem | null>(null);
  const [syncStatus, setSyncStatus] = useState<Record<string, SyncResult>>({});
  const [activeTab, setActiveTab] = useState<'overview' | 'systems' | 'sync' | 'metrics'>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');

  // Фильтрация систем
  const filteredSystems = useMemo(() => {
    return systems.filter(system => {
      const matchesSearch = system.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           system.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = filterType === 'all' || system.type === filterType;
      
      return matchesSearch && matchesType;
    });
  }, [systems, searchQuery, filterType]);

  // Получение статуса системы
  const getSystemStatus = (systemId: string): SystemStatus | null => {
    return metrics?.systemsStatus && Array.isArray(metrics.systemsStatus) 
      ? metrics.systemsStatus.find(s => s?.systemId === systemId) || null 
      : null;
  };

  // Получение иконки для типа системы
  const getSystemIcon = (type: string) => {
    switch (type) {
      case 'jira': return '🟦';
      case 'trello': return '🟨';
      case 'github': return '⚫';
      case 'azure_devops': return '🔵';
      default: return '⚙️';
    }
  };

  // Получение цвета статуса
  const getStatusColor = (status: SystemStatus | null) => {
    if (!status) return 'gray';
    
    switch (status?.health) {
      case 'healthy': return 'green';
      case 'warning': return 'yellow';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  // Обработчик подключения системы
  const handleConnect = (config: TaskManagementSystem) => {
    onSystemConnect?.(config);
    setShowConnectionModal(false);
  };

  // Обработчик синхронизации
  const handleSync = (localSystemId: string, externalSystemId: string) => {
    onSyncTasks?.(localSystemId, externalSystemId);
    setShowSyncModal(false);
  };

  // Рендер карточки системы
  const renderSystemCard = (system: TaskManagementSystem) => {
    const status = getSystemStatus(system.id);
    const statusColor = getStatusColor(status);

    return (
      <div
        key={system.id}
        className={`bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow ${
          selectedSystemId === system.id ? 'ring-2 ring-blue-500' : ''
        }`}
      >
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{getSystemIcon(system.type)}</span>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{system.name}</h3>
                <p className="text-sm text-gray-600">{system.description}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {system.isActive ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <XCircle className="w-5 h-5 text-gray-400" />
              )}
              
              <div className={`w-3 h-3 rounded-full ${
                statusColor === 'green' ? 'bg-green-500' :
                statusColor === 'yellow' ? 'bg-yellow-500' :
                statusColor === 'red' ? 'bg-red-500' : 'bg-gray-400'
              }`} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <div className="text-sm text-gray-500">Тип системы</div>
              <div className="font-medium capitalize">{system.type.replace('_', ' ')}</div>
            </div>
            
            <div>
              <div className="text-sm text-gray-500">Последняя синхронизация</div>
              <div className="font-medium">
                {system?.lastSync && typeof system.lastSync === 'object' && 'toLocaleDateString' in system.lastSync ? (
                  <span className="text-sm">{system.lastSync.toLocaleDateString('ru-RU')}</span>
                ) : (
                  <span className="text-sm text-gray-400">Никогда</span>
                )}
              </div>
            </div>
            
            <div>
              <div className="text-sm text-gray-500">Статус синхронизации</div>
              <div className="flex items-center space-x-2">
                {system?.syncStatus === 'syncing' && <RefreshCw className="w-4 h-4 animate-spin" />}
                <span className={`text-sm font-medium ${
                  system?.syncStatus === 'syncing' ? 'text-blue-600' :
                  system?.syncStatus === 'success' ? 'text-green-600' :
                  system?.syncStatus === 'error' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {system?.syncStatus === 'syncing' ? 'Синхронизация...' :
                   system?.syncStatus === 'success' ? 'Успешно' :
                   system?.syncStatus === 'error' ? 'Ошибка' : 'Простой'}
                </span>
              </div>
            </div>
            
            <div>
              <div className="text-sm text-gray-500">URL</div>
              <div className="flex items-center space-x-1">
                <span className="text-sm font-mono truncate">{system.baseUrl}</span>
                <ExternalLink className="w-3 h-3 text-gray-400 flex-shrink-0" />
              </div>
            </div>
          </div>

          {status && status.lastError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <span className="text-sm text-red-700">Последняя ошибка: {status.lastError}</span>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              {status && (
                <>
                  <span>Успешность: {status?.syncSuccessRate || 0}%</span>
                  <span>Ошибки: {status?.errorCount || 0}</span>
                  <span>Предупреждения: {status?.warningCount || 0}</span>
                </>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {!readOnly && (
                <>
                  <button
                    onClick={() => {
                      setEditingSystem(system);
                      setShowSettingsModal(true);
                    }}
                    className="p-2 text-gray-400 hover:text-blue-600 rounded"
                    title="Настройки"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => onSystemDisconnect?.(system.id)}
                    className="p-2 text-gray-400 hover:text-red-600 rounded"
                    title="Отключить"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => setShowSyncModal(true)}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200"
                    disabled={!system.isActive}
                  >
                    Синхронизировать
                  </button>
                </>
              )}
              
              <button
                onClick={() => setSelectedSystemId(
                  selectedSystemId === system.id ? null : system.id
                )}
                className="p-2 text-gray-400 hover:text-gray-600 rounded"
                title={selectedSystemId === system.id ? 'Скрыть детали' : 'Показать детали'}
              >
                {selectedSystemId === system.id ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </div>
        
        {selectedSystemId === system.id && (
          <div className="border-t border-gray-200 bg-gray-50 p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">Настройки синхронизации</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Автосинхронизация:</span>
                    <span className={system?.settings?.autoSync ? 'text-green-600' : 'text-gray-600'}>
                      {system?.settings?.autoSync ? 'Включена' : 'Отключена'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Интервал:</span>
                    <span>{system?.settings?.syncInterval || 0} мин</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Webhooks:</span>
                    <span className={system?.settings?.webhookEnabled ? 'text-green-600' : 'text-gray-600'}>
                      {system?.settings?.webhookEnabled ? 'Включены' : 'Отключены'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Направление:</span>
                    <span>{system?.settings?.syncDirection === 'two-way' ? 'Двусторонняя' : 'Односторонняя'}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Маппинг полей</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Название:</span>
                    <span className="font-mono">{system?.settings?.fieldMapping?.summary || 'summary'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Описание:</span>
                    <span className="font-mono">{system?.settings?.fieldMapping?.description || 'description'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Исполнитель:</span>
                    <span className="font-mono">{system?.settings?.fieldMapping?.assignee || 'assignee'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Статус:</span>
                    <span className="font-mono">{system?.settings?.fieldMapping?.status || 'status'}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Рендер обзорной панели
  const renderOverview = () => {
    const activeSystems = systems.filter(s => s.isActive).length;
    const totalTasks = metrics?.totalTasksSynced || 0;
    const successRate = metrics?.systemsStatus && Array.isArray(metrics.systemsStatus) && metrics.systemsStatus.length > 0 
      ? (metrics.systemsStatus.reduce((sum, s) => sum + (s?.syncSuccessRate || 0), 0) || 0) / metrics.systemsStatus.length
      : 0;

    return (
      <div className="space-y-6">
        {/* Общая статистика */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">{activeSystems}</div>
                <div className="text-sm text-gray-500">Подключенных систем</div>
              </div>
              <Link className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">{totalTasks.toLocaleString()}</div>
                <div className="text-sm text-gray-500">Синхронизированных задач</div>
              </div>
              <GitBranch className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">{successRate.toFixed(1)}%</div>
                <div className="text-sm text-gray-500">Успешность синхронизации</div>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {metrics?.lastSyncDate && typeof metrics.lastSyncDate === 'object' && 'toLocaleDateString' in metrics.lastSyncDate 
                    ? metrics.lastSyncDate.toLocaleDateString('ru-RU') 
                    : 'Не было'
                  }
                </div>
                <div className="text-sm text-gray-500">Последняя синхронизация</div>
              </div>
              <Clock className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </div>

        {/* Состояние систем */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold">Состояние систем</h3>
          </div>
          
          <div className="p-6">
            {metrics?.systemsStatus && Array.isArray(metrics.systemsStatus) && metrics.systemsStatus.length > 0 ? (
              metrics.systemsStatus.map(status => (
                <div key={status?.systemId || Math.random()} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      status?.health === 'healthy' ? 'bg-green-500' :
                      status?.health === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <div>
                      <div className="font-medium">{status?.systemName || 'Неизвестная система'}</div>
                      <div className="text-sm text-gray-500">
                        {status?.isConnected ? 'Подключено' : 'Отключено'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>Успешность: {status?.syncSuccessRate || 0}%</span>
                    <span>Ошибки: {status?.errorCount || 0}</span>
                    {status?.lastSyncDate && typeof status.lastSyncDate === 'object' && 'toLocaleDateString' in status.lastSyncDate && (
                      <span>Последняя: {status.lastSyncDate.toLocaleDateString('ru-RU')}</span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                Нет данных о состоянии систем
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Рендер панели систем
  const renderSystems = () => {
    return (
      <div className="space-y-6">
        {/* Поиск и фильтры */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Поиск систем..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Все типы</option>
              <option value="jira">Jira</option>
              <option value="trello">Trello</option>
              <option value="github">GitHub</option>
              <option value="azure_devops">Azure DevOps</option>
            </select>
          </div>
          
          {!readOnly && (
            <button
              onClick={() => setShowConnectionModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              <span>Подключить систему</span>
            </button>
          )}
        </div>

        {/* Список систем */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredSystems.map(renderSystemCard)}
        </div>

        {filteredSystems.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            {searchQuery || filterType !== 'all' 
              ? 'Системы не найдены' 
              : 'Нет подключенных систем'
            }
          </div>
        )}
      </div>
    );
  };

  // Рендер панели синхронизации
  const renderSync = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">История синхронизации</h3>
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50">
              <Download className="w-4 h-4 inline mr-1" />
              Экспорт
            </button>
          </div>
          
          <div className="text-center text-gray-500 py-12">
            <RefreshCw className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>История синхронизации будет отображаться здесь</p>
          </div>
        </div>
      </div>
    );
  };

  // Рендер панели метрик
  const renderMetrics = () => {
    if (!metrics) {
      return (
        <div className="text-center text-gray-500 py-12">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>Метрики интеграции недоступны</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Общие метрики */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="text-2xl font-bold text-gray-900">{metrics?.totalSyncs || 0}</div>
            <div className="text-sm text-gray-500">Всего синхронизаций</div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="text-2xl font-bold text-green-600">{metrics?.successfulSyncs || 0}</div>
            <div className="text-sm text-gray-500">Успешных</div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="text-2xl font-bold text-red-600">{metrics?.failedSyncs || 0}</div>
            <div className="text-sm text-gray-500">Неудачных</div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="text-2xl font-bold text-blue-600">
              {((metrics?.averageSyncDuration || 0) / 1000).toFixed(1)}с
            </div>
            <div className="text-sm text-gray-500">Ср. время синхронизации</div>
          </div>
        </div>

        {/* Детальная статистика по системам */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold">Статистика по системам</h3>
          </div>
          
          <div className="p-6">
            {metrics.systemsStatus && Array.isArray(metrics.systemsStatus) ? (
              metrics.systemsStatus.map(system => (
                <div key={system?.systemId || Math.random()} className="flex items-center justify-between py-4 border-b border-gray-100 last:border-b-0">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      system?.health === 'healthy' ? 'bg-green-500' :
                      system?.health === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <div>
                      <div className="font-medium">{system?.systemName || 'Неизвестная система'}</div>
                      <div className="text-sm text-gray-500">
                        {system?.isConnected ? 'Подключено' : 'Отключено'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-6 text-sm">
                    <div className="text-center">
                      <div className="font-medium">{system?.syncSuccessRate || 0}%</div>
                      <div className="text-gray-500">Успешность</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="font-medium">{system?.errorCount || 0}</div>
                      <div className="text-gray-500">Ошибки</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="font-medium">{system?.warningCount || 0}</div>
                      <div className="text-gray-500">Предупреждения</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="font-medium">
                        {system?.lastSyncDate && typeof system.lastSyncDate === 'object' && 'toLocaleDateString' in system.lastSyncDate 
                          ? system.lastSyncDate.toLocaleDateString('ru-RU') 
                          : 'Никогда'
                        }
                      </div>
                      <div className="text-gray-500">Последняя</div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                Нет данных о системах
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Заголовок */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Интеграция с системами задач</h1>
            <p className="text-gray-600 mt-1">Подключение и синхронизация с Jira, Trello, GitHub и другими</p>
          </div>
          
          {metrics && (
            <div className="flex items-center space-x-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{metrics?.successfulSyncs || 0}</div>
                <div className="text-sm text-gray-500">Успешных синхронизаций</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{(metrics?.totalTasksSynced || 0).toLocaleString()}</div>
                <div className="text-sm text-gray-500">Задач синхронизировано</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Навигация */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6">
          <div className="flex space-x-8">
            {[
              { key: 'overview', label: 'Обзор', icon: Eye },
              { key: 'systems', label: 'Системы', icon: Link },
              { key: 'sync', label: 'Синхронизация', icon: RefreshCw },
              { key: 'metrics', label: 'Метрики', icon: Settings }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm ${
                    activeTab === tab.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Контент */}
      <div className="p-6" style={{ height: height - 120 }}>
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'systems' && renderSystems()}
        {activeTab === 'sync' && renderSync()}
        {activeTab === 'metrics' && renderMetrics()}
      </div>

      {/* Модальное окно подключения системы */}
      {showConnectionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Подключение системы</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Тип системы</label>
                <select className="w-full border border-gray-300 rounded px-3 py-2">
                  <option value="jira">Jira</option>
                  <option value="trello">Trello</option>
                  <option value="github">GitHub</option>
                  <option value="azure_devops">Azure DevOps</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
                <input
                  type="text"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  placeholder="Моя Jira система"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                <input
                  type="url"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  placeholder="https://mycompany.atlassian.net"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Аутентификация</label>
                <select className="w-full border border-gray-300 rounded px-3 py-2">
                  <option value="api_token">API Token</option>
                  <option value="oauth">OAuth</option>
                  <option value="basic">Basic Auth</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API Token</label>
                <input
                  type="password"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  placeholder="Введите API token"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowConnectionModal(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                onClick={() => {
                  // Здесь была бы логика подключения
                  setShowConnectionModal(false);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Подключить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно синхронизации */}
      {showSyncModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Синхронизация задач</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Локальная система</label>
                <select className="w-full border border-gray-300 rounded px-3 py-2">
                  {systems.filter(s => s.isActive).map(system => (
                    <option key={system.id} value={system.id}>{system.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Внешняя система</label>
                <select className="w-full border border-gray-300 rounded px-3 py-2">
                  {systems.filter(s => s.isActive).map(system => (
                    <option key={system.id} value={system.id}>{system.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="includeSubtasks" className="rounded" />
                <label htmlFor="includeSubtasks" className="text-sm text-gray-700">
                  Включить подзадачи
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="includeComments" className="rounded" />
                <label htmlFor="includeComments" className="text-sm text-gray-700">
                  Включить комментарии
                </label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowSyncModal(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                onClick={() => {
                  // Здесь была бы логика синхронизации
                  setShowSyncModal(false);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Синхронизировать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectIntegrations;