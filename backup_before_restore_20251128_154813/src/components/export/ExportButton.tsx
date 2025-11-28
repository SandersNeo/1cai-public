import React, { useState } from 'react';
import { 
  Download, 
  FileText, 
  FileSpreadsheet, 
  Presentation, 
  Image,
  Code,
  Settings
} from 'lucide-react';
import { useExport } from '../../hooks/useExport';
import { ExportFormat } from '../../services/export-service';

interface ExportButtonProps {
  data: any;
  title?: string;
  filename?: string;
  className?: string;
  variant?: 'default' | 'compact' | 'icon';
  disabled?: boolean;
}

const formatConfig = {
  pdf: {
    label: 'PDF',
    icon: FileText,
    color: 'text-red-600',
    description: 'Документ для печати'
  },
  docx: {
    label: 'Word',
    icon: FileText,
    color: 'text-blue-600',
    description: 'Редактируемый документ'
  },
  xlsx: {
    label: 'Excel',
    icon: FileSpreadsheet,
    color: 'text-green-600',
    description: 'Таблица данных'
  },
  pptx: {
    label: 'PowerPoint',
    icon: Presentation,
    color: 'text-orange-600',
    description: 'Презентация'
  },
  mermaid: {
    label: 'Mermaid',
    icon: Code,
    color: 'text-purple-600',
    description: 'Диаграмма в коде'
  },
  bpmn: {
    label: 'BPMN',
    icon: Image,
    color: 'text-indigo-600',
    description: 'Диаграмма процессов'
  }
};

export const ExportButton: React.FC<ExportButtonProps> = ({
  data,
  title = 'Экспорт данных',
  filename = 'export',
  className = '',
  variant = 'default',
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pdf');
  const { exportData, isExporting, progress, error } = useExport({
    role: data.role || { id: 'default', name: 'Unknown', description: '' },
    scenario: data.scenario || { id: 'default', title: 'Unknown', description: '' },
    results: data.results || [],
    codeExamples: data.codeExamples || [],
    executionTime: data.executionTime
  });

  const handleExport = async (format: ExportFormat) => {
    try {
      await exportData(format, data, {
        title,
        filename: `${filename}.${format}`,
        includeMetadata: true,
        includeTimestamp: true,
        customOptions: {}
      });
      
      setIsOpen(false);
    } catch (err) {
      console.error('Export failed:', err);
      // Типизация ошибки: err может быть Error или любым другим типом
      if (err instanceof Error) {
        console.error('Export error details:', err.message);
      }
    }
  };

  const renderCompactButton = () => (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg font-medium transition-all duration-200
          ${disabled 
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-lg'
          }
          ${className}
        `}
      >
        <Download size={16} />
        <span>Экспорт</span>
      </button>
      
      {isOpen && (
        <div className="absolute top-full mt-2 right-0 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-2">
            <div className="text-sm text-gray-600 mb-2 px-2">Выберите формат:</div>
            {Object.entries(formatConfig).map(([format, config]) => {
              const Icon = config.icon;
              return (
                <button
                  key={format}
                  onClick={() => handleExport(format as ExportFormat)}
                  disabled={disabled || isExporting}
                  className="
                    w-full flex items-center gap-3 px-3 py-2 text-left rounded-md
                    hover:bg-gray-50 transition-colors duration-150
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                >
                  <Icon size={16} className={config.color} />
                  <div>
                    <div className="font-medium text-gray-900">{config.label}</div>
                    <div className="text-xs text-gray-500">{config.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );

  const renderIconButton = () => (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          p-2 rounded-lg transition-all duration-200
          ${disabled 
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-lg'
          }
          ${className}
        `}
        title="Экспорт"
      >
        <Download size={20} />
      </button>
      
      {isOpen && (
        <div className="absolute top-full mt-2 right-0 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-2">
            <div className="text-sm text-gray-600 mb-2 px-2">Выберите формат:</div>
            {Object.entries(formatConfig).map(([format, config]) => {
              const Icon = config.icon;
              return (
                <button
                  key={format}
                  onClick={() => handleExport(format as ExportFormat)}
                  disabled={disabled || isExporting}
                  className="
                    w-full flex items-center gap-3 px-3 py-2 text-left rounded-md
                    hover:bg-gray-50 transition-colors duration-150
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                >
                  <Icon size={16} className={config.color} />
                  <div>
                    <div className="font-medium text-gray-900">{config.label}</div>
                    <div className="text-xs text-gray-500">{config.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );

  const renderDefaultButton = () => (
    <div className="flex items-center gap-2">
      <select
        value={selectedFormat}
        onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
        disabled={disabled}
        className="
          px-3 py-2 border border-gray-300 rounded-md text-sm
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          disabled:bg-gray-100 disabled:cursor-not-allowed
        "
      >
        {Object.entries(formatConfig).map(([format, config]) => (
          <option key={format} value={format}>
            {config.label} - {config.description}
          </option>
        ))}
      </select>
      
      <button
        onClick={() => handleExport(selectedFormat)}
        disabled={disabled || isExporting}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200
          ${disabled || isExporting
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-lg'
          }
          ${className}
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
            Экспорт
          </>
        )}
      </button>
      
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
        title="Дополнительные опции"
      >
        <Settings size={16} />
      </button>
      
      {isOpen && (
        <div className="absolute top-full mt-2 right-0 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-4">
            <h3 className="font-medium text-gray-900 mb-3">Все форматы:</h3>
            <div className="space-y-2">
              {Object.entries(formatConfig).map(([format, config]) => {
                const Icon = config.icon;
                return (
                  <button
                    key={format}
                    onClick={() => {
                      setSelectedFormat(format as ExportFormat);
                      handleExport(format as ExportFormat);
                    }}
                    disabled={disabled || isExporting}
                    className="
                      w-full flex items-center gap-3 px-3 py-2 text-left rounded-md
                      hover:bg-gray-50 transition-colors duration-150
                      disabled:opacity-50 disabled:cursor-not-allowed
                    "
                  >
                    <Icon size={16} className={config.color} />
                    <div>
                      <div className="font-medium text-gray-900">{config.label}</div>
                      <div className="text-xs text-gray-500">{config.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Click outside to close dropdown
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isOpen && !(event.target as Element).closest('.export-button-container')) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const buttonClass = variant === 'icon' 
    ? renderIconButton() 
    : variant === 'compact' 
    ? renderCompactButton()
    : renderDefaultButton();

  return (
    <div className={`export-button-container relative ${className}`}>
      {buttonClass}
      
      {error && (
        <div className="absolute top-full mt-2 right-0 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 z-50">
          <div className="font-medium mb-1">Ошибка экспорта:</div>
          <div>{error}</div>
        </div>
      )}
    </div>
  );
};

export default ExportButton;