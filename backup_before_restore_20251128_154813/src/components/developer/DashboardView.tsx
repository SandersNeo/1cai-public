/**
 * UI компонент для интерактивных дашбордов аналитики данных
 * Предоставляет визуальную среду для создания и управления дашбордами
 */

import React, { useState, useEffect, useRef } from 'react';
import { DashboardService, Dashboard, DashboardWidget, DashboardFilter } from '../../services/dashboard-service';

interface DashboardViewProps {
  className?: string;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ className = '' }) => {
  const [dashboardService] = useState(() => new DashboardService());
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [currentDashboard, setCurrentDashboard] = useState<Dashboard | null>(null);
  const [templates, setTemplates] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<DashboardWidget | null>(null);
  const [dragData, setDragData] = useState<{ type: string; widget?: DashboardWidget } | null>(null);
  const dashboardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadDashboards();
    loadTemplates();
  }, []);

  const loadDashboards = () => {
    const userDashboards = dashboardService.getUserDashboards('current-user');
    setDashboards(userDashboards);
  };

  const loadTemplates = () => {
    const availableTemplates = dashboardService.getTemplates();
    setTemplates(availableTemplates);
  };

  const createDashboard = async (name: string, templateId?: string) => {
    try {
      const dashboardId = dashboardService.createDashboard(name, `Дашборд: ${name}`, templateId);
      loadDashboards();
      const newDashboard = dashboardService.getDashboard(dashboardId);
      if (newDashboard) {
        setCurrentDashboard(newDashboard);
      }
      setIsCreating(false);
    } catch (error) {
      console.error('Ошибка создания дашборда:', error);
    }
  };

  const updateDashboard = (updates: Partial<Dashboard>) => {
    if (!currentDashboard) return;
    
    const success = dashboardService.updateDashboard(currentDashboard.id, updates);
    if (success) {
      const updated = dashboardService.getDashboard(currentDashboard.id);
      setCurrentDashboard(updated);
      loadDashboards();
    }
  };

  const addWidget = (type: string) => {
    if (!currentDashboard) return;

    const newWidget: Omit<DashboardWidget, 'id'> = {
      type: type as any,
      title: 'Новый виджет',
      position: { x: 0, y: 0, width: 3, height: 2 },
      config: getDefaultWidgetConfig(type),
      refreshInterval: 30000,
      filters: [],
      actions: []
    };

    const widgetId = dashboardService.addWidget(currentDashboard.id, newWidget);
    const updatedDashboard = dashboardService.getDashboard(currentDashboard.id);
    setCurrentDashboard(updatedDashboard);
  };

  const updateWidget = (widgetId: string, updates: Partial<DashboardWidget>) => {
    if (!currentDashboard) return;

    const success = dashboardService.updateWidget(currentDashboard.id, widgetId, updates);
    if (success) {
      const updated = dashboardService.getDashboard(currentDashboard.id);
      setCurrentDashboard(updated);
    }
  };

  const removeWidget = (widgetId: string) => {
    if (!currentDashboard) return;

    const success = dashboardService.removeWidget(currentDashboard.id, widgetId);
    if (success) {
      const updated = dashboardService.getDashboard(currentDashboard.id);
      setCurrentDashboard(updated);
      if (selectedWidget?.id === widgetId) {
        setSelectedWidget(null);
      }
    }
  };

  const getDefaultWidgetConfig = (type: string) => {
    switch (type) {
      case 'metric':
        return {
          id: 'metric_' + Date.now(),
          name: 'Метрика',
          type: 'number',
          source: 'data.value',
          format: 'number',
          color: '#3b82f6',
          icon: '📊'
        };
      case 'chart':
        return {
          id: 'chart_' + Date.now(),
          type: 'bar',
          title: 'График',
          dataSource: 'data.values',
          xAxis: 'category',
          yAxis: 'value',
          colorScheme: '#3b82f6'
        };
      case 'table':
        return {
          id: 'table_' + Date.now(),
          columns: [
            { key: 'name', label: 'Название', sortable: true },
            { key: 'value', label: 'Значение', sortable: true }
          ],
          dataSource: 'data.rows'
        };
      default:
        return {};
    }
  };

  const handleDragStart = (e: React.DragEvent, widget: DashboardWidget) => {
    setDragData({ type: 'move', widget });
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetPosition: { x: number; y: number }) => {
    e.preventDefault();
    if (!dragData || !dragData.widget || !currentDashboard) return;

    const widget = dragData.widget;
    const newPosition = {
      ...widget.position,
      x: Math.floor(targetPosition.x / (dashboardRef.current?.clientWidth || 1) * 6),
      y: Math.floor(targetPosition.y / 100)
    };

    updateWidget(widget.id, { position: newPosition });
    setDragData(null);
  };

  const exportDashboard = () => {
    if (!currentDashboard) return;
    
    const exportData = dashboardService.exportDashboard(currentDashboard.id);
    const blob = new Blob([exportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentDashboard.name}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderDashboardList = () => (
    <div className="dashboard-list">
      <div className="dashboard-header">
        <h2>Мои дашборды</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setIsCreating(true)}
        >
          + Создать дашборд
        </button>
      </div>
      
      <div className="dashboard-grid">
        {dashboards.map(dashboard => (
          <div 
            key={dashboard.id}
            className="dashboard-card"
            onClick={() => setCurrentDashboard(dashboard)}
          >
            <div className="dashboard-card-header">
              <h3>{dashboard.name}</h3>
              <span className={`status-badge ${dashboard.isPublic ? 'public' : 'private'}`}>
                {dashboard.isPublic ? 'Публичный' : 'Частный'}
              </span>
            </div>
            <p className="dashboard-description">{dashboard.description}</p>
            <div className="dashboard-stats">
              <span>Виджеты: {dashboard.widgets.length}</span>
              <span>Обновлен: {new Date(dashboard.updatedAt).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderDashboardEditor = () => (
    <div className="dashboard-editor">
      <div className="editor-header">
        <div className="editor-controls">
          <button 
            className="btn btn-secondary"
            onClick={() => setCurrentDashboard(null)}
          >
            ← Назад
          </button>
          <input
            type="text"
            className="dashboard-title"
            value={currentDashboard?.name || ''}
            onChange={(e) => updateDashboard({ name: e.target.value })}
            onFocus={() => setIsEditing(true)}
            onBlur={() => setIsEditing(false)}
          />
        </div>
        
        <div className="editor-actions">
          <button className="btn btn-outline" onClick={exportDashboard}>
            Экспорт
          </button>
          <button 
            className="btn btn-primary"
            onClick={() => updateDashboard({ isPublic: !currentDashboard?.isPublic })}
          >
            {currentDashboard?.isPublic ? 'Сделать приватным' : 'Опубликовать'}
          </button>
        </div>
      </div>

      <div className="editor-content">
        <div className="widget-palette">
          <h3>Виджеты</h3>
          <div className="widget-types">
            {['metric', 'chart', 'table', 'text'].map(type => (
              <button
                key={type}
                className="widget-type"
                onClick={() => addWidget(type)}
                draggable
                onDragStart={(e) => {
                  setDragData({ type: 'add', widget: undefined });
                }}
              >
                <span className="widget-icon">
                  {type === 'metric' && '📊'}
                  {type === 'chart' && '📈'}
                  {type === 'table' && '📋'}
                  {type === 'text' && '📝'}
                </span>
                <span className="widget-label">
                  {type === 'metric' && 'Метрика'}
                  {type === 'chart' && 'График'}
                  {type === 'table' && 'Таблица'}
                  {type === 'text' && 'Текст'}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div 
          className="dashboard-canvas"
          ref={dashboardRef}
          onDragOver={handleDragOver}
          onDrop={(e) => {
            const rect = dashboardRef.current?.getBoundingClientRect();
            if (rect) {
              const position = { x: e.clientX - rect.left, y: e.clientY - rect.top };
              handleDrop(e, position);
            }
          }}
        >
          {currentDashboard?.widgets.map(widget => (
            <div
              key={widget.id}
              className={`dashboard-widget ${selectedWidget?.id === widget.id ? 'selected' : ''}`}
              style={{
                left: `${(widget.position.x / 6) * 100}%`,
                top: `${widget.position.y * 100}px`,
                width: `${(widget.position.width / 6) * 100}%`,
                height: `${widget.position.height * 100}px`
              }}
              onClick={() => setSelectedWidget(widget)}
              draggable
              onDragStart={(e) => handleDragStart(e, widget)}
            >
              <div className="widget-header">
                <span className="widget-title">{widget.title}</span>
                <button 
                  className="widget-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeWidget(widget.id);
                  }}
                >
                  ×
                </button>
              </div>
              <div className="widget-content">
                {renderWidgetContent(widget)}
              </div>
            </div>
          ))}
        </div>

        {selectedWidget && (
          <div className="widget-properties">
            <h3>Свойства виджета</h3>
            <div className="property-group">
              <label>Название:</label>
              <input
                type="text"
                value={selectedWidget.title}
                onChange={(e) => updateWidget(selectedWidget.id, { title: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Ширина:</label>
              <input
                type="number"
                min="1"
                max="6"
                value={selectedWidget.position.width}
                onChange={(e) => updateWidget(selectedWidget.id, { 
                  position: { ...selectedWidget.position, width: parseInt(e.target.value) }
                })}
              />
            </div>
            <div className="property-group">
              <label>Высота:</label>
              <input
                type="number"
                min="1"
                max="10"
                value={selectedWidget.position.height}
                onChange={(e) => updateWidget(selectedWidget.id, { 
                  position: { ...selectedWidget.position, height: parseInt(e.target.value) }
                })}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderWidgetContent = (widget: DashboardWidget) => {
    switch (widget.type) {
      case 'metric':
        return (
          <div className="metric-widget">
            <div className="metric-value">
              {Math.floor(Math.random() * 1000)}
            </div>
            <div className="metric-label">Метрика</div>
          </div>
        );
      case 'chart':
        return (
          <div className="chart-widget">
            <div className="chart-placeholder">
              📈 График данных
            </div>
          </div>
        );
      case 'table':
        return (
          <div className="table-widget">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Название</th>
                  <th>Значение</th>
                </tr>
              </thead>
              <tbody>
                {[1, 2, 3].map(i => (
                  <tr key={i}>
                    <td>Показатель {i}</td>
                    <td>{Math.floor(Math.random() * 100)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      case 'text':
        return (
          <div className="text-widget">
            <p>Текстовый виджет для отображения описаний и комментариев</p>
          </div>
        );
      default:
        return <div>Неизвестный тип виджета</div>;
    }
  };

  const renderCreateModal = () => (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>Создать дашборд</h2>
          <button onClick={() => setIsCreating(false)}>×</button>
        </div>
        <div className="modal-content">
          <div className="form-group">
            <label>Название дашборда:</label>
            <input 
              type="text" 
              placeholder="Введите название..."
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  const name = (e.target as HTMLInputElement).value;
                  if (name.trim()) {
                    createDashboard(name);
                  }
                }
              }}
            />
          </div>
          
          <div className="templates-section">
            <h3>Или выберите шаблон:</h3>
            <div className="templates-grid">
              {templates.map(template => (
                <div 
                  key={template.id}
                  className="template-card"
                  onClick={() => {
                    const name = prompt('Название дашборда:', template.name) || template.name;
                    createDashboard(name, template.id);
                  }}
                >
                  <h4>{template.name}</h4>
                  <p>{template.description}</p>
                  <div className="template-category">{template.category}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={() => setIsCreating(false)}>
            Отмена
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`dashboard-view ${className}`}>
      {!currentDashboard && renderDashboardList()}
      {currentDashboard && renderDashboardEditor()}
      {isCreating && renderCreateModal()}
    </div>
  );
};

export default DashboardView;