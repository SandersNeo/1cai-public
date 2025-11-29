from typing import List
from src.modules.project_manager.domain.models import Task, TaskPriority, TaskStatus

class TaskDecomposer:
    """
    Service for decomposing high-level tasks into subtasks.
    Follows INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable).
    """
    
    def decompose(self, parent_task: Task) -> List[Task]:
        """
        Decomposes a parent task into smaller, manageable subtasks.
        This is a heuristic-based decomposition (simulated logic for now).
        In a real scenario, this would use LLM to generate subtasks.
        """
        subtasks = []
        
        # Heuristic: If task description contains "frontend" and "backend", split it.
        desc_lower = parent_task.description.lower()
        
        if "frontend" in desc_lower or "ui" in desc_lower:
            subtasks.append(self._create_subtask(parent_task, "Frontend Implementation", "Implement UI components"))
            
        if "backend" in desc_lower or "api" in desc_lower:
            subtasks.append(self._create_subtask(parent_task, "Backend API", "Implement API endpoints"))
            
        if "database" in desc_lower or "model" in desc_lower:
            subtasks.append(self._create_subtask(parent_task, "Database Schema", "Define and migrate DB schema"))
            
        if "test" in desc_lower:
            subtasks.append(self._create_subtask(parent_task, "Testing", "Write unit and integration tests"))
            
        # If no specific keywords found, create generic subtasks
        if not subtasks:
            subtasks.append(self._create_subtask(parent_task, "Analysis & Design", "Analyze requirements and design solution"))
            subtasks.append(self._create_subtask(parent_task, "Implementation", "Write code"))
            subtasks.append(self._create_subtask(parent_task, "Verification", "Test and verify"))
            
        return subtasks

    def _create_subtask(self, parent: Task, suffix: str, desc: str) -> Task:
        return Task(
            id=f"{parent.id}-{suffix.replace(' ', '-').lower()}",
            title=f"{parent.title} - {suffix}",
            description=desc,
            priority=parent.priority,
            status=TaskStatus.TODO,
            dependencies=[parent.id]
        )
