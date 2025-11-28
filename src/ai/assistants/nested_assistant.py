"""
Nested Assistant

AI assistant with multi-scale conversational memory.
Integrates ConversationalMemory for long-term context retention.
"""

import time
from typing import Any, Dict, List, Optional

from src.ml.continual_learning.conversational_memory import ConversationalMemory
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class NestedAssistant:
    """
    AI assistant with Nested Learning memory

    Features:
    - Multi-scale conversational memory
    - Long-term context retention
    - User preference learning
    - Session management

    Example:
        >>> assistant = NestedAssistant(role="developer")
        >>> assistant.start_session("session_123")
        >>> response = assistant.process_message(
        ...     "Как создать функцию в 1С?",
        ...     context={"project": "MyProject"}
        ... )
        >>> assistant.provide_feedback(response_id, rating=5)
    """

    def __init__(self, role: str, name: str, system_prompt: str, base_assistant: Optional[Any] = None):
        """
        Initialize nested assistant

        Args:
            role: Assistant role (developer, architect, etc.)
            name: Assistant name
            system_prompt: System prompt
            base_assistant: Base assistant implementation (optional)
        """
        self.role = role
        self.name = name
        self.system_prompt = system_prompt
        self.base = base_assistant

        # Conversational memory
        self.memory = ConversationalMemory()

        # Response history for feedback
        self.response_history: Dict[str, Dict] = {}

        # Statistics
        self.stats = {"total_messages": 0, "total_sessions": 0,
            "total_feedback": 0, "avg_rating": 0.0}

        logger.info("Created NestedAssistant: %s ({role})", name)

    def start_session(self, session_id: str):
        """
        Start new conversation session

        Args:
            session_id: Unique session ID
        """
        self.memory.start_session(session_id)
        self.stats["total_sessions"] += 1

        logger.info("Started session %s for {self.name}", session_id)

    def end_session(self):
        """End current session"""
        summary = self.memory.get_session_summary()
        self.memory.end_session()

        logger.info(f"Ended session for {self.name}", extra={"summary": summary})

    def process_message(self, user_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process user message with memory-enhanced context

        Args:
            user_message: User's message
            context: Optional context

        Returns:
            Dict with response and metadata
        """
        context = context or {}
        self.stats["total_messages"] += 1

        # Store user message
        self.memory.store_message("user", user_message, context)

        # Retrieve relevant context from memory
        relevant_context = self.memory.get_relevant_history(
            user_message, max_messages=10)

        # Build enhanced prompt with context
        enhanced_prompt = self._build_enhanced_prompt(
            user_message, relevant_context, context)

        # Generate response (using base assistant if available)
        if self.base:
            response_text = self._generate_with_base(enhanced_prompt)
        else:
            response_text = self._generate_fallback(enhanced_prompt)

        # Store assistant response
        self.memory.store_message("assistant", response_text, context)

        # Generate response ID for feedback
        response_id = self._generate_response_id(user_message, response_text)

        # Store for feedback
        self.response_history[response_id] = {
            "user_message": user_message,
            "response": response_text,
            "context": context,
            "relevant_context": relevant_context,
            "timestamp": time.time(),
        }

        logger.debug("Processed message", extra={
                     "assistant": self.name, "context_messages": len(relevant_context)})

        return {
            "response": response_text,
            "response_id": response_id,
            "context_used": len(relevant_context),
            "session_id": self.memory.current_session_id,
        }

    def provide_feedback(self, response_id: str, rating: int, comments: Optional[str] = None):
        """
        Provide feedback on assistant response

        Args:
            response_id: Response identifier
            rating: Rating 1-5
            comments: Optional comments
        """
        if response_id not in self.response_history:
            logger.warning("Unknown response_id: %s", response_id)
            return

        self.stats["total_feedback"] += 1

        # Update average rating
        self.stats["avg_rating"] = self.stats["avg_rating"] * 0.9 + rating * 0.1

        # Get original interaction
        interaction = self.response_history[response_id]

        # Learn from feedback
        self.memory.learn_from_interaction(
            user_message=interaction["user_message"],
            assistant_response=interaction["response"],
            feedback={"rating": rating, "comments": comments, "timestamp": time.time()},
        )

        logger.info(
            "Received feedback",
            extra={"assistant": self.name, "rating": rating,
                "avg_rating": self.stats["avg_rating"]},
        )

    def _build_enhanced_prompt(self, user_message: str, relevant_context: List[Dict], context: Dict) -> str:
        """Build enhanced prompt with memory context"""
        # System prompt
        prompt_parts = [f"System: {self.system_prompt}\n"]

        # Add relevant context if available
        if relevant_context:
            prompt_parts.append("\nRelevant context from previous conversations:\n")
            for msg in relevant_context[:5]:  # Top 5
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content[:100]}...\n")

        # Add current context
        if context:
            prompt_parts.append(f"\nCurrent context: {context}\n")

        # Add user message
        prompt_parts.append(f"\nUser: {user_message}\n")
        prompt_parts.append("Assistant:")

        return "".join(prompt_parts)

    def _generate_with_base(self, prompt: str) -> str:
        """Generate response using base assistant"""
        try:
            # Call base assistant
            response = self.base.generate(prompt)
            return response
        except Exception as e:
            logger.error(f"Base assistant failed: {e}", exc_info=True)
            return self._generate_fallback(prompt)

    def _generate_fallback(self, prompt: str) -> str:
        """Fallback response generation"""
        # Simple fallback
        return f"[{self.name}] Обрабатываю ваш запрос с учётом контекста..."

    def _generate_response_id(self, user_message: str, response: str) -> str:
        """Generate unique response ID"""
        import hashlib

        combined = f"{user_message}:{response}:{time.time()}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """Get assistant statistics"""
        memory_stats = self.memory.get_stats()

        return {**self.stats, "memory": memory_stats.to_dict(), "preferences": self.memory.get_user_preferences()}

    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        memory_health = self.memory.health_check()

        return {
            "status": "healthy",
            "assistant": self.name,
            "role": self.role,
            "total_messages": self.stats["total_messages"],
            "avg_rating": self.stats["avg_rating"],
            "memory": memory_health,
        }
