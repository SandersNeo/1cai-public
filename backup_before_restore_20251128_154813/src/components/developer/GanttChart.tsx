/**
 * Компонент интерактивной Gantt диаграммы для управления проектами
 * Поддерживает drag & drop, редактирование задач, просмотр зависимостей
 * и интеграцию с планированием ресурсов для 1C-разработки
 */

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { 
  Calendar, 
  Clock, 
  Users, 
  AlertTriangle, 
  Download, 
  Settings,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Filter,
  ChevronRight,
  ChevronDown
} from 'lucide-react';
import { 
  GanttDiagram, 
  Project, 
  ProjectTask, 
  ProjectDependency,
  CriticalPathTask,
  GanttChartConfig,
  ProjectMetrics
} from '../../services/gantt-diagram-service';
import { GanttDiagramService } from '../../services/gantt-diagram-service';

interface GanttChartProps {
  diagram: GanttDiagram;
  onDiagramChange?: (diagram: GanttDiagram) => void;
  onTaskSelect?: (taskId: string | null) => void;
  onTaskEdit?: (task: ProjectTask) => void;
  onTaskDelete?: (taskId: string) => void;
  readOnly?: boolean;
  showControls?: boolean;
  showMetrics?: boolean;
  height?: number;
  width?: number;
}

interface TimelineScale {
  unit: 'hour' | 'day' | 'week' | 'month';
  count: number;
  step: number;
}

interface DragState {
  isDragging: boolean;
  taskId: string | null;
  dragType: 'move' | 'resize-start' | 'resize-end' | null;
  startX: number;
  startDate: Date;
  startY: number;
}

