"""
Scenario Memory

Multi-scale memory system for automation scenarios.
Implements 4-level continuum memory for workflow optimization.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.modules.nested_learning.services.cms import ContinuumMemorySystem
from src.modules.nested_learning.services.memory_level import MemoryLevel, MemoryLevelConfig
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ScenarioMemoryLevel(MemoryLevel):
    """Memory level for scenario executions"""

    def __init__(self, config: MemoryLevelConfig, level_type: str):
        """
        Initialize scenario memory level

        Args:
            config: Level configuration
            level_type: Type of level (immediate, session, etc.)
        """
        super().__init__(config)
        self.level_type = level_type

    def encode(self, data: Any, context: Dict) -> np.ndarray:
        """
        Encode scenario execution

        Args:
            data: Execution data (dict)
            context: Additional context

        Returns:
            Execution embedding
        """
        self.stats.total_encodes += 1

        # Extract execution features
        if isinstance(data, dict):
            scenario_id = data.get("scenario_id", "unknown")
            success = data.get("success", False)
            duration = data.get("duration", 0.0)
            parameters = data.get("parameters", {})
        else:
            scenario_id = str(data)
            success = False
            duration = 0.0
            parameters = {}

        # Create feature string based on level
        if self.level_type == "immediate":
            # Recent execution details
            features = f"{scenario_id}:{success}:{duration:.2f}"
        elif self.level_type == "session":
            # Session patterns
            features = f"{scenario_id}:{success}:{json.dumps(parameters, sort_keys=True)}"
        elif self.level_type == "project":
            # Project-wide patterns
            features = f"{scenario_id}:{success}"
        elif self.level_type == "domain":
            # Domain knowledge
            features = scenario_id
        else:
            features = str(data)

        # Hash to embedding
        feature_hash = hashlib.sha256(features.encode()).digest()
        embedding = np.array(
            [float(b) / 255.0 for b in feature_hash[:128]], dtype="float32")

        return embedding


class ScenarioMemory(ContinuumMemorySystem):
    """
    Multi-scale memory for scenario automation

    4 levels:
    - immediate (L0): Last 10 executions
    - session (L1): Current session
    - project (L2): Project-specific patterns
    - domain (L3): General automation knowledge

    Example:
        >>> memory = ScenarioMemory()
        >>> memory.track_execution(
        ...     scenario_id="deploy_app",
        ...     success=True,
        ...     duration=120.5,
        ...     parameters={"env": "staging"}
        ... )
        >>> patterns = memory.analyze_success_patterns("deploy_app")
        >>> print(f"Success rate: {patterns['success_rate']:.1%}")
    """

    def __init__(self):
        """Initialize scenario memory"""
        levels = [
            ("immediate", 1, 0.01),  # Every execution
            ("session", 10, 0.001),  # Every 10 executions
            ("project", 100, 0.0001),  # Project patterns
            ("domain", int(1e9), 0.0),  # Static knowledge
        ]

        super().__init__(levels, embedding_dim=128)

        # Override with ScenarioMemoryLevel
        for name, level in self.levels.items():
            config = level.config

            # Mark domain as frozen
            if name == "domain":
                config.frozen = True

            self.levels[name] = ScenarioMemoryLevel(config, level_type=name)

        # Execution history
        self.execution_history: List[Dict] = []

        # Success patterns by scenario
        self.success_patterns: Dict[str, List[Dict]] = {}

        # Failure patterns
        self.failure_patterns: Dict[str, List[Dict]] = {}

        logger.info("Created ScenarioMemory with 4 levels")

    def track_execution(
        self,
        scenario_id: str,
        success: bool,
        duration: float,
        parameters: Dict,
        error: Optional[str] = None,
        context: Optional[Dict] = None,
    ):
        """
        Track scenario execution

        Args:
            scenario_id: Scenario identifier
            success: Whether execution succeeded
            duration: Execution duration (seconds)
            parameters: Execution parameters
            error: Error message if failed
            context: Optional context
        """
        context = context or {}

        execution = {
            "scenario_id": scenario_id,
            "success": success,
            "duration": duration,
            "parameters": parameters,
            "error": error,
            "timestamp": time.time(),
            **context,
        }

        # Store in history
        self.execution_history.append(execution)

        # Keep last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

        # Store in CMS
        exec_id = self._generate_execution_id(scenario_id, execution)
        self.store("immediate", exec_id, execution)

        # Update patterns
        if success:
            if scenario_id not in self.success_patterns:
                self.success_patterns[scenario_id] = []

            self.success_patterns[scenario_id].append(
                {"parameters": parameters, "duration": duration, "timestamp": time.time()}
            )

            # Keep last 100 successes per scenario
            if len(self.success_patterns[scenario_id]) > 100:
                self.success_patterns[scenario_id] = self.success_patterns[scenario_id][-100:]
        else:
            if scenario_id not in self.failure_patterns:
                self.failure_patterns[scenario_id] = []

            self.failure_patterns[scenario_id].append(
                {"parameters": parameters, "error": error, "timestamp": time.time()}
            )

            # Keep last 50 failures per scenario
            if len(self.failure_patterns[scenario_id]) > 50:
                self.failure_patterns[scenario_id] = self.failure_patterns[scenario_id][-50:]

        # Advance step
        self.step()

        logger.info("Tracked execution", extra={
                    "scenario_id": scenario_id, "success": success, "duration": duration})

    def analyze_success_patterns(self, scenario_id: str) -> Dict[str, Any]:
        """
        Analyze success patterns for scenario

        Args:
            scenario_id: Scenario to analyze

        Returns:
            Dict with success patterns and recommendations
        """
        # Get all executions for this scenario
        scenario_executions = [
            e for e in self.execution_history if e["scenario_id"] == scenario_id]

        if not scenario_executions:
            return {
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "recommended_parameters": {},
                "total_executions": 0,
                "successful_executions": 0,
            }

        # Calculate metrics
        total_executions = len(scenario_executions)
        successful = [e for e in scenario_executions if e["success"]]
        success_count = len(successful)
        success_rate = success_count / total_executions

        # Average duration for successful executions
        avg_duration = sum(e["duration"] for e in successful) / \
                           len(successful) if successful else 0.0

        # Find most common successful parameters
        recommended = self._find_common_parameters(successful)

        return {
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "recommended_parameters": recommended,
            "total_executions": total_executions,
            "successful_executions": success_count,
            "failed_executions": total_executions - success_count,
        }

    def suggest_modifications(self, scenario_id: str, current_parameters: Dict) -> Dict[str, Any]:
        """
        Suggest parameter modifications for better success

        Args:
            scenario_id: Scenario ID
            current_parameters: Current parameters

        Returns:
            Suggested modifications with reasoning
        """
        analysis = self.analyze_success_patterns(scenario_id)

        if analysis["total_executions"] == 0:
            return {
                "action": "keep",
                "suggested_parameters": current_parameters,
                "reason": "No execution history available",
                "confidence": 0.0,
            }

        success_rate = analysis["success_rate"]

        if success_rate < 0.3:
            # Very low success rate - major changes needed
            return {
                "action": "replace",
                "suggested_parameters": analysis["recommended_parameters"],
                "reason": f"Very low success rate ({success_rate:.1%})",
                "confidence": 0.8,
                "changes": self._compute_parameter_diff(current_parameters, analysis["recommended_parameters"]),
            }

        elif success_rate < 0.7:
            # Medium success rate - suggest improvements
            merged = self._merge_parameters(
                current_parameters, analysis["recommended_parameters"])
            return {
                "action": "modify",
                "suggested_parameters": merged,
                "reason": f"Medium success rate ({success_rate:.1%})",
                "confidence": 0.6,
                "changes": self._compute_parameter_diff(current_parameters, merged),
            }

        else:
            # High success rate - keep current
            return {
                "action": "keep",
                "suggested_parameters": current_parameters,
                "reason": f"Good success rate ({success_rate:.1%})",
                "confidence": 0.9,
                "changes": {},
            }

    def _find_common_parameters(self, executions: List[Dict]) -> Dict[str, Any]:
        """Find most common parameters in successful executions"""
        if not executions:
            return {}

        # Count parameter values
        param_counts: Dict[str, Dict[str, int]] = {}

        for execution in executions:
            for key, value in execution.get("parameters", {}).items():
                if key not in param_counts:
                    param_counts[key] = {}

                value_str = str(value)
                param_counts[key][value_str] = param_counts[key].get(value_str, 0) + 1

        # Find most common value for each parameter
        recommended = {}
        for key, value_counts in param_counts.items():
            if value_counts:
                # Get most common value
                most_common = max(value_counts.items(), key=lambda x: x[1])
                value_str, count = most_common

                # Use if appears in >50% of executions
                if count / len(executions) > 0.5:
                    # Try to convert back to original type
                    try:
                        recommended[key] = json.loads(value_str)
                    except:
                        recommended[key] = value_str

        return recommended

    def _merge_parameters(self, current: Dict, recommended: Dict) -> Dict:
        """Merge current and recommended parameters"""
        merged = current.copy()

        # Add recommended parameters that aren't in current
        for key, value in recommended.items():
            if key not in merged:
                merged[key] = value

        return merged

    def _compute_parameter_diff(self, old: Dict, new: Dict) -> Dict[str, Tuple[Any, Any]]:
        """Compute differences between parameter sets"""
        changes = {}

        # Find changed values
        for key in set(old.keys()) | set(new.keys()):
            old_val = old.get(key)
            new_val = new.get(key)

            if old_val != new_val:
                changes[key] = (old_val, new_val)

        return changes

    def _generate_execution_id(self, scenario_id: str, execution: Dict) -> str:
        """Generate unique execution ID"""
        timestamp = str(execution.get("timestamp", time.time()))
        combined = f"{scenario_id}:{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get_execution_history(self, scenario_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get execution history

        Args:
            scenario_id: Optional scenario filter
            limit: Maximum results

        Returns:
            List of executions
        """
        if scenario_id:
            history = [e for e in self.execution_history if e["scenario_id"] == scenario_id]
        else:
            history = self.execution_history

        return history[-limit:]

    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "levels": len(self.levels),
            "total_executions": len(self.execution_history),
            "scenarios_tracked": len(set(e["scenario_id"] for e in self.execution_history)),
            "success_patterns": len(self.success_patterns),
            "failure_patterns": len(self.failure_patterns),
        }
