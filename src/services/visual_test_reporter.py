# [NEXUS IDENTITY] ID: 8530230735427419019 | DATE: 2025-11-19

"""
Генератор визуальных отчетов о тестах YAxUnit.

Создает HTML отчеты с графиками, временными линиями и интерактивными элементами.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from src.utils.structured_logging import StructuredLogger
from src.services.test_metrics import TestMetrics

logger = StructuredLogger(__name__).logger


@dataclass
class VisualReportConfig:
    """Конфигурация визуального отчета"""

    include_charts: bool = True
    include_timeline: bool = True
    include_coverage: bool = True
    theme: str = "light"  # light, dark
    format: str = "html"  # html, pdf


class VisualTestReporter:
    """
    Генератор визуальных отчетов о тестах.
    """

    def __init__(self, templates_dir: Path = Path("templates/test_reports")):
        """
        Инициализация генератора отчетов.

        Args:
            templates_dir: Директория с шаблонами отчетов
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "VisualTestReporter initialized",
            extra={"templates_dir": str(self.templates_dir)},
        )

    def generate_html_report(
        self,
        metrics: TestMetrics,
        output_path: Path,
        config: Optional[VisualReportConfig] = None,
        historical_data: Optional[List[TestMetrics]] = None,
    ) -> Path:
        """
        Генерирует HTML отчет с графиками.

        Args:
            metrics: Текущие метрики тестов
            output_path: Путь для сохранения отчета
            config: Конфигурация отчета
            historical_data: Исторические данные для сравнения

        Returns:
            Путь к созданному отчету
        """
        config = config or VisualReportConfig()

        logger.info(
            "Generating HTML report",
            extra={
                "output_path": str(output_path),
                "include_charts": config.include_charts,
            },
        )

        # Генерация HTML
        html_content = self._generate_html_content(
            metrics=metrics,
            config=config,
            historical_data=historical_data or [],
        )

        # Сохранение
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        logger.info("HTML report generated", extra={"output_path": str(output_path)})

        return output_path

    def _generate_html_content(
        self,
        metrics: TestMetrics,
        config: VisualReportConfig,
        historical_data: List[TestMetrics],
    ) -> str:
        """Генерирует HTML содержимое отчета."""

        # Расчет процентов
        pass_rate = (
            (metrics.passed_tests / metrics.total_tests * 100)
            if metrics.total_tests > 0
            else 0.0
        )
        fail_rate = (
            (metrics.failed_tests / metrics.total_tests * 100)
            if metrics.total_tests > 0
            else 0.0
        )

        # Данные для графиков
        chart_data = {
            "total": metrics.total_tests,
            "passed": metrics.passed_tests,
            "failed": metrics.failed_tests,
            "skipped": metrics.skipped_tests,
            "pass_rate": pass_rate,
            "fail_rate": fail_rate,
        }

        # HTML шаблон
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAxUnit Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        .header {{
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header .timestamp {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .metric-card.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        
        .metric-card.warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        
        .metric-card.info {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .chart-container {{
            margin: 30px 0;
            height: 400px;
            position: relative;
        }}
        
        .section {{
            margin: 30px 0;
        }}
        
        .section h2 {{
            color: #2c3e50;
            font-size: 22px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }}
        
        .timeline {{
            margin: 20px 0;
        }}
        
        .timeline-item {{
            padding: 15px;
            border-left: 3px solid #667eea;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        
        .timeline-item.success {{
            border-left-color: #38ef7d;
        }}
        
        .timeline-item.failure {{
            border-left-color: #f5576c;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 YAxUnit Test Report</h1>
            <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card success">
                <div class="metric-value">{metrics.passed_tests}</div>
                <div class="metric-label">Passed Tests</div>
            </div>
            <div class="metric-card warning">
                <div class="metric-value">{metrics.failed_tests}</div>
                <div class="metric-label">Failed Tests</div>
            </div>
            <div class="metric-card info">
                <div class="metric-value">{metrics.total_tests}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{pass_rate:.1f}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
        </div>
        
        {self._generate_charts_section(chart_data) if config.include_charts else ''}
        
        {self._generate_timeline_section(historical_data) if config.include_timeline and historical_data else ''}
        
        {self._generate_coverage_section(metrics) if config.include_coverage else ''}
        
        <div class="footer">
            <p>Generated by 1C AI Stack - YAxUnit Integration</p>
            <p>Test Execution Time: {metrics.execution_time:.2f}s</p>
        </div>
    </div>
    
    <script>
        // Инициализация графиков
        {self._generate_chart_js(chart_data) if config.include_charts else ''}
    </script>
</body>
</html>
"""

        return html

    def _generate_charts_section(self, chart_data: Dict) -> str:
        """Генерирует секцию с графиками."""
        return f"""
        <div class="section">
            <h2>📈 Test Results Chart</h2>
            <div class="chart-container">
                <canvas id="testResultsChart"></canvas>
            </div>
        </div>
        """

    def _generate_chart_js(self, chart_data: Dict) -> str:
        """Генерирует JavaScript для графиков."""
        return f"""
        const ctx = document.getElementById('testResultsChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Passed', 'Failed', 'Skipped'],
                    datasets: [{{
                        data: [{chart_data['passed']}, {chart_data['failed']}, {chart_data['skipped']}],
                        backgroundColor: [
                            'rgba(56, 239, 125, 0.8)',
                            'rgba(245, 87, 108, 0.8)',
                            'rgba(127, 140, 141, 0.8)'
                        ],
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }},
                        title: {{
                            display: true,
                            text: 'Test Results Distribution'
                        }}
                    }}
                }}
            }});
        }}
        """

    def _generate_timeline_section(self, historical_data: List[TestMetrics]) -> str:
        """Генерирует секцию временной линии."""
        timeline_items = []
        for i, metrics in enumerate(historical_data[-10:]):  # Последние 10 записей
            status = "success" if metrics.failed_tests == 0 else "failure"
            timeline_items.append(
                f"""
            <div class="timeline-item {status}">
                <strong>{metrics.timestamp or 'Unknown'}</strong>
                <div>Tests: {metrics.total_tests} | Passed: {metrics.passed_tests} | Failed: {metrics.failed_tests}</div>
            </div>
            """
            )

        return f"""
        <div class="section">
            <h2>📅 Test Execution Timeline</h2>
            <div class="timeline">
                {''.join(timeline_items)}
            </div>
        </div>
        """

    def _generate_coverage_section(self, metrics: TestMetrics) -> str:
        """Генерирует секцию покрытия."""
        return f"""
        <div class="section">
            <h2>🎯 Code Coverage</h2>
            <div class="metrics-grid">
                <div class="metric-card info">
                    <div class="metric-value">{metrics.code_coverage:.1f}%</div>
                    <div class="metric-label">Code Coverage</div>
                </div>
                <div class="metric-card info">
                    <div class="metric-value">{metrics.branch_coverage:.1f}%</div>
                    <div class="metric-label">Branch Coverage</div>
                </div>
            </div>
        </div>
        """
