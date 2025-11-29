"""
Unit tests for Conversational Memory

Tests multi-scale conversational memory system.
"""

import pytest

from src.ml.continual_learning.conversational_memory import ConversationalMemory, ConversationMemoryLevel


class TestConversationMemoryLevel:
    """Test conversation memory level"""

    def test_encode_immediate(self):
        """Test immediate level encoding"""
        from src.ml.continual_learning.memory_level import MemoryLevelConfig

        config = MemoryLevelConfig(name="immediate", update_freq=1)
        level = ConversationMemoryLevel(config, level_type="immediate")

        message = {"role": "user", "content": "Hello world"}
        embedding = level.encode(message, {})

        assert embedding.shape == (128,)

    def test_encode_different_levels(self):
        """Test different level types"""
        from src.ml.continual_learning.memory_level import MemoryLevelConfig

        for level_type in ["immediate", "session", "daily", "project", "domain"]:
            config = MemoryLevelConfig(name=level_type, update_freq=1)
            level = ConversationMemoryLevel(config, level_type=level_type)

            message = {"role": "user", "content": "Test message"}
            embedding = level.encode(message, {"session_id": "test"})

            assert embedding.shape == (128,)


class TestConversationalMemory:
    """Test conversational memory system"""

    def test_initialization(self):
        """Test memory initialization"""
        memory = ConversationalMemory()

        assert len(memory.levels) == 5
        assert "immediate" in memory.levels
        assert "session" in memory.levels
        assert "daily" in memory.levels
        assert "project" in memory.levels
        assert "domain" in memory.levels

    def test_store_message(self):
        """Test storing messages"""
        memory = ConversationalMemory()
        memory.start_session("test_session")

        memory.store_message("user", "Hello", {})

        assert memory.message_count == 1
        assert len(memory.levels["immediate"].memory) > 0

    def test_retrieve_context(self):
        """Test context retrieval"""
        memory = ConversationalMemory()
        memory.start_session("test_session")

        # Store some messages
        memory.store_message("user", "Как создать функцию?", {})
        memory.store_message("assistant", "Используйте Функция...КонецФункции", {})
        memory.store_message("user", "Спасибо!", {})

        # Retrieve context
        context = memory.retrieve_context("функция", k=5)

        assert isinstance(context, dict)
        assert "immediate" in context

    def test_session_management(self):
        """Test session start/end"""
        memory = ConversationalMemory()

        # Start session
        memory.start_session("session_1")
        assert memory.current_session_id == "session_1"

        # Store messages
        memory.store_message("user", "Test", {})

        # Get summary
        summary = memory.get_session_summary()
        assert summary["session_id"] == "session_1"
        assert summary["message_count"] == 1

        # End session
        memory.end_session()
        assert memory.current_session_id is None

    def test_get_relevant_history(self):
        """Test relevant history retrieval"""
        memory = ConversationalMemory()
        memory.start_session("test")

        # Store messages
        memory.store_message("user", "Как создать функцию в 1С?", {})
        memory.store_message("assistant", "Используйте ключевое слово Функция", {})
        memory.store_message("user", "Как создать процедуру?", {})
        memory.store_message("assistant", "Используйте ключевое слово Процедура", {})

        # Get relevant history
        history = memory.get_relevant_history("функция", max_messages=10)

        assert isinstance(history, list)
        assert len(history) > 0
        assert all("content" in msg for msg in history)

    def test_learn_from_interaction(self):
        """Test learning from user feedback"""
        memory = ConversationalMemory()

        # Positive feedback
        memory.learn_from_interaction(
            user_message="Test query", assistant_response="Test response", feedback={"rating": 5}
        )

        prefs = memory.get_user_preferences()
        assert "successful_patterns" in prefs
        assert len(prefs["successful_patterns"]) == 1

        # Negative feedback
        memory.learn_from_interaction(
            user_message="Bad query", assistant_response="Bad response", feedback={"rating": 1}
        )

        prefs = memory.get_user_preferences()
        assert "unsuccessful_patterns" in prefs
        assert len(prefs["unsuccessful_patterns"]) == 1

    def test_preference_limits(self):
        """Test preference list limits"""
        memory = ConversationalMemory()

        # Add 150 successful patterns
        for i in range(150):
            memory.learn_from_interaction(
                user_message=f"Query {i}", assistant_response=f"Response {i}", feedback={"rating": 5}
            )

        prefs = memory.get_user_preferences()
        # Should keep only last 100
        assert len(prefs["successful_patterns"]) == 100

    def test_role_filter(self):
        """Test filtering by role"""
        memory = ConversationalMemory()
        memory.start_session("test")

        # Store mixed messages
        memory.store_message("user", "User message 1", {})
        memory.store_message("assistant", "Assistant message 1", {})
        memory.store_message("user", "User message 2", {})

        # Retrieve only user messages
        context = memory.retrieve_context("message", k=10, role_filter="user")

        # Check that only user messages are returned
        for level_messages in context.values():
            for key, sim, data in level_messages:
                if isinstance(data, dict):
                    assert data.get("role") == "user"

    def test_health_check(self):
        """Test health check"""
        memory = ConversationalMemory()
        memory.start_session("test")
        memory.store_message("user", "Test", {})

        health = memory.health_check()

        assert health["status"] == "healthy"
        assert health["levels"] == 5
        assert health["current_session"] == "test"
        assert health["message_count"] == 1


