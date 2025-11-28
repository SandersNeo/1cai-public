/**
 * Компонент редактора BPMN диаграмм для 1C процессов
 * Предоставляет визуальный интерфейс для создания и редактирования диаграмм
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  BPMNDiagram,
  BPMNElement,
  BPMNSequenceFlow,
  BPMNPool,
  bpmnDiagramService,
  BPMN_ELEMENT_TYPES,
  C1C_TASK_TYPES
} from '../../services/bpmn-diagram-service';

interface BPMNDiagramEditorProps {
  width?: number;
  height?: number;
  readonly?: boolean;
  onDiagramChange?: (diagram: BPMNDiagram) => void;
}

interface DraggedElement {
  type: string;
  name: string;
  x: number;
  y: number;
  properties?: Record<string, any>;
}

export const BPMNDiagramEditor: React.FC<BPMNDiagramEditorProps> = ({
  width = 1200,
  height = 800,
  readonly = false,
  onDiagramChange
}) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [diagram, setDiagram] = useState<BPMNDiagram | null>(null);
  const [selectedElement, setSelectedElement] = useState<string | null>(null);
  const [selectedPool, setSelectedPool] = useState<string | null>(null);
  const [draggedElement, setDraggedElement] = useState<DraggedElement | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState<string | null>(null);
  const [templateType, setTemplateType] = useState<string>('');

  // Инициализация диаграммы
  useEffect(() => {
    const newDiagram = bpmnDiagramService.createDiagram('Новая диаграмма BPMN');
    setDiagram(newDiagram);
  }, []);

  // Обработка изменения диаграммы
  const handleDiagramChange = (newDiagram: BPMNDiagram) => {
    setDiagram(newDiagram);
    onDiagramChange?.(newDiagram);
  };

  // Создание шаблона процесса
  const createTemplate = (type: string) => {
    if (!diagram) return;

    let poolId: string;
    switch (type) {
      case 'document-processing':
        poolId = bpmnDiagramService.createDocumentProcessingTemplate('Обработка документа');
        break;
      case 'reference-update':
        poolId = bpmnDiagramService.createReferenceUpdateTemplate('Обновление справочника');
        break;
      case 'integration':
        poolId = bpmnDiagramService.createIntegrationProcessTemplate('Интеграция');
        break;
      default:
        poolId = bpmnDiagramService.addPool('Новый пул');
    }

    const updatedDiagram = bpmnDiagramService.saveDiagram();
    if (updatedDiagram) {
      handleDiagramChange(updatedDiagram);
      setTemplateType('');
    }
  };

  // Добавление пула
  const addPool = () => {
    if (!diagram || readonly) return;
    
    const poolName = prompt('Введите название пула:');
    if (poolName) {
      const poolId = bpmnDiagramService.addPool(poolName);
      const updatedDiagram = bpmnDiagramService.saveDiagram();
      if (updatedDiagram) {
        handleDiagramChange(updatedDiagram);
        setSelectedPool(poolId);
      }
    }
  };

  // Добавление элемента
  const addElement = (poolId: string, type: string) => {
    if (!diagram || readonly) return;

    const name = prompt('Введите название элемента:');
    if (!name) return;

    const elementId = bpmnDiagramService.addElement(poolId, type, name, 100, 100);
    const updatedDiagram = bpmnDiagramService.saveDiagram();
    if (updatedDiagram) {
      handleDiagramChange(updatedDiagram);
    }
  };

  // Добавление потока
  const startConnection = (elementId: string) => {
    if (!diagram || readonly || isConnecting) return;
    
    setIsConnecting(true);
    setConnectionStart(elementId);
  };

  const completeConnection = (elementId: string) => {
    if (!diagram || !connectionStart || !selectedPool || readonly) return;

    if (connectionStart !== elementId) {
      bpmnDiagramService.addSequenceFlow(selectedPool, connectionStart, elementId);
      const updatedDiagram = bpmnDiagramService.saveDiagram();
      if (updatedDiagram) {
        handleDiagramChange(updatedDiagram);
      }
    }

    setIsConnecting(false);
    setConnectionStart(null);
  };

  // Удаление элемента
  const deleteElement = (elementId: string) => {
    if (!diagram || readonly) return;
    
    const updatedDiagram = bpmnDiagramService.saveDiagram();
    if (updatedDiagram) {
      const pool = updatedDiagram.pools.find(p => p.elements.some(e => e.id === elementId));
      if (pool) {
        pool.elements = pool.elements.filter(e => e.id !== elementId);
        pool.sequenceFlows = pool.sequenceFlows.filter(f => f.from !== elementId && f.to !== elementId);
        handleDiagramChange(updatedDiagram);
      }
    }
  };

  // Экспорт диаграммы
  const exportDiagram = (format: string) => {
    if (!diagram) return;

    let content = '';
    let filename = '';
    let mimeType = '';

    switch (format) {
      case 'bpmn':
        content = bpmnDiagramService.exportToBPMN();
        filename = `${diagram.name}.bpmn`;
        mimeType = 'application/xml';
        break;
      case 'json':
        content = bpmnDiagramService.exportToJSON();
        filename = `${diagram.name}.json`;
        mimeType = 'application/json';
        break;
      case 'graphml':
        content = bpmnDiagramService.exportToGraphML();
        filename = `${diagram.name}.graphml`;
        mimeType = 'application/xml';
        break;
      case '1c-code':
        content = bpmnDiagramService.generate1CCode();
        filename = `${diagram.name}_1C.bsl`;
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
  };

  // Валидация диаграммы
  const validateDiagram = () => {
    const validation = bpmnDiagramService.validateDiagram();
    
    let message = `Валидация завершена:\n`;
    message += `Статус: ${validation.isValid ? '✅ Валидна' : '❌ Содержит ошибки'}\n\n`;
    
    if (validation.errors.length > 0) {
      message += `Ошибки (${validation.errors.length}):\n`;
      validation.errors.forEach(error => message += `• ${error}\n`);
      message += '\n';
    }
    
    if (validation.warnings.length > 0) {
      message += `Предупреждения (${validation.warnings.length}):\n`;
      validation.warnings.forEach(warning => message += `• ${warning}\n`);
    }
    
    alert(message);
  };

  // Отрисовка элемента BPMN
  const renderElement = (element: BPMNElement, poolIndex: number) => {
    const isSelected = selectedElement === element.id;
    const isConnectionSource = connectionStart === element.id;
    
    let elementStyle = 'absolute border-2 border-gray-300 rounded cursor-move flex items-center justify-center text-xs text-center';
    let elementClass = '';

    // Стили для разных типов элементов
    switch (element.type) {
      case BPMN_ELEMENT_TYPES.START_EVENT:
        elementStyle += ' bg-green-100 border-green-400 rounded-full';
        break;
      case BPMN_ELEMENT_TYPES.END_EVENT:
        elementStyle += ' bg-red-100 border-red-400 rounded-full';
        break;
      case C1C_TASK_TYPES.DOCUMENT_PROCESSING:
        elementStyle += ' bg-blue-100 border-blue-400';
        break;
      case C1C_TASK_TYPES.REFERENCE_UPDATE:
        elementStyle += ' bg-yellow-100 border-yellow-400';
        break;
      case C1C_TASK_TYPES.USER_TASK:
        elementStyle += ' bg-purple-100 border-purple-400';
        break;
      default:
        elementStyle += ' bg-gray-100 border-gray-400';
    }

    if (isSelected) elementStyle += ' ring-2 ring-blue-400';
    if (isConnectionSource) elementStyle += ' ring-2 ring-green-400';
    if (isConnecting && connectionStart) elementStyle += ' cursor-crosshair';

    return (
      <div
        key={element.id}
        className={elementStyle}
        style={{
          left: element.x,
          top: element.y,
          width: element.width,
          height: element.height,
          zIndex: 10
        }}
        onClick={() => {
          if (isConnecting) {
            completeConnection(element.id);
          } else {
            setSelectedElement(element.id);
          }
        }}
        onMouseDown={() => {
          if (!isConnecting) {
            startConnection(element.id);
          }
        }}
      >
        <div className="px-1">
          <div className="font-medium">{element.name}</div>
          <div className="text-xs opacity-75">{element.type}</div>
        </div>
        
        {readonly && (
          <button
            className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
            onClick={(e) => {
              e.stopPropagation();
              if (confirm(`Удалить элемент "${element.name}"?`)) {
                deleteElement(element.id);
              }
            }}
          >
            ×
          </button>
        )}
      </div>
    );
  };

  // Отрисовка потока
  const renderSequenceFlow = (flow: BPMNSequenceFlow, pool: BPMNPool) => {
    const fromElement = pool.elements.find(el => el.id === flow.from);
    const toElement = pool.elements.find(el => el.id === flow.to);
    
    if (!fromElement || !toElement) return null;

    const fromX = fromElement.x + fromElement.width / 2;
    const fromY = fromElement.y + fromElement.height / 2;
    const toX = toElement.x + toElement.width / 2;
    const toY = toElement.y + toElement.height / 2;

    const pathData = `M ${fromX} ${fromY} L ${toX} ${toY}`;

    return (
      <svg
        key={flow.id}
        className="absolute pointer-events-none"
        style={{
          left: 0,
          top: 0,
          width: '100%',
          height: '100%',
          zIndex: 1
        }}
      >
        <defs>
          <marker
            id={`arrowhead-${flow.id}`}
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
          </marker>
        </defs>
        <path
          d={pathData}
          stroke="#666"
          strokeWidth="2"
          fill="none"
          markerEnd={`url(#arrowhead-${flow.id})`}
        />
        {flow.name && (
          <text
            x={(fromX + toX) / 2}
            y={(fromY + toY) / 2 - 5}
            textAnchor="middle"
            className="fill-gray-600 text-xs"
          >
            {flow.name}
          </text>
        )}
      </svg>
    );
  };

  // Палитра элементов
  const ElementPalette = () => (
    <div className="w-64 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto">
      <h3 className="font-semibold mb-4">Палитра элементов</h3>
      
      {/* Шаблоны */}
      <div className="mb-6">
        <h4 className="font-medium mb-2">Шаблоны процессов:</h4>
        <div className="space-y-2">
          <button
            className="w-full text-left px-3 py-2 bg-blue-100 hover:bg-blue-200 rounded border"
            onClick={() => setTemplateType('document-processing')}
          >
            📄 Обработка документа
          </button>
          <button
            className="w-full text-left px-3 py-2 bg-green-100 hover:bg-green-200 rounded border"
            onClick={() => setTemplateType('reference-update')}
          >
            📊 Обновление справочника
          </button>
          <button
            className="w-full text-left px-3 py-2 bg-purple-100 hover:bg-purple-200 rounded border"
            onClick={() => setTemplateType('integration')}
          >
            🔗 Интеграционный процесс
          </button>
        </div>
      </div>

      {/* События */}
      <div className="mb-6">
        <h4 className="font-medium mb-2">События:</h4>
        <div className="space-y-1">
          <div
            className="px-3 py-2 bg-green-100 rounded cursor-move border"
            draggable={!readonly}
            onDragStart={(e) => {
              if (!readonly) {
                setDraggedElement({
                  type: BPMN_ELEMENT_TYPES.START_EVENT,
                  name: 'Начало',
                  x: 0,
                  y: 0
                });
              }
            }}
          >
            ⚪ Старт
          </div>
          <div
            className="px-3 py-2 bg-red-100 rounded cursor-move border"
            draggable={!readonly}
            onDragStart={(e) => {
              if (!readonly) {
                setDraggedElement({
                  type: BPMN_ELEMENT_TYPES.END_EVENT,
                  name: 'Завершение',
                  x: 0,
                  y: 0
                });
              }
            }}
          >
            🔴 Конец
          </div>
        </div>
      </div>

      {/* Задачи */}
      <div className="mb-6">
        <h4 className="font-medium mb-2">Задачи:</h4>
        <div className="space-y-1">
          <div
            className="px-3 py-2 bg-blue-100 rounded cursor-move border"
            draggable={!readonly}
            onDragStart={(e) => {
              if (!readonly) {
                setDraggedElement({
                  type: C1C_TASK_TYPES.DOCUMENT_PROCESSING,
                  name: 'Обработка документа',
                  x: 0,
                  y: 0
                });
              }
            }}
          >
            📄 Документ 1C
          </div>
          <div
            className="px-3 py-2 bg-yellow-100 rounded cursor-move border"
            draggable={!readonly}
            onDragStart={(e) => {
              if (!readonly) {
                setDraggedElement({
                  type: C1C_TASK_TYPES.REFERENCE_UPDATE,
                  name: 'Обновление справочника',
                  x: 0,
                  y: 0
                });
              }
            }}
          >
            📊 Справочник
          </div>
          <div
            className="px-3 py-2 bg-purple-100 rounded cursor-move border"
            draggable={!readonly}
            onDragStart={(e) => {
              if (!readonly) {
                setDraggedElement({
                  type: BPMN_ELEMENT_TYPES.USER_TASK,
                  name: 'Пользовательская задача',
                  x: 0,
                  y: 0
                });
              }
            }}
          >
            👤 Пользователь
          </div>
        </div>
      </div>
    </div>
  );

  if (!diagram) {
    return <div>Загрузка редактора...</div>;
  }

  return (
    <div className="flex h-full bg-gray-100">
      {/* Палитра элементов */}
      {!readonly && <ElementPalette />}

      {/* Главная область редактирования */}
      <div className="flex-1 flex flex-col">
        {/* Панель инструментов */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold">Редактор BPMN: {diagram.name}</h2>
              {isConnecting && (
                <div className="bg-green-100 text-green-800 px-3 py-1 rounded">
                  Режим соединения - выберите целевой элемент
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {!readonly && (
                <>
                  <button
                    className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                    onClick={addPool}
                  >
                    + Пул
                  </button>
                  <button
                    className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                    onClick={validateDiagram}
                  >
                    ✓ Проверить
                  </button>
                </>
              )}
              
              <div className="relative">
                <button className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700">
                  📥 Экспорт
                </button>
                <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded shadow-lg z-10 min-w-40">
                  <button
                    className="block w-full text-left px-3 py-2 hover:bg-gray-100"
                    onClick={() => exportDiagram('bpmn')}
                  >
                    BPMN 2.0 XML
                  </button>
                  <button
                    className="block w-full text-left px-3 py-2 hover:bg-gray-100"
                    onClick={() => exportDiagram('json')}
                  >
                    JSON
                  </button>
                  <button
                    className="block w-full text-left px-3 py-2 hover:bg-gray-100"
                    onClick={() => exportDiagram('graphml')}
                  >
                    GraphML
                  </button>
                  <button
                    className="block w-full text-left px-3 py-2 hover:bg-gray-100"
                    onClick={() => exportDiagram('1c-code')}
                  >
                    Код 1C
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Модальное окно для выбора шаблона */}
        {templateType && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h3 className="text-lg font-semibold mb-4">Подтвердите создание шаблона</h3>
              <p className="mb-4">
                {templateType === 'document-processing' && 'Создать шаблон процесса обработки документа?'}
                {templateType === 'reference-update' && 'Создать шаблон процесса обновления справочника?'}
                {templateType === 'integration' && 'Создать шаблон интеграционного процесса?'}
              </p>
              <div className="flex space-x-3">
                <button
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  onClick={() => createTemplate(templateType)}
                >
                  Создать
                </button>
                <button
                  className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                  onClick={() => setTemplateType('')}
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Канвас диаграммы */}
        <div
          ref={canvasRef}
          className="flex-1 relative bg-white overflow-auto"
          style={{ width, height: height - 120 }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            if (!draggedElement || !selectedPool) return;
            
            const rect = canvasRef.current?.getBoundingClientRect();
            if (!rect) return;

            const x = e.clientX - rect.left - draggedElement.x;
            const y = e.clientY - rect.top - draggedElement.y;
            
            bpmnDiagramService.addElement(
              selectedPool,
              draggedElement.type,
              draggedElement.name,
              x,
              y
            );
            
            const updatedDiagram = bpmnDiagramService.saveDiagram();
            if (updatedDiagram) {
              handleDiagramChange(updatedDiagram);
            }
            
            setDraggedElement(null);
          }}
        >
          {diagram.pools.map((pool, poolIndex) => (
            <div
              key={pool.id}
              className={`relative mb-4 ${
                selectedPool === pool.id ? 'ring-2 ring-blue-400' : ''
              }`}
              style={{
                left: pool.y,
                minHeight: pool.height
              }}
              onClick={() => setSelectedPool(pool.id)}
            >
              {/* Заголовок пула */}
              <div className="bg-gray-200 px-4 py-2 font-semibold border-b border-gray-300">
                {pool.name}
              </div>
              
              {/* Элементы пула */}
              <div className="relative bg-gray-50" style={{ minHeight: pool.height }}>
                {pool.elements.map(element => renderElement(element, poolIndex))}
                
                {/* Потоки пула (svg накладывается поверх элементов) */}
                <svg
                  className="absolute inset-0 pointer-events-none"
                  style={{ zIndex: 1 }}
                >
                  {pool.sequenceFlows.map(flow => renderSequenceFlow(flow, pool))}
                </svg>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BPMNDiagramEditor;