/**
 * Компонент автоматических отчетов и KPI Dashboard
 * Обеспечивает генерацию отчетов, мониторинг KPI и аналитику проектов
 */

import React, { useState, useEffect, useMemo } from 'react';
import { 
  FileText, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  BarChart3,
  PieChart,
  Calendar,
  Download,
  Settings,
  Plus,
  Eye,
  Edit,
  Trash2,
  Play,
  RefreshCw,
  Search,
  Target,
  DollarSign,
  Activity
} from 'lucide-react';
import { 
  ReportTemplate,
  GeneratedReport,
  KPIDashboard,
  KPI,
  ReportType,
  StatusLevel,
  MetricData,
  KPICategory,
  KPIFrequency,
  ReportFormat
} from '../../services/automated-reporting-service';
import { AutomatedReportingService } from '../../services/automated-reporting-service';

interface ReportsDashboardProps {
  projectId: string;
  templates: ReportTemplate[];
  reports: GeneratedReport[];
  kpiDashboard?: KPIDashboard;
  onGenerateReport?: (templateId: string, parameters: Record<string, any>) => void;
  onExportReport?: (reportId: string, format: string) => void;
  onCreateTemplate?: (template: Omit<ReportTemplate, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onEditTemplate?: (templateId: string) => void;
  readOnly?: boolean;
  height?: number;
}

interface KPICardProps {
  kpi: KPI;
  currentValue: number;
  trend: 'up' | 'down' | 'stable';
  change: number;
  lastUpdate: Date;
}

interface ExtendedKPI extends KPI {
  currentValue: number;
  trend: 'up' | 'down' | 'stable';
  change: number;
  lastUpdate: Date;
}

interface ReportCardProps {
  report: GeneratedReport;
  onView?: (reportId: string) => void;
  onExport?: (reportId: string) => void;
  onDelete?: (reportId: string) => void;
}

interface TemplateCardProps {
  template: ReportTemplate;
  onGenerate?: (templateId: string) => void;
  onEdit?: (templateId: string) => void;
  onDuplicate?: (templateId: string) => void;
  onDelete?: (templateId: string) => void;
}

const ReportsDashboard: React.FC<ReportsDashboardProps> = ({
  projectId,
  templates,
  reports,
  kpiDashboard,
  onGenerateReport,
  onExportReport,
  onCreateTemplate,
  onEditTemplate,
  readOnly = false,
  height = 800
}) => {
  const [activeTab, setActiveTab] = useState<'kpi' | 'reports' | 'templates' | 'analytics'>('kpi');
  const [selectedKPI, setSelectedKPI] = useState<string | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ReportTemplate | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [dateRange, setDateRange] = useState<'week' | 'month' | 'quarter'>('week');

  // Сервис отчетов
  const reportingService = useMemo(() => new AutomatedReportingService(), []);

  // Фильтрация отчетов
  const filteredReports = useMemo(() => {
    return reports.filter(report => {
      const matchesSearch = report.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = filterType === 'all' || report.type === filterType;
      
      return matchesSearch && matchesType;
    }).sort((a, b) => b.generatedAt.getTime() - a.generatedAt.getTime());
  }, [reports, searchQuery, filterType]);

  // Фильтрация шаблонов
  const filteredTemplates = useMemo(() => {
    return templates.filter(template => {
      const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = filterType === 'all' || template.type === filterType;
      
      return matchesSearch && matchesType;
    });
  }, [templates, searchQuery, filterType]);

  // Получение цвета для статуса
  const getStatusColor = (status: StatusLevel): string => {
    switch (status) {
      case 'excellent': return '#10b981';
      case 'good': return '#3b82f6';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  // Получение иконки для статуса
  const getStatusIcon = (status: StatusLevel) => {
    switch (status) {
      case 'excellent': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'good': return <CheckCircle className="w-5 h-5 text-blue-500" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'critical': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default: return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  // Рендер KPI карточки
  const KPICard: React.FC<KPICardProps> = ({ kpi, currentValue, trend, change, lastUpdate }) => {
    const getStatus = (value: number): StatusLevel => {
      if (value >= kpi.thresholds.excellent) return 'excellent';
      if (value >= kpi.thresholds.good) return 'good';
      if (value >= kpi.thresholds.warning) return 'warning';
      return 'critical';
    };

    const status = getStatus(currentValue);
    const statusColor = getStatusColor(status);

    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div 
              className="w-10 h-10 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: `${statusColor}20` }}
            >
              {kpi.category === 'schedule' && <Clock className="w-5 h-5" style={{ color: statusColor }} />}
              {kpi.category === 'quality' && <Target className="w-5 h-5" style={{ color: statusColor }} />}
              {kpi.category === 'financial' && <DollarSign className="w-5 h-5" style={{ color: statusColor }} />}
              {kpi.category === 'productivity' && <TrendingUp className="w-5 h-5" style={{ color: statusColor }} />}
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{kpi.name}</h3>
              <p className="text-sm text-gray-500">{kpi.description}</p>
            </div>
          </div>
          
          {getStatusIcon(status)}
        </div>
        
        <div className="mb-4">
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-gray-900">
              {typeof currentValue === 'number' ? currentValue.toFixed(1) : currentValue}
            </span>
            <span className="text-sm text-gray-500">{kpi.unit}</span>
            <span className="text-sm font-medium" style={{ color: statusColor }}>
              {kpi.target}
            </span>
          </div>
          
          <div className="flex items-center space-x-2 mt-2">
            {trend === 'up' && <TrendingUp className="w-4 h-4 text-green-500" />}
            {trend === 'down' && <TrendingDown className="w-4 h-4 text-red-500" />}
            {trend === 'stable' && <Activity className="w-4 h-4 text-gray-400" />}
            <span className={`text-sm ${change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-500'}`}>
              {change > 0 ? '+' : ''}{change.toFixed(1)}%
            </span>
            <span className="text-sm text-gray-400">за период</span>
          </div>
        </div>
        
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Цель: {kpi.target}{kpi.unit}</span>
          <span>Обновлено: {lastUpdate.toLocaleDateString('ru-RU')}</span>
        </div>
      </div>
    );
  };

  // Рендер карточки отчета
  const ReportCard: React.FC<ReportCardProps> = ({ report, onView, onExport, onDelete }) => {
    const getStatusColor = (status: string): string => {
      switch (status) {
        case 'completed': return '#10b981';
        case 'generating': return '#3b82f6';
        case 'failed': return '#ef4444';
        default: return '#6b7280';
      }
    };

    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <FileText className="w-6 h-6 text-gray-400" />
            <div>
              <h3 className="font-medium text-gray-900">{report.title}</h3>
              <p className="text-sm text-gray-500">{report.templateName}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span 
              className="px-2 py-1 text-xs font-medium rounded"
              style={{ 
                backgroundColor: `${getStatusColor(report.status)}20`,
                color: getStatusColor(report.status)
              }}
            >
              {report.status === 'completed' ? 'Завершен' :
               report.status === 'generating' ? 'Генерация' :
               report.status === 'failed' ? 'Ошибка' : report.status}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div>
            <span className="text-gray-500">Тип:</span>
            <div className="font-medium">{report.type}</div>
          </div>
          <div>
            <span className="text-gray-500">Формат:</span>
            <div className="font-medium">{report.format.toUpperCase()}</div>
          </div>
          <div>
            <span className="text-gray-500">Создан:</span>
            <div className="font-medium">{report.generatedAt.toLocaleDateString('ru-RU')}</div>
          </div>
          <div>
            <span className="text-gray-500">Время генерации:</span>
            <div className="font-medium">{(report.executionTime / 1000).toFixed(1)}с</div>
          </div>
        </div>
        
        {report.summary && (
          <div className="mb-4">
            <div className="text-sm text-gray-500 mb-1">Общий статус:</div>
            <div className="flex items-center space-x-2">
              {getStatusIcon(report.summary.overallStatus)}
              <span 
                className="text-sm font-medium"
                style={{ color: getStatusColor(report.summary.overallStatus) }}
              >
                {report.summary.overallStatus === 'excellent' ? 'Отлично' :
                 report.summary.overallStatus === 'good' ? 'Хорошо' :
                 report.summary.overallStatus === 'warning' ? 'Предупреждение' : 'Критично'}
              </span>
            </div>
          </div>
        )}
        
        {report.summary?.alerts && report.summary.alerts.length > 0 && (
          <div className="mb-4">
            <div className="text-sm text-gray-500 mb-2">Алерты ({report.summary.alerts.length}):</div>
            <div className="space-y-1">
              {report.summary.alerts.slice(0, 2).map(alert => (
                <div key={alert.id} className="text-sm text-yellow-700 bg-yellow-50 p-2 rounded">
                  {alert.title}
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>Размер: {report.fileSize ? `${(report.fileSize / 1024).toFixed(1)} KB` : 'N/A'}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            {onView && (
              <button
                onClick={() => onView(report.id)}
                className="p-1 text-gray-400 hover:text-blue-600 rounded"
                title="Просмотр"
              >
                <Eye className="w-4 h-4" />
              </button>
            )}
            
            {onExport && (
              <button
                onClick={() => onExport(report.id)}
                className="p-1 text-gray-400 hover:text-green-600 rounded"
                title="Экспорт"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
            
            {!readOnly && onDelete && (
              <button
                onClick={() => onDelete(report.id)}
                className="p-1 text-gray-400 hover:text-red-600 rounded"
                title="Удалить"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Рендер карточки шаблона
  const TemplateCard: React.FC<TemplateCardProps> = ({ template, onGenerate, onEdit, onDuplicate, onDelete }) => {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{template.name}</h3>
              <p className="text-sm text-gray-500">{template.description}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span 
              className={`px-2 py-1 text-xs font-medium rounded ${
                template.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
              }`}
            >
              {template.isActive ? 'Активен' : 'Отключен'}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div>
            <span className="text-gray-500">Тип:</span>
            <div className="font-medium">{template.type}</div>
          </div>
          <div>
            <span className="text-gray-500">Категория:</span>
            <div className="font-medium">{template.category}</div>
          </div>
          <div>
            <span className="text-gray-500">Секций:</span>
            <div className="font-medium">{template.sections.length}</div>
          </div>
          <div>
            <span className="text-gray-500">Форматов:</span>
            <div className="font-medium">{template.format.length}</div>
          </div>
        </div>
        
        {template.schedule && (
          <div className="mb-4">
            <div className="text-sm text-gray-500 mb-1">Расписание:</div>
            <div className="flex items-center space-x-2 text-sm">
              <Calendar className="w-4 h-4 text-gray-400" />
              <span>
                {template.schedule.frequency === 'daily' ? 'Ежедневно' :
                 template.schedule.frequency === 'weekly' ? 'Еженедельно' :
                 template.schedule.frequency === 'monthly' ? 'Ежемесячно' : template.schedule.frequency}
                в {template.schedule.time}
              </span>
            </div>
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Получателей: {template.recipients.length}
          </div>
          
          <div className="flex items-center space-x-2">
            {onGenerate && (
              <button
                onClick={() => onGenerate(template.id)}
                className="p-1 text-gray-400 hover:text-blue-600 rounded"
                title="Создать отчет"
              >
                <Play className="w-4 h-4" />
              </button>
            )}
            
            {!readOnly && onEdit && (
              <button
                onClick={() => onEdit(template.id)}
                className="p-1 text-gray-400 hover:text-blue-600 rounded"
                title="Редактировать"
              >
                <Edit className="w-4 h-4" />
              </button>
            )}
            
            {!readOnly && onDelete && (
              <button
                onClick={() => onDelete(template.id)}
                className="p-1 text-gray-400 hover:text-red-600 rounded"
                title="Удалить"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Рендер панели KPI
  const renderKPIPanel = () => {
    const mockKPIs: ExtendedKPI[] = [
      {
        id: 'schedule_performance',
        name: 'Производительность графика',
        description: 'Отношение фактического времени к плановому',
        category: 'schedule' as KPICategory,
        unit: '%',
        calculation: {
          type: 'percentage' as const,
          formula: '(actual_hours / planned_hours) * 100',
          parameters: {}
        },
        target: 100,
        thresholds: { excellent: 110, good: 100, warning: 90, critical: 75 },
        frequency: 'weekly' as KPIFrequency,
        dataSource: 'schedule_metrics',
        isActive: true,
        owner: 'project_manager',
        currentValue: 87,
        trend: 'down',
        change: -5.2,
        lastUpdate: new Date()
      },
      {
        id: 'budget_variance',
        name: 'Отклонение от бюджета',
        description: 'Процентное отклонение от запланированного бюджета',
        category: 'financial' as KPICategory,
        unit: '%',
        calculation: {
          type: 'percentage' as const,
          formula: '((actual_cost - budget) / budget) * 100',
          parameters: {}
        },
        target: 0,
        thresholds: { excellent: -2, good: 5, warning: 10, critical: 20 },
        frequency: 'weekly' as KPIFrequency,
        dataSource: 'financial_metrics',
        isActive: true,
        owner: 'finance_manager',
        currentValue: 3.2,
        trend: 'up',
        change: 1.8,
        lastUpdate: new Date()
      },
      {
        id: 'quality_score',
        name: 'Показатель качества',
        description: 'Средний показатель качества выполненных работ',
        category: 'quality' as KPICategory,
        unit: 'балл',
        calculation: {
          type: 'average' as const,
          formula: 'AVG(quality_rating)',
          parameters: {}
        },
        target: 4.5,
        thresholds: { excellent: 4.8, good: 4.5, warning: 4.0, critical: 3.5 },
        frequency: 'weekly' as KPIFrequency,
        dataSource: 'quality_metrics',
        isActive: true,
        owner: 'quality_manager',
        currentValue: 4.3,
        trend: 'stable',
        change: 0.1,
        lastUpdate: new Date()
      },
      {
        id: 'team_productivity',
        name: 'Продуктивность команды',
        description: 'Средняя продуктивность команды по задачам',
        category: 'productivity' as KPICategory,
        unit: '%',
        calculation: {
          type: 'percentage' as const,
          formula: '(completed_tasks / total_tasks) * 100',
          parameters: {}
        },
        target: 85,
        thresholds: { excellent: 95, good: 85, warning: 70, critical: 60 },
        frequency: 'weekly' as KPIFrequency,
        dataSource: 'productivity_metrics',
        isActive: true,
        owner: 'team_lead',
        currentValue: 92,
        trend: 'up',
        change: 3.5,
        lastUpdate: new Date()
      }
    ];

    return (
      <div className="space-y-6">
        {/* KPI Overview */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Обзор KPI проекта</h2>
            <div className="flex items-center space-x-3">
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value as 'week' | 'month' | 'quarter')}
                className="border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value="week">Неделя</option>
                <option value="month">Месяц</option>
                <option value="quarter">Квартал</option>
              </select>
              
              <button className="p-2 border border-gray-300 rounded hover:bg-gray-50">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {mockKPIs.map(kpi => (
              <KPICard
                key={kpi.id}
                kpi={kpi}
                currentValue={kpi.currentValue}
                trend={kpi.trend}
                change={kpi.change}
                lastUpdate={kpi.lastUpdate}
              />
            ))}
          </div>
        </div>

        {/* KPI Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Тренд производительности</h3>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-16 h-16 text-gray-300" />
              <span className="ml-4 text-gray-500">График в разработке...</span>
            </div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Распределение по категориям</h3>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <PieChart className="w-16 h-16 text-gray-300" />
              <span className="ml-4 text-gray-500">Диаграмма в разработке...</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Рендер панели отчетов
  const renderReportsPanel = () => {
    return (
      <div className="space-y-6">
        {/* Поиск и фильтры */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Поиск отчетов..."
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
              <option value="progress">Прогресс</option>
              <option value="status">Статус</option>
              <option value="kpi">KPI</option>
              <option value="executive">Исполнительный</option>
              <option value="comprehensive">Комплексный</option>
            </select>
          </div>
          
          <button
            onClick={() => setShowReportModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            <span>Создать отчет</span>
          </button>
        </div>

        {/* Список отчетов */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredReports.map(report => (
            <ReportCard
              key={report.id}
              report={report}
              onView={(id) => console.log('Просмотр отчета:', id)}
              onExport={(id) => onExportReport?.(id, 'pdf' as ReportFormat)}
              onDelete={(id) => console.log('Удаление отчета:', id)}
            />
          ))}
        </div>

        {filteredReports.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium">Нет отчетов</p>
            <p className="text-sm">
              {searchQuery || filterType !== 'all' 
                ? 'Отчеты не найдены' 
                : 'Создайте первый отчет для начала работы'
              }
            </p>
          </div>
        )}
      </div>
    );
  };

  // Рендер панели шаблонов
  const renderTemplatesPanel = () => {
    return (
      <div className="space-y-6">
        {/* Поиск и фильтры */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Поиск шаблонов..."
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
              <option value="progress">Прогресс</option>
              <option value="status">Статус</option>
              <option value="kpi">KPI</option>
              <option value="executive">Исполнительный</option>
            </select>
          </div>
          
          {!readOnly && (
            <button
              onClick={() => setShowTemplateModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              <span>Создать шаблон</span>
            </button>
          )}
        </div>

        {/* Список шаблонов */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredTemplates.map(template => (
            <TemplateCard
              key={template.id}
              template={template}
              onGenerate={(id) => onGenerateReport?.(id, { projectId: projectId })}
              onEdit={(id) => onEditTemplate?.(id)}
              onDuplicate={(id) => console.log('Дублирование шаблона:', id)}
              onDelete={(id) => console.log('Удаление шаблона:', id)}
            />
          ))}
        </div>

        {filteredTemplates.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium">Нет шаблонов</p>
            <p className="text-sm">
              {searchQuery || filterType !== 'all' 
                ? 'Шаблоны не найдены' 
                : 'Создайте первый шаблон для автоматической генерации отчетов'
              }
            </p>
          </div>
        )}
      </div>
    );
  };

  // Рендер панели аналитики
  const renderAnalyticsPanel = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Аналитика и тренды</h3>
          <div className="h-96 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">Аналитика будет добавлена в следующих обновлениях</p>
            </div>
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
            <h1 className="text-2xl font-bold text-gray-900">Автоматические отчеты</h1>
            <p className="text-gray-600 mt-1">Мониторинг KPI, генерация отчетов и аналитика проектов</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{reports.length}</div>
              <div className="text-sm text-gray-500">Всего отчетов</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{templates.filter(t => t.isActive).length}</div>
              <div className="text-sm text-gray-500">Активных шаблонов</div>
            </div>
          </div>
        </div>
      </div>

      {/* Навигация */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6">
          <div className="flex space-x-8">
            {[
              { key: 'kpi', label: 'KPI Dashboard', icon: TrendingUp },
              { key: 'reports', label: 'Отчеты', icon: FileText },
              { key: 'templates', label: 'Шаблоны', icon: Settings },
              { key: 'analytics', label: 'Аналитика', icon: BarChart3 }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as 'kpi' | 'reports' | 'templates' | 'analytics')}
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
        {activeTab === 'kpi' && renderKPIPanel()}
        {activeTab === 'reports' && renderReportsPanel()}
        {activeTab === 'templates' && renderTemplatesPanel()}
        {activeTab === 'analytics' && renderAnalyticsPanel()}
      </div>

      {/* Модальное окно создания шаблона */}
      {showTemplateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Создание шаблона отчета</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
                <input
                  type="text"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  placeholder="Название шаблона"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
                <textarea
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  rows={3}
                  placeholder="Описание шаблона"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Тип отчета</label>
                <select className="w-full border border-gray-300 rounded px-3 py-2">
                  <option value="progress">Прогресс</option>
                  <option value="status">Статус</option>
                  <option value="kpi">KPI</option>
                  <option value="executive">Исполнительный</option>
                  <option value="comprehensive">Комплексный</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Категория</label>
                <select className="w-full border border-gray-300 rounded px-3 py-2">
                  <option value="management">Управление</option>
                  <option value="executive">Исполнительная</option>
                  <option value="team">Команда</option>
                  <option value="stakeholder">Заинтересованные лица</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="autoSchedule" className="rounded" />
                <label htmlFor="autoSchedule" className="text-sm text-gray-700">
                  Включить автоматическое расписание
                </label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowTemplateModal(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                onClick={() => {
                  // Логика создания шаблона
                  setShowTemplateModal(false);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Создать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsDashboard;