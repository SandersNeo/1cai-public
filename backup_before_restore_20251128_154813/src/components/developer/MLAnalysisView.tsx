/**
 * UI компонент для ML анализа и прогнозирования
 * Предоставляет интерфейс для обучения моделей и получения предсказаний
 */

import React, { useState, useEffect } from 'react';
import { MLAnalysisService, MLModel, DatasetConfig, PredictionRequest } from '../../services/ml-analysis-service';

interface MLAnalysisViewProps {
  className?: string;
}

export const MLAnalysisView: React.FC<MLAnalysisViewProps> = ({ className = '' }) => {
  const [mlService] = useState(() => new MLAnalysisService());
  const [activeTab, setActiveTab] = useState<'models' | 'datasets' | 'predictions' | 'evaluation'>('models');
  const [models, setModels] = useState<MLModel[]>([]);
  const [datasets, setDatasets] = useState<DatasetConfig[]>([]);
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [trainingConfig, setTrainingConfig] = useState({
    datasetId: '',
    targetColumn: '',
    featureColumns: [] as string[],
    algorithm: 'linear_regression',
    hyperparameters: {}
  });

  useEffect(() => {
    loadModels();
    loadDatasets();
  }, []);

  const loadModels = () => {
    const allModels = mlService.getAllModels();
    setModels(allModels);
  };

  const loadDatasets = () => {
    const allDatasets = mlService.getAllDatasets();
    setDatasets(allDatasets);
  };

  const createModel = async () => {
    if (!trainingConfig.datasetId || !trainingConfig.targetColumn) {
      alert('Выберите набор данных и целевую колонку');
      return;
    }

    setIsTraining(true);
    try {
      const modelId = mlService.createModel({
        datasetId: trainingConfig.datasetId,
        targetColumn: trainingConfig.targetColumn,
        featureColumns: trainingConfig.featureColumns,
        algorithm: trainingConfig.algorithm,
        hyperparameters: trainingConfig.hyperparameters,
        validationMethod: 'k_fold',
        validationParams: { k: 5 },
        preprocessing: {
          handleMissing: 'fill_mean',
          handleOutliers: 'remove',
          featureScaling: 'standardize',
          encoding: 'one_hot',
          featureSelection: 'correlation',
          dimensionalityReduction: 'none'
        }
      });

      // Ожидание завершения обучения
      setTimeout(() => {
        setIsTraining(false);
        loadModels();
        const newModel = mlService.getModel(modelId);
        if (newModel) {
          setSelectedModel(newModel);
        }
      }, 5000);

    } catch (error) {
      console.error('Ошибка создания модели:', error);
      setIsTraining(false);
    }
  };

  const runPrediction = async () => {
    if (!selectedModel) return;

    const request: PredictionRequest = {
      modelId: selectedModel.id,
      features: {
        current_value: Math.random() * 1000,
        time_factor: Date.now() / 86400000,
        category: 'A'
      },
      includeConfidence: true
    };

    try {
      const result = mlService.predict(request);
      setPredictionResult(result);
    } catch (error) {
      console.error('Ошибка предсказания:', error);
    }
  };

  const runForecast = async () => {
    if (!selectedModel) return;

    try {
      const forecast = mlService.forecastTimeSeries(selectedModel.id, 12);
      setPredictionResult({
        type: 'forecast',
        data: forecast
      });
    } catch (error) {
      console.error('Ошибка прогнозирования:', error);
    }
  };

  const evaluateModel = () => {
    if (!selectedModel) return;

    try {
      const evaluation = mlService.evaluateModel(selectedModel.id);
      setPredictionResult({
        type: 'evaluation',
        data: evaluation
      });
    } catch (error) {
      console.error('Ошибка оценки модели:', error);
    }
  };

  const exportModel = () => {
    if (!selectedModel) return;

    try {
      const exportData = mlService.exportModel(selectedModel.id);
      const blob = new Blob([exportData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedModel.name}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Ошибка экспорта модели:', error);
    }
  };

  const renderModelsTab = () => (
    <div className="models-tab">
      <div className="tab-header">
        <h3>Модели машинного обучения</h3>
        <button 
          className="btn btn-primary"
          onClick={() => setActiveTab('models')}
        >
          + Создать модель
        </button>
      </div>

      <div className="models-grid">
        {models.map(model => (
          <div 
            key={model.id}
            className={`model-card ${selectedModel?.id === model.id ? 'selected' : ''}`}
            onClick={() => setSelectedModel(model)}
          >
            <div className="model-header">
              <h4>{model.name}</h4>
              <span className={`status-badge ${model.status}`}>
                {model.status === 'ready' && 'Готова'}
                {model.status === 'training' && 'Обучение'}
                {model.status === 'failed' && 'Ошибка'}
              </span>
            </div>
            
            <div className="model-info">
              <div className="model-algorithm">{model.algorithm}</div>
              <div className="model-type">{model.type}</div>
              {model.performance.accuracy && (
                <div className="model-metric">
                  Точность: {(model.performance.accuracy * 100).toFixed(1)}%
                </div>
              )}
              {model.performance.r2 && (
                <div className="model-metric">
                  R²: {model.performance.r2.toFixed(3)}
                </div>
              )}
            </div>
            
            <div className="model-actions">
              {model.status === 'ready' && (
                <button 
                  className="btn btn-sm btn-primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedModel(model);
                    runPrediction();
                  }}
                >
                  Предсказать
                </button>
              )}
              <button 
                className="btn btn-sm btn-outline"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedModel(model);
                  evaluateModel();
                }}
              >
                Оценить
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedModel && (
        <div className="model-details">
          <h3>Детали модели: {selectedModel.name}</h3>
          <div className="details-grid">
            <div className="detail-group">
              <h4>Информация</h4>
              <div className="detail-item">
                <strong>Алгоритм:</strong> {selectedModel.algorithm}
              </div>
              <div className="detail-item">
                <strong>Тип:</strong> {selectedModel.type}
              </div>
              <div className="detail-item">
                <strong>Создана:</strong> {new Date(selectedModel.createdAt).toLocaleString()}
              </div>
              <div className="detail-item">
                <strong>Последнее обучение:</strong> {new Date(selectedModel.lastTrained).toLocaleString()}
              </div>
            </div>

            {selectedModel.performance.featureImportance && (
              <div className="detail-group">
                <h4>Важность признаков</h4>
                {selectedModel.performance.featureImportance.map(feature => (
                  <div key={feature.feature} className="feature-importance">
                    <span>{feature.feature}</span>
                    <div className="importance-bar">
                      <div 
                        className={`importance-fill ${feature.type}`}
                        style={{ width: `${feature.importance * 100}%` }}
                      />
                    </div>
                    <span className="importance-value">
                      {(feature.importance * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="detail-actions">
              <button className="btn btn-primary" onClick={runPrediction}>
                Запустить предсказание
              </button>
              {selectedModel.type === 'time_series' && (
                <button className="btn btn-secondary" onClick={runForecast}>
                  Прогноз на 12 периодов
                </button>
              )}
              <button className="btn btn-outline" onClick={evaluateModel}>
                Полная оценка
              </button>
              <button className="btn btn-outline" onClick={exportModel}>
                Экспорт модели
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderDatasetsTab = () => (
    <div className="datasets-tab">
      <div className="tab-header">
        <h3>Наборы данных</h3>
      </div>

      <div className="datasets-grid">
        {datasets.map(dataset => (
          <div key={dataset.id} className="dataset-card">
            <div className="dataset-header">
              <h4>{dataset.name}</h4>
              <span className="dataset-source">{dataset.source}</span>
            </div>
            
            <div className="dataset-info">
              <div className="dataset-sample">
                Размер выборки: {dataset.sampleSize || 'Неизвестно'}
              </div>
              <div className="dataset-columns">
                Колонок: {dataset.columns.length}
              </div>
              {dataset.targetColumn && (
                <div className="dataset-target">
                  Целевая: {dataset.targetColumn}
                </div>
              )}
            </div>

            <div className="dataset-columns-list">
              <h5>Колонки данных:</h5>
              {dataset.columns.slice(0, 5).map(col => (
                <div key={col.name} className="column-item">
                  <span className="column-name">{col.name}</span>
                  <span className={`column-type ${col.type}`}>{col.type}</span>
                  {col.isFeature && <span className="feature-badge">Признак</span>}
                  {col.isTarget && <span className="target-badge">Цель</span>}
                </div>
              ))}
              {dataset.columns.length > 5 && (
                <div className="more-columns">
                  ... и еще {dataset.columns.length - 5} колонок
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderPredictionsTab = () => (
    <div className="predictions-tab">
      <div className="tab-header">
        <h3>Предсказания</h3>
      </div>

      {selectedModel ? (
        <div className="prediction-workspace">
          <div className="prediction-input">
            <h4>Входные данные для предсказания</h4>
            <div className="input-form">
              <div className="form-group">
                <label>Текущее значение:</label>
                <input 
                  type="number" 
                  defaultValue={100}
                  onChange={(e) => {
                    // Обновление параметров предсказания
                  }}
                />
              </div>
              <div className="form-group">
                <label>Временной фактор:</label>
                <input 
                  type="number" 
                  defaultValue={Date.now() / 86400000}
                  step="0.1"
                />
              </div>
              <div className="form-group">
                <label>Категория:</label>
                <select defaultValue="A">
                  <option value="A">Категория A</option>
                  <option value="B">Категория B</option>
                  <option value="C">Категория C</option>
                </select>
              </div>
              
              <div className="prediction-actions">
                <button className="btn btn-primary" onClick={runPrediction}>
                  Предсказать
                </button>
                {selectedModel.type === 'time_series' && (
                  <button className="btn btn-secondary" onClick={runForecast}>
                    Прогноз
                  </button>
                )}
              </div>
            </div>
          </div>

          {predictionResult && (
            <div className="prediction-results">
              <h4>Результаты предсказания</h4>
              
              {predictionResult.type === 'forecast' ? (
                <div className="forecast-results">
                  <div className="forecast-metrics">
                    <div className="forecast-metric">
                      <strong>Тренд:</strong> {predictionResult.data.trend}
                    </div>
                    <div className="forecast-metric">
                      <strong>Сезонность:</strong> 
                      {predictionResult.data.seasonality ? 
                        `${predictionResult.data.seasonality.period} (${(predictionResult.data.seasonality.strength * 100).toFixed(0)}%)` : 
                        'Не обнаружена'
                      }
                    </div>
                  </div>
                  
                  <div className="forecast-chart">
                    <h5>Прогноз на 12 периодов:</h5>
                    <div className="chart-placeholder">
                      📈 Временной ряд с прогнозом
                    </div>
                  </div>
                </div>
              ) : predictionResult.type === 'evaluation' ? (
                <div className="evaluation-results">
                  <div className="evaluation-metrics">
                    <div className="metric-row">
                      <span>Точность:</span>
                      <span>{(predictionResult.data.evaluationMetrics.accuracy! * 100).toFixed(1)}%</span>
                    </div>
                    <div className="metric-row">
                      <span>Precision:</span>
                      <span>{(predictionResult.data.evaluationMetrics.precision! * 100).toFixed(1)}%</span>
                    </div>
                    <div className="metric-row">
                      <span>Recall:</span>
                      <span>{(predictionResult.data.evaluationMetrics.recall! * 100).toFixed(1)}%</span>
                    </div>
                    <div className="metric-row">
                      <span>F1-Score:</span>
                      <span>{(predictionResult.data.evaluationMetrics.f1Score! * 100).toFixed(1)}%</span>
                    </div>
                    {predictionResult.data.evaluationMetrics.mse && (
                      <div className="metric-row">
                        <span>MSE:</span>
                        <span>{predictionResult.data.evaluationMetrics.mse.toFixed(4)}</span>
                      </div>
                    )}
                    {predictionResult.data.evaluationMetrics.r2 && (
                      <div className="metric-row">
                        <span>R²:</span>
                        <span>{predictionResult.data.evaluationMetrics.r2.toFixed(4)}</span>
                      </div>
                    )}
                  </div>

                  <div className="evaluation-recommendations">
                    <h5>Рекомендации:</h5>
                    <ul>
                      {predictionResult.data.recommendations.map((rec: string, index: number) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="single-prediction">
                  <div className="prediction-value">
                    <strong>Предсказание:</strong> {predictionResult.prediction}
                  </div>
                  {predictionResult.confidence && (
                    <div className="prediction-confidence">
                      <strong>Уверенность:</strong> {(predictionResult.confidence * 100).toFixed(1)}%
                    </div>
                  )}
                  {predictionResult.probabilities && (
                    <div className="prediction-probabilities">
                      <strong>Вероятности:</strong>
                      {Object.entries(predictionResult.probabilities).map(([className, prob]) => (
                        <div key={className} className="probability-item">
                          <span>{className}:</span>
                          <span>{(prob * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {predictionResult.featureImpact && (
                    <div className="feature-impact">
                      <strong>Влияние признаков:</strong>
                      {predictionResult.featureImpact.map((impact: any, index: number) => (
                        <div key={index} className="impact-item">
                          <span>{impact.feature}:</span>
                          <span className={impact.direction}>
                            {impact.direction === 'positive' ? '↗' : '↘'} {impact.impact.toFixed(2)}
                          </span>
                          <span className="impact-explanation">{impact.explanation}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="no-model-selected">
          <p>Выберите модель для выполнения предсказаний</p>
        </div>
      )}
    </div>
  );

  const renderCreateModelModal = () => (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>Создать модель машинного обучения</h2>
          <button onClick={() => setActiveTab('models')}>×</button>
        </div>
        <div className="modal-content">
          <div className="form-section">
            <h3>Конфигурация обучения</h3>
            
            <div className="form-group">
              <label>Набор данных:</label>
              <select 
                value={trainingConfig.datasetId}
                onChange={(e) => {
                  const dataset = datasets.find(d => d.id === e.target.value);
                  setTrainingConfig({
                    ...trainingConfig,
                    datasetId: e.target.value,
                    targetColumn: dataset?.targetColumn || '',
                    featureColumns: dataset?.features || []
                  });
                }}
              >
                <option value="">Выберите набор данных</option>
                {datasets.map(dataset => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.name}
                  </option>
                ))}
              </select>
            </div>

            {trainingConfig.datasetId && (
              <>
                <div className="form-group">
                  <label>Целевая колонка:</label>
                  <select
                    value={trainingConfig.targetColumn}
                    onChange={(e) => setTrainingConfig({
                      ...trainingConfig,
                      targetColumn: e.target.value
                    })}
                  >
                    <option value="">Выберите целевую колонку</option>
                    {datasets
                      .find(d => d.id === trainingConfig.datasetId)
                      ?.columns
                      .filter(col => col.type === 'numeric' || col.isTarget)
                      .map(col => (
                        <option key={col.name} value={col.name}>
                          {col.name} ({col.type})
                        </option>
                      ))
                    }
                  </select>
                </div>

                <div className="form-group">
                  <label>Алгоритм:</label>
                  <select
                    value={trainingConfig.algorithm}
                    onChange={(e) => setTrainingConfig({
                      ...trainingConfig,
                      algorithm: e.target.value
                    })}
                  >
                    <option value="linear_regression">Линейная регрессия</option>
                    <option value="random_forest_regressor">Random Forest</option>
                    <option value="svm_regressor">SVM регрессия</option>
                    <option value="logistic_regression">Логистическая регрессия</option>
                    <option value="random_forest_classifier">Random Forest классификатор</option>
                    <option value="kmeans">K-means кластеризация</option>
                    <option value="isolation_forest">Isolation Forest</option>
                    <option value="lstm">LSTM (временные ряды)</option>
                    <option value="arima">ARIMA</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Признаки (автоматически):</label>
                  <div className="features-list">
                    {trainingConfig.featureColumns.map(feature => (
                      <span key={feature} className="feature-tag">
                        {feature}
                      </span>
                    ))}
                  </div>
                  <small>Признаки выбираются автоматически на основе набора данных</small>
                </div>
              </>
            )}
          </div>
        </div>
        <div className="modal-footer">
          <button 
            className="btn btn-secondary" 
            onClick={() => setActiveTab('models')}
          >
            Отмена
          </button>
          <button 
            className="btn btn-primary" 
            onClick={createModel}
            disabled={isTraining || !trainingConfig.datasetId || !trainingConfig.targetColumn}
          >
            {isTraining ? 'Обучение...' : 'Создать и обучить'}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`ml-analysis-view ${className}`}>
      <div className="view-header">
        <h1>ML Анализ и прогнозирование</h1>
        <div className="view-actions">
          <button 
            className={`btn ${activeTab === 'models' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('models')}
          >
            Модели
          </button>
          <button 
            className={`btn ${activeTab === 'datasets' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('datasets')}
          >
            Данные
          </button>
          <button 
            className={`btn ${activeTab === 'predictions' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('predictions')}
          >
            Предсказания
          </button>
        </div>
      </div>

      <div className="view-content">
        {activeTab === 'models' && renderModelsTab()}
        {activeTab === 'datasets' && renderDatasetsTab()}
        {activeTab === 'predictions' && renderPredictionsTab()}
      </div>

      {isTraining && (
        <div className="training-overlay">
          <div className="training-modal">
            <div className="training-spinner">⏳</div>
            <h3>Обучение модели...</h3>
            <p>Пожалуйста, подождите. Это может занять несколько минут.</p>
          </div>
        </div>
      )}

      {activeTab === 'models' && !selectedModel && (
        <div className="create-model-prompt">
          <button 
            className="btn btn-primary btn-large"
            onClick={renderCreateModelModal}
          >
            + Создать первую модель
          </button>
        </div>
      )}
    </div>
  );
};

export default MLAnalysisView;