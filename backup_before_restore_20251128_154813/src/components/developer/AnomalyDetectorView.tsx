/**
 * UI компонент для обнаружения аномалий
 * Предоставляет интерфейс для мониторинга и управления системой обнаружения аномалий
 */

import React, { useState, useEffect } from 'react';
import { AnomalyDetectionService, AnomalyDetectionJob, AnomalyResult, AnomalyAlgorithm } from '../../services/anomaly-detection-service';

interface AnomalyDetectorViewProps {
  className?: string;
}

export const AnomalyDetectorView: React.FC<AnomalyDetectorViewProps> = ({ className = '' }) => {
  const [anomalyService] = useState(() => new AnomalyDetectionService());
  const [activeTab, setActiveTab] = useState<'jobs' | 'anomalies' | 'algorithms' | 'alerts'>('jobs');
  const [jobs, setJobs] = useState<AnomalyDetectionJob[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyResult[]>([]);
  const [algorithms, setAlgorithms] = useState<AnomalyAlgorithm[]>([]);
  const [selectedJob, setSelectedJob] = useState<AnomalyDetectionJob | null>(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState<AnomalyResult | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [jobConfig, setJobConfig] = useState({
    name: '',
    description: '',
    algorithmName: 'zscore',
    threshold: 0.8,
    dataSourceType: 'database' as const,
    fields: [] as string[],
    filters: [] as any[]
  });

  useEffect(() => {
    loadJobs();
    loadAnomalies();
    loadAlgorithms();
  }, []);

  const loadJobs = () => {
    const allJobs = anomalyService.getAllJobs();
    setJobs(allJobs);
  };

  const loadAnomalies = () => {
    const allAnomalies = anomalyService.getAllResults();
    setAnomalies(allAnomalies);
  };

  const loadAlgorithms = () => {
    const availableAlgorithms = anomalyService.getAvailableAlgorithms();
    setAlgorithms(availableAlgorithms);
  };

  const createJob = async () => {
    if (!jobConfig.name.trim()) {
      alert('Введите название задания');
      return;
    }

    setIsScanning(true);
    try {
      const jobId = anomalyService.createJob(jobConfig.name, jobConfig.description);
      
      // Настройка алгоритма
      anomalyService.setAlgorithm(jobId, jobConfig.algorithmName);
      anomalyService.updateAlgorithmParameters(jobId, {
        threshold: jobConfig.threshold
      });

      // Настройка источника данных
      anomalyService.setDataSource(jobId, {
        type: jobConfig.dataSourceType,
        connection: {
          database: '1c_anomaly_source'
        },
        fields: jobConfig.fields,
        filters: jobConfig.filters
      });

      loadJobs();
      setIsCreating(false);
      setJobConfig({
        name: '',
        description: '',
        algorithmName: 'zscore',
        threshold: 0.8,
        dataSourceType: 'database',
        fields: [],
        filters: []
      });
    } catch (error) {
      console.error('Ошибка создания задания:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const runScan = async (jobId: string) => {
    setIsScanning(true);
    try {
      await anomalyService.runScan(jobId);
      
      // Обновление списков после сканирования
      setTimeout(() => {
        loadJobs();
        loadAnomalies();
        setIsScanning(false);
      }, 3000);
    } catch (error) {
      console.error('Ошибка запуска сканирования:', error);
      setIsScanning(false);
    }
  };

  const updateJobStatus = (jobId: string, status: AnomalyDetectionJob['status']) => {
    anomalyService.updateJobStatus(jobId, status);
    loadJobs();
  };

  const resolveAnomaly = (jobId: string, anomalyId: string) => {
    const resolvedBy = prompt('Комментарий к решению аномалии:', 'Проверено и подтверждено') || 'Решено';
    anomalyService.resolveAnomaly(jobId, anomalyId, resolvedBy);
    loadAnomalies();
    loadJobs();
  };

  const runJobNow = (jobId: string) => {
    runScan(jobId);
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#ea580c';
      case 'medium': return '#d97706';
      case 'low': return '#65a30d';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'active': return '🟢';
      case 'paused': return '🟡';
      case 'disabled': return '🔴';
      default: return '⚪';
    }
  };

  const renderJobsTab = () => (
    <div className="jobs-tab">
      <div className="tab-header">
        <h3>Задания обнаружения аномалий</h3>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setIsCreating(true)}
          >
            + Создать задание
          </button>
        </div>
      </div>

      <div className="jobs-grid">
        {jobs.map(job => (
          <div 
            key={job.id}
            className={`job-card ${selectedJob?.id === job.id ? 'selected' : ''}`}
            onClick={() => setSelectedJob(job)}
          >
            <div className="job-header">
              <div className="job-title-section">
                <h4>{job.name}</h4>
                <div className="job-status-info">
                  <span className="status-icon">{getStatusIcon(job.status)}</span>
                  <span className={`status-badge ${job.status}`}>
                    {job.status === 'active' && 'Активно'}
                    {job.status === 'paused' && 'Приостановлено'}
                    {job.status === 'disabled' && 'Отключено'}
                  </span>
                </div>
              </div>
            </div>

            <div className="job-info">
              <p className="job-description">{job.description}</p>
              
              <div className="job-metrics">
                <div className="metric">
                  <span className="metric-label">Сканирований:</span>
                  <span className="metric-value">{job.statistics.totalScans}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Аномалий:</span>
                  <span className="metric-value warning">{job.statistics.anomaliesDetected}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Решено:</span>
                  <span className="metric-value success">{job.statistics.anomaliesResolved}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Точность:</span>
                  <span className="metric-value">{job.statistics.accuracy.toFixed(1)}%</span>
                </div>
              </div>

              <div className="job-algorithm">
                <strong>Алгоритм:</strong> {job.algorithm.name}
              </div>

              <div className="job-schedule">
                {job.lastScan && (
                  <span className="last-scan">
                    Последнее сканирование: {new Date(job.lastScan).toLocaleString()}
                  </span>
                )}
                {job.nextScan && (
                  <span className="next-scan">
                    Следующее: {new Date(job.nextScan).toLocaleString()}
                  </span>
                )}
              </div>

              <div className="top-anomalies">
                <strong>Частые аномалии:</strong>
                {job.statistics.mostCommonAnomalyTypes.slice(0, 3).map(type => (
                  <span key={type.type} className="anomaly-type-tag">
                    {type.type.replace('_', ' ')} ({type.count})
                  </span>
                ))}
              </div>
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
                  runJobNow(job.id);
                }}
                disabled={isScanning}
              >
                Сканировать
              </button>
              
              <button 
                className="btn btn-sm btn-outline"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedJob(job);
                  loadJobAnomalies(job.id);
                }}
              >
                Аномалии
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
              <h4>Конфигурация</h4>
              <div className="detail-item">
                <strong>Алгоритм:</strong> {selectedJob.algorithm.name}
              </div>
              <div className="detail-item">
                <strong>Тип:</strong> {selectedJob.algorithm.type}
              </div>
              <div className="detail-item">
                <strong>Порог:</strong> {(selectedJob.threshold * 100).toFixed(0)}%
              </div>
              <div className="detail-item">
                <strong>Создано:</strong> {new Date(selectedJob.createdAt).toLocaleString()}
              </div>
            </div>

            <div className="detail-section">
              <h4>Источник данных</h4>
              <div className="detail-item">
                <strong>Тип:</strong> {selectedJob.dataSource.type}
              </div>
              {selectedJob.dataSource.tableName && (
                <div className="detail-item">
                  <strong>Таблица:</strong> {selectedJob.dataSource.tableName}
                </div>
              )}
              <div className="detail-item">
                <strong>Поля:</strong> {selectedJob.dataSource.fields.join(', ')}
              </div>
            </div>

            <div className="detail-section">
              <h4>Уведомления ({selectedJob.alerts.length})</h4>
              {selectedJob.alerts.map(alert => (
                <div key={alert.id} className="alert-item">
                  <span className="alert-type">{alert.type}</span>
                  <span className="alert-enabled">{alert.enabled ? 'Включен' : 'Отключен'}</span>
                </div>
              ))}
            </div>

            <div className="detail-section">
              <h4>Производительность</h4>
              <div className="performance-grid">
                <div className="perf-item">
                  <span className="perf-value">{selectedJob.statistics.avgDetectionTime}мс</span>
                  <span className="perf-label">Среднее время</span>
                </div>
                <div className="perf-item">
                  <span className="perf-value">{selectedJob.statistics.falsePositives}</span>
                  <span className="perf-label">Ложных срабатываний</span>
                </div>
                <div className="perf-item">
                  <span className="perf-value">
                    {selectedJob.statistics.anomaliesResolved > 0 ? 
                      ((selectedJob.statistics.anomaliesResolved / selectedJob.statistics.anomaliesDetected) * 100).toFixed(0) : 
                      0
                    }%
                  </span>
                  <span className="perf-label">Разрешено</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const loadJobAnomalies = (jobId: string) => {
    const jobAnomalies = anomalyService.getJobResults(jobId);
    setAnomalies(jobAnomalies);
    setActiveTab('anomalies');
  };

  const renderAnomaliesTab = () => {
    const unresolvedAnomalies = anomalies.filter(a => !a.resolved);
    const resolvedAnomalies = anomalies.filter(a => a.resolved);

    return (
      <div className="anomalies-tab">
        <div className="tab-header">
          <h3>Обнаруженные аномалии</h3>
          <div className="filter-controls">
            <button 
              className={`btn btn-sm ${selectedAnomaly ? 'btn-outline' : 'btn-primary'}`}
              onClick={() => setSelectedAnomaly(null)}
            >
              Все ({anomalies.length})
            </button>
            <button 
              className="btn btn-sm btn-outline"
              onClick={() => setSelectedAnomaly(unresolvedAnomalies[0] || null)}
            >
              Неразрешенные ({unresolvedAnomalies.length})
            </button>
            <button 
              className="btn btn-sm btn-outline"
              onClick={() => setSelectedAnomaly(resolvedAnomalies[0] || null)}
            >
              Разрешенные ({resolvedAnomalies.length})
            </button>
          </div>
        </div>

        <div className="anomalies-content">
          <div className="anomalies-list">
            {anomalies.map(anomaly => (
              <div 
                key={anomaly.id}
                className={`anomaly-card ${selectedAnomaly?.id === anomaly.id ? 'selected' : ''} ${anomaly.resolved ? 'resolved' : 'unresolved'}`}
                onClick={() => setSelectedAnomaly(anomaly)}
              >
                <div className="anomaly-header">
                  <div className="anomaly-info">
                    <span className="anomaly-type">{anomaly.anomalyType.replace('_', ' ')}</span>
                    <span 
                      className="severity-badge"
                      style={{ backgroundColor: getSeverityColor(anomaly.severity) }}
                    >
                      {anomaly.severity}
                    </span>
                  </div>
                  <div className="anomaly-time">
                    {new Date(anomaly.timestamp).toLocaleString()}
                  </div>
                </div>

                <div className="anomaly-description">
                  {anomaly.description}
                </div>

                <div className="anomaly-metrics">
                  <div className="anomaly-metric">
                    <span>Уверенность:</span>
                    <span className="confidence-value">{(anomaly.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="anomaly-metric">
                    <span>Влияние:</span>
                    <span className="impact-value">{anomaly.metrics.businessImpact.level}</span>
                  </div>
                  <div className="anomaly-metric">
                    <span>Записей:</span>
                    <span className="records-value">{anomaly.affectedRecords.length}</span>
                  </div>
                </div>

                {anomaly.resolved && (
                  <div className="anomaly-resolution">
                    <span className="resolution-status">✅ Разрешено</span>
                    <span className="resolution-time">
                      {anomaly.resolvedAt ? new Date(anomaly.resolvedAt).toLocaleString() : ''}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {selectedAnomaly && (
            <div className="anomaly-details">
              <h3>Детали аномалии</h3>
              
              <div className="anomaly-info-grid">
                <div className="info-section">
                  <h4>Основная информация</h4>
                  <div className="info-item">
                    <strong>ID:</strong> {selectedAnomaly.id}
                  </div>
                  <div className="info-item">
                    <strong>Тип:</strong> {selectedAnomaly.anomalyType.replace('_', ' ')}
                  </div>
                  <div className="info-item">
                    <strong>Важность:</strong> 
                    <span 
                      className="severity-badge inline"
                      style={{ backgroundColor: getSeverityColor(selectedAnomaly.severity) }}
                    >
                      {selectedAnomaly.severity}
                    </span>
                  </div>
                  <div className="info-item">
                    <strong>Уверенность:</strong> {(selectedAnomaly.confidence * 100).toFixed(1)}%
                  </div>
                  <div className="info-item">
                    <strong>Время обнаружения:</strong> {new Date(selectedAnomaly.timestamp).toLocaleString()}
                  </div>
                  <div className="info-item">
                    <strong>Статус:</strong> 
                    <span className={selectedAnomaly.resolved ? 'resolved-status' : 'unresolved-status'}>
                      {selectedAnomaly.resolved ? 'Разрешено' : 'Не разрешено'}
                    </span>
                  </div>
                </div>

                <div className="info-section">
                  <h4>Бизнес-влияние</h4>
                  <div className="info-item">
                    <strong>Уровень:</strong> {selectedAnomaly.metrics.businessImpact.level}
                  </div>
                  <div className="info-item">
                    <strong>Описание:</strong> {selectedAnomaly.metrics.businessImpact.description}
                  </div>
                  <div className="info-item">
                    <strong>Риск:</strong> {selectedAnomaly.metrics.businessImpact.riskLevel}
                  </div>
                  {selectedAnomaly.metrics.businessImpact.estimatedCost && (
                    <div className="info-item">
                      <strong>Оценочная стоимость:</strong> {selectedAnomaly.metrics.businessImpact.estimatedCost.toLocaleString()} ₽
                    </div>
                  )}
                </div>

                <div className="info-section">
                  <h4>Метрики</h4>
                  <div className="info-item">
                    <strong>Затронутые поля:</strong> {selectedAnomaly.metrics.affectedFields.join(', ')}
                  </div>
                  <div className="info-item">
                    <strong>Оценка влияния:</strong> {selectedAnomaly.metrics.impactScore.toFixed(1)}
                  </div>
                  <div className="info-item">
                    <strong>Объем данных:</strong> {selectedAnomaly.metrics.dataVolume}
                  </div>
                  <div className="info-item">
                    <strong>Статистическая значимость:</strong> {(selectedAnomaly.metrics.statisticalSignificance * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="affected-records">
                <h4>Затронутые записи</h4>
                <div className="records-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Поле</th>
                        <th>Значение</th>
                        <th>Ожидаемое</th>
                        <th>Отклонение</th>
                        <th>Z-Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedAnomaly.affectedRecords.map((record, index) => (
                        <tr key={index}>
                          <td>{record.field}</td>
                          <td className="value-cell">{String(record.originalValue)}</td>
                          <td className="expected-cell">
                            {record.expectedValue !== undefined ? String(record.expectedValue) : '-'}
                          </td>
                          <td className="deviation-cell">
                            {record.deviation.toFixed(2)}
                          </td>
                          <td className="zscore-cell">
                            {record.zScore !== undefined ? record.zScore.toFixed(2) : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="recommendations">
                <h4>Рекомендации</h4>
                <ul className="recommendations-list">
                  {selectedAnomaly.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>

              {!selectedAnomaly.resolved && (
                <div className="resolution-actions">
                  <button 
                    className="btn btn-success"
                    onClick={() => resolveAnomaly(selectedAnomaly.jobId, selectedAnomaly.id)}
                  >
                    Отметить как решенное
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {anomalies.length === 0 && (
          <div className="no-anomalies">
            <div className="no-anomalies-icon">🔍</div>
            <h3>Аномалии не обнаружены</h3>
            <p>Все системы работают в нормальном режиме</p>
          </div>
        )}
      </div>
    );
  };

  const renderAlgorithmsTab = () => (
    <div className="algorithms-tab">
      <div className="tab-header">
        <h3>Алгоритмы обнаружения аномалий</h3>
      </div>

      <div className="algorithms-grid">
        {algorithms.map(algorithm => (
          <div key={algorithm.name} className="algorithm-card">
            <div className="algorithm-header">
              <h4>{algorithm.name}</h4>
              <span className="algorithm-type">{algorithm.type}</span>
            </div>

            <div className="algorithm-description">
              {algorithm.description}
            </div>

            <div className="algorithm-details">
              <div className="supported-types">
                <strong>Поддерживаемые типы данных:</strong>
                <div className="type-tags">
                  {algorithm.supportedDataTypes.map(type => (
                    <span key={type} className="type-tag">{type}</span>
                  ))}
                </div>
              </div>
            </div>

            <div className="algorithm-usage">
              <strong>Использование:</strong>
              <div className="usage-count">
                {jobs.filter(job => job.algorithm.name === algorithm.name).length} заданий
              </div>
            </div>

            <div className="algorithm-actions">
              <button 
                className="btn btn-sm btn-primary"
                onClick={() => {
                  setJobConfig({...jobConfig, algorithmName: algorithm.name});
                  setIsCreating(true);
                }}
              >
                Использовать
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderAlertsTab = () => {
    const allAlerts = jobs.flatMap(job => 
      job.alerts.map(alert => ({
        ...alert,
        jobName: job.name,
        jobId: job.id
      }))
    );

    return (
      <div className="alerts-tab">
        <div className="tab-header">
          <h3>Конфигурация уведомлений</h3>
          <button className="btn btn-primary">
            Создать уведомление
          </button>
        </div>

        <div className="alerts-grid">
          {allAlerts.map((alert, index) => (
            <div key={index} className="alert-card">
              <div className="alert-header">
                <h4>{alert.jobName}</h4>
                <span className={`alert-status ${alert.enabled ? 'enabled' : 'disabled'}`}>
                  {alert.enabled ? 'Включено' : 'Отключено'}
                </span>
              </div>

              <div className="alert-info">
                <div className="alert-type">
                  <strong>Тип:</strong> {alert.type}
                </div>
                <div className="alert-recipients">
                  <strong>Получатели:</strong> {alert.recipients.join(', ')}
                </div>
                <div className="alert-triggers">
                  <strong>Условия:</strong>
                  <ul>
                    {alert.triggers.map((trigger, triggerIndex) => (
                      <li key={triggerIndex}>
                        {trigger.condition} {trigger.operator} {trigger.value}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="alert-template">
                <strong>Шаблон:</strong>
                <div className="template-preview">
                  <div className="template-subject">{alert.template.subject}</div>
                  <div className="template-message">{alert.template.message}</div>
                </div>
              </div>

              <div className="alert-actions">
                <button className="btn btn-sm btn-outline">
                  Редактировать
                </button>
                <button className={`btn btn-sm ${alert.enabled ? 'btn-warning' : 'btn-success'}`}>
                  {alert.enabled ? 'Отключить' : 'Включить'}
                </button>
              </div>
            </div>
          ))}
        </div>

        {allAlerts.length === 0 && (
          <div className="no-alerts">
            <div className="no-alerts-icon">🔔</div>
            <h3>Уведомления не настроены</h3>
            <p>Создайте задания с уведомлениями для получения оповещений об аномалиях</p>
          </div>
        )}
      </div>
    );
  };

  const renderCreateJobModal = () => (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>Создать задание обнаружения аномалий</h2>
          <button onClick={() => setIsCreating(false)}>×</button>
        </div>
        <div className="modal-content">
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
            <h3>Алгоритм</h3>
            <div className="form-group">
              <label>Алгоритм обнаружения:</label>
              <select
                value={jobConfig.algorithmName}
                onChange={(e) => setJobConfig({...jobConfig, algorithmName: e.target.value})}
              >
                {algorithms.map(algorithm => (
                  <option key={algorithm.name} value={algorithm.name}>
                    {algorithm.name} - {algorithm.description}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Порог чувствительности:</label>
              <input 
                type="range" 
                min="0.1" 
                max="1" 
                step="0.1"
                value={jobConfig.threshold}
                onChange={(e) => setJobConfig({...jobConfig, threshold: parseFloat(e.target.value)})}
              />
              <div className="threshold-display">
                {(jobConfig.threshold * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Источник данных</h3>
            <div className="form-group">
              <label>Тип источника:</label>
              <select
                value={jobConfig.dataSourceType}
                onChange={(e) => setJobConfig({...jobConfig, dataSourceType: e.target.value as any})}
              >
                <option value="database">База данных</option>
                <option value="file">Файл</option>
                <option value="api">API</option>
                <option value="stream">Поток данных</option>
              </select>
            </div>
            <div className="form-group">
              <label>Поля для анализа (через запятую):</label>
              <input 
                type="text" 
                value={jobConfig.fields.join(', ')}
                onChange={(e) => setJobConfig({
                  ...jobConfig, 
                  fields: e.target.value.split(',').map(f => f.trim()).filter(f => f)
                })}
                placeholder="amount, quantity, timestamp"
              />
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
            disabled={isScanning || !jobConfig.name.trim() || jobConfig.fields.length === 0}
          >
            {isScanning ? 'Создание...' : 'Создать задание'}
          </button>
        </div>
      </div>
    </div>
  );

  const statistics = anomalyService.getStatistics();

  return (
    <div className={`anomaly-detector-view ${className}`}>
      <div className="view-header">
        <h1>Обнаружение аномалий</h1>
        <div className="view-stats">
          <div className="stat-item">
            <span className="stat-value">{statistics.totalJobs}</span>
            <span className="stat-label">Заданий</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{statistics.activeJobs}</span>
            <span className="stat-label">Активных</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{statistics.totalAnomalies}</span>
            <span className="stat-label">Аномалий</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{statistics.resolutionRate}</span>
            <span className="stat-label">Разрешено</span>
          </div>
        </div>
        <div className="view-actions">
          <button 
            className={`btn ${activeTab === 'jobs' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('jobs')}
          >
            Задания
          </button>
          <button 
            className={`btn ${activeTab === 'anomalies' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('anomalies')}
          >
            Аномалии
          </button>
          <button 
            className={`btn ${activeTab === 'algorithms' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('algorithms')}
          >
            Алгоритмы
          </button>
          <button 
            className={`btn ${activeTab === 'alerts' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('alerts')}
          >
            Уведомления
          </button>
        </div>
      </div>

      <div className="view-content">
        {activeTab === 'jobs' && renderJobsTab()}
        {activeTab === 'anomalies' && renderAnomaliesTab()}
        {activeTab === 'algorithms' && renderAlgorithmsTab()}
        {activeTab === 'alerts' && renderAlertsTab()}
      </div>

      {isCreating && renderCreateJobModal()}

      {isScanning && (
        <div className="scanning-overlay">
          <div className="scanning-modal">
            <div className="scanning-spinner">🔍</div>
            <h3>Обнаружение аномалий...</h3>
            <p>Анализируем данные на предмет аномальных паттернов</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnomalyDetectorView;