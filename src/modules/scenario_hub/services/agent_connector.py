import httpx
from typing import Dict, Any, Optional


class AgentConnector:
    """
    Сервис для взаимодействия с другими AI-агентами через их API.
    Действует как клиент для внутренней коммуникации агент-агент.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def call_agent(
        self, agent_name: str, endpoint: str, method: str = "POST", data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Вызывает API эндпоинт конкретного агента.
        """
        url = f"{self.base_url}/{agent_name}/{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, params=data)
                elif method == "POST":
                    response = await client.post(url, json=data)
                else:
                    raise ValueError(f"Неподдерживаемый метод: {method}")

                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                # В реальной системе мы могли бы повторить попытку или логировать это лучше
                raise RuntimeError(f"Не удалось вызвать агента {agent_name}: {str(e)}")

    async def analyze_risk(self, description: str, probability: int, impact: int) -> Dict[str, Any]:
        """Обертка для Анализа Рисков (Project Manager)"""
        return await self.call_agent(
            "project_manager",
            "analyze_risk",
            data={"description": description, "probability": probability, "impact": impact},
        )

    async def scan_code(self, code: str) -> Dict[str, Any]:
        """Обертка для Сканирования Уязвимостей (Security Officer)"""
        pass
