"""
Session Analyzer Service

Сервис для анализа сессий пользователей.
"""

from typing import List

from src.modules.ras_monitor.domain.exceptions import SessionAnalysisError
from src.modules.ras_monitor.domain.models import Session, SessionAnalysis, SessionState
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class SessionAnalyzer:
    """
    Сервис анализа сессий

    Features:
    - Session tracking
    - Resource usage analysis
    - Long-running session detection
    - Session state monitoring
    """

    # Thresholds
    LONG_RUNNING_HOURS = 8
    HIGH_CPU_MS = 10000
    HIGH_MEMORY_MB = 512.0

    def __init__(self):
        """Initialize analyzer"""

    async def analyze_sessions(
        self,
        sessions: List[Session]
    ) -> SessionAnalysis:
        """
        Анализ сессий

        Args:
            sessions: Список сессий

        Returns:
            SessionAnalysis
        """
        try:
            logger.info(
                "Analyzing sessions",
                extra={"sessions_count": len(sessions)}
            )

            # Group by state
            sessions_by_state = self._group_by_state(sessions)

            # Find top CPU sessions
            top_cpu_sessions = self._find_top_cpu_sessions(sessions)

            # Find top memory sessions
            top_memory_sessions = self._find_top_memory_sessions(sessions)

            # Find long-running sessions
            long_running_sessions = self._find_long_running_sessions(
                sessions
            )

            return SessionAnalysis(
                total_sessions=len(sessions),
                sessions_by_state=sessions_by_state,
                top_cpu_sessions=top_cpu_sessions[:5],
                top_memory_sessions=top_memory_sessions[:5],
                long_running_sessions=long_running_sessions[:5]
            )

        except Exception as e:
            logger.error("Failed to analyze sessions: %s", e)
            raise SessionAnalysisError(
                f"Failed to analyze sessions: {e}",
                details={}
            )

    def _group_by_state(self, sessions: List[Session]) -> dict:
        """Группировка по состоянию"""
        result = {}
        for session in sessions:
            state = session.state.value
            result[state] = result.get(state, 0) + 1
        return result

    def _find_top_cpu_sessions(
        self,
        sessions: List[Session]
    ) -> List[Session]:
        """Поиск сессий с высоким CPU"""
        return sorted(
            sessions,
            key=lambda s: s.cpu_time_ms,
            reverse=True
        )

    def _find_top_memory_sessions(
        self,
        sessions: List[Session]
    ) -> List[Session]:
        """Поиск сессий с высокой памятью"""
        return sorted(
            sessions,
            key=lambda s: s.memory_mb,
            reverse=True
        )

    def _find_long_running_sessions(
        self,
        sessions: List[Session]
    ) -> List[Session]:
        """Поиск долгих сессий"""
        from datetime import datetime, timedelta

        threshold = datetime.now() - timedelta(hours=self.LONG_RUNNING_HOURS)

        return [
            s for s in sessions
            if s.started_at < threshold
        ]

    async def detect_problematic_sessions(
        self,
        sessions: List[Session]
    ) -> List[dict]:
        """
        Детекция проблемных сессий

        Args:
            sessions: Список сессий

        Returns:
            Список проблемных сессий с описанием проблем
        """
        problematic = []

        for session in sessions:
            issues = []

            # High CPU
            if session.cpu_time_ms > self.HIGH_CPU_MS:
                issues.append(
                    f"High CPU usage: {session.cpu_time_ms} ms"
                )

            # High memory
            if session.memory_mb > self.HIGH_MEMORY_MB:
                issues.append(
                    f"High memory usage: {session.memory_mb} MB"
                )

            # Blocked state
            if session.state == SessionState.BLOCKED:
                issues.append("Session is blocked")

            if issues:
                problematic.append({
                    "session": session,
                    "issues": issues
                })

        return problematic


__all__ = ["SessionAnalyzer"]
