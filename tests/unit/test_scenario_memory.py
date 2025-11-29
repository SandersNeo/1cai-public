"""
Unit tests for Scenario Memory

Tests scenario memory and self-modification.
"""

import pytest

from src.ml.continual_learning.scenario_memory import ScenarioMemory, ScenarioMemoryLevel


class TestScenarioMemoryLevel:
    """Test scenario memory level"""

    def test_encode_immediate(self):
        """Test immediate level encoding"""
        from src.ml.continual_learning.memory_level import MemoryLevelConfig

        config = MemoryLevelConfig(name="immediate", update_freq=1)
        level = ScenarioMemoryLevel(config, level_type="immediate")

        execution = {"scenario_id": "test_scenario", "success": True, "duration": 10.5, "parameters": {"env": "test"}}

        embedding = level.encode(execution, {})

        assert embedding.shape == (128,)


class TestScenarioMemory:
    """Test scenario memory system"""

    def test_initialization(self):
        """Test memory initialization"""
        memory = ScenarioMemory()

        assert len(memory.levels) == 4
        assert "immediate" in memory.levels
        assert "session" in memory.levels
        assert "project" in memory.levels
        assert "domain" in memory.levels

    def test_track_execution(self):
        """Test tracking executions"""
        memory = ScenarioMemory()

        memory.track_execution(scenario_id="test_scenario", success=True, duration=10.5, parameters={"env": "staging"})

        assert len(memory.execution_history) == 1
        assert len(memory.success_patterns["test_scenario"]) == 1

    def test_analyze_success_patterns(self):
        """Test success pattern analysis"""
        memory = ScenarioMemory()

        # Track multiple executions
        for i in range(10):
            memory.track_execution(
                scenario_id="test_scenario",
                success=i % 2 == 0,  # 50% success rate
                duration=10.0 + i,
                parameters={"env": "staging", "version": i},
            )

        analysis = memory.analyze_success_patterns("test_scenario")

        assert analysis["total_executions"] == 10
        assert analysis["successful_executions"] == 5
        assert analysis["success_rate"] == 0.5
        assert analysis["avg_duration"] > 0

    def test_suggest_modifications_low_success(self):
        """Test suggestions for low success rate"""
        memory = ScenarioMemory()

        # Track mostly failures
        for i in range(10):
            memory.track_execution(
                scenario_id="failing_scenario",
                success=i < 2,  # 20% success rate
                duration=10.0,
                parameters={"env": "staging" if i < 2 else "production"},
            )

        suggestions = memory.suggest_modifications("failing_scenario", {"env": "production"})

        assert suggestions["action"] == "replace"
        assert suggestions["confidence"] > 0.5

    def test_suggest_modifications_high_success(self):
        """Test suggestions for high success rate"""
        memory = ScenarioMemory()

        # Track mostly successes
        for i in range(10):
            memory.track_execution(
                scenario_id="good_scenario",
                success=i < 8,  # 80% success rate
                duration=10.0,
                parameters={"env": "staging"},
            )

        suggestions = memory.suggest_modifications("good_scenario", {"env": "staging"})

        assert suggestions["action"] == "keep"
        assert suggestions["confidence"] > 0.5

    def test_get_execution_history(self):
        """Test execution history retrieval"""
        memory = ScenarioMemory()

        # Track executions
        memory.track_execution("scenario1", True, 10.0, {})
        memory.track_execution("scenario2", True, 15.0, {})
        memory.track_execution("scenario1", False, 20.0, {})

        # Get all history
        all_history = memory.get_execution_history()
        assert len(all_history) == 3

        # Get scenario-specific history
        scenario1_history = memory.get_execution_history(scenario_id="scenario1")
        assert len(scenario1_history) == 2

    def test_health_check(self):
        """Test health check"""
        memory = ScenarioMemory()

        memory.track_execution("test", True, 10.0, {})

        health = memory.health_check()

        assert health["status"] == "healthy"
        assert health["total_executions"] == 1
        assert health["scenarios_tracked"] == 1


class TestNestedScenarioHub:
    """Test nested scenario hub"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test hub initialization"""
        from src.modules.scenario_hub.nested_scenario_hub import NestedScenarioHub

        hub = NestedScenarioHub()

        assert hub.memory is not None
        assert len(hub.scenarios) == 0

    @pytest.mark.asyncio
    async def test_register_scenario(self):
        """Test scenario registration"""
        from src.modules.scenario_hub.nested_scenario_hub import NestedScenarioHub

        hub = NestedScenarioHub()

        async def test_executor(**kwargs):
            return {"status": "success"}

        hub.register_scenario(scenario_id="test_scenario", executor=test_executor, default_parameters={"env": "test"})

        assert "test_scenario" in hub.scenarios

    @pytest.mark.asyncio
    async def test_execute_scenario(self):
        """Test scenario execution"""
        from src.modules.scenario_hub.nested_scenario_hub import NestedScenarioHub

        hub = NestedScenarioHub()

        async def test_executor(**kwargs):
            return {"status": "success", "env": kwargs.get("env")}

        hub.register_scenario(scenario_id="test_scenario", executor=test_executor, default_parameters={"env": "test"})

        result = await hub.execute_scenario(scenario_id="test_scenario", auto_optimize=False)

        assert result["success"] is True
        assert result["result"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_auto_optimization(self):
        """Test auto-optimization"""
        from src.modules.scenario_hub.nested_scenario_hub import NestedScenarioHub

        hub = NestedScenarioHub()

        async def test_executor(**kwargs):
            # Succeed only with env=staging
            if kwargs.get("env") == "staging":
                return {"status": "success"}
            else:
                raise Exception("Wrong environment")

        hub.register_scenario(
            scenario_id="test_scenario", executor=test_executor, default_parameters={"env": "production"}
        )

        # Execute multiple times to build pattern
        for _ in range(5):
            await hub.execute_scenario("test_scenario", parameters={"env": "staging"}, auto_optimize=False)

        # Now execute with auto-optimization
        result = await hub.execute_scenario("test_scenario", auto_optimize=True)

        # Should have optimized parameters
        assert result["auto_optimized"] is True

    @pytest.mark.asyncio
    async def test_get_scenario_analysis(self):
        """Test scenario analysis"""
        from src.modules.scenario_hub.nested_scenario_hub import NestedScenarioHub

        hub = NestedScenarioHub()

        async def test_executor(**kwargs):
            return {"status": "success"}

        hub.register_scenario("test_scenario", test_executor)

        # Execute a few times
        for _ in range(3):
            await hub.execute_scenario("test_scenario")

        # Get analysis
        analysis = hub.get_scenario_analysis("test_scenario")

        assert "success_rate" in analysis
        assert "suggestions" in analysis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