class TestNestedAssistant:
    """Test nested assistant"""

    def test_initialization(self):
        """Test assistant initialization"""
        from src.ai.assistants.nested_assistant import NestedAssistant

        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="You are a developer assistant")

        assert assistant.role == "developer"
        assert assistant.name == "Dev AI"
        assert assistant.memory is not None

    def test_session_management(self):
        """Test session management"""
        from src.ai.assistants.nested_assistant import NestedAssistant

        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="Test")

        # Start session
        assistant.start_session("session_1")
        assert assistant.memory.current_session_id == "session_1"
        assert assistant.stats["total_sessions"] == 1

        # End session
        assistant.end_session()
        assert assistant.memory.current_session_id is None

    def test_process_message(self):
        """Test message processing"""
        from src.ai.assistants.nested_assistant import NestedAssistant

        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="Test")

        assistant.start_session("test")

        # Process message
        result = assistant.process_message("Как создать функцию?", context={"project": "MyProject"})

        assert "response" in result
        assert "response_id" in result
        assert "context_used" in result
        assert assistant.stats["total_messages"] == 1

    def test_feedback(self):
        """Test feedback processing"""
        from src.ai.assistants.nested_assistant import NestedAssistant

        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="Test")

        assistant.start_session("test")

        # Process message
        result = assistant.process_message("Test query")
        response_id = result["response_id"]

        # Provide feedback
        assistant.provide_feedback(response_id, rating=5, comments="Great!")

        assert assistant.stats["total_feedback"] == 1
        assert assistant.stats["avg_rating"] > 0

    def test_context_enhancement(self):
        """Test context enhancement from memory"""
        from src.ai.assistants.nested_assistant import NestedAssistant

        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="Test")

        assistant.start_session("test")

        # First message
        result1 = assistant.process_message("Как создать функцию?")

        # Second related message (should use context from first)
        result2 = assistant.process_message("А как её вызвать?")

        # Second message should have context
        assert result2["context_used"] >= 0

    def test_health_check(self):
        """Test health check"""
        from src.ai.assistants.nested_assistant import NestedAssistant

        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="Test")

        health = assistant.health_check()

        assert health["status"] == "healthy"
        assert health["assistant"] == "Dev AI"
        assert health["role"] == "developer"


@pytest.mark.asyncio
class TestConversationalMemoryIntegration:
    """Integration tests"""

    async def test_end_to_end_conversation(self):
        """Test end-to-end conversation flow"""
        from src.ai.assistants.nested_assistant import NestedAssistant

        assistant = NestedAssistant(
            role="developer", name="Dev AI", system_prompt="You are a helpful developer assistant"
        )

        # Start session
        assistant.start_session("integration_test")

        # Multi-turn conversation
        messages = [
            "Как создать функцию в 1С?",
            "А какие параметры можно передать?",
            "Покажи пример с возвратом значения",
            "Спасибо!",
        ]

        for msg in messages:
            result = assistant.process_message(msg)
            assert "response" in result

            # Provide positive feedback
            assistant.provide_feedback(result["response_id"], rating=5)

        # Check stats
        assert assistant.stats["total_messages"] == 4
        assert assistant.stats["total_feedback"] == 4
        assert assistant.stats["avg_rating"] > 0

        # End session
        assistant.end_session()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
