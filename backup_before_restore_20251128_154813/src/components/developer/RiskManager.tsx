/**
 * Компонент управления рисками проекта
 * Обеспечивает визуализацию, анализ и управление рисками с AI-подсказками
 * Поддерживает матрицу вероятности/влияния, тренды и рекомендации
 */

import React, { useState, useEffect, useMemo } from 'react';
import { 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Shield, 
  Target, 
  Clock,
  DollarSign,
  Users,
  Filter,
  Download,
  Settings,
  Eye,
  EyeOff,
  Plus,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { 
  RiskFactor, 
  RiskSeverity,
  RiskCategory,
  AIRiskAnalysisResult,
  MitigationStrategy,
  RiskTrend
} from '../../services/risk-analysis-service';
import { RiskAnalysisService } from '../../services/risk-analysis-service';

interface RiskManagerProps {
  projectId: string;
  risks: RiskFactor[];
  analysis: AIRiskAnalysisResult | null;
  onRiskSelect?: (riskId: string | null) => void;
  onRiskEdit?: (risk: RiskFactor) => void;
  onRiskDelete?: (riskId: string) => void;
  onRiskAdd?: () => void;
  onMitigationCreate?: (riskId: string, strategy: MitigationStrategy) => void;
  readOnly?: boolean;
  showAdvanced?: boolean;
  height?: number;
}

interface RiskFilters {
  category: string;
  severity: RiskSeverity | 'all';
  status: string;
  assignee: string;
  search: string;
}

interface RiskVisualization {
  matrix: {
    highImpact: RiskFactor[];
    mediumImpact: RiskFactor[];
    lowImpact: RiskFactor[];
  };
  timeline: RiskFactor[];
  trends: RiskTrend[];
}

const RiskManager: React.FC<RiskManagerProps> = ({
  projectId,
  risks,
  analysis,
  onRiskSelect,
  onRiskEdit,
  onRiskDelete,
  onRiskAdd,
  onMitigationCreate,
  readOnly = false,
  showAdvanced = true,
  height = 800
}) => {
  const [selectedRiskId, setSelectedRiskId] = useState<string | null>(null);
  const [filters, setFilters] = useState<RiskFilters>({
    category: 'all',
    severity: 'all',
    status: 'all',
    assignee: 'all',
    search: ''
  });
  
  // Состояние модальных окон
  const [showRiskModal, setShowRiskModal] = useState(false);
  const [showMitigationModal, setShowMitigationModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [editingRisk, setEditingRisk] = useState<RiskFactor | null>(null);
  const [selectedRiskForMitigation, setSelectedRiskForMitigation] = useState<string | null>(null);
  
  // Состояние представлений
  const [activeView, setActiveView] = useState<'matrix' | 'list' | 'timeline' | 'trends'>('matrix');
  const [showResolvedRisks, setShowResolvedRisks] = useState(false);
  
  // Сервис анализа рисков
  const riskService = useMemo(() => new RiskAnalysisService(), []);
  
  // Фильтрованные риски
  const filteredRisks = useMemo(() => {
    return risks.filter(risk => {
      // Фильтр по категории
      if (filters.category !== 'all' && risk.category.id !== filters.category) {
        return false;
      }
      
      // Фильтр по серьезности
      if (filters.severity !== 'all' && risk.severity !== filters.severity) {
        return false;
      }
      
      // Фильтр по статусу
      if (filters.status !== 'all' && risk.status.current !== filters.status) {
        return false;
      }
      
      // Фильтр по исполнителю (упрощенно)
      if (filters.assignee !== 'all' && risk.mitigationStrategies[0]?.owner !== filters.assignee) {
        return false;
      }
      
      // Текстовый поиск
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        return risk.title.toLowerCase().includes(searchLower) ||
               risk.description.toLowerCase().includes(searchLower);
      }
      
      return true;
    }).filter(risk => showResolvedRisks || risk.status.current !== 'resolved');
  }, [risks, filters, showResolvedRisks]);
  
  // Визуализация для матрицы
  const riskMatrix = useMemo(() => {
    const matrix = {
      highImpact: [] as RiskFactor[],
      mediumImpact: [] as RiskFactor[],
      lowImpact: [] as RiskFactor[]
    };
    
    filteredRisks.forEach(risk => {
      const impactScore = (risk.impact.schedule + risk.impact.budget + risk.impact.quality + risk.impact.risk) / 4;
      
      if (impactScore >= 70) {
        matrix.highImpact.push(risk);
      } else if (impactScore >= 40) {
        matrix.mediumImpact.push(risk);
      } else {
        matrix.lowImpact.push(risk);
      }
    });
    
    return matrix;
  }, [filteredRisks]);
  
  // Обработчики событий
  const handleRiskClick = (risk: RiskFactor, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedRiskId(risk.id);
    onRiskSelect?.(risk.id);
  };
  
  const handleRiskEdit = (risk: RiskFactor, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingRisk(risk);
    setShowRiskModal(true);
  };
  
  const handleRiskDelete = (riskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Удалить риск?')) {
      onRiskDelete?.(riskId);
    }
  };
  
  const handleMitigationCreate = (riskId: string) => {
    setSelectedRiskForMitigation(riskId);
    setShowMitigationModal(true);
  };
  
  // Получение цвета для серьезности риска
  const getRiskColor = (severity: RiskSeverity): string => {
    switch (severity) {
      case 'critical': return '#ef4444';
      case 'high': return '#f59e0b';
      case 'medium': return '#3b82f6';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };
  
  // Получение иконки для серьезности
  const getSeverityIcon = (severity: RiskSeverity) => {
    switch (severity) {
      case 'critical': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'high': return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'medium': return <AlertCircle className="w-4 h-4 text-blue-500" />;
      case 'low': return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };
  
  // Получение тренда для риска
  const getRiskTrend = (risk: RiskFactor): 'up' | 'down' | 'stable' => {
    const worseningIndicators = risk.earlyWarning.filter(i => i.trend === 'worsening').length;
    const improvingIndicators = risk.earlyWarning.filter(i => i.trend === 'improving').length;
    
    if (worseningIndicators > improvingIndicators) return 'up';
    if (improvingIndicators > worseningIndicators) return 'down';
    return 'stable';
  };
  
  // Получение тренда риска для списка
  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-red-500" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-green-500" />;
      case 'stable': return <div className="w-4 h-4 bg-gray-400 rounded-full" />;
    }
  };
  
  // Рендер матрицы рисков
  const renderRiskMatrix = () => {
    const matrixSize = 300;
    const cellSize = matrixSize / 3;
    
    const probabilityRanges = [
      { label: '0-33%', min: 0, max: 33 },
      { label: '34-66%', min: 34, max: 66 },
      { label: '67-100%', min: 67, max: 100 }
    ];
    
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Матрица рисков</h3>
        
        <div className="relative">
          {/* Заголовки осей */}
          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-sm font-medium text-gray-600">
            Вероятность возникновения
          </div>
          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -rotate-90 text-sm font-medium text-gray-600">
            Влияние на проект
          </div>
          
          {/* Матрица */}
          <div 
            className="border border-gray-300 relative"
            style={{ width: matrixSize, height: matrixSize }}
          >
            {/* Ячейки матрицы */}
            {probabilityRanges.map((range, probIndex) => 
              ['highImpact', 'mediumImpact', 'lowImpact'].map((impactLevel, impactIndex) => {
                const cellRisks = matrix[impactLevel as keyof typeof matrix].filter(risk => 
                  risk.probability >= range.min && risk.probability <= range.max
                );
                
                const isCritical = probIndex === 2 && impactIndex === 0; // высокая вероятность, высокое влияние
                const isLow = probIndex === 0 && impactIndex === 2; // низкая вероятность, низкое влияние
                
                return (
                  <div
                    key={`${probIndex}-${impactIndex}`}
                    className={`absolute border border-gray-200 ${
                      isCritical ? 'bg-red-100' : 
                      isLow ? 'bg-green-50' : 'bg-gray-50'
                    }`}
                    style={{
                      left: probIndex * cellSize,
                      top: impactIndex * cellSize,
                      width: cellSize,
                      height: cellSize
                    }}
                  >
                    {/* Риски в ячейке */}
                    <div className="absolute inset-2">
                      {cellRisks.slice(0, 3).map((risk, riskIndex) => (
                        <div
                          key={risk.id}
                          className={`w-3 h-3 rounded-full cursor-pointer border-2 border-white shadow-sm mb-1 ${
                            selectedRiskId === risk.id ? 'ring-2 ring-blue-500' : ''
                          }`}
                          style={{ 
                            backgroundColor: getRiskColor(risk.severity),
                            marginTop: riskIndex * 8
                          }}
                          onClick={(e) => handleRiskClick(risk, e)}
                          title={`${risk.title} (${risk.probability}%)`}
                        />
                      ))}
                      
                      {cellRisks.length > 3 && (
                        <div className="text-xs text-gray-500 font-medium">
                          +{cellRisks.length - 3}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
            
            {/* Подписи вероятности */}
            {probabilityRanges.map((range, index) => (
              <div
                key={`prob-${index}`}
                className="absolute text-xs text-gray-600"
                style={{
                  left: index * cellSize + cellSize / 2 - 15,
                  bottom: -20
                }}
              >
                {range.label}
              </div>
            ))}
            
            {/* Подписи влияния */}
            {['Высокое', 'Среднее', 'Низкое'].map((label, index) => (
              <div
                key={`impact-${index}`}
                className="absolute text-xs text-gray-600"
                style={{
                  left: -40,
                  top: index * cellSize + cellSize / 2 - 8
                }}
              >
                {label}
              </div>
            ))}
          </div>
        </div>
        
        {/* Легенда */}
        <div className="mt-6 flex items-center justify-center space-x-6">
          {['critical', 'high', 'medium', 'low'].map(severity => (
            <div key={severity} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getRiskColor(severity as RiskSeverity) }}
              />
              <span className="text-sm text-gray-600 capitalize">{severity}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };
  
  // Рендер списка рисков
  const renderRiskList = () => {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Список рисков</h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">
                {filteredRisks.length} из {risks.length}
              </span>
              {!readOnly && (
                <button
                  onClick={onRiskAdd}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  + Добавить
                </button>
              )}
            </div>
          </div>
        </div>
        
        <div className="divide-y divide-gray-200">
          {filteredRisks.map(risk => {
            const trend = getRiskTrend(risk);
            const isSelected = selectedRiskId === risk.id;
            
            return (
              <div
                key={risk.id}
                className={`p-4 hover:bg-gray-50 cursor-pointer ${
                  isSelected ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                }`}
                onClick={(e) => handleRiskClick(risk, e)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      {getSeverityIcon(risk.severity)}
                      <h4 className="font-medium text-gray-900">{risk.title}</h4>
                      <span 
                        className="px-2 py-1 text-xs font-medium rounded"
                        style={{ 
                          backgroundColor: `${getRiskColor(risk.severity)}20`,
                          color: getRiskColor(risk.severity)
                        }}
                      >
                        {risk.severity.toUpperCase()}
                      </span>
                      {getTrendIcon(trend)}
                    </div>
                    
                    <p className="text-sm text-gray-600 mt-1">{risk.description}</p>
                    
                    <div className="flex items-center space-x-4 mt-3">
                      <div className="flex items-center space-x-1 text-sm text-gray-500">
                        <Target className="w-4 h-4" />
                        <span>{risk.probability}%</span>
                      </div>
                      
                      <div className="flex items-center space-x-1 text-sm text-gray-500">
                        <Shield className="w-4 h-4" />
                        <span>{Math.round((risk.impact.schedule + risk.impact.budget + risk.impact.quality) / 3)}%</span>
                      </div>
                      
                      {risk.timeToImpact && (
                        <div className="flex items-center space-x-1 text-sm text-gray-500">
                          <Clock className="w-4 h-4" />
                          <span>{risk.timeToImpact}д</span>
                        </div>
                      )}
                      
                      <span className="text-xs text-gray-400">
                        {risk.category.name}
                      </span>
                    </div>
                    
                    {/* Индикаторы раннего предупреждения */}
                    {risk.earlyWarning.length > 0 && (
                      <div className="mt-2">
                        <div className="flex space-x-2">
                          {risk.earlyWarning.slice(0, 3).map(indicator => (
                            <div
                              key={indicator.id}
                              className={`px-2 py-1 text-xs rounded ${
                                indicator.trend === 'worsening' ? 'bg-red-100 text-red-700' :
                                indicator.trend === 'improving' ? 'bg-green-100 text-green-700' :
                                'bg-gray-100 text-gray-700'
                              }`}
                            >
                              {indicator.name}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    {!readOnly && (
                      <>
                        <button
                          onClick={(e) => handleRiskEdit(risk, e)}
                          className="p-1 text-gray-400 hover:text-blue-600"
                          title="Редактировать"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => handleRiskDelete(risk.id, e)}
                          className="p-1 text-gray-400 hover:text-red-600"
                          title="Удалить"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                        {risk.mitigationStrategies.length === 0 && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMitigationCreate(risk.id);
                            }}
                            className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200"
                          >
                            + Митигация
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };
  
  // Рендер детальной информации о риске
  const renderRiskDetails = () => {
    if (!selectedRiskId) return null;
    
    const risk = risks.find(r => r.id === selectedRiskId);
    if (!risk) return null;
    
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            {getSeverityIcon(risk.severity)}
            <h3 className="text-lg font-semibold">{risk.title}</h3>
          </div>
          <button
            onClick={() => setSelectedRiskId(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>
        
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium mb-2">Описание</h4>
            <p className="text-sm text-gray-600 mb-4">{risk.description}</p>
            
            <h4 className="font-medium mb-2">Метрики</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Вероятность:</span>
                <span className="text-sm font-medium">{risk.probability}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Влияние на сроки:</span>
                <span className="text-sm font-medium">{risk.impact.schedule}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Влияние на бюджет:</span>
                <span className="text-sm font-medium">{risk.impact.budget}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Влияние на качество:</span>
                <span className="text-sm font-medium">{risk.impact.quality}%</span>
              </div>
            </div>
            
            {risk.timeToImpact && (
              <div className="mt-4">
                <h4 className="font-medium mb-2">Временная оценка</h4>
                <div className="flex items-center space-x-2 text-sm">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span>Проявится через {risk.timeToImpact} дней</span>
                </div>
              </div>
            )}
          </div>
          
          <div>
            <h4 className="font-medium mb-2">Индикаторы предупреждения</h4>
            <div className="space-y-2">
              {risk.earlyWarning.map(indicator => (
                <div
                  key={indicator.id}
                  className={`p-2 rounded text-sm ${
                    indicator.trend === 'worsening' ? 'bg-red-50 text-red-700' :
                    indicator.trend === 'improving' ? 'bg-green-50 text-green-700' :
                    'bg-gray-50 text-gray-700'
                  }`}
                >
                  <div className="font-medium">{indicator.name}</div>
                  <div className="text-xs">{indicator.description}</div>
                </div>
              ))}
            </div>
            
            {risk.mitigationStrategies.length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium mb-2">Стратегии митигации</h4>
                <div className="space-y-2">
                  {risk.mitigationStrategies.map(strategy => (
                    <div
                      key={strategy.id}
                      className="p-3 bg-green-50 border border-green-200 rounded"
                    >
                      <div className="font-medium text-green-900">{strategy.title}</div>
                      <div className="text-sm text-green-700 mt-1">{strategy.description}</div>
                      <div className="flex justify-between items-center mt-2 text-xs text-green-600">
                        <span>Эффективность: {strategy.effectiveness}%</span>
                        <span>Срок: {strategy.timeToImplement}д</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };
  
  // Рендер панели инструментов
  const renderToolbar = () => {
    return (
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Переключатель представлений */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              {[
                { key: 'matrix', label: 'Матрица', icon: Target },
                { key: 'list', label: 'Список', icon: AlertTriangle },
                { key: 'timeline', label: 'Временная шкала', icon: Clock },
                { key: 'trends', label: 'Тренды', icon: TrendingUp }
              ].map(view => {
                const Icon = view.icon;
                return (
                  <button
                    key={view.key}
                    onClick={() => setActiveView(view.key as any)}
                    className={`flex items-center space-x-2 px-3 py-1 rounded text-sm ${
                      activeView === view.key 
                        ? 'bg-white text-blue-600 shadow-sm' 
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{view.label}</span>
                  </button>
                );
              })}
            </div>
            
            {/* Переключатель решенных рисков */}
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showResolvedRisks}
                onChange={(e) => setShowResolvedRisks(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-600">Показать решенные</span>
            </label>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* Фильтры */}
            <div className="flex items-center space-x-2">
              <select
                value={filters.category}
                onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                className="border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value="all">Все категории</option>
                <option value="technical">Технические</option>
                <option value="schedule">Сроки</option>
                <option value="budget">Бюджет</option>
                <option value="quality">Качество</option>
                <option value="resource">Ресурсы</option>
                <option value="organizational">Организационные</option>
                <option value="external">Внешние</option>
              </select>
              
              <select
                value={filters.severity}
                onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value as RiskSeverity | 'all' }))}
                className="border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value="all">Все уровни</option>
                <option value="critical">Критические</option>
                <option value="high">Высокие</option>
                <option value="medium">Средние</option>
                <option value="low">Низкие</option>
              </select>
            </div>
            
            {/* Поиск */}
            <input
              type="text"
              placeholder="Поиск рисков..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="border border-gray-300 rounded px-3 py-1 text-sm"
            />
            
            {/* Действия */}
            {analysis && (
              <button
                onClick={() => setShowAnalysisModal(true)}
                className="px-3 py-1 bg-purple-100 text-purple-700 rounded text-sm hover:bg-purple-200"
              >
                AI Анализ
              </button>
            )}
            
            <button className="p-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded">
              <Download className="w-4 h-4" />
            </button>
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
            <h1 className="text-2xl font-bold text-gray-900">Управление рисками</h1>
            <p className="text-gray-600 mt-1">AI-анализ и мониторинг проектных рисков</p>
          </div>
          
          {analysis && (
            <div className="flex items-center space-x-4">
              <div className="text-center">
                <div className="text-2xl font-bold" style={{ color: getRiskColor(analysis.riskLevel) }}>
                  {analysis.overallRiskScore}%
                </div>
                <div className="text-sm text-gray-500">Общий риск</div>
              </div>
              
              <div className="text-center">
                <div className="text-xl font-semibold text-gray-900">
                  {analysis.topRisks.length}
                </div>
                <div className="text-sm text-gray-500">Высоких рисков</div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Панель инструментов */}
      {renderToolbar()}
      
      {/* Основной контент */}
      <div 
        className="p-6"
        style={{ height: height - 120 }}
      >
        <div className="grid grid-cols-12 gap-6 h-full">
          {/* Основная область */}
          <div className="col-span-9">
            {activeView === 'matrix' && renderRiskMatrix()}
            {activeView === 'list' && renderRiskList()}
            {activeView === 'timeline' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4">Временная шкала рисков</h3>
                <div className="text-center text-gray-500 py-12">
                  Временная шкала рисков в разработке...
                </div>
              </div>
            )}
            {activeView === 'trends' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4">Тренды рисков</h3>
                <div className="text-center text-gray-500 py-12">
                  График трендов рисков в разработке...
                </div>
              </div>
            )}
          </div>
          
          {/* Боковая панель с деталями */}
          <div className="col-span-3">
            {selectedRiskId ? (
              renderRiskDetails()
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-center text-gray-500">
                  <Shield className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Выберите риск для просмотра деталей</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Модальное окно анализа рисков */}
      {showAnalysisModal && analysis && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">AI Анализ рисков</h3>
              <button
                onClick={() => setShowAnalysisModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="text-center">
                <div 
                  className="text-3xl font-bold"
                  style={{ color: getRiskColor(analysis.riskLevel) }}
                >
                  {analysis.riskLevel.toUpperCase()}
                </div>
                <div className="text-sm text-gray-500">Уровень риска проекта</div>
              </div>
              
              <div>
                <div className="text-sm font-medium mb-2">Топ риски:</div>
                <div className="space-y-2">
                  {analysis.topRisks.slice(0, 3).map((risk, index) => (
                    <div key={risk.id} className="flex items-center space-x-2 text-sm">
                      <span className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                        {index + 1}
                      </span>
                      <span className="truncate">{risk.title}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <div className="text-sm font-medium mb-2">Рекомендации:</div>
                <div className="space-y-1">
                  {analysis.prioritizedActions.slice(0, 3).map((action, index) => (
                    <div key={index} className="text-sm text-gray-600">
                      • {action.action}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowAnalysisModal(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskManager;