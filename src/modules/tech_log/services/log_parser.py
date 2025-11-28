"""
Log Parser Service

Сервис для парсинга технологического журнала 1С.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from src.modules.tech_log.domain.exceptions import LogFileNotFoundError, LogParsingError
from src.modules.tech_log.domain.models import (
    LogAnalysisResult,
    Severity,
    TechLogEvent,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class LogParser:
    """
    Сервис парсинга tech log

    Features:
    - Tech log file parsing
    - Event extraction
    - Time period filtering
    - Multi-file support
    """

    # Thresholds for severity determination
    SLOW_QUERY_MS = 1000
    VERY_SLOW_QUERY_MS = 5000

    def __init__(self):
        """Initialize parser"""

    async def parse_tech_log(
        self,
        log_path: str,
        time_period: Optional[Tuple[datetime, datetime]] = None
    ) -> LogAnalysisResult:
        """
        Парсинг технологического журнала

        Args:
            log_path: Путь к файлу(ам) tech log
            time_period: Период анализа (начало, конец)

        Returns:
            LogAnalysisResult
        """
        try:
            logger.info(
                "Parsing tech log",
                extra={"log_path": log_path}
            )

            # Find log files
            log_files = self._find_log_files(log_path, time_period)

            if not log_files:
                raise LogFileNotFoundError(
                    f"No log files found at {log_path}",
                    details={"log_path": log_path}
                )

            # Parse all files
            all_events = []
            for log_file in log_files:
                events = await self._parse_log_file(log_file)
                all_events.extend(events)

            # Group events
            events_by_type = self._group_by_type(all_events)
            events_by_severity = self._group_by_severity(all_events)

            # Determine time period
            if all_events:
                time_start = min(e.timestamp for e in all_events)
                time_end = max(e.timestamp for e in all_events)
            else:
                time_start = datetime.now()
                time_end = datetime.now()

            return LogAnalysisResult(
                total_events=len(all_events),
                time_period_start=time_start,
                time_period_end=time_end,
                events_by_type=events_by_type,
                events_by_severity=events_by_severity
            )

        except Exception as e:
            logger.error("Failed to parse tech log: %s", e)
            raise LogParsingError(
                f"Failed to parse tech log: {e}",
                details={"log_path": log_path}
            )

    def _find_log_files(
        self,
        log_path: str,
        time_period: Optional[Tuple[datetime, datetime]]
    ) -> List[Path]:
        """Поиск файлов tech log"""
        path = Path(log_path)

        if path.is_file():
            return [path]
        elif path.is_dir():
            # Find all .log files
            return list(path.glob("*.log"))
        else:
            return []

    async def _parse_log_file(self, log_file: Path) -> List[TechLogEvent]:
        """Парсинг одного файла tech log"""
        events = []

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple parsing (упрощенная версия)
            # Формат: timestamp,event_type,duration,process,...
            lines = content.split('\n')

            for line in lines:
                if not line.strip():
                    continue

                try:
                    event = self._parse_event_line(line)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.debug("Failed to parse line: %s", e)
                    continue

        except Exception as e:
            logger.error("Failed to read log file %s: {e}", log_file)

        return events

    def _parse_event_line(self, line: str) -> Optional[TechLogEvent]:
        """Парсинг строки события"""
        # Упрощенный парсинг
        # Формат: 59:49.123456-1234,DBMSSQL,5,process=rphost,...

        parts = line.split(',')
        if len(parts) < 3:
            return None

        try:
            # Parse timestamp (упрощенно)
            timestamp = datetime.now()

            # Parse event type
            event_type = parts[1] if len(parts) > 1 else "UNKNOWN"

            # Parse duration
            duration_ms = int(parts[2]) if len(parts) > 2 else 0

            # Determine severity
            severity = self._determine_severity(
                event_type,
                duration_ms,
                None
            )

            return TechLogEvent(
                timestamp=timestamp,
                duration_ms=duration_ms,
                event_type=event_type,
                process=parts[3] if len(parts) > 3 else "",
                user="",
                application="",
                event=event_type,
                context="",
                severity=severity
            )

        except Exception as e:
            logger.debug("Failed to parse event: %s", e)
            return None

    def _determine_severity(
        self,
        event_type: str,
        duration_ms: int,
        error: Optional[str]
    ) -> Severity:
        """Определение severity"""
        if error:
            return Severity.ERROR

        if event_type == "EXCP":
            return Severity.ERROR

        if duration_ms >= self.VERY_SLOW_QUERY_MS:
            return Severity.CRITICAL

        if duration_ms >= self.SLOW_QUERY_MS:
            return Severity.WARNING

        return Severity.INFO

    def _group_by_type(
        self,
        events: List[TechLogEvent]
    ) -> dict:
        """Группировка по типу события"""
        result = {}
        for event in events:
            event_type = event.event_type
            result[event_type] = result.get(event_type, 0) + 1
        return result

    def _group_by_severity(
        self,
        events: List[TechLogEvent]
    ) -> dict:
        """Группировка по severity"""
        result = {}
        for event in events:
            severity = event.severity.value
            result[severity] = result.get(severity, 0) + 1
        return result


__all__ = ["LogParser"]
