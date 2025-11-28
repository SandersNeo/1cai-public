/**
 * Компонент анализатора требований с NLP функциональностью
 * Предоставляет интерфейс для анализа и структурирования текстовых требований
 */

import React, { useState, useEffect } from 'react';
import {
  Requirement,
  AnalysisResult,
  Entity,
  Relationship,
  Risk,
  Suggestion,
  nlpAnalysisService
} from '../../services/nlp-analysis-service';

interface RequirementAnalyzerProps {
  onAnalysisComplete?: (result: AnalysisResult) => void;
  readonly?: boolean;
}

interface TabType {
  id: string;
  label: string;
  icon: string;
}

export const RequirementAnalyzer: React.FC<RequirementAnalyzerProps> = ({
  onAnalysisComplete,
  readonly = false
}) => {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [selectedRequirement, setSelectedRequirement] = useState<string | null>(null);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<string>('input');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [newRequirement, setNewRequirement] = useState({
    title: '',
    description: '',
    type: 'functional' as const,
    priority: 'should-have' as const,
    complexity: 'medium' as const,
    businessValue: 5,
    tags: [] as string[]
  });

  const tabs: TabType[] = [
    { id: 'input', label: 'Ввод требований', icon: '📝' },
    { id: 'analysis', label: 'Анализ', icon: '🔍' },
    { id: 'entities', label: 'Сущности', icon: '🏷️' },
    { id: 'relationships', label: 'Связи', icon: '🔗' },
    { id: 'risks', label: 'Риски', icon: '⚠️' },
    { id: 'suggestions', label: 'Предложения', icon: '💡' },
    { id: 'requirements', label: 'Все требования', icon: '📋' }
  ];

  // Загрузка требований при монтировании
  useEffect(() => {
    loadRequirements();
  }, []);

  const loadRequirements = () => {
    const loaded = nlpAnalysisService.getAllRequirements();
    setRequirements(loaded);
  };

  const handleAddRequirement = async () => {
    if (!newRequirement.title || !newRequirement.description) {
      alert('Заполните название и описание требования');
      return;
    }

    try {
      const requirementId = nlpAnalysisService.addRequirement({
        title: newRequirement.title,
        description: newRequirement.description,
        type: newRequirement.type,
        priority: newRequirement.priority,
        complexity: newRequirement.complexity,
        businessValue: newRequirement.businessValue,
        status: 'draft',
        tags: newRequirement.tags,
        entities: [],
        relationships: [],
        acceptanceCriteria: [],
        dependencies: [],
        riskLevel: 'medium'
      });

      // Сразу анализируем новое требование
      await analyzeRequirement(requirementId);

      // Очищаем форму
      setNewRequirement({
        title: '',
        description: '',
        type: 'functional',
        priority: 'should-have',
        complexity: 'medium',
        businessValue: 5,
        tags: []
      });

      loadRequirements();
      setActiveTab('requirements');
    } catch (error) {
      console.error('Ошибка добавления требования:', error);
      alert('Ошибка при добавлении требования');
    }
  };

  const analyzeRequirement = async (requirementId: string) => {
    setIsAnalyzing(true);
    try {
      const analysis = await nlpAnalysisService.analyzeRequirement(requirementId);
      if (analysis) {
        setCurrentAnalysis(analysis);
        onAnalysisComplete?.(analysis);
      }
    } catch (error) {
      console.error('Ошибка анализа:', error);
      alert('Ошибка при анализе требования');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSelectRequirement = async (requirementId: string) => {
    setSelectedRequirement(requirementId);
    
    // Загружаем существующий анализ или создаем новый
    // TODO: Нужен публичный метод для доступа к кэшу анализа
    // Для простоты всегда анализируем заново
    await analyzeRequirement(requirementId);
    
    setActiveTab('analysis');
  };

  const handleDeleteRequirement = (requirementId: string) => {
    if (confirm('Удалить это требование?')) {
      nlpAnalysisService.deleteRequirement(requirementId);
      loadRequirements();
      if (selectedRequirement === requirementId) {
        setSelectedRequirement(null);
        setCurrentAnalysis(null);
      }
    }
  };

  const handleExportData = () => {
    const data = nlpAnalysisService.exportToJSON();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `requirements_analysis_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImportData = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const jsonData = e.target?.result as string;
        const success = nlpAnalysisService.importFromJSON(jsonData);
        if (success) {
          loadRequirements();
          alert('Данные успешно импортированы');
        } else {
          alert('Ошибка при импорте данных');
        }
      } catch (error) {
        alert('Ошибка при чтении файла');
      }
    };
    reader.readAsText(file);
  };

  // Отрисовка вкладки ввода требований
  const renderInputTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Новое требование</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Название требования
            </label>
            <input
              type="text"
              value={newRequirement.title}
              onChange={(e) => setNewRequirement({...newRequirement, title: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Например: Система управления складскими запасами"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Описание требования
            </label>
            <textarea
              value={newRequirement.description}
              onChange={(e) => setNewRequirement({...newRequirement, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={6}
              placeholder="Детальное описание функциональности, бизнес-процессов, интеграций..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Тип требования
              </label>
              <select
                value={newRequirement.type}
                onChange={(e) => setNewRequirement({...newRequirement, type: e.target.value as 'functional' | 'non-functional' | 'business' | 'technical'})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="functional">Функциональное</option>
                <option value="non-functional">Нефункциональное</option>
                <option value="business">Бизнес</option>
                <option value="technical">Техническое</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Приоритет
              </label>
              <select
                value={newRequirement.priority}
                onChange={(e) => setNewRequirement({...newRequirement, priority: e.target.value as 'must-have' | 'should-have' | 'could-have' | 'wont-have'})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="must-have">Обязательно</option>
                <option value="should-have">Желательно</option>
                <option value="could-have">Возможно</option>
                <option value="wont-have">Не будет</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Сложность
              </label>
              <select
                value={newRequirement.complexity}
                onChange={(e) => setNewRequirement({...newRequirement, complexity: e.target.value as 'low' | 'medium' | 'high'})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Низкая</option>
                <option value="medium">Средняя</option>
                <option value="high">Высокая</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Бизнес-ценность (1-10)
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={newRequirement.businessValue}
                onChange={(e) => {
                  const value = parseInt(e.target.value);
                  setNewRequirement({...newRequirement, businessValue: isNaN(value) ? 1 : Math.max(1, Math.min(10, value))});
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex space-x-4">
            <button
              onClick={handleAddRequirement}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Добавить и анализировать
            </button>
            <button
              onClick={() => setActiveTab('requirements')}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Перейти к списку
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Отрисовка вкладки анализа
  const renderAnalysisTab = () => (
    <div className="space-y-6">
      {!selectedRequirement ? (
        <div className="text-center py-8 text-gray-500">
          Выберите требование для анализа
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Результат анализа</h3>
              {isAnalyzing && (
                <div className="flex items-center text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                  Анализируется...
                </div>
              )}
            </div>
            
            {currentAnalysis && (
              <div className="space-y-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Краткое изложение</h4>
                  <p className="text-blue-800">{currentAnalysis.summary || 'Краткое изложение недоступно'}</p>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-green-50 p-4 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {currentAnalysis.metadata ? Math.round(currentAnalysis.metadata.confidence * 100) : 0}%
                    </div>
                    <div className="text-sm text-green-700">Уверенность</div>
                  </div>
                  <div className="bg-yellow-50 p-4 rounded-lg text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {currentAnalysis.entities?.length || 0}
                    </div>
                    <div className="text-sm text-yellow-700">Сущности</div>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {currentAnalysis.relationships?.length || 0}
                    </div>
                    <div className="text-sm text-purple-700">Связи</div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Ключевые фразы</h4>
                  <div className="flex flex-wrap gap-2">
                    {(currentAnalysis.metadata?.keyPhrases || []).map((phrase, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                      >
                        {phrase}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );

  // Отрисовка вкладки сущностей
  const renderEntitiesTab = () => (
    <div className="space-y-6">
      {currentAnalysis?.entities ? (
        <div className="grid gap-4">
          {currentAnalysis.entities.map((entity) => (
            <div key={entity.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{entity.name}</h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  entity.type === 'document' ? 'bg-blue-100 text-blue-800' :
                  entity.type === 'reference' ? 'bg-green-100 text-green-800' :
                  entity.type === 'user' ? 'bg-purple-100 text-purple-800' :
                  entity.type === 'integration' ? 'bg-orange-100 text-orange-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {entity.type}
                </span>
              </div>
              
              <p className="text-gray-600 mb-3">{entity.description}</p>
              
              {entity.attributes.length > 0 && (
                <div>
                  <h4 className="font-medium text-sm text-gray-700 mb-2">Атрибуты:</h4>
                  <div className="flex flex-wrap gap-1">
                    {entity.attributes.map((attr, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-gray-50 text-gray-600 rounded text-sm"
                      >
                        {attr}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          Нет данных об entities для отображения
        </div>
      )}
    </div>
  );

  // Отрисовка вкладки связей
  const renderRelationshipsTab = () => (
    <div className="space-y-6">
      {currentAnalysis?.relationships ? (
        <div className="space-y-4">
          {currentAnalysis.relationships.map((relationship) => {
            const sourceEntity = currentAnalysis.entities.find(e => e.id === relationship.sourceEntityId);
            const targetEntity = currentAnalysis.entities.find(e => e.id === relationship.targetEntityId);
            
            return (
              <div key={relationship.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className="text-lg font-medium">
                      {sourceEntity?.name || 'Неизвестно'}
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${
                      relationship.type === 'creates' ? 'bg-green-100 text-green-800' :
                      relationship.type === 'updates' ? 'bg-blue-100 text-blue-800' :
                      relationship.type === 'reads' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {relationship.type}
                    </div>
                    <div className="text-lg font-medium">
                      {targetEntity?.name || 'Неизвестно'}
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs ${
                    relationship.strength === 'strong' ? 'bg-red-100 text-red-800' :
                    relationship.strength === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {relationship.strength}
                  </div>
                </div>
                
                <p className="text-gray-600">{relationship.description}</p>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          Нет данных о связях для отображения
        </div>
      )}
    </div>
  );

  // Отрисовка вкладки рисков
  const renderRisksTab = () => (
    <div className="space-y-6">
      {currentAnalysis?.risks ? (
        <div className="space-y-4">
          {currentAnalysis.risks.map((risk) => {
            <div key={risk.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{risk.type} риск</h3>
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                  risk.severity === 'critical' ? 'bg-red-200 text-red-800' :
                  risk.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                  risk.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {risk.severity}
                </div>
              </div>
              
              <p className="text-gray-600 mb-4">{risk.description}</p>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <span className="text-sm font-medium text-gray-700">Вероятность: </span>
                  <span className="text-sm">{Math.round(risk.probability * 100)}%</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">Влияние: </span>
                  <span className="text-sm">{risk.impact}/10</span>
                </div>
              </div>
              
              <div className="bg-blue-50 p-3 rounded">
                <h4 className="font-medium text-blue-900 mb-1">Митигация:</h4>
                <p className="text-blue-800 text-sm">{risk.mitigation}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          Нет данных о рисках для отображения
        </div>
      )}
    </div>
  );

  // Отрисовка вкладки предложений
  const renderSuggestionsTab = () => (
    <div className="space-y-6">
      {currentAnalysis?.suggestions ? (
        <div className="space-y-4">
          {currentAnalysis.suggestions.map((suggestion) => {
            <div key={suggestion.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{suggestion.title}</h3>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    suggestion.priority === 'high' ? 'bg-red-100 text-red-800' :
                    suggestion.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {suggestion.priority}
                  </span>
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs">
                    {suggestion.category}
                  </span>
                </div>
              </div>
              
              <p className="text-gray-600 mb-4">{suggestion.description}</p>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm font-medium text-gray-700">Сложность: </span>
                  <span className="text-sm">{suggestion.effort}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">Категория: </span>
                  <span className="text-sm">{suggestion.category}</span>
                </div>
              </div>
              
              {suggestion.benefits.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-medium text-sm text-gray-700 mb-2">Преимущества:</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {suggestion.benefits.map((benefit, index) => (
                      <li key={index}>{benefit}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          Нет данных о предложениях для отображения
        </div>
      )}
    </div>
  );

  // Отрисовка вкладки всех требований
  const renderRequirementsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Все требования ({requirements.length})</h3>
        <div className="flex space-x-2">
          <button
            onClick={handleExportData}
            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
          >
            📥 Экспорт
          </button>
          <label className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 cursor-pointer">
            📤 Импорт
            <input
              type="file"
              accept=".json"
              onChange={handleImportData}
              className="hidden"
            />
          </label>
        </div>
      </div>
      
      {requirements.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          Нет требований. Добавьте первое требование во вкладке "Ввод требований".
        </div>
      ) : (
        <div className="grid gap-4">
          {requirements.map((requirement) => (
            <div
              key={requirement.id}
              className={`bg-white rounded-lg shadow p-6 cursor-pointer transition-all ${
                selectedRequirement === requirement.id ? 'ring-2 ring-blue-500' : 'hover:shadow-lg'
              }`}
              onClick={() => handleSelectRequirement(requirement.id)}
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold">{requirement.title}</h4>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    requirement.priority === 'must-have' ? 'bg-red-100 text-red-800' :
                    requirement.priority === 'should-have' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {requirement.priority}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    requirement.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                    requirement.status === 'analyzed' ? 'bg-blue-100 text-blue-800' :
                    requirement.status === 'approved' ? 'bg-green-100 text-green-800' :
                    'bg-purple-100 text-purple-800'
                  }`}>
                    {requirement.status}
                  </span>
                </div>
              </div>
              
              <p className="text-gray-600 mb-3 line-clamp-2">{requirement.description}</p>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>Тип: {requirement.type}</span>
                  <span>Сложность: {requirement.complexity}</span>
                  <span>Ценность: {requirement.businessValue}/10</span>
                </div>
                
                {!readonly && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteRequirement(requirement.id);
                    }}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    🗑️ Удалить
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Анализатор требований с NLP</h2>
          <div className="text-sm text-gray-500">
            Общее количество требований: {requirements.length}
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
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Контент вкладок */}
      <div className="flex-1 overflow-auto p-6">
        {activeTab === 'input' && renderInputTab()}
        {activeTab === 'analysis' && renderAnalysisTab()}
        {activeTab === 'entities' && renderEntitiesTab()}
        {activeTab === 'relationships' && renderRelationshipsTab()}
        {activeTab === 'risks' && renderRisksTab()}
        {activeTab === 'suggestions' && renderSuggestionsTab()}
        {activeTab === 'requirements' && renderRequirementsTab()}
      </div>
    </div>
  );
};

export default RequirementAnalyzer;