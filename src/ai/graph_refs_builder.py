# [NEXUS IDENTITY] ID: -6690728770009980192 | DATE: 2025-11-19

"""
Graph Refs Builder для Scenario Hub
-----------------------------------

Утилита для автоматического построения graph_refs (ссылок на узлы Unified Change Graph)
для сценариев Scenario Hub на основе реальных артефактов проекта.

Используется для:
- Автоматического связывания сценариев с реальными узлами графа
- Построения traceability между требованиями, кодом, тестами и инфраструктурой
- Impact-анализа изменений
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from src.ai.code_analysis.graph import CodeGraphBackend, NodeKind

logger = logging.getLogger(__name__)


class GraphRefsBuilder:
    """
    Построитель graph_refs для сценариев на основе реальных артефактов проекта.
    """

    def __init__(self, backend: Optional[CodeGraphBackend] = None) -> None:
        """
        Args:
            backend: Backend графа (опционально, для поиска существующих узлов)
        """
        self.backend = backend
        self.project_root = Path(__file__).parent.parent.parent

    def set_backend(self, backend: CodeGraphBackend) -> None:
        """Установить backend графа."""
        self.backend = backend

    def build_refs_for_feature(
        self,
        feature_id: str,
        *,
        code_paths: Optional[List[str]] = None,
        test_paths: Optional[List[str]] = None,
        doc_paths: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Построить graph_refs для фичи на основе путей к коду, тестам и документации.

        Args:
            feature_id: Идентификатор фичи (например, "DEMO_FEATURE")
            code_paths: Список путей к файлам кода (например, ["src/ai/orchestrator.py"])
            test_paths: Список путей к тестам (например, ["tests/unit/test_orchestrator.py"])
            doc_paths: Список путей к документации (например, ["docs/06-features/AI_ORCHESTRATOR_GUIDE.md"])

        Returns:
            Список graph_refs в формате "node:<id>:<KIND>"
        """
        refs: List[str] = []

        # BA Requirement узел
        ba_req_id = f"ba-requirement:{feature_id}"
        refs.append(f"node:{ba_req_id}:BA_REQUIREMENT")

        # Узлы для файлов кода
        if code_paths:
            for code_path in code_paths:
                # Нормализовать путь
                normalized_path = self._normalize_path(code_path)
                if normalized_path:
                    # Определить тип узла по расширению/пути
                    node_kind = self._infer_node_kind(normalized_path)
                    node_id = self._build_node_id(normalized_path, node_kind)
                    refs.append(f"node:{node_id}:{node_kind.value}")

        # Узлы для тестов
        if test_paths:
            for test_path in test_paths:
                normalized_path = self._normalize_path(test_path)
                if normalized_path:
                    # Тесты всегда TEST_CASE или TEST_SUITE
                    node_id = self._build_node_id(normalized_path, NodeKind.TEST_CASE)
                    refs.append(f"node:{node_id}:TEST_CASE")

        # Узлы для документации
        if doc_paths:
            for doc_path in doc_paths:
                normalized_path = self._normalize_path(doc_path)
                if normalized_path:
                    node_id = self._build_node_id(normalized_path, NodeKind.FILE)
                    refs.append(f"node:{node_id}:FILE")

        return refs

    def build_refs_for_service(
        self,
        service_name: str,
        *,
        deployment_path: Optional[str] = None,
        helm_chart_path: Optional[str] = None,
        alert_paths: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Построить graph_refs для сервиса на основе инфраструктурных артефактов.

        Args:
            service_name: Имя сервиса (например, "ai-orchestrator")
            deployment_path: Путь к K8s deployment манифесту
            helm_chart_path: Путь к Helm chart
            alert_paths: Список путей к alert правилам

        Returns:
            Список graph_refs
        """
        refs: List[str] = []

        # Service узел
        service_id = f"service:{service_name}"
        refs.append(f"node:{service_id}:SERVICE")

        # Deployment узел
        if deployment_path:
            normalized_path = self._normalize_path(deployment_path)
            if normalized_path:
                node_id = self._build_node_id(normalized_path, NodeKind.K8S_DEPLOYMENT)
                refs.append(f"node:{node_id}:K8S_DEPLOYMENT")

        # Helm chart узел
        if helm_chart_path:
            normalized_path = self._normalize_path(helm_chart_path)
            if normalized_path:
                node_id = self._build_node_id(normalized_path, NodeKind.HELM_CHART)
                refs.append(f"node:{node_id}:HELM_CHART")

        # Alert узлы
        if alert_paths:
            for alert_path in alert_paths:
                normalized_path = self._normalize_path(alert_path)
                if normalized_path:
                    node_id = self._build_node_id(normalized_path, NodeKind.ALERT)
                    refs.append(f"node:{node_id}:ALERT")

        return refs

    def build_refs_for_module(
        self,
        module_path: str,
        *,
        functions: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Построить graph_refs для BSL модуля.

        Args:
            module_path: Путь к модулю (например, "ОбщийМодуль.УправлениеЗаказами")
            functions: Список имён функций/процедур в модуле

        Returns:
            Список graph_refs
        """
        refs: List[str] = []

        # Module узел
        module_id = f"module:{module_path}"
        refs.append(f"node:{module_id}:MODULE")

        # Function узлы
        if functions:
            for func_name in functions:
                func_id = f"function:{module_path}:{func_name}"
                refs.append(f"node:{func_id}:FUNCTION")

        return refs

    async def find_refs_by_keywords(
        self,
        keywords: List[str],
        *,
        node_kinds: Optional[List[NodeKind]] = None,
    ) -> List[str]:
        """
        Найти graph_refs по ключевым словам (если backend доступен).

        Args:
            keywords: Список ключевых слов для поиска
            node_kinds: Фильтр по типам узлов

        Returns:
            Список graph_refs найденных узлов
        """
        if not self.backend:
            logger.debug("Backend not available, returning empty refs")
            return []

        try:
            from src.ai.code_analysis.graph_query_helper import GraphQueryHelper

            helper = GraphQueryHelper(self.backend)
            # Используем первое ключевое слово для поиска
            if keywords:
                query = " ".join(keywords)
                found_nodes = await helper.find_nodes_by_query(
                    query,
                    max_results=10,
                    node_kinds=node_kinds,
                )
                return [f"node:{node.id}:{node.kind.value}" for node in found_nodes]
        except Exception as e:
            logger.debug("Failed to find refs by keywords: %s", e)

        return []

    def _normalize_path(self, path: str) -> Optional[str]:
        """
        Нормализовать путь к файлу относительно project_root.

        Args:
            path: Путь к файлу (может быть абсолютным или относительным)

        Returns:
            Нормализованный путь или None, если файл не существует
        """
        # Если путь абсолютный, сделать его относительным к project_root
        if Path(path).is_absolute():
            try:
                rel_path = Path(path).relative_to(self.project_root)
                return str(rel_path).replace("\\", "/")
            except ValueError:
                # Путь не внутри project_root
                return None

        # Если путь относительный, проверить существование
        full_path = self.project_root / path
        if full_path.exists():
            return path.replace("\\", "/")

        return None

    def _infer_node_kind(self, path: str) -> NodeKind:
        """
        Определить тип узла по пути к файлу.

        Args:
            path: Путь к файлу

        Returns:
            NodeKind для этого файла
        """
        path_lower = path.lower()

        # Python модули
        if path.endswith(".py") and "src/" in path:
            if "test" in path_lower:
                return NodeKind.TEST_CASE
            elif "agent" in path_lower or "orchestrator" in path_lower:
                return NodeKind.MODULE
            else:
                return NodeKind.MODULE

        # YAML/JSON конфигурации
        if path.endswith((".yaml", ".yml", ".json")):
            if "deployment" in path_lower or "k8s" in path_lower:
                return NodeKind.K8S_DEPLOYMENT
            elif "helm" in path_lower or "chart" in path_lower:
                return NodeKind.HELM_CHART
            elif "alert" in path_lower:
                return NodeKind.ALERT
            elif "playbook" in path_lower:
                return NodeKind.FILE

        # Markdown документация
        if path.endswith(".md"):
            return NodeKind.FILE

        # По умолчанию - FILE
        return NodeKind.FILE

    def _build_node_id(self, path: str, kind: NodeKind) -> str:
        """
        Построить ID узла на основе пути и типа.

        Args:
            path: Путь к файлу
            kind: Тип узла

        Returns:
            ID узла в формате "<kind>:<path>"
        """
        # Убрать расширение для некоторых типов
        if kind in (NodeKind.MODULE, NodeKind.FILE):
            base_path = path.rsplit(".", 1)[0] if "." in path else path
            return f"{kind.value}:{base_path}"
        else:
            return f"{kind.value}:{path}"


# Глобальный экземпляр для удобства
_graph_refs_builder = GraphRefsBuilder()


def build_refs_for_feature(
    feature_id: str,
    *,
    code_paths: Optional[List[str]] = None,
    test_paths: Optional[List[str]] = None,
    doc_paths: Optional[List[str]] = None,
) -> List[str]:
    """
    Удобная функция для построения graph_refs для фичи.

    Args:
        feature_id: Идентификатор фичи
        code_paths: Пути к файлам кода
        test_paths: Пути к тестам
        doc_paths: Пути к документации

    Returns:
        Список graph_refs
    """
    return _graph_refs_builder.build_refs_for_feature(
        feature_id,
        code_paths=code_paths,
        test_paths=test_paths,
        doc_paths=doc_paths,
    )


def build_refs_for_service(
    service_name: str,
    *,
    deployment_path: Optional[str] = None,
    helm_chart_path: Optional[str] = None,
    alert_paths: Optional[List[str]] = None,
) -> List[str]:
    """
    Удобная функция для построения graph_refs для сервиса.

    Args:
        service_name: Имя сервиса
        deployment_path: Путь к deployment манифесту
        helm_chart_path: Путь к Helm chart
        alert_paths: Пути к alert правилам

    Returns:
        Список graph_refs
    """
    return _graph_refs_builder.build_refs_for_service(
        service_name,
        deployment_path=deployment_path,
        helm_chart_path=helm_chart_path,
        alert_paths=alert_paths,
    )
