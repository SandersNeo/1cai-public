import React, { useState, useEffect } from 'react';
import { 
  X, 
  Download, 
  FileText, 
  FileSpreadsheet, 
  Presentation, 
  Image,
  Code,
  Settings,
  Calendar,
  User,
  Tag,
  CheckSquare,
  Eye,
  Globe
} from 'lucide-react';
import { useExport } from '../../hooks/useExport';
import { ExportFormat, ExportOptions } from '../../services/export-service';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: any;
  initialTitle?: string;
  initialFilename?: string;
  onExportComplete?: (filename: string) => void;
}

const formatConfig = {
  pdf: {
    label: 'PDF документ',
    icon: FileText,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    description: 'Универсальный формат для чтения и печати',
    features: ['Поддержка таблиц', 'Готов для печати', 'Защита от редактирования']
  },
  docx: {
    label: 'Microsoft Word',
    icon: FileText,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    description: 'Редактируемый документ с расширенными возможностями',
    features: ['Полная редактируемость', 'Поддержка стилей', 'Макросы и скрипты']
  },
  xlsx: {
    label: 'Microsoft Excel',
    icon: FileSpreadsheet,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    description: 'Электронная таблица с данными и формулами',
    features: ['Поддержка формул', 'Сортировка и фильтрация', 'Графики и диаграммы']
  },
  pptx: {
    label: 'PowerPoint презентация',
    icon: Presentation,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    description: 'Слайдовая презентация с анимацией',
    features: ['Анимированные слайды', 'Встроенные диаграммы', 'Аудио и видео']
  },
  mermaid: {
    label: 'Mermaid диаграмма',
    icon: Code,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    description: 'Диаграмма в виде текстового кода',
    features: ['Версионирование кода', 'Легкое редактирование', 'Интеграция с Git']
  },
  bpmn: {
    label: 'BPMN диаграмма',
    icon: Image,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    description: 'Диаграмма бизнес-процессов',
    features: ['Стандарт BPMN 2.0', 'Интерактивная визуализация', 'Экспорт в SVG/PNG']
  }
};

