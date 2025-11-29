"""
Unit tests for Continuum Memory System
"""

import pytest
import numpy as np

from src.ml.continual_learning.cms import ContinuumMemorySystem
from src.ml.continual_learning.memory_level import MemoryLevel, MemoryLevelConfig


class TestMemoryLevelConfig:
    """Test MemoryLevelConfig validation"""

    def test_valid_config(self):
        """Test valid configuration"""
        config = MemoryLevelConfig(name="test", update_freq=10, learning_rate=0.001, threshold=0.5, capacity=1000)
        assert config.name == "test"
        assert config.update_freq == 10
        assert config.learning_rate == 0.001

    def test_invalid_update_freq(self):
        """Test invalid update frequency"""
        with pytest.raises(ValueError):
            MemoryLevelConfig(name="test", update_freq=0, learning_rate=0.001)  # Invalid

    def test_invalid_learning_rate(self):
        """Test invalid learning rate"""
        with pytest.raises(ValueError):
            MemoryLevelConfig(name="test", update_freq=1, learning_rate=1.5)  # Invalid (>1.0)


class TestMemoryLevel:
    """Test MemoryLevel functionality"""

    @pytest.fixture
    def level(self):
        """Create test memory level"""
        config = MemoryLevelConfig(name="test", update_freq=1, learning_rate=0.001, threshold=0.5, capacity=100)
        return MemoryLevel(config)

    def test_creation(self, level):
        """Test level creation"""
        assert level.config.name == "test"
        assert level.step_count == 0
        assert len(level) == 0

    def test_encode(self, level):
        """Test encoding"""
        embedding = level.encode("test data", {})
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)  # Default dimension

    def test_should_update_frozen(self):
        """Test that frozen levels never update"""
        config = MemoryLevelConfig(name="frozen", update_freq=1, learning_rate=0.0, frozen=True)
        level = MemoryLevel(config)

        assert not level.should_update(surprise=1.0)

    def test_should_update_frequency(self, level):
        """Test update frequency check"""
        # Step 0: should update (0 % 1 == 0)
        assert level.should_update(surprise=0.8)

        # Advance step
        level.step()

        # Step 1: should update (1 % 1 == 0)
        assert level.should_update(surprise=0.8)

    def test_should_update_threshold(self, level):
        """Test surprise threshold check"""
        # Low surprise - should not update
        assert not level.should_update(surprise=0.3)

        # High surprise - should update
        assert level.should_update(surprise=0.8)

    def test_update(self, level):
        """Test memory update"""
        # Update with high surprise
        level.update("key1", "data1", surprise=0.8)

        # Check stored
        assert "key1" in level.memory
        assert "key1" in level.metadata
        assert level.update_count == 1

    def test_get(self, level):
        """Test retrieval"""
        # Store
        level.update("key1", "data1", surprise=0.8)

        # Retrieve
        embedding = level.get("key1")
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)

    def test_capacity_eviction(self):
        """Test that old entries are evicted when capacity exceeded"""
        config = MemoryLevelConfig(name="test", update_freq=1, learning_rate=0.001, capacity=3)  # Small capacity
        level = MemoryLevel(config)

        # Add 4 items (exceeds capacity)
        for i in range(4):
            level.update(f"key{i}", f"data{i}", surprise=0.8)
            level.step()

        # Should have only 3 items
        assert len(level) == 3

        # First item should be evicted
        assert "key0" not in level.memory


