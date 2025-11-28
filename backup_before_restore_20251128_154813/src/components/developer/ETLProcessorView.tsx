/**
 * UI компонент для ETL процессов
 * Предоставляет интерфейс для создания и управления ETL заданиями
 */

import React, { useState, useEffect } from 'react';
import { ETLService, ETLJob, TransformationStep, ExecutionLog } from '../../services/etl-service';

interface ETLProcessorViewProps {
  className?: string;
}

export const ETLProcessorView: React.FC<ETLProcessorViewProps> = ({ className = '' }) => {
  const [etlService] = useState(() => new ETLService());
  const [activeTab, setActiveTab] = useState<'jobs' | 'executions' | 'monitoring' | 'quality'>('jobs');
  const [jobs, setJobs] = useState<ETLJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<ETLJob | null>(null);
  const [executions, setExecutions] = useState<ExecutionLog[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [jobConfig, setJobConfig] = useState({
    name: '',
    description: '',
    sourceType: '1c_database' as const,
    destinationType: '1c_database' as const,
    transformations: [] as Omit<TransformationStep, 'id'>[]
  });

  useEffect(() => {
    loadJobs();
    loadExecutions();
  }, []);

  const loadJobs = () => {
    const allJobs = etlService.getAllJobs();
    setJobs(allJobs);
  };

  const loadExecutions = () => {
    if (selectedJob) {
      const jobExecutions = etlService.getJobExecutionLogs(selectedJob.id);
      setExecutions(jobExecutions);
    }
  };

  const createJob = async () => {
    if (!jobConfig.name.trim()) {
      alert('Введите название задания');
      return;
    }

    setIsRunning(true);
    try {
      const jobId = etlService.createJob(jobConfig.name, jobConfig.description);
      
      // Настройка источника данных
      etlService.updateSource(jobId, {
        type: jobConfig.sourceType,
        config: {
          database: '1c_source',
          tableName: 'source_table'
        }
      });

      // Настройка места назначения
      etlService.updateDestination(jobId, {
        type: jobConfig.destinationType,
        config: {
          database: '1c_destination',
          tableName: 'destination_table',
          createTable: true,
          upsert: true
        }
      });

      // Добавление трансформаций
      for (const transform of jobConfig.transformations) {
        etlService.addTransformation(jobId, transform);
      }

      loadJobs();
      setIsCreating(false);
      setJobConfig({
        name: '',
        description: '',
        sourceType: '1c_database',
        destinationType: '1c_database',
        transformations: []
      });
    } catch (error) {
      console.error('Ошибка создания задания:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const runJob = async (jobId: string) => {
    setIsRunning(true);
    try {
      const executionId = await etlService.runJob(jobId);
      
      // Обновление списков после завершения
      setTimeout(() => {
        loadJobs();
        if (selectedJob?.id === jobId) {
          loadExecutions();
        }
        setIsRunning(false);
      }, 2000);
    } catch (error) {
      console.error('Ошибка запуска задания:', error);
      setIsRunning(false);
    }
  };

  const runAllJobs = async () => {
    setIsRunning(true);
    try {
      const executionIds = await etlService.runAllActiveJobs();
      
      // Обновление списков
      setTimeout(() => {
        loadJobs();
        setIsRunning(false);
      }, 3000);
    } catch (error) {
      console.error('Ошибка запуска заданий:', error);
      setIsRunning(false);
    }
  };

  const updateJobStatus = (jobId: string, status: ETLJob['status']) => {
    etlService.updateJobStatus(jobId, status);
    loadJobs();
  };

  const addTransformation = (type: string) => {
    const newTransform: Omit<TransformationStep, 'id'> = {
      name: getTransformationName(type),
      type: type as any,
      config: getDefaultTransformConfig(type),
      order: jobConfig.transformations.length + 1,
      enabled: true
    };

    setJobConfig({
      ...jobConfig,
      transformations: [...jobConfig.transformations, newTransform]
    });
  };

  const removeTransformation = (index: number) => {
    setJobConfig({
      ...jobConfig,
      transformations: jobConfig.transformations.filter((_, i) => i !== index)
    });
  };

  const getTransformationName = (type: string): string => {
    const names: Record<string, string> = {
      'filter': 'Фильтрация данных',
      'map': 'Преобразование полей',
      'aggregate': 'Агрегация данных',
      'join': 'Объединение таблиц',
      'clean': 'Очистка данных',
      'convert': 'Конвертация типов',
      'enrich': 'Обогащение данными',
      'validate': 'Валидация данных'
    };
    return names[type] || 'Новая трансформация';
  };

  const getDefaultTransformConfig = (type: string) => {
    switch (type) {
      case 'filter':
        return {
          conditions: [
            { field: 'amount', operator: 'gt', value: 0 }
          ],
          logicalOperator: 'and'
        };
      case 'map':
        return {
          mappings: [
            { sourceField: 'old_field', targetField: 'new_field' }
          ]
        };
      case 'aggregate':
        return {
          groupBy: ['category'],
          aggregations: [
            { field: 'amount', function: 'sum', alias: 'total_amount' }
          ]
        };
      case 'clean':
        return {
          removeNulls: true,
          trimStrings: true,
          validateEmails: false
        };
      case 'convert':
        return {
          field: 'amount',
          function: 'number'
        };
      case 'enrich':
        return {
          enrichmentSource: {
            type: 'lookup_table',
            config: { table: 'reference_data' }
          },
          matchingFields: [
            { sourceField: 'category', targetField: 'category', matchType: 'exact' }
          ],
          outputFields: ['description', 'parent_category']
        };
      default:
        return {};
    }
  };

  const renderJobsTab = () => (
    <div className="jobs-tab">
      <div className="tab-header">
        <h3>ETL задания</h3>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setIsCreating(true)}
          >
            + Создать задание
          </button>
          <button 
            className="btn btn-secondary"
            onClick={runAllJobs}
            disabled={isRunning}
          >
            Запустить все активные
          </button>
        </div>
      </div>

      <div className="jobs-grid">
        {jobs.map(job => (
          <div 
            key={job.id}
            className={`job-card ${selectedJob?.id === job.id ? 'selected' : ''}`}
            onClick={() => {
              setSelectedJob(job);
              loadExecutions();
            }}
          >
            <div className="job-header">
              <h4>{job.name}</h4>
              <div className="job-status">
                <span className={`status-badge ${job.status}`}>
                  {job.status === 'active' && 'Активно'}
                  {job.status === 'paused' && 'Приостановлено'}
                  {job.status === 'draft' && 'Черновик'}
                  {job.status === 'failed' && 'Ошибка'}
                  {job.status === 'completed' && 'Завершено'}
                </span>
              </div>
            </div>

            <div className="job-info">
              <p className="job-description">{job.description}</p>
              
              <div className="job-metrics">
                <div className="metric">
                  <span className="metric-label">Запусков:</span>
                  <span className="metric-value">{job.statistics.totalRuns}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Успешно:</span>
                  <span className="metric-value success">{job.statistics.successfulRuns}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Ошибки:</span>
                  <span className="metric-value error">{job.statistics.failedRuns}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Записей:</span>
                  <span className="metric-value">{job.statistics.totalRecordsProcessed}</span>
                </div>
              </div>

              <div className="job-schedule">
                {job.schedule ? (
                  <span className="schedule-info">
                    Расписание: {job.schedule.type}
                    {job.nextRun && (
                      <span className="next-run">
                        Следующий запуск: {new Date(job.nextRun).toLocaleString()}
                      </span>
                    )}
                  </span>
                ) : (
                  <span className="schedule-info manual">Вручную</span>
                )}
              </div>

              {job.lastRun && (
                <div className="job-last-run">
                  Последний запуск: {new Date(job.lastRun).toLocaleString()}
                </div>
              )}
            </div>

            <div className="job-actions">
              {job.status === 'active' ? (
                <button 
                  className="btn btn-sm btn-warning"
                  onClick={(e) => {
                    e.stopPropagation();
                    updateJobStatus(job.id, 'paused');
                  }}
                >
                  Пауза
                </button>
              ) : (
                <button 
                  className="btn btn-sm btn-success"
                  onClick={(e) => {
                    e.stopPropagation();
                    updateJobStatus(job.id, 'active');
                  }}
                >
                  Активировать
                </button>
              )}
              
              <button 
                className="btn btn-sm btn-primary"
                onClick={(e) => {
                  e.stopPropagation();
                  runJob(job.id);
                }}
                disabled={isRunning}
              >
                Запустить
              </button>
              
              <button 
                className="btn btn-sm btn-outline"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedJob(job);
                  loadExecutions();
                  setActiveTab('executions');
                }}
              >
                Логи
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedJob && (
        <div className="job-details">
          <h3>Детали задания: {selectedJob.name}</h3>
          
          <div className="details-grid">
            <div className="detail-section">
              <h4>Источник данных</h4>
              <div className="detail-item">
                <strong>Тип:</strong> {selectedJob.source.type}
              </div>
              {selectedJob.source.config.tableName && (
                <div className="detail-item">
                  <strong>Таблица:</strong> {selectedJob.source.config.tableName}
                </div>
              )}
            </div>

            <div className="detail-section">
              <h4>Место назначения</h4>
              <div className="detail-item">
                <strong>Тип:</strong> {selectedJob.destination.type}
              </div>
              {selectedJob.destination.config.tableName && (
                <div className="detail-item">
                  <strong>Таблица:</strong> {selectedJob.destination.config.tableName}
                </div>
              )}
              <div className="detail-item">
                <strong>Режим:</strong> 
                {selectedJob.destination.upsert ? 'Обновление/вставка' : 'Только вставка'}
              </div>
            </div>

            <div className="detail-section">
              <h4>Трансформации ({selectedJob.transformations.length})</h4>
              {selectedJob.transformations.map(transform => (
                <div key={transform.id} className="transform-item">
                  <span className={`transform-status ${transform.enabled ? 'enabled' : 'disabled'}`}>
                    {transform.enabled ? '✓' : '○'}
                  </span>
                  <span className="transform-name">{transform.name}</span>
                  <span className="transform-type">{transform.type}</span>
                </div>
              ))}
            </div>

            <div className="detail-section">
              <h4>Статистика</h4>
              <div className="stat-grid">
                <div className="stat-item">
                  <span className="stat-value">{selectedJob.statistics.successRate.toFixed(1)}%</span>
                  <span className="stat-label">Успешность</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{(selectedJob.statistics.averageExecutionTime / 1000).toFixed(1)}с</span>
                  <span className="stat-label">Среднее время</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{selectedJob.statistics.errorRate.toFixed(1)}%</span>
                  <span className="stat-label">Ошибок</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{selectedJob.statistics.totalRecordsProcessed}</span>
                  <span className="stat-label">Всего записей</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderExecutionsTab = () => (
    <div className="executions-tab">
      <div className="tab-header">
        <h3>Журналы выполнения</h3>
        {selectedJob && (
          <span className="job-name">Задание: {selectedJob.name}</span>
        )}
      </div>

      <div className="executions-list">
        {executions.length > 0 ? (
          executions.map(execution => (
            <div key={execution.id} className={`execution-card ${execution.status}`}>
              <div className="execution-header">
                <div className="execution-status">
                  <span className={`status-indicator ${execution.status}`}>
                    {execution.status === 'success' && '✅'}
                    {execution.status === 'failed' && '❌'}
                    {execution.status === 'running' && '⏳'}
                    {execution.status === 'cancelled' && '⏹️'}
                  </span>
                  <span className="execution-time">
                    {new Date(execution.startTime).toLocaleString()}
                  </span>
                </div>
                
                <div className="execution-duration">
                  {execution.endTime ? 
                    `${((execution.endTime.getTime() - execution.startTime.getTime()) / 1000).toFixed(1)}с` :
                    'Выполняется...'
                  }
                </div>
              </div>

              <div className="execution-metrics">
                <div className="metric-item">
                  <span className="metric-label">Обработано:</span>
                  <span className="metric-value">{execution.recordsProcessed.toLocaleString()}</span>
                </div>
                <div className="metric-item success">
                  <span className="metric-label">Загружено:</span>
                  <span className="metric-value">{execution.recordsLoaded.toLocaleString()}</span>
                </div>
                <div className="metric-item error">
                  <span className="metric-label">Ошибки:</span>
                  <span className="metric-value">{execution.recordsFailed}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Скорость:</span>
                  <span className="metric-value">{execution.metrics.throughput.toFixed(0)}/сек</span>
                </div>
              </div>

              {execution.errorMessage && (
                <div className="execution-error">
                  <strong>Ошибка:</strong> {execution.errorMessage}
                </div>
              )}

              {execution.warnings && execution.warnings.length > 0 && (
                <div className="execution-warnings">
                  <strong>Предупреждения:</strong>
                  <ul>
                    {execution.warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="execution-timing">
                <div className="timing-bar">
                  <div 
                    className="timing-segment read"
                    style={{ 
                      width: `${(execution.metrics.sourceReadTime / execution.metrics.totalTime) * 100}%` 
                    }}
                    title={`Чтение: ${(execution.metrics.sourceReadTime / 1000).toFixed(1)}с`}
                  />
                  <div 
                    className="timing-segment transform"
                    style={{ 
                      width: `${(execution.metrics.transformationTime / execution.metrics.totalTime) * 100}%` 
                    }}
                    title={`Трансформация: ${(execution.metrics.transformationTime / 1000).toFixed(1)}с`}
                  />
                  <div 
                    className="timing-segment write"
                    style={{ 
                      width: `${(execution.metrics.destinationWriteTime / execution.metrics.totalTime) * 100}%` 
                    }}
                    title={`Запись: ${(execution.metrics.destinationWriteTime / 1000).toFixed(1)}с`}
                  />
                </div>
                <div className="timing-legend">
                  <span className="legend-item read">Чтение</span>
                  <span className="legend-item transform">Трансформация</span>
                  <span className="legend-item write">Запись</span>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="no-executions">
            <p>Нет журналов выполнения для выбранного задания</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderMonitoringTab = () => {
    const statistics = etlService.getETLStatistics();
    
    return (
      <div className="monitoring-tab">
        <div className="tab-header">
          <h3>Мониторинг системы</h3>
        </div>

        <div className="monitoring-dashboard">
          <div className="dashboard-cards">
            <div className="dashboard-card">
              <h4>Общая статистика</h4>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{statistics.totalJobs}</div>
                  <div className="stat-label">Всего заданий</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{statistics.activeJobs}</div>
                  <div className="stat-label">Активных</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{statistics.totalExecutions}</div>
                  <div className="stat-label">Запусков</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{statistics.successfulExecutions}</div>
                  <div className="stat-label">Успешных</div>
                </div>
              </div>
            </div>

            <div className="dashboard-card">
              <h4>Производительность</h4>
              <div className="performance-metrics">
                <div className="metric-row">
                  <span>Обработано записей:</span>
                  <span className="metric-value">{statistics.totalRecordsProcessed.toLocaleString()}</span>
                </div>
                <div className="metric-row">
                  <span>Среднее время выполнения:</span>
                  <span className="metric-value">{(statistics.avgExecutionTime / 1000).toFixed(1)}с</span>
                </div>
                <div className="metric-row">
                  <span>Скорость обработки:</span>
                  <span className="metric-value">~{(statistics.totalRecordsProcessed / (statistics.totalExecutions * statistics.avgExecutionTime / 1000)).toFixed(0)}/сек</span>
                </div>
              </div>
            </div>
          </div>

          <div className="system-health">
            <h4>Состояние системы</h4>
            <div className="health-indicators">
              <div className="health-item healthy">
                <span className="health-icon">💚</span>
                <span className="health-label">База данных</span>
                <span className="health-status">Подключена</span>
              </div>
              <div className="health-item healthy">
                <span className="health-icon">💚</span>
                <span className="health-label">API сервисы</span>
                <span className="health-status">Доступны</span>
              </div>
              <div className="health-item warning">
                <span className="health-icon">💛</span>
                <span className="health-label">Внешние интеграции</span>
                <span className="health-status">Частично доступны</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderQualityTab = () => (
    <div className="quality-tab">
      <div className="tab-header">
        <h3>Качество данных</h3>
        <button className="btn btn-primary">
          Запустить проверки
        </button>
      </div>

      <div className="quality-dashboard">
        <div className="quality-checks">
          <div className="quality-card passed">
            <div className="quality-header">
              <h4>Полнота данных клиентов</h4>
              <span className="quality-score">98.5%</span>
            </div>
            <div className="quality-details">
              <p>Критическая полнота email-адресов составляет 98.5%</p>
              <div className="quality-metrics">
                <span>Всего записей: 1,000</span>
                <span>Прошло проверку: 985</span>
                <span>Не прошло: 15</span>
              </div>
            </div>
            <div className="quality-actions">
              <button className="btn btn-sm btn-outline">Детали</button>
              <button className="btn btn-sm btn-outline">Настройки</button>
            </div>
          </div>

          <div className="quality-card warning">
            <div className="quality-header">
              <h4>Точность финансовых данных</h4>
              <span className="quality-score">92.1%</span>
            </div>
            <div className="quality-details">
              <p>Обнаружены расхождения в 7.9% транзакций</p>
              <div className="quality-metrics">
                <span>Всего записей: 5,000</span>
                <span>Прошло проверку: 4,605</span>
                <span>Не прошло: 395</span>
              </div>
            </div>
            <div className="quality-actions">
              <button className="btn btn-sm btn-primary">Исправить</button>
              <button className="btn btn-sm btn-outline">Детали</button>
            </div>
          </div>

          <div className="quality-card passed">
            <div className="quality-header">
              <h4>Уникальность ключей</h4>
              <span className="quality-score">100%</span>
            </div>
            <div className="quality-details">
              <p>Все ключевые поля уникальны</p>
              <div className="quality-metrics">
                <span>Проверено таблиц: 12</span>
                <span>Дубликатов: 0</span>
              </div>
            </div>
            <div className="quality-actions">
              <button className="btn btn-sm btn-outline">Отчет</button>
            </div>
          </div>
        </div>

        <div className="quality-recommendations">
          <h4>Рекомендации по улучшению качества</h4>
          <ul className="recommendations-list">
            <li className="recommendation-item">
              <span className="recommendation-icon">⚠️</span>
              <div className="recommendation-content">
                <strong>Улучшить валидацию email</strong>
                <p>Добавить проверку формата email при вводе данных</p>
              </div>
            </li>
            <li className="recommendation-item">
              <span className="recommendation-icon">🔄</span>
              <div className="recommendation-content">
                <strong>Автоматическая синхронизация</strong>
                <p>Настроить регулярную проверку целостности данных</p>
              </div>
            </li>
            <li className="recommendation-item">
              <span className="recommendation-icon">📊</span>
              <div className="recommendation-content">
                <strong>Мониторинг качества</strong>
                <p>Добавить дашборд для отслеживания метрик качества данных</p>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );

  const renderCreateJobModal = () => (
    <div className="modal-overlay">
      <div className="modal large">
        <div className="modal-header">
          <h2>Создать ETL задание</h2>
          <button onClick={() => setIsCreating(false)}>×</button>
        </div>
        <div className="modal-content">
          <div className="job-config-form">
            <div className="form-section">
              <h3>Основная информация</h3>
              <div className="form-group">
                <label>Название задания:</label>
                <input 
                  type="text" 
                  value={jobConfig.name}
                  onChange={(e) => setJobConfig({...jobConfig, name: e.target.value})}
                  placeholder="Введите название задания"
                />
              </div>
              <div className="form-group">
                <label>Описание:</label>
                <textarea 
                  value={jobConfig.description}
                  onChange={(e) => setJobConfig({...jobConfig, description: e.target.value})}
                  placeholder="Описание задания"
                  rows={3}
                />
              </div>
            </div>

            <div className="form-section">
              <h3>Источник данных</h3>
              <div className="form-group">
                <label>Тип источника:</label>
                <select
                  value={jobConfig.sourceType}
                  onChange={(e) => setJobConfig({...jobConfig, sourceType: e.target.value as any})}
                >
                  <option value="1c_database">1C База данных</option>
                  <option value="external_database">Внешняя БД</option>
                  <option value="file">Файл</option>
                  <option value="api">API</option>
                  <option value="cloud_storage">Облачное хранилище</option>
                </select>
              </div>
            </div>

            <div className="form-section">
              <h3>Место назначения</h3>
              <div className="form-group">
                <label>Тип назначения:</label>
                <select
                  value={jobConfig.destinationType}
                  onChange={(e) => setJobConfig({...jobConfig, destinationType: e.target.value as any})}
                >
                  <option value="1c_database">1C База данных</option>
                  <option value="external_database">Внешняя БД</option>
                  <option value="file">Файл</option>
                  <option value="data_warehouse">Хранилище данных</option>
                </select>
              </div>
            </div>

            <div className="form-section">
              <h3>Трансформации</h3>
              <div className="transformations-palette">
                {['filter', 'map', 'aggregate', 'clean', 'convert', 'enrich', 'validate'].map(type => (
                  <button
                    key={type}
                    className="transform-add-btn"
                    onClick={() => addTransformation(type)}
                  >
                    + {getTransformationName(type)}
                  </button>
                ))}
              </div>

              {jobConfig.transformations.length > 0 && (
                <div className="transformations-list">
                  <h4>Добавленные трансформации:</h4>
                  {jobConfig.transformations.map((transform, index) => (
                    <div key={index} className="transform-item-config">
                      <div className="transform-header">
                        <span className="transform-order">{index + 1}</span>
                        <span className="transform-name">{transform.name}</span>
                        <button 
                          className="btn btn-sm btn-danger"
                          onClick={() => removeTransformation(index)}
                        >
                          Удалить
                        </button>
                      </div>
                      <div className="transform-config">
                        <code>{JSON.stringify(transform.config, null, 2)}</code>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="modal-footer">
          <button 
            className="btn btn-secondary" 
            onClick={() => setIsCreating(false)}
          >
            Отмена
          </button>
          <button 
            className="btn btn-primary" 
            onClick={createJob}
            disabled={isRunning || !jobConfig.name.trim()}
          >
            {isRunning ? 'Создание...' : 'Создать задание'}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`etl-processor-view ${className}`}>
      <div className="view-header">
        <h1>ETL Процессы</h1>
        <div className="view-actions">
          <button 
            className={`btn ${activeTab === 'jobs' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('jobs')}
          >
            Задания
          </button>
          <button 
            className={`btn ${activeTab === 'executions' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('executions')}
          >
            Выполнения
          </button>
          <button 
            className={`btn ${activeTab === 'monitoring' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('monitoring')}
          >
            Мониторинг
          </button>
          <button 
            className={`btn ${activeTab === 'quality' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('quality')}
          >
            Качество
          </button>
        </div>
      </div>

      <div className="view-content">
        {activeTab === 'jobs' && renderJobsTab()}
        {activeTab === 'executions' && renderExecutionsTab()}
        {activeTab === 'monitoring' && renderMonitoringTab()}
        {activeTab === 'quality' && renderQualityTab()}
      </div>

      {isCreating && renderCreateJobModal()}

      {isRunning && (
        <div className="running-overlay">
          <div className="running-modal">
            <div className="running-spinner">⚙️</div>
            <h3>Выполнение операции...</h3>
            <p>Пожалуйста, подождите</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ETLProcessorView;