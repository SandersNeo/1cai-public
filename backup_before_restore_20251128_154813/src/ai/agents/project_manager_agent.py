"""
Project Manager AI Agent

Специализированный агент для project management, task planning,
effort estimation, и resource allocation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent


class TaskPriority(str, Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task status"""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class ProjectManagerAgent(BaseAgent):
    """
    Project Manager AI Agent для автоматического планирования и управления.

    Capabilities:
    - Task decomposition
    - Effort estimation
    - Sprint planning
    - Resource allocation
    - Risk management
    - Progress tracking
    """

    # Effort estimation factors
    COMPLEXITY_MULTIPLIERS = {
        "simple": 1.0,
        "moderate": 1.5,
        "complex": 2.5,
        "very_complex": 4.0,
    }

    # Risk factors
    RISK_FACTORS = {
        "new_technology": 1.3,
        "unclear_requirements": 1.5,
        "tight_deadline": 1.2,
        "large_team": 1.1,
        "legacy_code": 1.4,
    }

    def __init__(self):
        super().__init__(
            agent_name="project_manager_agent",
            capabilities=[
                AgentCapability.PROJECT_MANAGEMENT,
            ],
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process project management request.

        Args:
            input_data: {
                "action": str,  # decompose, estimate, plan_sprint, etc.
                "data": dict,   # Action-specific data
            }

        Returns:
            Processing result
        """
        action = input_data.get("action", "")
        data = input_data.get("data", {})

        if action == "decompose_task":
            return await self._decompose_task(data)
        elif action == "estimate_effort":
            return await self._estimate_effort(data)
        elif action == "plan_sprint":
            return await self._plan_sprint(data)
        elif action == "allocate_resources":
            return await self._allocate_resources(data)
        elif action == "assess_risks":
            return await self._assess_risks(data)
        elif action == "track_progress":
            return await self._track_progress(data)
        else:
            return {"error": f"Unknown action: {action}"}

    async def _decompose_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompose high-level task into subtasks.

        Args:
            data: {
                "task_description": str,
                "max_depth": int,  # Decomposition depth
            }

        Returns:
            Task decomposition tree
        """
        description = data.get("task_description", "")
        max_depth = data.get("max_depth", 3)

        # Analyze task complexity
        complexity = self._analyze_complexity(description)

        # Generate subtasks (placeholder - в production: AI model)
        subtasks = self._generate_subtasks(description, complexity, max_depth)

        return {
            "original_task": description,
            "complexity": complexity,
            "subtasks": subtasks,
            "total_subtasks": len(subtasks),
            "estimated_depth": min(max_depth, len(subtasks) // 3),
        }

    async def _estimate_effort(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate effort for tasks.

        Args:
            data: {
                "tasks": List[{
                    "description": str,
                    "complexity": str,
                    "risk_factors": List[str],
                }]
            }

        Returns:
            Effort estimates
        """
        tasks = data.get("tasks", [])
        estimates = []

        for task in tasks:
            description = task.get("description", "")
            complexity = task.get("complexity", "moderate")
            risk_factors = task.get("risk_factors", [])

            # Base estimate (hours)
            base_hours = self._calculate_base_hours(description)

            # Apply complexity multiplier
            complexity_mult = self.COMPLEXITY_MULTIPLIERS.get(complexity, 1.5)

            # Apply risk factors
            risk_mult = 1.0
            for risk in risk_factors:
                risk_mult *= self.RISK_FACTORS.get(risk, 1.0)

            # Final estimate
            estimated_hours = base_hours * complexity_mult * risk_mult

            estimates.append(
                {
                    "task": description,
                    "base_hours": round(
                        base_hours,
                        1),
                    "complexity": complexity,
                    "risk_factors": risk_factors,
                    "estimated_hours": round(
                        estimated_hours,
                        1),
                    "estimated_days": round(
                        estimated_hours / 8,
                        1),
                    "confidence": self._calculate_confidence(
                        complexity,
                        risk_factors),
                })

        total_hours = sum(e["estimated_hours"] for e in estimates)

        return {
            "estimates": estimates,
            "total_hours": round(total_hours, 1),
            "total_days": round(total_hours / 8, 1),
            "total_weeks": round(total_hours / 40, 1),
        }

    async def _plan_sprint(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan sprint with tasks and capacity.

        Args:
            data: {
                "sprint_duration_days": int,
                "team_capacity_hours": float,
                "tasks": List[Dict],
                "priorities": Dict[str, str],
            }

        Returns:
            Sprint plan
        """
        duration = data.get("sprint_duration_days", 14)
        capacity = data.get("team_capacity_hours", 80)
        tasks = data.get("tasks", [])
        priorities = data.get("priorities", {})

        # Sort tasks by priority
        sorted_tasks = self._prioritize_tasks(tasks, priorities)

        # Allocate tasks to sprint
        sprint_tasks = []
        remaining_capacity = capacity

        for task in sorted_tasks:
            task_hours = task.get("estimated_hours", 8)

            if task_hours <= remaining_capacity:
                sprint_tasks.append(task)
                remaining_capacity -= task_hours
            else:
                # Task doesn't fit
                break

        return {
            "sprint_duration_days": duration,
            "team_capacity_hours": capacity,
            "allocated_tasks": sprint_tasks,
            "total_allocated_hours": capacity - remaining_capacity,
            "remaining_capacity_hours": remaining_capacity,
            "capacity_utilization": round(
                (capacity - remaining_capacity) / capacity * 100, 1
            ),
            "backlog_tasks": len(tasks) - len(sprint_tasks),
        }

    async def _allocate_resources(
            self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allocate resources to tasks.

        Args:
            data: {
                "tasks": List[Dict],
                "team_members": List[{
                    "name": str,
                    "skills": List[str],
                    "capacity_hours": float,
                }]
            }

        Returns:
            Resource allocation
        """
        tasks = data.get("tasks", [])
        team = data.get("team_members", [])

        allocations = []

        for task in tasks:
            required_skills = task.get("required_skills", [])
            estimated_hours = task.get("estimated_hours", 8)

            # Find best match
            best_match = self._find_best_resource(task, team, required_skills)

            if best_match:
                allocations.append(
                    {
                        "task": task.get("description", ""),
                        "assigned_to": best_match["name"],
                        "match_score": best_match["match_score"],
                        "estimated_hours": estimated_hours,
                    }
                )

        return {
            "allocations": allocations,
            "total_tasks": len(tasks),
            "allocated_tasks": len(allocations),
            "unallocated_tasks": len(tasks) - len(allocations),
        }

    async def _assess_risks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess project risks.

        Args:
            data: {
                "project_description": str,
                "timeline_days": int,
                "team_size": int,
                "technologies": List[str],
            }

        Returns:
            Risk assessment
        """
        data.get("project_description", "")
        timeline = data.get("timeline_days", 90)
        team_size = data.get("team_size", 5)
        technologies = data.get("technologies", [])

        risks = []

        # Timeline risk
        if timeline < 30:
            risks.append({"type": "timeline",
                          "severity": "high",
                          "description": "Very tight timeline",
                          "mitigation": "Consider MVP approach or timeline extension",
                          })

        # Team size risk
        if team_size > 10:
            risks.append(
                {
                    "type": "team_size",
                    "severity": "medium",
                    "description": "Large team coordination overhead",
                    "mitigation": "Implement clear communication protocols",
                }
            )

        # Technology risk
        new_tech_count = len([t for t in technologies if "new" in t.lower()])
        if new_tech_count > 0:
            risks.append(
                {
                    "type": "technology",
                    "severity": "medium",
                    "description": f"{new_tech_count} new technologies",
                    "mitigation": "Allocate time for learning and POCs",
                }
            )

        # Calculate overall risk score
        risk_score = self._calculate_risk_score(risks)

        return {
            "risks": risks,
            "total_risks": len(risks),
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
        }

    async def _track_progress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track project progress.

        Args:
            data: {
                "tasks": List[{
                    "description": str,
                    "status": str,
                    "estimated_hours": float,
                    "actual_hours": float,
                }]
            }

        Returns:
            Progress report
        """
        tasks = data.get("tasks", [])

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("status") == "done"])
        in_progress_tasks = len(
            [t for t in tasks if t.get("status") == "in_progress"])
        blocked_tasks = len([t for t in tasks if t.get("status") == "blocked"])

        total_estimated = sum(t.get("estimated_hours", 0) for t in tasks)
        total_actual = sum(t.get("actual_hours", 0) for t in tasks)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "blocked_tasks": blocked_tasks,
            "completion_percentage": (
                round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
            ),
            "total_estimated_hours": round(total_estimated, 1),
            "total_actual_hours": round(total_actual, 1),
            "variance_hours": round(total_actual - total_estimated, 1),
            "variance_percentage": (
                round((total_actual - total_estimated) / total_estimated * 100, 1)
                if total_estimated > 0
                else 0
            ),
        }

    # Helper methods

    def _analyze_complexity(self, description: str) -> str:
        """Analyze task complexity"""
        word_count = len(description.split())

        if word_count < 10:
            return "simple"
        elif word_count < 30:
            return "moderate"
        elif word_count < 60:
            return "complex"
        else:
            return "very_complex"

    def _generate_subtasks(
        self, description: str, complexity: str, max_depth: int
    ) -> List[Dict]:
        """Generate subtasks (placeholder)"""
        # В production: AI model для генерации
        num_subtasks = {
            "simple": 2,
            "moderate": 4,
            "complex": 6,
            "very_complex": 8,
        }.get(complexity, 4)

        return [
            {
                "id": i + 1,
                "description": f"Subtask {i + 1} for: {description[:30]}...",
                "estimated_hours": 4.0,
            }
            for i in range(num_subtasks)
        ]

    def _calculate_base_hours(self, description: str) -> float:
        """Calculate base effort hours"""
        # Simple heuristic based on description length
        word_count = len(description.split())
        return max(2.0, word_count * 0.5)

    def _calculate_confidence(
            self,
            complexity: str,
            risk_factors: List[str]) -> float:
        """Calculate estimation confidence (0-1)"""
        base_confidence = {
            "simple": 0.9,
            "moderate": 0.7,
            "complex": 0.5,
            "very_complex": 0.3,
        }.get(complexity, 0.5)

        # Reduce confidence for each risk factor
        confidence = base_confidence * (0.9 ** len(risk_factors))

        return round(confidence, 2)

    def _prioritize_tasks(
        self, tasks: List[Dict], priorities: Dict[str, str]
    ) -> List[Dict]:
        """Sort tasks by priority"""
        priority_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
        }

        def get_priority_value(task):
            task_id = task.get("id", "")
            priority = priorities.get(task_id, "medium")
            return priority_order.get(priority, 2)

        return sorted(tasks, key=get_priority_value)

    def _find_best_resource(
        self, task: Dict, team: List[Dict], required_skills: List[str]
    ) -> Optional[Dict]:
        """Find best team member for task"""
        best_match = None
        best_score = 0

        for member in team:
            member_skills = set(member.get("skills", []))
            required_skills_set = set(required_skills)

            # Calculate match score
            matching_skills = member_skills.intersection(required_skills_set)
            match_score = (
                len(matching_skills) / len(required_skills_set)
                if required_skills_set
                else 0
            )

            if match_score > best_score:
                best_score = match_score
                best_match = {
                    **member,
                    "match_score": round(match_score, 2),
                }

        return best_match

    def _calculate_risk_score(self, risks: List[Dict]) -> float:
        """Calculate overall risk score (0-100)"""
        severity_scores = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 2,
        }

        total_score = sum(
            severity_scores.get(r.get("severity", "medium"), 4) for r in risks
        )

        return min(100.0, total_score * 5)

    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level from score"""
        if risk_score >= 70:
            return "critical"
        elif risk_score >= 40:
            return "high"
        elif risk_score >= 20:
            return "medium"
        else:
            return "low"


__all__ = ["ProjectManagerAgent", "TaskPriority", "TaskStatus"]
