"""
Модуль доменных моделей для анализатора производительности.
"""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class ImportMetric:
    """
    Модель метрики импорта модуля.
    
    Attributes:
        module_name (str): Имя модуля.
        import_time_ms (float): Время импорта в миллисекундах.
        is_toplevel (bool): Является ли импорт верхнеуровневым.
        children (List['ImportMetric']): Вложенные импорты.
    """
    module_name: str
    import_time_ms: float
    is_toplevel: bool = True
    children: List['ImportMetric'] = field(default_factory=list)

@dataclass
class StartupReport:
    """
    Отчет о времени запуска приложения.
    
    Attributes:
        total_time_ms (float): Общее время запуска.
        imports (List[ImportMetric]): Список метрик импортов.
        timestamp (datetime): Время формирования отчета.
    """
    total_time_ms: float
    imports: List[ImportMetric]
    timestamp: datetime = field(default_factory=datetime.now)
