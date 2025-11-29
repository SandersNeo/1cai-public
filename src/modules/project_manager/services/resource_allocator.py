from typing import List, Dict, Optional
from src.modules.project_manager.domain.models import AgentProfile, Skill, Task


class ResourceAllocator:
    """
    Сервис для управления ресурсами агентов и навыками.
    """

    def __init__(self):
        # Инициализация агентов по умолчанию (в реальном приложении это было бы из БД)
        self.agents = [
            AgentProfile(id="developer_ai", name="Developer", skills=[Skill.PYTHON, Skill.BSL, Skill.SQL]),
            AgentProfile(id="qa_ai", name="QA Engineer", skills=[Skill.TESTING, Skill.PYTHON]),
            AgentProfile(id="ba_ai", name="Business Analyst", skills=[Skill.ANALYSIS]),
            AgentProfile(id="devops_ai", name="DevOps", skills=[Skill.DEVOPS]),
            AgentProfile(id="security_ai", name="Security Officer", skills=[Skill.SECURITY]),
            AgentProfile(id="tech_writer_ai", name="Technical Writer", skills=[Skill.DOCS]),
        ]

    def get_best_agent_for_task(self, task: Task) -> Optional[AgentProfile]:
        """
        Находит наиболее подходящего агента для задачи на основе тегов/навыков.
        """
        required_skills = self._infer_skills_from_task(task)

        best_agent = None
        max_match = -1

        for agent in self.agents:
            match_count = sum(1 for s in required_skills if s in agent.skills)
            if match_count > max_match:
                max_match = match_count
                best_agent = agent
            elif match_count == max_match and match_count > 0:
                # Тай-брейкер: эффективность? Пока берем первого найденного.
                pass

        return best_agent

    def _infer_skills_from_task(self, task: Task) -> List[Skill]:
        """
        Выводит требуемые навыки из тегов или описания задачи.
        """
        skills = []
        text = (task.title + " " + task.description + " " + " ".join(task.tags)).upper()

        if "PYTHON" in text or "BACKEND" in text or "ПИТОН" in text or "БЭКЕНД" in text:
            skills.append(Skill.PYTHON)
        if "SQL" in text or "DATABASE" in text or "БАЗА" in text or "БД" in text:
            skills.append(Skill.SQL)
        if "BSL" in text or "1C" in text or "1С" in text:
            skills.append(Skill.BSL)
        if "TEST" in text or "QA" in text or "ТЕСТ" in text:
            skills.append(Skill.TESTING)
        if "DEPLOY" in text or "CI/CD" in text or "ДЕПЛОЙ" in text:
            skills.append(Skill.DEVOPS)
        if "DOC" in text or "ДОК" in text:
            skills.append(Skill.DOCS)
        if "SECURITY" in text or "AUDIT" in text or "БЕЗОПАСНОСТЬ" in text or "АУДИТ" in text:
            skills.append(Skill.SECURITY)

        return skills

    def check_capacity(self, tasks: List[Task]) -> Dict[str, int]:
        """
        Рассчитывает требуемую емкость по навыкам.
        """
        skill_load = {s: 0 for s in Skill}

        for task in tasks:
            skills = self._infer_skills_from_task(task)
            points = task.story_points or 1
            if not skills:
                # По умолчанию Python, если неизвестно
                skill_load[Skill.PYTHON] += points
            else:
                # Распределяем очки по навыкам (упрощенно)
                for s in skills:
                    skill_load[s] += points

        return {k.value: v for k, v in skill_load.items() if v > 0}
