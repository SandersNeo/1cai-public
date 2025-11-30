"""
Conversational Memory

Multi-scale memory system for AI assistants.
Implements 5-level continuum memory for conversations.
"""

import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.modules.nested_learning.services.cms import ContinuumMemorySystem
from src.modules.nested_learning.services.memory_level import MemoryLevel, MemoryLevelConfig
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ConversationMemoryLevel(MemoryLevel):
    """Memory level for conversation messages"""

    def __init__(self, config: MemoryLevelConfig, level_type: str):
        """
        Initialize conversation memory level

        Args:
            config: Level configuration
            level_type: Type of level (immediate, session, etc.)
        """
        super().__init__(config)
        self.level_type = level_type

    def encode(self, data: Any, context: Dict) -> np.ndarray:
        """
        Encode conversation message

        Args:
            data: Message data (dict or string)
            context: Additional context

        Returns:
            Message embedding
        """
        self.stats.total_encodes += 1

        # Extract message content
        if isinstance(data, dict):
            content = data.get("content", str(data))
            data.get("role", "unknown")
        elif isinstance(data, str):
            content = data
        else:
            content = str(data)

        # Extract features based on level type
        if self.level_type == "immediate":
            # Last few words for immediate context
            features = self._extract_immediate_features(content)
        elif self.level_type == "session":
            # Key topics for session
            features = self._extract_session_features(content, context)
        elif self.level_type == "daily":
            # Daily themes
            features = self._extract_daily_features(content, context)
        elif self.level_type == "project":
            # Project-specific patterns
            features = self._extract_project_features(content, context)
        elif self.level_type == "domain":
            # Domain knowledge (1C, BSL, etc.)
            features = self._extract_domain_features(content)
        else:
            features = content

        # Hash to embedding
        feature_hash = hashlib.sha256(features.encode()).digest()
        embedding = np.array(
            [float(b) / 255.0 for b in feature_hash[:128]], dtype="float32")

        return embedding

    def _extract_immediate_features(self, content: str) -> str:
        """Extract immediate context features"""
        # Last 50 characters
        return content[-50:] if len(content) > 50 else content

    def _extract_session_features(self, content: str, context: Dict) -> str:
        """Extract session-level features"""
        # Combine content with session context
        session_id = context.get("session_id", "unknown")
        return f"{session_id}:{content[:100]}"

    def _extract_daily_features(self, content: str, context: Dict) -> str:
        """Extract daily features"""
        # Date + content summary
        import datetime

        date = datetime.datetime.now().strftime("%Y-%m-%d")
        return f"{date}:{content[:100]}"

    def _extract_project_features(self, content: str, context: Dict) -> str:
        """Extract project-specific features"""
        project = context.get("project", "unknown")
        return f"{project}:{content[:100]}"

    def _extract_domain_features(self, content: str) -> str:
        """Extract domain knowledge features"""
        # Extract 1C/BSL keywords
        keywords = [
            "Функция",
            "Процедура",
            "КонецФункции",
            "КонецПроцедуры",
            "Если",
            "Тогда",
            "КонецЕсли",
            "Для",
            "КонецЦикла",
            "Запрос",
            "Выборка",
            "Новый",
            "Возврат",
        ]

        found = [kw for kw in keywords if kw in content]
        return " ".join(found) if found else content[:50]


