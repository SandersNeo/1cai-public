/**
 * Компонент ROI калькулятора для Business Analyst
 * Предоставляет интерактивный интерфейс для расчета экономической эффективности проектов
 */

import React, { useState, useEffect } from 'react';
import {
  ROIProject,
  ROICalculation,
  ROIScenario,
  roiCalculatorService
} from '../../services/roi-calculator-service';

interface ROICalculatorViewProps {
  readonly?: boolean;
  onProjectChange?: (project: ROIProject) => void;
}

interface ProjectForm {
  name: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  developmentCost: number;
  implementationCost: number;
  maintenanceCost: number;
  timeSavingsHours: number;
  timeSavingsTransactions: number;
  timeSavingsRate: number;
  costReductions: Array<{ description: string; amount: number; frequency: string }>;
  revenueIncreases: Array<{ description: string; amount: number; frequency: string }>;
  riskReductions: Array<{ description: string; riskValue: number; probability: number; reduction: number }>;
  implementationPeriod: number;
  riskLevel: string;
  notes: string;
}

export const ROICalculatorView: React.FC<ROICalculatorViewProps> = ({
  readonly = false,
  onProjectChange
}) => {
  const [projects, setProjects] = useState<ROIProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [currentProject, setCurrentProject] = useState<ROIProject | null>(null);
  const [calculation, setCalculation] = useState<ROICalculation | null>(null);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [activeTab, setActiveTab] = useState('projects');
  const [activeView, setActiveView] = useState<'overview' | 'analysis' | 'comparison' | 'scenarios'>('overview');
  const [calculationParameters, setCalculationParameters] = useState({
    discountRate: 0.10,
    timeHorizon: 3
  });
  const [projectForm, setProjectForm] = useState<ProjectForm>({
    name: '',
    description: '',
    category: 'custom',
    priority: 'medium',
    status: 'planning',
    developmentCost: 0,
    implementationCost: 0,
    maintenanceCost: 0,
    timeSavingsHours: 0,
    timeSavingsTransactions: 0,
    timeSavingsRate: 1000,
    costReductions: [],
    revenueIncreases: [],
    riskReductions: [],
    implementationPeriod: 3,
    riskLevel: 'medium',
    notes: ''
  });

  // Загрузка данных при монтировании
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = () => {
    const loaded = roiCalculatorService.getAllProjects();
    setProjects(loaded);
    if (loaded.length > 0 && !selectedProject) {
      setSelectedProject(loaded[0].id);
    }
  };

  // Загрузка проекта при выборе
  useEffect(() => {
    if (selectedProject) {
      const project = roiCalculatorService.getProject(selectedProject);
      if (project) {
        setCurrentProject(project);
        calculateProjectROI(selectedProject);
        onProjectChange?.(project);
      }
    }
  }, [selectedProject]);

  const calculateProjectROI = (projectId: string) => {
    try {
      const calc = roiCalculatorService.calculateROI(projectId, calculationParameters);
      setCalculation(calc);
    } catch (error) {
      console.error('Ошибка расчета ROI:', error);
    }
  };

  const handleCreateProject = () => {
    if (!projectForm.name.trim()) {
      alert('Введите название проекта');
      return;
    }

    try {
      const projectId = roiCalculatorService.createProject({
        name: projectForm.name,
        description: projectForm.description,
        category: projectForm.category as any,
        priority: projectForm.priority as any,
        status: projectForm.status as any,
        developmentCost: projectForm.developmentCost,
        implementationCost: projectForm.implementationCost,
        maintenanceCost: projectForm.maintenanceCost,
        timeSavings: {
          hoursPerTransaction: projectForm.timeSavingsHours,
          transactionsPerMonth: projectForm.timeSavingsTransactions,
          hourlyRate: projectForm.timeSavingsRate
        },
        costReduction: projectForm.costReductions.map(item => ({
          ...item,
          frequency: item.frequency as 'monthly' | 'quarterly' | 'yearly'
        })),
        revenueIncrease: projectForm.revenueIncreases.map(item => ({
          ...item,
          frequency: item.frequency as 'monthly' | 'quarterly' | 'yearly'
        })),
        riskReduction: projectForm.riskReductions,
        implementationPeriod: projectForm.implementationPeriod,
        riskLevel: projectForm.riskLevel as any,
        createdBy: 'user',
        notes: projectForm.notes
      });

      // Сразу рассчитываем ROI
      calculateProjectROI(projectId);

      // Очищаем форму
      resetProjectForm();
      setShowProjectModal(false);
      loadProjects();
      setSelectedProject(projectId);
    } catch (error) {
      console.error('Ошибка создания проекта:', error);
      alert('Ошибка при создании проекта');
    }
  };

  const resetProjectForm = () => {
    setProjectForm({
      name: '',
      description: '',
      category: 'custom',
      priority: 'medium',
      status: 'planning',
      developmentCost: 0,
      implementationCost: 0,
      maintenanceCost: 0,
      timeSavingsHours: 0,
      timeSavingsTransactions: 0,
      timeSavingsRate: 1000,
      costReductions: [],
      revenueIncreases: [],
      riskReductions: [],
      implementationPeriod: 3,
      riskLevel: 'medium',
      notes: ''
    });
  };

  const handleDeleteProject = (projectId: string) => {
    if (confirm('Удалить этот проект?')) {
      roiCalculatorService.deleteProject(projectId);
      loadProjects();
      if (selectedProject === projectId) {
        setSelectedProject(null);
        setCurrentProject(null);
        setCalculation(null);
      }
    }
  };

  const handleExportProjects = () => {
    try {
      const data = roiCalculatorService.exportProjectsData('json');
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `roi_projects_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('Ошибка при экспорте проектов');
    }
  };

  const handleImportProjects = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = e.target?.result as string;
        const count = roiCalculatorService.importProjectsData(data);
        alert(`Импортировано ${count} проектов`);
        loadProjects();
      } catch (error) {
        alert('Ошибка при импорте проектов');
      }
    };
    reader.readAsText(file);
  };

  const handleGenerateReport = () => {
    if (projects.length === 0) {
      alert('Нет проектов для генерации отчета');
      return;
    }

    try {
      const report = roiCalculatorService.generateROIReport(
        projects.map(p => p.id),
        'detailed'
      );
      
      const blob = new Blob([report], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `roi_report_${new Date().toISOString().split('T')[0]}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('Ошибка при генерации отчета');
    }
  };

  // Отрисовка обзора проектов
  const renderOverview = () => {
    const stats = roiCalculatorService.getServiceStatistics();
    
    return (
      <div className="space-y-6">
        {/* Общая статистика */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.totalProjects}</div>
            <div className="text-sm text-gray-600">Всего проектов</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-green-600">{stats.averageROI.toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Средний ROI</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-purple-600">
              {(stats.totalInvestment / 1000000).toFixed(1)}М
            </div>
            <div className="text-sm text-gray-600">Инвестиции (руб.)</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {(stats.totalBenefits / 1000000).toFixed(1)}М
            </div>
            <div className="text-sm text-gray-600">Выгоды (руб.)</div>
          </div>
        </div>

        {/* Лучшие проекты */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Топ проектов по ROI</h3>
          <div className="space-y-4">
            {roiCalculatorService.getTopProjects(5).map((project, index) => (
              <div key={project.id} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center space-x-4">
                  <div className="text-lg font-bold text-gray-400">#{index + 1}</div>
                  <div>
                    <div className="font-medium">{project.name}</div>
                    <div className="text-sm text-gray-600">{project.category}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-green-600">
                    {roiCalculatorService.calculateROI(project.id)?.roiPercentage.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600">ROI</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Список проектов */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Все проекты</h3>
            <button
              onClick={() => setShowProjectModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              + Новый проект
            </button>
          </div>
          
          <div className="grid gap-4">
            {projects.map(project => (
              <div
                key={project.id}
                className={`p-4 border rounded cursor-pointer transition-all ${
                  selectedProject === project.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                }`}
                onClick={() => setSelectedProject(project.id)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="font-semibold">{project.name}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        project.priority === 'critical' ? 'bg-red-100 text-red-800' :
                        project.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                        project.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {project.priority}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        project.status === 'completed' ? 'bg-green-100 text-green-800' :
                        project.status === 'deployed' ? 'bg-blue-100 text-blue-800' :
                        project.status === 'development' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                    
                    <p className="text-gray-600 text-sm mb-2">{project.description}</p>
                    
                    <div className="grid grid-cols-4 gap-4 text-sm text-gray-500">
                      <div>
                        <span className="font-medium">Инвестиции:</span><br />
                        {(project.developmentCost + project.implementationCost).toLocaleString()} руб.
                      </div>
                      <div>
                        <span className="font-medium">Категория:</span><br />
                        {project.category}
                      </div>
                      <div>
                        <span className="font-medium">Создан:</span><br />
                        {new Date(project.createdAt).toLocaleDateString()}
                      </div>
                      <div>
                        <span className="font-medium">ROI:</span><br />
                        {roiCalculatorService.calculateROI(project.id)?.roiPercentage.toFixed(1) || 0}%
                      </div>
                    </div>
                  </div>
                  
                  {!readonly && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteProject(project.id);
                      }}
                      className="text-red-600 hover:text-red-800 text-sm ml-4"
                    >
                      Удалить
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {projects.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              Нет проектов. Создайте первый проект.
            </div>
          )}
        </div>
      </div>
    );
  };

  // Отрисовка детального анализа проекта
  const renderAnalysis = () => {
    if (!currentProject || !calculation) {
      return (
        <div className="text-center py-8 text-gray-500">
          Выберите проект для анализа
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Информация о проекте */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">{currentProject.name}</h3>
          <p className="text-gray-600 mb-4">{currentProject.description}</p>
          
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Категория:</span>
              <div>{currentProject.category}</div>
            </div>
            <div>
              <span className="font-medium text-gray-700">Приоритет:</span>
              <div>{currentProject.priority}</div>
            </div>
            <div>
              <span className="font-medium text-gray-700">Статус:</span>
              <div>{currentProject.status}</div>
            </div>
          </div>
        </div>

        {/* Основные показатели ROI */}
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h4 className="text-lg font-semibold mb-4">Финансовые показатели</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Общие инвестиции:</span>
                <span className="font-bold">{calculation.totalInvestment.toLocaleString()} руб.</span>
              </div>
              <div className="flex justify-between">
                <span>Общие выгоды:</span>
                <span className="font-bold text-green-600">{calculation.totalBenefits.toLocaleString()} руб.</span>
              </div>
              <div className="flex justify-between">
                <span>Чистая приведенная стоимость:</span>
                <span className={`font-bold ${calculation.netPresentValue >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {calculation.netPresentValue.toLocaleString()} руб.
                </span>
              </div>
              <div className="flex justify-between border-t pt-3">
                <span>ROI:</span>
                <span className={`font-bold text-2xl ${calculation.roiPercentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {calculation.roiPercentage.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h4 className="text-lg font-semibold mb-4">Показатели эффективности</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Период окупаемости:</span>
                <span className="font-bold">{calculation.paybackPeriod.toFixed(1)} мес.</span>
              </div>
              <div className="flex justify-between">
                <span>Точка безубыточности:</span>
                <span className="font-bold">{calculation.breakEvenPoint} мес.</span>
              </div>
              <div className="flex justify-between">
                <span>IRR:</span>
                <span className="font-bold text-blue-600">{calculation.efficiencyRatios.internalRateOfReturn.toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Индекс прибыльности:</span>
                <span className="font-bold">{calculation.efficiencyRatios.profitabilityIndex.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Анализ рисков */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h4 className="text-lg font-semibold mb-4">Анализ рисков</h4>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-4 bg-blue-50 rounded">
              <div className="text-xl font-bold text-blue-600">{calculation.riskAdjustedROI.toFixed(2)}%</div>
              <div className="text-sm text-gray-600">Скорректированный ROI</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded">
              <div className="text-xl font-bold text-green-600">{calculation.scenarioAnalysis.optimistic.toFixed(2)}%</div>
              <div className="text-sm text-gray-600">Оптимистичный</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded">
              <div className="text-xl font-bold text-red-600">{calculation.scenarioAnalysis.pessimistic.toFixed(2)}%</div>
              <div className="text-sm text-gray-600">Пессимистичный</div>
            </div>
          </div>
        </div>

        {/* Денежные потоки */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h4 className="text-lg font-semibold mb-4">Денежные потоки</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Период</th>
                  <th className="text-right py-2">Чистый поток</th>
                  <th className="text-right py-2">Накопленный</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2 font-medium">Начальные инвестиции</td>
                  <td className="py-2 text-right text-red-600">
                    -{calculation.totalInvestment.toLocaleString()}
                  </td>
                  <td className="py-2 text-right">
                    -{calculation.totalInvestment.toLocaleString()}
                  </td>
                </tr>
                {calculation.netCashFlow.map((flow, index) => (
                  <tr key={index} className="border-b">
                    <td className="py-2">Год {index + 1}</td>
                    <td className={`py-2 text-right ${flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {flow.toLocaleString()}
                    </td>
                    <td className="py-2 text-right">
                      {calculation.cumulativeCashFlow[index].toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Отрисовка формы создания проекта
  const renderProjectForm = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Название проекта
          </label>
          <input
            type="text"
            value={projectForm.name}
            onChange={(e) => setProjectForm({...projectForm, name: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Например: Автоматизация складского учета"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Категория
          </label>
          <select
            value={projectForm.category}
            onChange={(e) => setProjectForm({...projectForm, category: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="automation">Автоматизация</option>
            <option value="integration">Интеграция</option>
            <option value="reporting">Отчетность</option>
            <option value="user-interface">Пользовательский интерфейс</option>
            <option value="data-management">Управление данными</option>
            <option value="custom">Пользовательская</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Описание
        </label>
        <textarea
          value={projectForm.description}
          onChange={(e) => setProjectForm({...projectForm, description: e.target.value})}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          placeholder="Описание проекта и его целей"
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Приоритет
          </label>
          <select
            value={projectForm.priority}
            onChange={(e) => setProjectForm({...projectForm, priority: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="low">Низкий</option>
            <option value="medium">Средний</option>
            <option value="high">Высокий</option>
            <option value="critical">Критический</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Статус
          </label>
          <select
            value={projectForm.status}
            onChange={(e) => setProjectForm({...projectForm, status: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="planning">Планирование</option>
            <option value="analysis">Анализ</option>
            <option value="development">Разработка</option>
            <option value="testing">Тестирование</option>
            <option value="deployed">Внедрен</option>
            <option value="completed">Завершен</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Уровень риска
          </label>
          <select
            value={projectForm.riskLevel}
            onChange={(e) => setProjectForm({...projectForm, riskLevel: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="low">Низкий</option>
            <option value="medium">Средний</option>
            <option value="high">Высокий</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Стоимость разработки (руб.)
          </label>
          <input
            type="number"
            value={projectForm.developmentCost}
            onChange={(e) => setProjectForm({...projectForm, developmentCost: parseFloat(e.target.value) || 0})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Стоимость внедрения (руб.)
          </label>
          <input
            type="number"
            value={projectForm.implementationCost}
            onChange={(e) => setProjectForm({...projectForm, implementationCost: parseFloat(e.target.value) || 0})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Стоимость сопровождения/год (руб.)
          </label>
          <input
            type="number"
            value={projectForm.maintenanceCost}
            onChange={(e) => setProjectForm({...projectForm, maintenanceCost: parseFloat(e.target.value) || 0})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium mb-3">Экономия времени</h4>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Часов на операцию
            </label>
            <input
              type="number"
              step="0.1"
              value={projectForm.timeSavingsHours}
              onChange={(e) => setProjectForm({...projectForm, timeSavingsHours: parseFloat(e.target.value) || 0})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Операций в месяц
            </label>
            <input
              type="number"
              value={projectForm.timeSavingsTransactions}
              onChange={(e) => setProjectForm({...projectForm, timeSavingsTransactions: parseInt(e.target.value) || 0})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Стоимость часа (руб.)
            </label>
            <input
              type="number"
              value={projectForm.timeSavingsRate}
              onChange={(e) => setProjectForm({...projectForm, timeSavingsRate: parseFloat(e.target.value) || 0})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <button
          onClick={() => setShowProjectModal(false)}
          className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
        >
          Отмена
        </button>
        <button
          onClick={handleCreateProject}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Создать проект
        </button>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">ROI калькулятор</h2>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              Проектов: {projects.length}
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={handleExportProjects}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              >
                📥 Экспорт
              </button>
              <label className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 cursor-pointer">
                📤 Импорт
                <input
                  type="file"
                  accept=".json"
                  onChange={handleImportProjects}
                  className="hidden"
                />
              </label>
              <button
                onClick={handleGenerateReport}
                className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700"
              >
                📊 Отчет
              </button>
              <button
                onClick={() => setShowProjectModal(true)}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                + Проект
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Навигация по вкладкам */}
      <div className="bg-white border-b border-gray-200">
        <nav className="flex space-x-8 px-4">
          <button
            onClick={() => setActiveView('overview')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeView === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Обзор
          </button>
          <button
            onClick={() => setActiveView('analysis')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeView === 'analysis'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Анализ проекта
          </button>
          <button
            onClick={() => setActiveView('comparison')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeView === 'comparison'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Сравнение
          </button>
        </nav>
      </div>

      {/* Выбор проекта */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center space-x-4">
          <select
            value={selectedProject || ''}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Выберите проект</option>
            {projects.map(project => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>

          {calculation && (
            <div className="flex items-center space-x-4 text-sm">
              <div className="text-gray-600">
                ROI: <span className="font-bold text-green-600">{calculation.roiPercentage.toFixed(1)}%</span>
              </div>
              <div className="text-gray-600">
                NPV: <span className={`font-bold ${calculation.netPresentValue >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {calculation.netPresentValue.toLocaleString()} руб.
                </span>
              </div>
              <div className="text-gray-600">
                Окупаемость: <span className="font-bold">{calculation.paybackPeriod.toFixed(1)} мес.</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Контент */}
      <div className="flex-1 overflow-auto p-6">
        {activeView === 'overview' && renderOverview()}
        {activeView === 'analysis' && renderAnalysis()}
        {activeView === 'comparison' && (
          <div className="text-center py-8 text-gray-500">
            Функция сравнения проектов будет доступна в следующей версии
          </div>
        )}
      </div>

      {/* Модальное окно создания проекта */}
      {showProjectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-6">Создать новый ROI проект</h3>
            {renderProjectForm()}
          </div>
        </div>
      )}
    </div>
  );
};

export default ROICalculatorView;