/**
 * Компонент матрицы трассируемости для Business Analyst
 * Предоставляет интерактивный интерфейс для управления связями между требованиями, тестами и компонентами
 */

import React, { useState, useEffect } from 'react';
import {
  TraceabilityMatrix,
  MatrixItem,
  CoverageReport,
  CoverageIssue,
  traceabilityMatrixService
} from '../../services/traceability-matrix-service';

interface TraceabilityMatrixViewProps {
  readonly?: boolean;
  onMatrixChange?: (matrix: TraceabilityMatrix) => void;
}

interface MatrixFilter {
  sourceType: string;
  targetType: string;
  status: string;
  relationshipType: string;
}

export const TraceabilityMatrixView: React.FC<TraceabilityMatrixViewProps> = ({
  readonly = false,
  onMatrixChange
}) => {
  const [matrices, setMatrices] = useState<TraceabilityMatrix[]>([]);
  const [selectedMatrix, setSelectedMatrix] = useState<string | null>(null);
  const [currentMatrix, setCurrentMatrix] = useState<TraceabilityMatrix | null>(null);
  const [coverageReport, setCoverageReport] = useState<CoverageReport | null>(null);
  const [filter, setFilter] = useState<MatrixFilter>({
    sourceType: 'all',
    targetType: 'all',
    status: 'all',
    relationshipType: 'all'
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddItemModal, setShowAddItemModal] = useState(false);
  const [newMatrix, setNewMatrix] = useState({
    name: '',
    description: '',
    type: 'custom' as const
  });
  const [newItem, setNewItem] = useState({
    sourceType: 'requirement',
    sourceId: '',
    sourceName: '',
    targetType: 'test',
    targetId: '',
    targetName: '',
    relationshipType: 'tests',
    status: 'uncovered',
    coverage: 0,
    notes: ''
  });
  const [activeView, setActiveView] = useState<'table' | 'matrix' | 'coverage'>('table');

  // Загрузка данных при монтировании
  useEffect(() => {
    loadMatrices();
  }, []);

  const loadMatrices = () => {
    const loaded = traceabilityMatrixService.getAllMatrices();
    setMatrices(loaded);
    if (loaded.length > 0 && !selectedMatrix) {
      setSelectedMatrix(loaded[0].id);
    }
  };

  // Загрузка матрицы при выборе
  useEffect(() => {
    if (selectedMatrix) {
      const matrix = traceabilityMatrixService.getMatrix(selectedMatrix);
      if (matrix) {
        setCurrentMatrix(matrix);
        loadCoverageReport(selectedMatrix);
        onMatrixChange?.(matrix);
      }
    }
  }, [selectedMatrix]);

  const loadCoverageReport = (matrixId: string) => {
    try {
      const report = traceabilityMatrixService.generateCoverageReport(matrixId);
      setCoverageReport(report);
    } catch (error) {
      console.error('Ошибка загрузки отчета:', error);
    }
  };

  const handleCreateMatrix = () => {
    if (!newMatrix.name.trim()) {
      alert('Введите название матрицы');
      return;
    }

    try {
      const matrixId = traceabilityMatrixService.createMatrix(
        newMatrix.name,
        newMatrix.description,
        newMatrix.type
      );

      setNewMatrix({ name: '', description: '', type: 'custom' });
      setShowCreateModal(false);
      loadMatrices();
      setSelectedMatrix(matrixId);
    } catch (error) {
      console.error('Ошибка создания матрицы:', error);
      alert('Ошибка при создании матрицы');
    }
  };

  const handleDeleteMatrix = (matrixId: string) => {
    if (confirm('Удалить эту матрицу?')) {
      traceabilityMatrixService.deleteMatrix(matrixId);
      loadMatrices();
      if (selectedMatrix === matrixId) {
        setSelectedMatrix(null);
        setCurrentMatrix(null);
        setCoverageReport(null);
      }
    }
  };

  const handleAddItem = () => {
    if (!currentMatrix || !newItem.sourceName.trim() || !newItem.targetName.trim()) {
      alert('Заполните все обязательные поля');
      return;
    }

    try {
      const itemId = traceabilityMatrixService.addMatrixItem(
        currentMatrix.id,
        {
          type: newItem.sourceType,
          id: newItem.sourceId || newItem.sourceName,
          name: newItem.sourceName
        },
        {
          type: newItem.targetType,
          id: newItem.targetId || newItem.targetName,
          name: newItem.targetName
        },
        newItem.relationshipType,
        newItem.status,
        newItem.coverage
      );

      // Обновляем матрицу
      const updatedMatrix = traceabilityMatrixService.getMatrix(currentMatrix.id);
      if (updatedMatrix) {
        setCurrentMatrix(updatedMatrix);
        loadCoverageReport(currentMatrix.id);
      }

      // Очищаем форму
      setNewItem({
        sourceType: 'requirement',
        sourceId: '',
        sourceName: '',
        targetType: 'test',
        targetId: '',
        targetName: '',
        relationshipType: 'tests',
        status: 'uncovered',
        coverage: 0,
        notes: ''
      });
      setShowAddItemModal(false);
    } catch (error) {
      console.error('Ошибка добавления элемента:', error);
      alert('Ошибка при добавлении элемента');
    }
  };

  const handleUpdateItemStatus = (itemId: string, status: string) => {
    if (!currentMatrix) return;

    const success = traceabilityMatrixService.updateMatrixItem(
      currentMatrix.id,
      itemId,
      { status: status as any }
    );

    if (success) {
      const updatedMatrix = traceabilityMatrixService.getMatrix(currentMatrix.id);
      if (updatedMatrix) {
        setCurrentMatrix(updatedMatrix);
        loadCoverageReport(currentMatrix.id);
      }
    }
  };

  const handleExportMatrix = (format: 'json' | 'excel' | 'dot') => {
    if (!currentMatrix) return;

    let content = '';
    let filename = '';
    let mimeType = '';

    try {
      switch (format) {
        case 'json':
          content = traceabilityMatrixService.exportToJSON(currentMatrix.id);
          filename = `${currentMatrix.name}.json`;
          mimeType = 'application/json';
          break;
        case 'excel':
          content = traceabilityMatrixService.exportToExcel(currentMatrix.id);
          filename = `${currentMatrix.name}.csv`;
          mimeType = 'text/csv';
          break;
        case 'dot':
          content = traceabilityMatrixService.exportToDOT(currentMatrix.id);
          filename = `${currentMatrix.name}.dot`;
          mimeType = 'text/plain';
          break;
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Ошибка экспорта:', error);
      alert('Ошибка при экспорте матрицы');
    }
  };

  // Фильтрация элементов матрицы
  const getFilteredItems = (): MatrixItem[] => {
    if (!currentMatrix) return [];

    return currentMatrix.items.filter(item => {
      if (filter.sourceType !== 'all' && item.sourceType !== filter.sourceType) return false;
      if (filter.targetType !== 'all' && item.targetType !== filter.targetType) return false;
      if (filter.status !== 'all' && item.status !== filter.status) return false;
      if (filter.relationshipType !== 'all' && item.relationshipType !== filter.relationshipType) return false;
      return true;
    });
  };

  const filteredItems = getFilteredItems();

  // Статистика матрицы
  const getMatrixStats = () => {
    if (!currentMatrix) return null;

    const stats = {
      total: currentMatrix.items.length,
      covered: currentMatrix.items.filter(item => item.status === 'covered').length,
      partial: currentMatrix.items.filter(item => item.status === 'partial').length,
      uncovered: currentMatrix.items.filter(item => item.status === 'uncovered').length,
      blocked: currentMatrix.items.filter(item => item.status === 'blocked').length
    };

    return stats;
  };

  // Отрисовка табличного представления
  const renderTableView = () => (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Источник</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Тип</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Цель</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Тип</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Отношение</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Покрытие</th>
            {!readonly && <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {filteredItems.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-2 text-sm text-gray-900">{item.sourceName}</td>
              <td className="px-4 py-2 text-sm">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  item.sourceType === 'requirement' ? 'bg-blue-100 text-blue-800' :
                  item.sourceType === 'test' ? 'bg-green-100 text-green-800' :
                  item.sourceType === 'component' ? 'bg-purple-100 text-purple-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {item.sourceType}
                </span>
              </td>
              <td className="px-4 py-2 text-sm text-gray-900">{item.targetName}</td>
              <td className="px-4 py-2 text-sm">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  item.targetType === 'requirement' ? 'bg-blue-100 text-blue-800' :
                  item.targetType === 'test' ? 'bg-green-100 text-green-800' :
                  item.targetType === 'component' ? 'bg-purple-100 text-purple-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {item.targetType}
                </span>
              </td>
              <td className="px-4 py-2 text-sm text-gray-600">{item.relationshipType}</td>
              <td className="px-4 py-2 text-sm">
                <select
                  value={item.status}
                  onChange={(e) => handleUpdateItemStatus(item.id, e.target.value)}
                  disabled={readonly}
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    item.status === 'covered' ? 'bg-green-100 text-green-800' :
                    item.status === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                    item.status === 'uncovered' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  } ${readonly ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <option value="covered">Покрыто</option>
                  <option value="partial">Частично</option>
                  <option value="uncovered">Не покрыто</option>
                  <option value="blocked">Заблокировано</option>
                </select>
              </td>
              <td className="px-4 py-2 text-sm">
                <div className="flex items-center">
                  <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                    <div
                      className={`h-2 rounded-full ${
                        item.coverage >= 80 ? 'bg-green-500' :
                        item.coverage >= 50 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${item.coverage}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-600">{item.coverage}%</span>
                </div>
              </td>
              {!readonly && (
                <td className="px-4 py-2 text-sm">
                  <button
                    onClick={() => {
                      if (confirm('Удалить этот элемент?')) {
                        traceabilityMatrixService.deleteMatrixItem(currentMatrix!.id, item.id);
                        const updatedMatrix = traceabilityMatrixService.getMatrix(currentMatrix!.id);
                        if (updatedMatrix) {
                          setCurrentMatrix(updatedMatrix);
                          loadCoverageReport(currentMatrix!.id);
                        }
                      }
                    }}
                    className="text-red-600 hover:text-red-800 text-xs"
                  >
                    Удалить
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {filteredItems.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          Нет элементов для отображения
        </div>
      )}
    </div>
  );

  // Отрисовка матричного представления
  const renderMatrixView = () => {
    const items = filteredItems;
    const uniqueSources = [...new Set(items.map(item => item.sourceName))];
    const uniqueTargets = [...new Set(items.map(item => item.targetName))];

    return (
      <div className="overflow-auto">
        <table className="min-w-full border border-gray-200">
          <thead>
            <tr>
              <th className="p-2 border bg-gray-50 text-xs font-medium">Источник \\ Цель</th>
              {uniqueTargets.map(target => (
                <th key={target} className="p-2 border bg-gray-50 text-xs font-medium min-w-32">
                  {target}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {uniqueSources.map(source => (
              <tr key={source}>
                <td className="p-2 border bg-gray-50 text-xs font-medium max-w-48">
                  {source}
                </td>
                {uniqueTargets.map(target => {
                  const item = items.find(i => i.sourceName === source && i.targetName === target);
                  return (
                    <td key={`${source}-${target}`} className="p-2 border text-center">
                      {item ? (
                        <div className={`w-4 h-4 rounded-full mx-auto ${
                          item.status === 'covered' ? 'bg-green-500' :
                          item.status === 'partial' ? 'bg-yellow-500' :
                          item.status === 'uncovered' ? 'bg-red-500' :
                          'bg-gray-500'
                        }`} title={`${item.relationshipType}: ${item.status}`} />
                      ) : (
                        <div className="w-4 h-4 rounded-full bg-gray-200 mx-auto" />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Отрисовка отчета о покрытии
  const renderCoverageView = () => {
    if (!coverageReport) {
      return (
        <div className="text-center py-8 text-gray-500">
          Отчет о покрытии недоступен
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Общая статистика */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-blue-600">{coverageReport.totalItems}</div>
            <div className="text-sm text-gray-600">Всего элементов</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-green-600">{coverageReport.coveragePercentage}%</div>
            <div className="text-sm text-gray-600">Покрытие</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-yellow-600">{coverageReport.issues.length}</div>
            <div className="text-sm text-gray-600">Проблемы</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow text-center">
            <div className="text-2xl font-bold text-purple-600">{coverageReport.recommendations.length}</div>
            <div className="text-sm text-gray-600">Рекомендации</div>
          </div>
        </div>

        {/* Статус покрытия */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Статус покрытия</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-xl font-bold text-green-600">{coverageReport.coveredItems}</div>
              <div className="text-sm text-gray-600">Покрыто</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-yellow-600">{coverageReport.partialItems}</div>
              <div className="text-sm text-gray-600">Частично</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-red-600">{coverageReport.uncoveredItems}</div>
              <div className="text-sm text-gray-600">Не покрыто</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-gray-600">{coverageReport.blockedItems}</div>
              <div className="text-sm text-gray-600">Заблокировано</div>
            </div>
          </div>
        </div>

        {/* Проблемы */}
        {coverageReport.issues.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Выявленные проблемы</h3>
            <div className="space-y-4">
              {coverageReport.issues.map((issue, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{issue.type}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      issue.severity === 'critical' ? 'bg-red-200 text-red-800' :
                      issue.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                      issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-gray-600 mb-2">{issue.description}</p>
                  <p className="text-sm text-blue-600">{issue.suggestedAction}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Рекомендации */}
        {coverageReport.recommendations.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Рекомендации</h3>
            <ul className="space-y-2">
              {coverageReport.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span className="text-gray-700">{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const stats = getMatrixStats();

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Матрица трассируемости</h2>
          <div className="flex items-center space-x-4">
            {/* Статистика */}
            {stats && (
              <div className="flex space-x-4 text-sm">
                <span className="text-gray-600">Всего: {stats.total}</span>
                <span className="text-green-600">Покрыто: {stats.covered}</span>
                <span className="text-red-600">Не покрыто: {stats.uncovered}</span>
              </div>
            )}

            {/* Действия */}
            <div className="flex space-x-2">
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                + Матрица
              </button>
              {currentMatrix && (
                <>
                  <button
                    onClick={() => setShowAddItemModal(true)}
                    className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                  >
                    + Связь
                  </button>
                  <div className="relative">
                    <button className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700">
                      📥 Экспорт
                    </button>
                    <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded shadow-lg z-10 min-w-32">
                      <button
                        className="block w-full text-left px-3 py-2 hover:bg-gray-100 text-sm"
                        onClick={() => handleExportMatrix('json')}
                      >
                        JSON
                      </button>
                      <button
                        className="block w-full text-left px-3 py-2 hover:bg-gray-100 text-sm"
                        onClick={() => handleExportMatrix('excel')}
                      >
                        Excel (CSV)
                      </button>
                      <button
                        className="block w-full text-left px-3 py-2 hover:bg-gray-100 text-sm"
                        onClick={() => handleExportMatrix('dot')}
                      >
                        DOT (Graphviz)
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Выбор матрицы и фильтры */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center space-x-4">
          {/* Список матриц */}
          <select
            value={selectedMatrix || ''}
            onChange={(e) => setSelectedMatrix(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Выберите матрицу</option>
            {matrices.map(matrix => (
              <option key={matrix.id} value={matrix.id}>
                {matrix.name} ({matrix.type})
              </option>
            ))}
          </select>

          {/* Переключатель представления */}
          <div className="flex border border-gray-300 rounded-md">
            <button
              onClick={() => setActiveView('table')}
              className={`px-3 py-2 text-sm ${activeView === 'table' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700'}`}
            >
              Таблица
            </button>
            <button
              onClick={() => setActiveView('matrix')}
              className={`px-3 py-2 text-sm ${activeView === 'matrix' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700'}`}
            >
              Матрица
            </button>
            <button
              onClick={() => setActiveView('coverage')}
              className={`px-3 py-2 text-sm ${activeView === 'coverage' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700'}`}
            >
              Покрытие
            </button>
          </div>

          {/* Фильтры */}
          {activeView !== 'coverage' && (
            <div className="flex space-x-2">
              <select
                value={filter.sourceType}
                onChange={(e) => setFilter({...filter, sourceType: e.target.value})}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
              >
                <option value="all">Все типы источника</option>
                <option value="requirement">Требование</option>
                <option value="test">Тест</option>
                <option value="component">Компонент</option>
              </select>

              <select
                value={filter.targetType}
                onChange={(e) => setFilter({...filter, targetType: e.target.value})}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
              >
                <option value="all">Все типы цели</option>
                <option value="requirement">Требование</option>
                <option value="test">Тест</option>
                <option value="component">Компонент</option>
              </select>

              <select
                value={filter.status}
                onChange={(e) => setFilter({...filter, status: e.target.value})}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
              >
                <option value="all">Все статусы</option>
                <option value="covered">Покрыто</option>
                <option value="partial">Частично</option>
                <option value="uncovered">Не покрыто</option>
                <option value="blocked">Заблокировано</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Контент */}
      <div className="flex-1 overflow-auto p-6">
        {!currentMatrix ? (
          <div className="text-center py-8 text-gray-500">
            Выберите матрицу для просмотра
          </div>
        ) : (
          <>
            {activeView === 'table' && renderTableView()}
            {activeView === 'matrix' && renderMatrixView()}
            {activeView === 'coverage' && renderCoverageView()}
          </>
        )}
      </div>

      {/* Модальное окно создания матрицы */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Создать матрицу трассируемости</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название матрицы
                </label>
                <input
                  type="text"
                  value={newMatrix.name}
                  onChange={(e) => setNewMatrix({...newMatrix, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Например: Матрица требований к тестам"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Описание
                </label>
                <textarea
                  value={newMatrix.description}
                  onChange={(e) => setNewMatrix({...newMatrix, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Описание матрицы и её целей"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тип матрицы
                </label>
                <select
                  value={newMatrix.type}
                  onChange={(e) => setNewMatrix({...newMatrix, type: e.target.value as any})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="custom">Пользовательская</option>
                  <option value="requirements-to-tests">Требования к тестам</option>
                  <option value="requirements-to-components">Требования к компонентам</option>
                  <option value="requirements-to-artifacts">Требования к артефактам</option>
                </select>
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleCreateMatrix}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Создать
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно добавления элемента */}
      {showAddItemModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full">
            <h3 className="text-lg font-semibold mb-4">Добавить связь</h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тип источника
                  </label>
                  <select
                    value={newItem.sourceType}
                    onChange={(e) => setNewItem({...newItem, sourceType: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="requirement">Требование</option>
                    <option value="test">Тест</option>
                    <option value="component">Компонент</option>
                    <option value="artifact">Артефакт</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тип цели
                  </label>
                  <select
                    value={newItem.targetType}
                    onChange={(e) => setNewItem({...newItem, targetType: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="requirement">Требование</option>
                    <option value="test">Тест</option>
                    <option value="component">Компонент</option>
                    <option value="artifact">Артефакт</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название источника
                </label>
                <input
                  type="text"
                  value={newItem.sourceName}
                  onChange={(e) => setNewItem({...newItem, sourceName: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Название элемента источника"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название цели
                </label>
                <input
                  type="text"
                  value={newItem.targetName}
                  onChange={(e) => setNewItem({...newItem, targetName: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Название элемента цели"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Тип отношения
                  </label>
                  <select
                    value={newItem.relationshipType}
                    onChange={(e) => setNewItem({...newItem, relationshipType: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="implements">Реализует</option>
                    <option value="tests">Тестирует</option>
                    <option value="depends-on">Зависит от</option>
                    <option value="relates-to">Относится к</option>
                    <option value="blocked-by">Заблокирован</option>
                    <option value="supersedes">Заменяет</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Статус
                  </label>
                  <select
                    value={newItem.status}
                    onChange={(e) => setNewItem({...newItem, status: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="covered">Покрыто</option>
                    <option value="partial">Частично</option>
                    <option value="uncovered">Не покрыто</option>
                    <option value="blocked">Заблокировано</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Покрытие (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={newItem.coverage}
                  onChange={(e) => setNewItem({...newItem, coverage: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Примечания
                </label>
                <textarea
                  value={newItem.notes}
                  onChange={(e) => setNewItem({...newItem, notes: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="Дополнительные заметки"
                />
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleAddItem}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Добавить
              </button>
              <button
                onClick={() => setShowAddItemModal(false)}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TraceabilityMatrixView;