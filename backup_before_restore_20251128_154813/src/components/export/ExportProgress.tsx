import React, { useEffect, useState } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  Download, 
  FileText, 
  AlertCircle,
  RefreshCw,
  Clock
} from 'lucide-react';

interface ExportProgressProps {
  isVisible: boolean;
  format: string;
  filename: string;
  progress: number;
  status: 'idle' | 'exporting' | 'completed' | 'error';
  error?: string;
  onCancel?: () => void;
  onRetry?: () => void;
  onComplete?: () => void;
  estimatedTimeRemaining?: number;
  totalSize?: number;
  currentStep?: string;
}

const formatIcons = {
  pdf: '📄',
  docx: '📝',
  xlsx: '📊',
  pptx: '📈',
  mermaid: '🔄',
  bpmn: '📋'
};

const statusConfig = {
  idle: {
    icon: Clock,
    color: 'text-gray-400',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-300'
  },
  exporting: {
    icon: RefreshCw,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    animated: true
  },
  completed: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200'
  },
  error: {
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200'
  }
};

const formatDescriptions = {
  pdf: 'Создание PDF документа...',
  docx: 'Формирование Word документа...',
  xlsx: 'Генерация Excel таблицы...',
  pptx: 'Создание PowerPoint презентации...',
  mermaid: 'Отрисовка Mermaid диаграммы...',
  bpmn: 'Рендеринг BPMN схемы...'
};

export const ExportProgress: React.FC<ExportProgressProps> = ({
  isVisible,
  format,
  filename,
  progress,
  status,
  error,
  onCancel,
  onRetry,
  onComplete,
  estimatedTimeRemaining,
  totalSize,
  currentStep
}) => {
  const [animatedProgress, setAnimatedProgress] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Animate progress changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedProgress(progress);
    }, 100);
    return () => clearTimeout(timer);
  }, [progress]);

  // Track elapsed time
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (status === 'exporting') {
      setElapsedTime(0);
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [status]);

  // Auto-complete timer
  useEffect(() => {
    if (status === 'completed' && onComplete) {
      const timer = setTimeout(() => {
        onComplete();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [status, onComplete]);

  if (!isVisible) return null;

  const config = statusConfig[status];
  const StatusIcon = config.icon;
  const formatIcon = formatIcons[format as keyof typeof formatIcons] || '📁';
  const isAnimating = config.animated;

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}с`;
  };

  const getProgressColor = () => {
    if (status === 'error') return 'bg-red-500';
    if (status === 'completed') return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getStatusMessage = () => {
    switch (status) {
      case 'exporting':
        return currentStep || formatDescriptions[format as keyof typeof formatDescriptions] || 'Экспорт данных...';
      case 'completed':
        return 'Экспорт завершен успешно!';
      case 'error':
        return error || 'Произошла ошибка при экспорте';
      default:
        return 'Готов к экспорту';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className={`${config.bgColor} ${config.borderColor} border-b px-6 py-4`}>
          <div className="flex items-center gap-3">
            <div className="text-2xl">{formatIcon}</div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">
                Экспорт {format.toUpperCase()}
              </h3>
              <p className="text-sm text-gray-600 truncate" title={filename}>
                {filename}
              </p>
            </div>
            <StatusIcon 
              size={24} 
              className={`${config.color} ${isAnimating ? 'animate-spin' : ''}`}
            />
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Status Message */}
          <div className="mb-4">
            <p className="text-sm text-gray-700 font-medium">
              {getStatusMessage()}
            </p>
            {status === 'exporting' && currentStep && (
              <p className="text-xs text-gray-500 mt-1">
                {currentStep}
              </p>
            )}
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Прогресс</span>
              <span className="text-sm font-medium text-gray-900">
                {Math.round(animatedProgress)}%
              </span>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
                style={{ 
                  width: `${animatedProgress}%`,
                  transition: 'width 0.3s ease-in-out'
                }}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-600 mb-1">Время</div>
              <div className="font-medium">
                {status === 'exporting' ? (
                  <>
                    <div>Прошло: {formatTime(elapsedTime)}</div>
                    {estimatedTimeRemaining && (
                      <div className="text-xs text-gray-500">
                        Осталось: ~{formatTime(estimatedTimeRemaining)}
                      </div>
                    )}
                  </>
                ) : status === 'completed' ? (
                  formatTime(elapsedTime)
                ) : (
                  '—'
                )}
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-gray-600 mb-1">Размер</div>
              <div className="font-medium">
                {totalSize ? formatBytes(totalSize) : '—'}
              </div>
            </div>
          </div>

          {/* Error Details */}
          {status === 'error' && error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle size={16} className="text-red-600 mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-red-800">
                    Детали ошибки
                  </div>
                  <div className="text-sm text-red-700 mt-1">
                    {error}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Success Message */}
          {status === 'completed' && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle size={16} className="text-green-600" />
                <div>
                  <div className="text-sm font-medium text-green-800">
                    Экспорт завершен!
                  </div>
                  <div className="text-sm text-green-700">
                    Файл готов к загрузке
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t">
          <div className="text-xs text-gray-500">
            {status === 'exporting' && 'Пожалуйста, подождите...'}
            {status === 'completed' && 'Загрузка начнется автоматически'}
            {status === 'error' && 'Попробуйте еще раз'}
            {status === 'idle' && 'Готов к экспорту'}
          </div>
          
          <div className="flex items-center gap-2">
            {status === 'exporting' && onCancel && (
              <button
                onClick={onCancel}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 font-medium transition-colors"
              >
                Отмена
              </button>
            )}
            
            {status === 'error' && onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition-colors"
              >
                <RefreshCw size={14} />
                Повторить
              </button>
            )}
            
            {status === 'completed' && (
              <button
                onClick={onComplete}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium transition-colors"
              >
                <Download size={14} />
                Готово
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportProgress;