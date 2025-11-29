from typing import List, Dict
from datetime import date, timedelta
from src.modules.project_manager.domain.models import Task, Sprint, TaskPriority, TaskStatus
from src.modules.project_manager.domain.exceptions import SprintPlanningError
from src.modules.project_manager.services.resource_allocator import ResourceAllocator


class SprintPlanner:
    """
    Сервис для планирования спринтов на основе емкости команды и приоритетов задач.
    Использует планирование на основе Velocity и приоритизацию MoSCoW.
    """

    def __init__(self, resource_allocator: ResourceAllocator = None):
        self.resource_allocator = resource_allocator or ResourceAllocator()

    def plan_sprint(
        self, sprint_name: str, start_date: date, duration_weeks: int, capacity: int, backlog: List[Task]
    ) -> Sprint:
        """
        Создает план спринта, выбирая задачи из бэклога.
        """
        if capacity <= 0:
            raise SprintPlanningError("Capacity must be greater than 0.")

        # 1. Сортировка бэклога по приоритету (MUST > SHOULD > COULD > WONT)
        sorted_backlog = sorted(backlog, key=self._priority_sort_key)

        selected_tasks = []
        current_load = 0

        # 2. Заполнение спринта (Жадный алгоритм)
        for task in sorted_backlog:
            if task.status != TaskStatus.BACKLOG:
                continue  # Пропускаем задачи не из бэклога

            task_points = task.story_points or 0

            # Проверяем, влезает ли задача в оставшуюся емкость
            if current_load + task_points <= capacity:
                # Назначаем агента
                agent = self.resource_allocator.get_best_agent_for_task(task)
                if agent:
                    task.assignee_id = agent.id

                selected_tasks.append(task)
                current_load += task_points
            else:
                # Если это MUST have, мы могли бы предупредить или немного переполнить (но здесь придерживаемся емкости)
                pass

        # 3. Создание объекта Sprint
        end_date = start_date + timedelta(weeks=duration_weeks)

        return Sprint(
            id=f"sprint-{start_date.strftime('%Y%m%d')}",
            name=sprint_name,
            start_date=start_date,
            end_date=end_date,
            goal=f"Выполнить {len(selected_tasks)} задач с общим объемом {current_load} SP",
            capacity=capacity,
            tasks=selected_tasks,
        )

    def _priority_sort_key(self, task: Task) -> int:
        priority_map = {TaskPriority.MUST: 0, TaskPriority.SHOULD: 1, TaskPriority.COULD: 2, TaskPriority.WONT: 3}
        return priority_map.get(task.priority, 4)