const GanttChart: React.FC<GanttChartProps> = ({
  diagram,
  onDiagramChange,
  onTaskSelect,
  onTaskEdit,
  onTaskDelete,
  readOnly = false,
  showControls = true,
  showMetrics = true,
  height = 600,
  width = 1200
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    taskId: null,
    dragType: null,
    startX: 0,
    startDate: new Date(),
    startY: 0
  });
  
  // Управление масштабом и панорамированием
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  
  // Фильтры и настройки отображения
  const [filters, setFilters] = useState({
    showCompleted: true,
    showCriticalPath: true,
    showMilestones: true,
    showDependencies: true,
    statusFilter: 'all',
    priorityFilter: 'all',
    assigneeFilter: 'all'
  });
  
  // Состояние панели фильтров
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  
  // Состояние модальных окон
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showMetricsModal, setShowMetricsModal] = useState(false);
  const [editingTask, setEditingTask] = useState<ProjectTask | null>(null);
  
  // Сервис для работы с диаграммой
  const ganttService = useMemo(() => new GanttDiagramService(), []);
  
  // Вычисляемые данные
  const visibleTasks = useMemo(() => {
    let tasks: ProjectTask[] = [...diagram.project.tasks];
    
    if (!filters.showCompleted) {
      tasks = tasks.filter(task => task.status !== 'completed');
    }
    
    if (filters.statusFilter !== 'all') {
      tasks = tasks.filter(task => task.status === filters.statusFilter);
    }
    
    if (filters.priorityFilter !== 'all') {
      tasks = tasks.filter(task => task.priority === filters.priorityFilter);
    }
    
    if (filters.assigneeFilter !== 'all') {
      tasks = tasks.filter(task => task.assignee === filters.assigneeFilter);
    }
    
    return tasks;
  }, [diagram.project.tasks, filters]);
  
  const metrics = useMemo(() => {
    return ganttService.calculateMetrics(diagram.project, diagram.dependencies);
  }, [diagram.project, diagram.dependencies, ganttService]);
  
  const criticalPath = useMemo(() => {
    return ganttService.calculateCriticalPath(diagram.project, diagram.dependencies);
  }, [diagram.project, diagram.dependencies, ganttService]);
  
  // Временные масштабы
  const timelineConfig = useMemo(() => {
    const { startDate, endDate } = diagram.timeline;
    const totalDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (24 * 60 * 60 * 1000));
    
    let scale: TimelineScale;
    if (totalDays <= 30) {
      scale = { unit: 'day', count: totalDays, step: 1 };
    } else if (totalDays <= 90) {
      scale = { unit: 'week', count: Math.ceil(totalDays / 7), step: 1 };
    } else if (totalDays <= 365) {
      scale = { unit: 'month', count: Math.ceil(totalDays / 30), step: 1 };
    } else {
      scale = { unit: 'month', count: Math.ceil(totalDays / 30), step: 3 };
    }
    
    return scale;
  }, [diagram.timeline]);
  
  // Обработчики событий мыши
  const handleMouseDown = (e: React.MouseEvent, taskId: string, dragType: 'move' | 'resize-start' | 'resize-end') => {
    if (readOnly) return;
    
    e.preventDefault();
    setDragState({
      isDragging: true,
      taskId,
      dragType,
      startX: e.clientX,
      startDate: diagram.project.tasks.find(t => t.id === taskId)?.startDate || new Date(),
      startY: e.clientY
    });
    
    setSelectedTaskId(taskId);
  };
  
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragState.isDragging || !dragState.taskId) return;
    
    const deltaX = (e.clientX - dragState.startX) * zoomLevel;
    const daysDelta = Math.round(deltaX / (120 / zoomLevel)); // пикселей в день
    const taskIndex = diagram.project.tasks.findIndex(t => t.id === dragState.taskId);
    
    if (taskIndex === -1) return;
    
    const task = { ...diagram.project.tasks[taskIndex] };
    
    if (dragState.dragType === 'move') {
      // Перемещение всей задачи
      const newStartDate = new Date(dragState.startDate);
      newStartDate.setDate(newStartDate.getDate() + daysDelta);
      
      task.startDate = newStartDate;
      task.endDate = new Date(newStartDate.getTime() + task.duration * 24 * 60 * 60 * 1000);
    } else if (dragState.dragType === 'resize-start') {
      // Изменение начала задачи
      const newStartDate = new Date(dragState.startDate);
      newStartDate.setDate(newStartDate.getDate() + daysDelta);
      
      if (newStartDate < task.endDate) {
        const newDuration = Math.ceil((task.endDate.getTime() - newStartDate.getTime()) / (24 * 60 * 60 * 1000));
        task.startDate = newStartDate;
        task.duration = newDuration;
      }
    } else if (dragState.dragType === 'resize-end') {
      // Изменение конца задачи
      const newEndDate = new Date(dragState.startDate);
      newEndDate.setDate(newEndDate.getDate() + daysDelta);
      
      if (newEndDate > task.startDate) {
        const newDuration = Math.ceil((newEndDate.getTime() - task.startDate.getTime()) / (24 * 60 * 60 * 1000));
        task.duration = newDuration;
        task.endDate = newEndDate;
      }
    }
    
    const updatedProject = {
      ...diagram.project,
      tasks: diagram.project.tasks.map((t, i) => i === taskIndex ? task : t)
    };
    
    const updatedDiagram = {
      ...diagram,
      project: updatedProject,
      updatedAt: new Date()
    };
    
    onDiagramChange?.(updatedDiagram);
  };
  
  const handleMouseUp = () => {
    setDragState({
      isDragging: false,
      taskId: null,
      dragType: null,
      startX: 0,
      startDate: new Date(),
      startY: 0
    });
  };
  
  // Панорамирование диаграммы
  const handlePanStart = (e: React.MouseEvent) => {
    setIsPanning(true);
    setPanStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y });
  };
  
  const handlePanMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    
    setPanOffset({
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y
    });
  };
  
  const handlePanEnd = () => {
    setIsPanning(false);
  };
  
  // Управление масштабом
  const handleZoom = (delta: number) => {
    setZoomLevel(prev => Math.max(0.25, Math.min(4, prev + delta)));
  };
  
  const handleResetView = () => {
    setZoomLevel(1);
    setPanOffset({ x: 0, y: 0 });
  };
  
  // Управление задачами
  const handleTaskClick = (taskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedTaskId(taskId);
    onTaskSelect?.(taskId);
  };
  
  const handleAddTask = () => {
    setEditingTask(null);
    setShowTaskModal(true);
  };
  
  const handleEditTask = (task: ProjectTask, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTask(task);
    setShowTaskModal(true);
  };
  
  const handleDeleteTask = (taskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Удалить задачу?')) {
      onTaskDelete?.(taskId);
    }
  };
  
  // Экспорт диаграммы
  const handleExport = async (format: 'png' | 'svg' | 'pdf' | 'excel') => {
    try {
      const svgData = ganttService.generateSVG(diagram);
      const blob = new Blob([svgData], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `${diagram.project.name}_gantt.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Ошибка при экспорте:', error);
    }
  };
  
  // Вспомогательные функции для рендеринга
  const renderTimeline = () => {
    const { startDate } = diagram.timeline;
    const timelineWidth = (width - 300) * zoomLevel; // ширина левой панели
    const pixelsPerDay = timelineWidth / (Math.ceil((diagram.timeline.endDate.getTime() - startDate.getTime()) / (24 * 60 * 60 * 1000)) + 1);
    
    const periods: React.ReactNode[] = [];
    
    if (timelineConfig.unit === 'day') {
      for (let i = 0; i < timelineConfig.count; i++) {
        const date = new Date(startDate);
        date.setDate(date.getDate() + i * timelineConfig.step);
        const x = i * pixelsPerDay * timelineConfig.step;
        
        periods.push(
          <g key={i}>
            <line 
              x1={x} y1={0} 
              x2={x} y2={height - 100}
              stroke="#e5e7eb" 
              strokeWidth="0.5"
            />
            <text 
              x={x + pixelsPerDay / 2} 
              y="25" 
              textAnchor="middle" 
              className="text-sm fill-gray-600"
            >
              {date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
            </text>
            <text 
              x={x + pixelsPerDay / 2} 
              y="40" 
              textAnchor="middle" 
              className="text-xs fill-gray-500"
            >
              {date.getFullYear()}
            </text>
          </g>
        );
      }
    }
    
    return (
      <div className="border-b border-gray-200 bg-gray-50 h-16 relative overflow-hidden">
        <svg 
          ref={svgRef}
          className="absolute top-0 left-0"
          width={timelineWidth} 
          height="60"
        >
          {periods}
        </svg>
      </div>
    );
  };
  
  const renderTaskRow = (task: ProjectTask, index: number) => {
    const taskStartDays = Math.ceil((task.startDate.getTime() - diagram.timeline.startDate.getTime()) / (24 * 60 * 60 * 1000));
    const taskWidth = task.duration * 120 * zoomLevel; // 120 пикселей на день
    const taskX = taskStartDays * 120 * zoomLevel;
    const taskY = index * 32 + 70; // 32 пикселя на строку задачи
    
    const isCritical = criticalPath.find(c => c.taskId === task.id)?.isCritical || false;
    const isSelected = selectedTaskId === task.id;
    const isOverdue = task.status !== 'completed' && task.endDate < new Date();
    
    // Цвет задачи в зависимости от статуса
    const getTaskColor = () => {
      if (isOverdue) return '#ef4444'; // красный для просроченных
      switch (task.status) {
        case 'completed': return '#10b981'; // зеленый
        case 'in_progress': return '#3b82f6'; // синий
        case 'blocked': return '#f59e0b'; // желтый
        default: return '#6b7280'; // серый
      }
    };
    
    return (
      <div 
        key={task.id} 
        className={`relative h-8 border-b border-gray-100 ${
          isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
        }`}
        style={{ minWidth: (width - 300) * zoomLevel }}
      >
        {/* Информация о задаче (левая панель) */}
        <div className="absolute left-0 top-0 w-72 h-8 px-3 flex items-center z-10 bg-white">
          <div 
            className={`w-3 h-3 rounded-sm mr-2 cursor-pointer ${
              isCritical ? 'bg-red-500' : ''
            }`}
            style={{ backgroundColor: isCritical ? '#ef4444' : getTaskColor() }}
            onClick={(e) => handleTaskClick(task.id, e)}
          />
          <span 
            className={`text-sm truncate cursor-pointer ${
              task.status === 'completed' ? 'line-through text-gray-500' : ''
            }`}
            onClick={(e) => handleTaskClick(task.id, e)}
          >
            {task.name}
          </span>
          {task.assignee && (
            <span className="text-xs text-gray-400 ml-2 truncate">
              {task.assignee}
            </span>
          )}
        </div>
        
        {/* Полоса задачи (правая часть) */}
        <div className="absolute left-72 right-0 h-8" style={{ marginLeft: panOffset.x }}>
          <svg 
            width={taskWidth} 
            height="100%"
            className="absolute top-0"
            style={{ left: taskX }}
          >
            {/* Основная полоса */}
            <rect
              x="0"
              y="4"
              width={taskWidth - 16}
              height="20"
              fill={getTaskColor()}
              stroke={isCritical ? '#dc2626' : isSelected ? '#2563eb' : 'transparent'}
              strokeWidth={isSelected ? 2 : 1}
              rx="4"
              className="cursor-move"
              onMouseDown={(e) => handleMouseDown(e, task.id, 'move')}
            />
            
            {/* Прогресс */}
            {task.progress > 0 && (
              <rect
                x="0"
                y="4"
                width={(taskWidth - 16) * (task.progress / 100)}
                height="20"
                fill="#1f2937"
                opacity="0.6"
                rx="4"
              />
            )}
            
            {/* Маркеры для изменения размера */}
            {!readOnly && (
              <>
                <rect
                  x="0"
                  y="4"
                  width="8"
                  height="20"
                  fill="#374151"
                  opacity="0.8"
                  rx="4"
                  className="cursor-ew-resize"
                  onMouseDown={(e) => handleMouseDown(e, task.id, 'resize-start')}
                />
                <rect
                  x={taskWidth - 24}
                  y="4"
                  width="8"
                  height="20"
                  fill="#374151"
                  opacity="0.8"
                  rx="4"
                  className="cursor-ew-resize"
                  onMouseDown={(e) => handleMouseDown(e, task.id, 'resize-end')}
                />
              </>
            )}
            
            {/* Критический индикатор */}
            {isCritical && (
              <rect
                x="0"
                y="2"
                width={taskWidth - 16}
                height="24"
                fill="none"
                stroke="#ef4444"
                strokeWidth="2"
                strokeDasharray="4,2"
                rx="4"
              />
            )}
            
            {/* Текст на полосе */}
            <text
              x={8}
              y="18"
              className="text-xs fill-white font-medium"
              dominantBaseline="middle"
            >
              {task.progress}% ({task.duration}д)
            </text>
          </svg>
          
          {/* Кнопки управления задачей */}
          {!readOnly && isSelected && (
            <div className="absolute -top-8 -right-20 flex space-x-1 bg-white border border-gray-200 rounded shadow-sm p-1 z-20">
              <button
                onClick={(e) => handleEditTask(task, e)}
                className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                title="Редактировать"
              >
                <Settings size={14} />
              </button>
              <button
                onClick={(e) => handleDeleteTask(task.id, e)}
                className="p-1 text-red-600 hover:bg-red-50 rounded"
                title="Удалить"
              >
                ×
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };
  
  const renderDependencies = () => {
    if (!filters.showDependencies) return null;
    
    const dependencyPaths: React.ReactNode[] = [];
    
    diagram.dependencies.forEach((dep, index) => {
      const fromTask = diagram.project.tasks.find(t => t.id === dep.fromTaskId);
      const toTask = diagram.project.tasks.find(t => t.id === dep.toTaskId);
      
      if (!fromTask || !toTask) return;
      
      const fromIndex = diagram.project.tasks.indexOf(fromTask);
      const toIndex = diagram.project.tasks.indexOf(toTask);
      
      const fromX = 300 + (Math.ceil((fromTask.endDate.getTime() - diagram.timeline.startDate.getTime()) / (24 * 60 * 60 * 1000))) * 120 * zoomLevel + panOffset.x;
      const fromY = fromIndex * 32 + 74;
      const toX = 300 + (Math.ceil((toTask.startDate.getTime() - diagram.timeline.startDate.getTime()) / (24 * 60 * 60 * 1000))) * 120 * zoomLevel + panOffset.x;
      const toY = toIndex * 32 + 74;
      
      // Рисуем линию зависимости
      const midX = (fromX + toX) / 2;
      
      dependencyPaths.push(
        <g key={index}>
          <path
            d={`M ${fromX} ${fromY} Q ${midX} ${fromY} ${midX} ${toY} L ${toX - 10} ${toY}`}
            stroke="#6b7280"
            strokeWidth="1.5"
            fill="none"
            markerEnd="url(#arrowhead)"
          />
          <text
            x={midX}
            y={(fromY + toY) / 2 - 5}
            textAnchor="middle"
            className="text-xs fill-gray-500"
          >
            {dep.type.replace('_', '→')}
          </text>
        </g>
      );
    });
    
    return (
      <svg className="absolute top-0 left-0 pointer-events-none z-5">
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#6b7280"
            />
          </marker>
        </defs>
        {dependencyPaths}
      </svg>
    );
  };
  
  const renderMetrics = () => {
    if (!showMetrics) return null;
    
    return (
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{metrics.totalTasks}</div>
            <div className="text-sm text-gray-500">Всего задач</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{metrics.completedTasks}</div>
            <div className="text-sm text-gray-500">Выполнено</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{metrics.inProgressTasks}</div>
            <div className="text-sm text-gray-500">В работе</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{metrics.actualProgress.toFixed(1)}%</div>
            <div className="text-sm text-gray-500">Прогресс</div>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Заголовок и элементы управления */}
      {showControls && (
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-gray-900">{diagram.project.name}</h3>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Calendar size={16} />
              <span>{diagram.timeline.startDate.toLocaleDateString('ru-RU')} - {diagram.timeline.endDate.toLocaleDateString('ru-RU')}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Масштабирование */}
            <div className="flex items-center space-x-1 border border-gray-200 rounded">
              <button
                onClick={() => handleZoom(-0.25)}
                className="p-2 hover:bg-gray-100"
                title="Уменьшить"
              >
                <ZoomOut size={16} />
              </button>
              <span className="px-2 text-sm text-gray-600">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => handleZoom(0.25)}
                className="p-2 hover:bg-gray-100"
                title="Увеличить"
              >
                <ZoomIn size={16} />
              </button>
              <button
                onClick={handleResetView}
                className="p-2 hover:bg-gray-100 border-l border-gray-200"
                title="Сбросить"
              >
                <RotateCcw size={16} />
              </button>
            </div>
            
            {/* Фильтры */}
            <button
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              className="p-2 border border-gray-200 rounded hover:bg-gray-100"
              title="Фильтры"
            >
              <Filter size={16} />
            </button>
            
            {/* Метрики */}
            {showMetrics && (
              <button
                onClick={() => setShowMetricsModal(true)}
                className="p-2 border border-gray-200 rounded hover:bg-gray-100"
                title="Метрики"
              >
                <AlertTriangle size={16} />
              </button>
            )}
            
            {/* Экспорт */}
            <div className="relative group">
              <button className="p-2 border border-gray-200 rounded hover:bg-gray-100">
                <Download size={16} />
              </button>
              <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-30">
                <button
                  onClick={() => handleExport('svg')}
                  className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
                >
                  Экспорт в SVG
                </button>
                <button
                  onClick={() => handleExport('png')}
                  className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
                >
                  Экспорт в PNG
                </button>
                <button
                  onClick={() => handleExport('excel')}
                  className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
                >
                  Экспорт в Excel
                </button>
              </div>
            </div>
            
            {/* Добавление задачи */}
            {!readOnly && (
              <button
                onClick={handleAddTask}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
              >
                + Добавить задачу
              </button>
            )}
          </div>
        </div>
      )}
      
      {/* Панель фильтров */}
      {showFilterPanel && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Статус</label>
              <select
                value={filters.statusFilter}
                onChange={(e) => setFilters(prev => ({ ...prev, statusFilter: e.target.value }))}
                className="w-full border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value="all">Все</option>
                <option value="not_started">Не начато</option>
                <option value="in_progress">В работе</option>
                <option value="completed">Завершено</option>
                <option value="blocked">Заблокировано</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Приоритет</label>
              <select
                value={filters.priorityFilter}
                onChange={(e) => setFilters(prev => ({ ...prev, priorityFilter: e.target.value }))}
                className="w-full border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value="all">Все</option>
                <option value="low">Низкий</option>
                <option value="medium">Средний</option>
                <option value="high">Высокий</option>
                <option value="critical">Критический</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.showCompleted}
                  onChange={(e) => setFilters(prev => ({ ...prev, showCompleted: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm">Завершенные</span>
              </label>
            </div>
            
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.showCriticalPath}
                  onChange={(e) => setFilters(prev => ({ ...prev, showCriticalPath: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm">Критический путь</span>
              </label>
            </div>
          </div>
        </div>
      )}
      
      {/* Основная область диаграммы */}
      <div 
        ref={chartRef}
        className="relative overflow-auto"
        style={{ height: height - (showMetrics ? 200 : 100) }}
        onMouseMove={handlePanMove}
        onMouseUp={handlePanEnd}
        onMouseLeave={handlePanEnd}
      >
        <div 
          className="relative"
          style={{ width: width }}
        >
          {/* Временная шкала */}
          {renderTimeline()}
          
          {/* Строки задач */}
          <div 
            className="relative"
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            {visibleTasks.map((task, index) => renderTaskRow(task, index))}
          </div>
          
          {/* Зависимости */}
          {renderDependencies()}
        </div>
      </div>
      
      {/* Метрики проекта */}
      {renderMetrics()}
      
      {/* Модальное окно редактирования задачи */}
      {showTaskModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingTask ? 'Редактировать задачу' : 'Добавить задачу'}
            </h3>
            
            <form onSubmit={(e) => {
              e.preventDefault();
              setShowTaskModal(false);
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    defaultValue={editingTask?.name || ''}
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
                  <textarea
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    rows={3}
                    defaultValue={editingTask?.description || ''}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Начало</label>
                    <input
                      type="date"
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      defaultValue={editingTask?.startDate.toISOString().split('T')[0]}
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Длительность (дни)</label>
                    <input
                      type="number"
                      min="1"
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      defaultValue={editingTask?.duration || 7}
                      required
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Статус</label>
                    <select
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      defaultValue={editingTask?.status || 'not_started'}
                    >
                      <option value="not_started">Не начато</option>
                      <option value="in_progress">В работе</option>
                      <option value="completed">Завершено</option>
                      <option value="blocked">Заблокировано</option>
                      <option value="on_hold">Приостановлено</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Приоритет</label>
                    <select
                      className="w-full border border-gray-300 rounded px-3 py-2"
                      defaultValue={editingTask?.priority || 'medium'}
                    >
                      <option value="low">Низкий</option>
                      <option value="medium">Средний</option>
                      <option value="high">Высокий</option>
                      <option value="critical">Критический</option>
                    </select>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowTaskModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  {editingTask ? 'Сохранить' : 'Добавить'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Модальное окно метрик */}
      {showMetricsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Метрики проекта</h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-2xl font-bold text-blue-600">{metrics.totalTasks}</div>
                  <div className="text-sm text-gray-500">Всего задач</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">{metrics.completedTasks}</div>
                  <div className="text-sm text-gray-500">Выполнено</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">{metrics.inProgressTasks}</div>
                  <div className="text-sm text-gray-500">В работе</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">{metrics.blockedTasks}</div>
                  <div className="text-sm text-gray-500">Заблокировано</div>
                </div>
              </div>
              
              <div>
                <div className="text-lg font-semibold mb-2">Прогресс проекта</div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div 
                    className="bg-blue-600 h-4 rounded-full transition-all duration-300"
                    style={{ width: `${metrics.actualProgress}%` }}
                  />
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  {metrics.actualProgress.toFixed(1)}% выполнено
                </div>
              </div>
              
              <div>
                <div className="text-lg font-semibold mb-2">Критический путь</div>
                <div className="text-sm text-gray-600">
                  Длина: {metrics.criticalPathLength} дней
                </div>
              </div>
              
              <div>
                <div className="text-lg font-semibold mb-2">Предполагаемое завершение</div>
                <div className="text-sm text-gray-600">
                  {metrics.estimatedCompletion.toLocaleDateString('ru-RU')}
                </div>
              </div>
            </div>
            
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowMetricsModal(false)}
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

export default GanttChart;