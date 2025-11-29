from src.modules.project_manager.domain.models import Task
from src.modules.project_manager.domain.exceptions import InvalidEstimationError

class EffortEstimator:
    """
    Service for estimating task effort using Planning Poker logic (Fibonacci).
    """
    
    FIBONACCI_SCALE = [1, 2, 3, 5, 8, 13, 21]
    
    def estimate(self, task: Task) -> int:
        """
        Estimates the effort for a given task based on its characteristics.
        Returns a Fibonacci number.
        """
        complexity_score = 0
        
        # 1. Analyze Description Length (Heuristic)
        word_count = len(task.description.split())
        if word_count < 10: complexity_score += 1
        elif word_count < 50: complexity_score += 2
        else: complexity_score += 3
        
        # 2. Analyze Keywords (Heuristic)
        desc_lower = task.description.lower()
        if "migration" in desc_lower or "architecture" in desc_lower:
            complexity_score += 5
        elif "api" in desc_lower or "integration" in desc_lower:
            complexity_score += 3
        elif "ui" in desc_lower or "button" in desc_lower:
            complexity_score += 2
            
        # 3. Map to Fibonacci
        return self._map_to_fibonacci(complexity_score)
    
    def _map_to_fibonacci(self, score: int) -> int:
        """Maps a raw complexity score to the nearest Fibonacci number."""
        if score <= 1: return 1
        if score <= 2: return 2
        if score <= 3: return 3
        if score <= 5: return 5
        if score <= 8: return 8
        if score <= 13: return 13
        return 21  # Cap at 21, suggest decomposition
