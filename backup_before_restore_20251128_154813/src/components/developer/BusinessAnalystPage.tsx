/**
 * Страница Business Analyst - интеграционная тестовая страница
 * Объединяет все компоненты Business Analyst модуля в единый интерфейс
 */

import React, { useState, useEffect } from 'react';
import {
  BPMNDiagramEditor
} from '../../components/developer/BPMNDiagramEditor';
import RequirementAnalyzer from '../../components/developer/RequirementAnalyzer';
import TraceabilityMatrixView from '../../components/developer/TraceabilityMatrixView';
import ROICalculatorView from '../../components/developer/ROICalculatorView';
import { BPMNDiagram } from '../../services/bpmn-diagram-service';
import { Requirement } from '../../services/nlp-analysis-service';
import { TraceabilityMatrix } from '../../services/traceability-matrix-service';
import { ROIProject } from '../../services/roi-calculator-service';

interface BusinessAnalystPageProps {
  className?: string;
}

interface DashboardStats {
  totalDiagrams: number;
  totalRequirements: number;
  totalMatrices: number;
  totalProjects: number;
  averageROI: number;
  coveragePercentage: number;
}

export const BusinessAnalystPage: React.FC<BusinessAnalystPageProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
    totalDiagrams: 0,
    totalRequirements: 0,
    totalMatrices: 0,
    totalProjects: 0,
    averageROI: 0,
    coveragePercentage: 0
  });

  // Вкладки модуля
  const tabs = [
    { id: 'dashboard', label: 'Панель управления', icon: '📊' },
    { id: 'bpmn', label: 'BPMN диаграммы', icon: '🔄' },
    { id: 'requirements', label: 'Анализ требований', icon: '📝' },
    { id: 'traceability', label: 'Матрица трассируемости', icon: '🔗' },
    { id: 'roi', label: 'ROI калькулятор', icon: '💰' },
    { id: 'reports', label: 'Отчеты', icon: '📈' }
  ];

  // Загрузка статистики при монтировании
  useEffect(() => {
    loadDashboardStats();
  }, []);

  const loadDashboardStats = () => {
    // В реальном приложении здесь был бы загрузка из сервисов
    // Для демо используем моковые данные
    setDashboardStats({
      totalDiagrams: 3,
      totalRequirements: 12,
      totalMatrices: 2,
      totalProjects: 8,
      averageROI: 45.8,
      coveragePercentage: 78.5
    });
  };

  // Обработчики изменений от компонентов
  const handleBPMNChange = (diagram: BPMNDiagram) => {
    console.log('BPMN диаграмма изменена:', diagram.name);
    loadDashboardStats();
  };

  const handleRequirementAnalysis = (requirement: Requirement) => {
    console.log('Требование проанализировано:', requirement.title);
    loadDashboardStats();
  };

  const handleMatrixChange = (matrix: TraceabilityMatrix) => {
    console.log('Матрица трассируемости изменена:', matrix.name);
    loadDashboardStats();
  };

  const handleROIChange = (project: ROIProject) => {
    console.log('ROI проект изменен:', project.name);
    loadDashboardStats();
  };

  // Отрисовка панели управления
  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Обзорные метрики */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">BPMN диаграммы</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardStats.totalDiagrams}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Требования</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardStats.totalRequirements}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Матрицы</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardStats.totalMatrices}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">ROI проекты</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardStats.totalProjects}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100 text-red-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Средний ROI</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardStats.averageROI}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-indigo-100 text-indigo-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Покрытие</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardStats.coveragePercentage}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Быстрые действия */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Быстрые действия</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button
              onClick={() => setActiveTab('bpmn')}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left transition-colors"
            >
              <div className="text-2xl mb-2">🔄</div>
              <div className="font-medium">Создать BPMN диаграмму</div>
              <div className="text-sm text-gray-600">Моделирование бизнес-процессов</div>
            </button>

            <button
              onClick={() => setActiveTab('requirements')}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left transition-colors"
            >
              <div className="text-2xl mb-2">📝</div>
              <div className="font-medium">Анализировать требования</div>
              <div className="text-sm text-gray-600">NLP анализ текстовых требований</div>
            </button>

            <button
              onClick={() => setActiveTab('traceability')}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left transition-colors"
            >
              <div className="text-2xl mb-2">🔗</div>
              <div className="font-medium">Создать матрицу</div>
              <div className="text-sm text-gray-600">Трассируемость требований</div>
            </button>

            <button
              onClick={() => setActiveTab('roi')}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left transition-colors"
            >
              <div className="text-2xl mb-2">💰</div>
              <div className="font-medium">Рассчитать ROI</div>
              <div className="text-sm text-gray-600">Экономическая эффективность</div>
            </button>
          </div>
        </div>
      </div>

      {/* Последняя активность */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Последняя активность</h3>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-sm">🔄</span>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">Создана BPMN диаграмма "Процесс обработки заказа"</div>
                <div className="text-sm text-gray-500">2 часа назад</div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 text-sm">📝</span>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">Проанализированы требования для модуля "Складской учет"</div>
                <div className="text-sm text-gray-500">4 часа назад</div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600 text-sm">🔗</span>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">Обновлена матрица трассируемости "Требования → Тесты"</div>
                <div className="text-sm text-gray-500">1 день назад</div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 text-sm">💰</span>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">Рассчитан ROI для проекта "Автоматизация отчетности"</div>
                <div className="text-sm text-gray-500">2 дня назад</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Отрисовка отчетов
  const renderReports = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Готовые отчеты Business Analyst</h3>
        </div>
        <div className="p-6">
          <div className="grid gap-4">
            <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <div className="font-medium">Сводный отчет по BPMN диаграммам</div>
                  <div className="text-sm text-gray-600">Анализ всех бизнес-процессов в системе</div>
                </div>
              </div>
              <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Скачать PDF
              </button>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <div className="font-medium">Отчет по анализу требований</div>
                  <div className="text-sm text-gray-600">Результаты NLP анализа и извлеченные сущности</div>
                </div>
              </div>
              <button className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                Скачать DOCX
              </button>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                </div>
                <div>
                  <div className="font-medium">Матрица трассируемости</div>
                  <div className="text-sm text-gray-600">Связи между требованиями, тестами и компонентами</div>
                </div>
              </div>
              <button className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">
                Скачать Excel
              </button>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <div>
                  <div className="font-medium">ROI анализ проектов</div>
                  <div className="text-sm text-gray-600">Экономическая эффективность и рейтинг проектов</div>
                </div>
              </div>
              <button className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700">
                Скачать PPTX
              </button>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <div className="font-medium">Комплексный отчет Business Analyst</div>
                  <div className="text-sm text-gray-600">Объединенный отчет по всем модулям</div>
                </div>
              </div>
              <button className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
                Скачать PDF
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`h-full flex flex-col bg-gray-50 ${className}`}>
      {/* Заголовок */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Business Analyst Module</h2>
            <p className="text-sm text-gray-600">Модуль бизнес-анализа для 1C проектов</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-500">
              Последнее обновление: {new Date().toLocaleTimeString()}
            </div>
            <div className="flex space-x-2">
              <button className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200">
                ⚙️ Настройки
              </button>
              <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
                💾 Сохранить все
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Навигация по вкладкам */}
      <div className="bg-white border-b border-gray-200">
        <nav className="flex space-x-8 px-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Основной контент */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'dashboard' && renderDashboard()}
        
        {activeTab === 'bpmn' && (
          <BPMNDiagramEditor
            width={1200}
            height={700}
            onDiagramChange={handleBPMNChange}
          />
        )}
        
        {activeTab === 'requirements' && (
          <RequirementAnalyzer
            onAnalysisComplete={handleRequirementAnalysis}
          />
        )}
        
        {activeTab === 'traceability' && (
          <TraceabilityMatrixView
            onMatrixChange={handleMatrixChange}
          />
        )}
        
        {activeTab === 'roi' && (
          <ROICalculatorView
            onProjectChange={handleROIChange}
          />
        )}
        
        {activeTab === 'reports' && renderReports()}
      </div>
    </div>
  );
};

export default BusinessAnalystPage;