class ConversationalMemory(ContinuumMemorySystem):
    """
    Multi-scale conversational memory for AI assistants

    5 levels:
    - immediate (L0): Last 5 messages
    - session (L1): Current conversation
    - daily (L2): Today's conversations
    - project (L3): Project-specific context
    - domain (L4): Domain knowledge (1C, BSL, etc.)

    Example:
        >>> memory = ConversationalMemory()
        >>> memory.store_message("user", "Как создать функцию?", context={})
        >>> context = memory.retrieve_context(query="функция", k=5)
        >>> print(f"Found {len(context)} relevant messages")
    """

    def __init__(self):
        """Initialize conversational memory"""
        levels = [
            ("immediate", 1, 0.01),  # Every message
            ("session", 10, 0.001),  # Every 10 messages
            ("daily", 100, 0.0001),  # Every 100 messages
            ("project", 1000, 0.00001),  # Project patterns
            ("domain", int(1e9), 0.0),  # Static domain knowledge
        ]

        super().__init__(levels, embedding_dim=128)

        # Override with ConversationMemoryLevel
        for name, level in self.levels.items():
            config = level.config

            # Mark domain as frozen
            if name == "domain":
                config.frozen = True

            self.levels[name] = ConversationMemoryLevel(config, level_type=name)

        # Conversation state
        self.current_session_id: Optional[str] = None
        self.message_count = 0

        # User preferences
        self.user_preferences: Dict[str, Any] = {}

        logger.info("Created ConversationalMemory with 5 levels")

    def store_message(self, role: str, content: str, context: Optional[Dict] = None):
        """
        Store conversation message

        Args:
            role: "user" | "assistant" | "system"
            content: Message content
            context: Optional context (project, topic, etc.)
        """
        context = context or {}
        self.message_count += 1

        # Generate message ID
        msg_id = self._generate_message_id(role, content)

        # Prepare message data
        message_data = {
            "role": role,
            "content": content,
            "session_id": self.current_session_id,
            "timestamp": time.time(),
            **context,
        }

        # Store in appropriate levels
        self.store("immediate", msg_id, message_data)

        # Store in session level every 10 messages
        if self.message_count % 10 == 0:
            self.store("session", msg_id, message_data)

        # Store in daily level every 100 messages
        if self.message_count % 100 == 0:
            self.store("daily", msg_id, message_data)

        # Advance step
        self.step()

        logger.debug(
            "Stored message",
            extra={"role": role, "session_id": self.current_session_id,
                "message_count": self.message_count},
        )

    def retrieve_context(
        self, query: str, k: int = 5, levels: Optional[List[str]] = None, role_filter: Optional[str] = None
    ) -> Dict[str, List[Tuple[str, float, Dict]]]:
        """
        Retrieve relevant context for query

        Args:
            query: Query string
            k: Number of results per level
            levels: Levels to search (default: all except domain)
            role_filter: Filter by role (user/assistant/system)

        Returns:
            Dict mapping level -> [(key, similarity, message_data)]
        """
        if levels is None:
            levels = ["immediate", "session", "daily", "project"]

        # Retrieve from multiple levels
        results = self.retrieve_similar({"content": query}, levels=levels, k=k)

        # Filter by role if specified
        if role_filter:
            filtered = {}
            for level_name, messages in results.items():
                filtered[level_name] = [
                    (key, sim, data)
                    for key, sim, data in messages
                    if isinstance(data, dict) and data.get("role") == role_filter
                ]
            results = filtered

        return results

    def get_relevant_history(self, query: str, max_messages: int = 10) -> List[Dict]:
        """
        Get relevant conversation history

        Args:
            query: Query to find relevant messages
            max_messages: Maximum messages to return

        Returns:
            List of relevant messages sorted by relevance
        """
        # Retrieve from all levels
        results = self.retrieve_context(query, k=5)

        # Flatten and sort by similarity
        all_messages = []
        for level_name, messages in results.items():
            for key, similarity, data in messages:
                if isinstance(data, dict):
                    all_messages.append(
                        {"similarity": similarity, "level": level_name, **data})

        # Sort by similarity
        all_messages.sort(key=lambda x: x["similarity"], reverse=True)

        return all_messages[:max_messages]

    def learn_from_interaction(self, user_message: str, assistant_response: str, feedback: Optional[Dict] = None):
        """
        Learn from user interaction

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            feedback: Optional feedback (rating, corrections, etc.)
        """
        feedback = feedback or {}

        # Update user preferences based on feedback
        if "rating" in feedback:
            rating = feedback["rating"]

            # Track preferences
            if rating >= 4:  # Positive feedback
                self._update_preferences(
                    user_message, assistant_response, positive=True)
            elif rating <= 2:  # Negative feedback
                self._update_preferences(
                    user_message, assistant_response, positive=False)

        # Store interaction
        interaction_id = self._generate_message_id("interaction", user_message)
        interaction_data = {
            "user_message": user_message,
            "assistant_response": assistant_response,
            "feedback": feedback,
            "timestamp": time.time(),
        }

        # Store in project level for long-term learning
        self.store("project", interaction_id, interaction_data)

    def _update_preferences(self, user_message: str, assistant_response: str, positive: bool):
        """Update user preferences based on feedback"""
        # Extract patterns from positive/negative interactions
        if positive:
            # Track successful patterns
            if "successful_patterns" not in self.user_preferences:
                self.user_preferences["successful_patterns"] = []

            self.user_preferences["successful_patterns"].append(
                {
                    "query_pattern": user_message[:50],
                    "response_pattern": assistant_response[:50],
                    "timestamp": time.time(),
                }
            )

            # Keep last 100
            if len(self.user_preferences["successful_patterns"]) > 100:
                self.user_preferences["successful_patterns"] = self.user_preferences["successful_patterns"][-100:]
        else:
            # Track unsuccessful patterns to avoid
            if "unsuccessful_patterns" not in self.user_preferences:
                self.user_preferences["unsuccessful_patterns"] = []

            self.user_preferences["unsuccessful_patterns"].append(
                {
                    "query_pattern": user_message[:50],
                    "response_pattern": assistant_response[:50],
                    "timestamp": time.time(),
                }
            )

            # Keep last 50
            if len(self.user_preferences["unsuccessful_patterns"]) > 50:
                self.user_preferences["unsuccessful_patterns"] = self.user_preferences["unsuccessful_patterns"][-50:]

    def start_session(self, session_id: str):
        """
        Start new conversation session

        Args:
            session_id: Unique session identifier
        """
        self.current_session_id = session_id
        self.message_count = 0

        logger.info("Started conversation session: %s", session_id)

    def end_session(self):
        """End current session"""
        if self.current_session_id:
            logger.info(f"Ended conversation session: {self.current_session_id}")
            self.current_session_id = None

    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary"""
        if not self.current_session_id:
            return {"error": "No active session"}

        # Get session messages
        session_messages = []
        for key, data in self.levels["session"].memory.items():
            if isinstance(data, dict) and data.get("session_id") == self.current_session_id:
                session_messages.append(data)

        return {
            "session_id": self.current_session_id,
            "message_count": self.message_count,
            "total_messages": len(session_messages),
            "duration": time.time()
            - min((m.get("timestamp", time.time())
                  for m in session_messages), default=time.time())
            if session_messages
            else 0,
        }

    def _generate_message_id(self, role: str, content: str) -> str:
        """Generate unique message ID"""
        timestamp = str(time.time())
        combined = f"{role}:{content}:{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences"""
        return self.user_preferences.copy()

    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "levels": len(self.levels),
            "current_session": self.current_session_id,
            "message_count": self.message_count,
            "preferences_count": len(self.user_preferences),
        }