class TestContinuumMemorySystem:
    """Test CMS functionality"""

    @pytest.fixture
    def cms(self):
        """Create test CMS"""
        return ContinuumMemorySystem([("fast", 1, 0.001), ("medium", 10, 0.0001), ("slow", 100, 0.00001)])

    def test_creation(self, cms):
        """Test CMS creation"""
        assert len(cms.levels) == 3
        assert "fast" in cms.levels
        assert "medium" in cms.levels
        assert "slow" in cms.levels
        assert cms.global_step == 0

    def test_store(self, cms):
        """Test storing data"""
        embedding = np.random.rand(768).astype("float32")
        cms.store("fast", "key1", "data1", embedding)

        # Check stored in level
        assert "key1" in cms.levels["fast"].memory

        # Check added to index
        assert cms.index.size() == 1

    def test_retrieve(self, cms):
        """Test retrieving similar items"""
        # Store some data
        for i in range(5):
            embedding = np.random.rand(768).astype("float32")
            cms.store("fast", f"key{i}", f"data{i}", embedding)

        # Retrieve similar
        results = cms.retrieve("data0", "fast", k=3)

        assert len(results) <= 3
        assert all(len(r) == 3 for r in results)  # (key, sim, data)

    def test_retrieve_similar_multi_level(self, cms):
        """Test retrieving from multiple levels"""
        # Store in different levels
        for level_name in ["fast", "medium"]:
            for i in range(3):
                embedding = np.random.rand(768).astype("float32")
                cms.store(level_name, f"{level_name}_key{i}", f"data{i}", embedding)

        # Retrieve from multiple levels
        results = cms.retrieve_similar("data0", ["fast", "medium"], k=2)

        assert "fast" in results
        assert "medium" in results
        assert len(results["fast"]) <= 2
        assert len(results["medium"]) <= 2

    def test_update_level(self, cms):
        """Test updating specific level"""
        # Store initial data
        cms.store("fast", "key1", "data1")

        # Update with high surprise
        cms.update_level("fast", "key1", "new_data", surprise=0.9)

        # Check update count increased
        assert cms.levels["fast"].update_count > 0

    def test_encode_multi_level(self, cms):
        """Test multi-level encoding"""
        embedding = cms.encode_multi_level("test data", {})

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)

    def test_encode_multi_level_with_weights(self, cms):
        """Test multi-level encoding with custom weights"""
        weights = {"fast": 0.5, "medium": 0.3, "slow": 0.2}

        embedding = cms.encode_multi_level("test data", {}, weights=weights)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)

    def test_step(self, cms):
        """Test step counter advancement"""
        assert cms.global_step == 0

        cms.step()
        assert cms.global_step == 1

        # All levels should also step
        for level in cms.levels.values():
            assert level.step_count == 1

    def test_get_stats(self, cms):
        """Test statistics retrieval"""
        # Store some data
        cms.store("fast", "key1", "data1")
        cms.step()

        stats = cms.get_stats()

        assert stats.global_step == 1
        assert stats.total_levels == 3
        assert stats.total_memory_size >= 1
        assert "fast" in stats.levels

    def test_clear(self, cms):
        """Test clearing CMS"""
        # Store data
        cms.store("fast", "key1", "data1")
        cms.step()

        # Clear
        cms.clear()

        # Check cleared
        assert cms.global_step == 0
        assert all(len(level) == 0 for level in cms.levels.values())
        assert cms.index.size() == 0


class TestSurpriseBasedUpdates:
    """Test surprise-based selective updates"""

    def test_high_surprise_updates_all_levels(self):
        """Test that high surprise updates multiple levels"""
        cms = ContinuumMemorySystem([("fast", 1, 0.001), ("slow", 1, 0.0001)])  # Same freq for testing

        # Both levels have threshold 0.5
        cms.levels["fast"].config.threshold = 0.5
        cms.levels["slow"].config.threshold = 0.5

        # High surprise - should update both
        cms.update_level("fast", "key1", "data1", surprise=0.9)
        cms.update_level("slow", "key1", "data1", surprise=0.9)

        assert cms.levels["fast"].update_count == 1
        assert cms.levels["slow"].update_count == 1

    def test_low_surprise_no_updates(self):
        """Test that low surprise doesn't update"""
        cms = ContinuumMemorySystem([("test", 1, 0.001)])
        cms.levels["test"].config.threshold = 0.5

        # Low surprise - should not update
        cms.update_level("test", "key1", "data1", surprise=0.3)

        assert cms.levels["test"].update_count == 0

    def test_medium_surprise_selective_update(self):
        """Test that medium surprise updates only some levels"""
        cms = ContinuumMemorySystem([("sensitive", 1, 0.001), ("robust", 1, 0.001)])  # Low threshold  # High threshold

        cms.levels["sensitive"].config.threshold = 0.3
        cms.levels["robust"].config.threshold = 0.7

        # Medium surprise (0.5)
        cms.update_level("sensitive", "key1", "data1", surprise=0.5)
        cms.update_level("robust", "key1", "data1", surprise=0.5)

        # Sensitive should update, robust should not
        assert cms.levels["sensitive"].update_count == 1
        assert cms.levels["robust"].update_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
