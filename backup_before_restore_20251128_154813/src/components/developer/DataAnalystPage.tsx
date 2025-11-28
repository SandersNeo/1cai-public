/**
 * Интеграционная страница Data Analyst
 * Объединяет все компоненты аналитики данных в едином интерфейсе
 */

import React, { useState } from 'react';
import DashboardView from './DashboardView';
import MLAnalysisView from './MLAnalysisView';
import ETLProcessorView from './ETLProcessorView';
import AnomalyDetectorView from './AnomalyDetectorView';

interface DataAnalystPageProps {
  className?: string;
}

export const DataAnalystPage: React.FC<DataAnalystPageProps> = ({ className = '' }) => {
  const [activeModule, setActiveModule] = useState<'overview' | 'dashboards' | 'ml' | 'etl' | 'anomalies'>('overview');
  const [isLoading, setIsLoading] = useState(false);

  const handleModuleSwitch = (module: typeof activeModule) => {
    setIsLoading(true);
    setTimeout(() => {
      setActiveModule(module);
      setIsLoading(false);
    }, 300);
  };

  const renderOverview = () => {
    const mockStats = {
      totalDashboards: 12,
      activeDashboards: 8,
      totalModels: 15,
      trainedModels: 12,
      etlJobs: 25,
      activeJobs: 18,
      anomalyJobs: 8,
      activeAnomalyJobs: 6,
      totalAnomalies: 45,
      resolvedAnomalies: 38,
      dataQualityScore: 94.2,
      systemHealth: 97.8
    };

    return (
      <div className="data-analyst-overview">
        <div className="overview-header">
          <h1>📊 Data Analyst - Центр аналитики данных</h1>
          <p>Комплексная платформа для анализа данных 1C с ML, ETL и мониторингом</p>
        </div>

        <div className="overview-grid">
          <div className="overview-card primary">
            <div className="card-header">
              <h3>📈 Интерактивные дашборды</h3>
              <span className="card-icon">📊</span>
            </div>
            <div className="card-content">
              <div className="stat-row">
                <span>Всего дашбордов:</span>
                <strong>{mockStats.totalDashboards}</strong>
              </div>
              <div className="stat-row">
                <span>Активных:</span>
                <strong>{mockStats.activeDashboards}</strong>
              </div>
              <div className="stat-row">
                <span>Публичных:</span>
                <strong>5</strong>
              </div>
              <div className="stat-row">
                <span>Просмотров за месяц:</span>
                <strong>1,247</strong>
              </div>
            </div>
            <div className="card-actions">
              <button 
                className="btn btn-primary"
                onClick={() => handleModuleSwitch('dashboards')}
              >
                Открыть дашборды
              </button>
              <button className="btn btn-outline">
                Создать новый
              </button>
            </div>
          </div>

          <div className="overview-card primary">
            <div className="card-header">
              <h3>🤖 ML Анализ и прогнозирование</h3>
              <span className="card-icon">🧠</span>
            </div>
            <div className="card-content">
              <div className="stat-row">
                <span>Всего моделей:</span>
                <strong>{mockStats.totalModels}</strong>
              </div>
              <div className="stat-row">
                <span>Обученных:</span>
                <strong>{mockStats.trainedModels}</strong>
              </div>
              <div className="stat-row">
                <span>Средняя точность:</span>
                <strong>87.3%</strong>
              </div>
              <div className="stat-row">
                <span>Предсказаний за сегодня:</span>
                <strong>1,056</strong>
              </div>
            </div>
            <div className="card-actions">
              <button 
                className="btn btn-primary"
                onClick={() => handleModuleSwitch('ml')}
              >
                Открыть ML Studio
              </button>
              <button className="btn btn-outline">
                Создать модель
              </button>
            </div>
          </div>

          <div className="overview-card primary">
            <div className="card-header">
              <h3>⚙️ ETL Процессы</h3>
              <span className="card-icon">🔄</span>
            </div>
            <div className="card-content">
              <div className="stat-row">
                <span>Всего заданий:</span>
                <strong>{mockStats.etlJobs}</strong>
              </div>
              <div className="stat-row">
                <span>Активных:</span>
                <strong>{mockStats.activeJobs}</strong>
              </div>
              <div className="stat-row">
                <span>Запусков сегодня:</span>
                <strong>234</strong>
              </div>
              <div className="stat-row">
                <span>Обработано записей:</span>
                <strong>2.4M</strong>
              </div>
            </div>
            <div className="card-actions">
              <button 
                className="btn btn-primary"
                onClick={() => handleModuleSwitch('etl')}
              >
                Открыть ETL Manager
              </button>
              <button className="btn btn-outline">
                Создать задание
              </button>
            </div>
          </div>

          <div className="overview-card primary">
            <div className="card-header">
              <h3>🚨 Обнаружение аномалий</h3>
              <span className="card-icon">🔍</span>
            </div>
            <div className="card-content">
              <div className="stat-row">
                <span>Заданий мониторинга:</span>
                <strong>{mockStats.anomalyJobs}</strong>
              </div>
              <div className="stat-row">
                <span>Активных:</span>
                <strong>{mockStats.activeAnomalyJobs}</strong>
              </div>
              <div className="stat-row">
                <span>Обнаружено аномалий:</span>
                <strong className="warning">{mockStats.totalAnomalies}</strong>
              </div>
              <div className="stat-row">
                <span>Разрешено:</span>
                <strong className="success">{mockStats.resolvedAnomalies}</strong>
              </div>
            </div>
            <div className="card-actions">
              <button 
                className="btn btn-primary"
                onClick={() => handleModuleSwitch('anomalies')}
              >
                Открыть мониторинг
              </button>
              <button className="btn btn-outline">
                Настроить алерты
              </button>
            </div>
          </div>
        </div>

        <div className="overview-metrics">
          <div className="metrics-section">
            <h3>Системные метрики</h3>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-icon">💾</div>
                <div className="metric-content">
                  <div className="metric-value">{mockStats.dataQualityScore}%</div>
                  <div className="metric-label">Качество данных</div>
                </div>
                <div className="metric-trend positive">↗ +2.1%</div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">⚡</div>
                <div className="metric-content">
                  <div className="metric-value">{mockStats.systemHealth}%</div>
                  <div className="metric-label">Здоровье системы</div>
                </div>
                <div className="metric-trend stable">→ Стабильно</div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">⏱️</div>
                <div className="metric-content">
                  <div className="metric-value">1.2с</div>
                  <div className="metric-label">Среднее время ответа</div>
                </div>
                <div className="metric-trend positive">↗ -0.3с</div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">📊</div>
                <div className="metric-content">
                  <div className="metric-value">98.7%</div>
                  <div className="metric-label">Время работы</div>
                </div>
                <div className="metric-trend positive">↗ +0.2%</div>
              </div>
            </div>
          </div>

          <div className="recent-activities">
            <h3>Последние активности</h3>
            <div className="activities-list">
              <div className="activity-item success">
                <div className="activity-icon">✅</div>
                <div className="activity-content">
                  <div className="activity-title">ETL задание "Синхронизация клиентов" завершено успешно</div>
                  <div className="activity-time">2 минуты назад</div>
                </div>
              </div>

              <div className="activity-item warning">
                <div className="activity-icon">⚠️</div>
                <div className="activity-content">
                  <div className="activity-title">Обнаружена аномалия в данных продаж (критический уровень)</div>
                  <div className="activity-time">15 минут назад</div>
                </div>
              </div>

              <div className="activity-item info">
                <div className="activity-icon">📊</div>
                <div className="activity-content">
                  <div className="activity-title">Создан новый дашборд "Финансовая аналитика Q4"</div>
                  <div className="activity-time">1 час назад</div>
                </div>
              </div>

              <div className="activity-item success">
                <div className="activity-icon">🤖</div>
                <div className="activity-content">
                  <div className="activity-title">Модель машинного обучения "Прогноз продаж" переобучена</div>
                  <div className="activity-time">2 часа назад</div>
                </div>
              </div>

              <div className="activity-item info">
                <div className="activity-icon">🔄</div>
                <div className="activity-content">
                  <div className="activity-title">Запущено еженедельное ETL задание "Архивирование данных"</div>
                  <div className="activity-time">4 часа назад</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="quick-actions">
          <h3>Быстрые действия</h3>
          <div className="actions-grid">
            <button className="action-card" onClick={() => handleModuleSwitch('dashboards')}>
              <span className="action-icon">📊</span>
              <span className="action-title">Создать дашборд</span>
              <span className="action-desc">Создать новую аналитическую панель</span>
            </button>

            <button className="action-card" onClick={() => handleModuleSwitch('ml')}>
              <span className="action-icon">🤖</span>
              <span className="action-title">Обучить модель</span>
              <span className="action-desc">Создать и обучить ML модель</span>
            </button>

            <button className="action-card" onClick={() => handleModuleSwitch('etl')}>
              <span className="action-icon">⚙️</span>
              <span className="action-title">Настроить ETL</span>
              <span className="action-desc">Создать новое ETL задание</span>
            </button>

            <button className="action-card" onClick={() => handleModuleSwitch('anomalies')}>
              <span className="action-icon">🔍</span>
              <span className="action-title">Настроить мониторинг</span>
              <span className="action-desc">Добавить мониторинг аномалий</span>
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderActiveModule = () => {
    switch (activeModule) {
      case 'dashboards':
        return <DashboardView className="module-content" />;
      case 'ml':
        return <MLAnalysisView className="module-content" />;
      case 'etl':
        return <ETLProcessorView className="module-content" />;
      case 'anomalies':
        return <AnomalyDetectorView className="module-content" />;
      default:
        return renderOverview();
    }
  };

  return (
    <div className={`data-analyst-page ${className}`}>
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            {activeModule === 'overview' && (
              <>
                <h1>📊 Data Analyst</h1>
                <p>Центр аналитики данных 1C</p>
              </>
            )}
            {activeModule !== 'overview' && (
              <>
                <button 
                  className="btn btn-secondary btn-sm back-btn"
                  onClick={() => handleModuleSwitch('overview')}
                >
                  ← Назад к обзору
                </button>
                <div className="module-title">
                  <span className="module-icon">
                    {activeModule === 'dashboards' && '📊'}
                    {activeModule === 'ml' && '🤖'}
                    {activeModule === 'etl' && '⚙️'}
                    {activeModule === 'anomalies' && '🔍'}
                  </span>
                  <span>
                    {activeModule === 'dashboards' && 'Интерактивные дашборды'}
                    {activeModule === 'ml' && 'ML Анализ и прогнозирование'}
                    {activeModule === 'etl' && 'ETL Процессы'}
                    {activeModule === 'anomalies' && 'Обнаружение аномалий'}
                  </span>
                </div>
              </>
            )}
          </div>

          <div className="header-navigation">
            <button 
              className={`nav-btn ${activeModule === 'overview' ? 'active' : ''}`}
              onClick={() => handleModuleSwitch('overview')}
            >
              <span className="nav-icon">🏠</span>
              <span className="nav-label">Обзор</span>
            </button>
            <button 
              className={`nav-btn ${activeModule === 'dashboards' ? 'active' : ''}`}
              onClick={() => handleModuleSwitch('dashboards')}
            >
              <span className="nav-icon">📊</span>
              <span className="nav-label">Дашборды</span>
            </button>
            <button 
              className={`nav-btn ${activeModule === 'ml' ? 'active' : ''}`}
              onClick={() => handleModuleSwitch('ml')}
            >
              <span className="nav-icon">🤖</span>
              <span className="nav-label">ML</span>
            </button>
            <button 
              className={`nav-btn ${activeModule === 'etl' ? 'active' : ''}`}
              onClick={() => handleModuleSwitch('etl')}
            >
              <span className="nav-icon">⚙️</span>
              <span className="nav-label">ETL</span>
            </button>
            <button 
              className={`nav-btn ${activeModule === 'anomalies' ? 'active' : ''}`}
              onClick={() => handleModuleSwitch('anomalies')}
            >
              <span className="nav-icon">🔍</span>
              <span className="nav-label">Аномалии</span>
            </button>
          </div>
        </div>
      </div>

      <div className="page-content">
        {isLoading ? (
          <div className="loading-overlay">
            <div className="loading-spinner">⏳</div>
            <div className="loading-text">Загрузка модуля...</div>
          </div>
        ) : (
          renderActiveModule()
        )}
      </div>
    </div>
  );
};

export default DataAnalystPage;