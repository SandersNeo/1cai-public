"""
Сервис профилирования времени запуска.
"""
import time
import importlib
import sys
from typing import List
from src.modules.performance_analyzer.domain.models import ImportMetric, StartupReport

class StartupProfiler:
    """
    Профилировщик времени запуска и импортов.
    """
    
    def measure_import(self, module_name: str) -> ImportMetric:
        """
        Измеряет время импорта указанного модуля.
        
        Args:
            module_name (str): Имя модуля для импорта.
            
        Returns:
            ImportMetric: Метрики импорта.
        """
        start_time = time.perf_counter()
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.import_module(module_name)
        except Exception as e:
            # Логируем ошибку, но не прерываем профилирование
            print(f"Ошибка при импорте {module_name}: {e}")
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        return ImportMetric(
            module_name=module_name,
            import_time_ms=duration_ms
        )

    def run_analysis(self, target_modules: List[str]) -> StartupReport:
        """
        Запускает анализ для списка модулей.
        
        Args:
            target_modules (List[str]): Список модулей для проверки.
            
        Returns:
            StartupReport: Полный отчет о производительности.
        """
        start_total = time.perf_counter()
        metrics = []
        
        for module in target_modules:
            metric = self.measure_import(module)
            metrics.append(metric)
            
        end_total = time.perf_counter()
        total_ms = (end_total - start_total) * 1000
        
        return StartupReport(
            total_time_ms=total_ms,
            imports=metrics
        )