interface ExportOptionsState {
  title: string;
  filename: string;
  includeMetadata: boolean;
  includeTimestamp: boolean;
  includeAuthor: boolean;
  includeVersion: boolean;
  includeTags: boolean;
  watermark: boolean;
  customWatermark?: string;
  pageOrientation?: 'portrait' | 'landscape';
  pageSize?: 'A4' | 'A3' | 'Letter' | 'Legal';
  fontSize?: number;
  lineSpacing?: number;
  marginSize?: number;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  data,
  initialTitle = 'Экспорт данных',
  initialFilename = 'export',
  onExportComplete
}) => {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pdf');
  const [options, setOptions] = useState<ExportOptionsState>({
    title: initialTitle,
    filename: initialFilename,
    includeMetadata: true,
    includeTimestamp: true,
    includeAuthor: true,
    includeVersion: true,
    includeTags: true,
    watermark: false,
    customWatermark: '',
    pageOrientation: 'A4',
    fontSize: 12,
    lineSpacing: 1.2,
    marginSize: 20
  });
  
  const { exportData, isExporting, progress, error } = useExport({
    role: data.role || { id: 'default', name: 'Unknown', description: '' },
    scenario: data.scenario || { id: 'default', title: 'Unknown', description: '' },
    results: data.results || [],
    codeExamples: data.codeExamples || [],
    executionTime: data.executionTime
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    setOptions(prev => ({
      ...prev,
      title: initialTitle,
      filename: initialFilename
    }));
  }, [initialTitle, initialFilename]);

  const handleExport = async () => {
    try {
      const exportOptions: ExportOptions = {
        title: options.title,
        filename: options.filename,
        includeMetadata: options.includeMetadata,
        includeTimestamp: options.includeTimestamp,
        customOptions: {
          includeAuthor: options.includeAuthor,
          includeVersion: options.includeVersion,
          includeTags: options.includeTags,
          watermark: options.watermark,
          customWatermark: options.customWatermark,
          pageOrientation: options.pageOrientation,
          pageSize: options.pageSize,
          fontSize: options.fontSize,
          lineSpacing: options.lineSpacing,
          marginSize: options.marginSize
        }
      };

      const result = await exportData(selectedFormat, data, exportOptions);
      
      if (result && onExportComplete) {
        onExportComplete(result.filename);
      }
      
      onClose();
    } catch (err) {
      console.error('Export failed:', err);
      // Типизация ошибки: err может быть Error или любым другим типом
      if (err instanceof Error) {
        console.error('Export error details:', err.message);
      }
    }
  };

  const updateOption = <K extends keyof ExportOptionsState>(
    key: K, 
    value: ExportOptionsState[K]
  ) => {
    setOptions(prev => ({ ...prev, [key]: value }));
  };

  const generateFilename = () => {
    const timestamp = new Date().toISOString().split('T')[0];
    const sanitizedTitle = options.title
      .toLowerCase()
      .replace(/[^a-zа-я0-9\s]/gi, '')
      .replace(/\s+/g, '-');
    return `${sanitizedTitle}-${timestamp}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Экспорт данных</h2>
            <p className="text-gray-600 mt-1">Настройте параметры экспорта</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={24} className="text-gray-500" />
          </button>
        </div>

        <div className="flex h-[calc(90vh-8rem)]">
          {/* Left Panel - Format Selection */}
          <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
            <div className="p-4">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <FileText size={18} />
                Выберите формат
              </h3>
              <div className="space-y-3">
                {Object.entries(formatConfig).map(([format, config]) => {
                  const Icon = config.icon;
                  const isSelected = selectedFormat === format;
                  
                  return (
                    <button
                      key={format}
                      onClick={() => setSelectedFormat(format as ExportFormat)}
                      className={`
                        w-full text-left p-4 rounded-lg border-2 transition-all duration-200
                        ${isSelected 
                          ? `${config.bgColor} ${config.borderColor} border-opacity-100` 
                          : 'bg-white border-gray-200 hover:border-gray-300'
                        }
                      `}
                    >
                      <div className="flex items-start gap-3">
                        <Icon size={20} className={config.color} />
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{config.label}</div>
                          <div className="text-sm text-gray-600 mt-1">{config.description}</div>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {config.features.slice(0, 2).map((feature, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-gray-100 text-xs text-gray-600 rounded"
                              >
                                {feature}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Panel - Options */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6">
              <div className="space-y-6">
                {/* Basic Options */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Settings size={18} />
                    Основные настройки
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Заголовок документа
                      </label>
                      <input
                        type="text"
                        value={options.title}
                        onChange={(e) => updateOption('title', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Имя файла
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={options.filename}
                          onChange={(e) => updateOption('filename', e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="px-3 py-2 bg-gray-100 rounded-lg text-sm text-gray-600">
                          .{selectedFormat}
                        </span>
                      </div>
                      <button
                        onClick={() => updateOption('filename', generateFilename())}
                        className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                      >
                        Сгенерировать автоматически
                      </button>
                    </div>
                  </div>
                </div>

                {/* Metadata Options */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <Tag size={16} />
                    Включить метаданные
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={options.includeTimestamp}
                        onChange={(e) => updateOption('includeTimestamp', e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <Calendar size={16} className="text-gray-500" />
                      <span className="text-sm">Временная метка</span>
                    </label>
                    
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={options.includeAuthor}
                        onChange={(e) => updateOption('includeAuthor', e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <User size={16} className="text-gray-500" />
                      <span className="text-sm">Автор</span>
                    </label>
                    
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={options.includeVersion}
                        onChange={(e) => updateOption('includeVersion', e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <CheckSquare size={16} className="text-gray-500" />
                      <span className="text-sm">Версия документа</span>
                    </label>
                    
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={options.includeTags}
                        onChange={(e) => updateOption('includeTags', e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <Tag size={16} className="text-gray-500" />
                      <span className="text-sm">Теги и категории</span>
                    </label>
                  </div>
                </div>

                {/* Advanced Options Toggle */}
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium"
                >
                  <Eye size={16} />
                  {showAdvanced ? 'Скрыть' : 'Показать'} дополнительные настройки
                </button>

                {/* Advanced Options */}
                {showAdvanced && (
                  <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900">Дополнительные настройки</h4>
                    
                    {(selectedFormat === 'pdf' || selectedFormat === 'docx') && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Ориентация страницы
                          </label>
                          <select
                            value={options.pageOrientation}
                            onChange={(e) => updateOption('pageOrientation', e.target.value as 'portrait' | 'landscape')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="portrait">Книжная</option>
                            <option value="landscape">Альбомная</option>
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Размер страницы
                          </label>
                          <select
                            value={options.pageSize}
                            onChange={(e) => updateOption('pageSize', e.target.value as any)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="A4">A4</option>
                            <option value="A3">A3</option>
                            <option value="Letter">Letter</option>
                            <option value="Legal">Legal</option>
                          </select>
                        </div>
                      </>
                    )}
                    
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Размер шрифта
                        </label>
                        <input
                          type="number"
                          value={options.fontSize}
                          onChange={(e) => updateOption('fontSize', parseInt(e.target.value))}
                          min="8"
                          max="24"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Межстрочный интервал
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={options.lineSpacing}
                          onChange={(e) => updateOption('lineSpacing', parseFloat(e.target.value))}
                          min="0.8"
                          max="2.0"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Отступы (мм)
                        </label>
                        <input
                          type="number"
                          value={options.marginSize}
                          onChange={(e) => updateOption('marginSize', parseInt(e.target.value))}
                          min="5"
                          max="50"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-600">
            {Object.entries(formatConfig).find(([format]) => format === selectedFormat)?.[1]?.description}
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
            >
              Отмена
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting || !options.title.trim()}
              className={`
                flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-all duration-200
                ${isExporting || !options.title.trim()
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-lg'
                }
              `}
            >
              {isExporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  Экспорт...
                </>
              ) : (
                <>
                  <Download size={16} />
                  Экспорт в {formatConfig[selectedFormat].label}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-6 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <div className="font-medium mb-1">Ошибка экспорта:</div>
            <div className="text-sm">{error}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExportModal;