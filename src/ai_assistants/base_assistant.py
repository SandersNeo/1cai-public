# [NEXUS IDENTITY] ID: -3123437763713397881 | DATE: 2025-11-19

"""
Базовый класс для всех AI-ассистентов в системе автоматизации 1С
Использует LangChain и OpenAI API для обработки запросов
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    from supabase import Client
except ImportError:
    Client = Any

from pydantic import BaseModel, Field


# Упрощенные классы для тестирования (без внешних зависимостей)
class Document:
    """Класс Document.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    def __init__(self, page_content: str, metadata: dict = None):
        """TODO: Описать функцию __init__.
        
        Args:
            page_content: TODO: Описать параметр.
            metadata: TODO: Описать параметр.
        """
        self.page_content = page_content
        self.metadata = metadata or {}


class HumanMessage:
    """Класс HumanMessage.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    def __init__(self, content: str):
        """TODO: Описать функцию __init__.
        
        Args:
            content: TODO: Описать параметр.
        """
        self.content = content


class AIMessage:
    """Класс AIMessage.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    def __init__(self, content: str):
        """TODO: Описать функцию __init__.
        
        Args:
            content: TODO: Описать параметр.
        """
        self.content = content


class ChatPromptTemplate:
    """Класс ChatPromptTemplate.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    def __init__(self, messages):
        """TODO: Описать функцию __init__.
        
        Args:
            messages: TODO: Описать параметр.
        """
        self.messages = messages

    @classmethod
    def from_messages(cls, messages):
        """TODO: Описать функцию from_messages.
        
        Args:
            messages: TODO: Описать параметр.
        """
        return cls(messages)

    def format_prompt(self, **kwargs):
        """TODO: Описать функцию format_prompt."""
        class MockPromptValue:
            """Класс MockPromptValue.
            
            TODO: Добавить описание класса.
            
            Attributes:
                TODO: Описать атрибуты класса.
            """
            def __init__(self, messages):
                """TODO: Описать функцию __init__.
                
                Args:
                    messages: TODO: Описать параметр.
                """
                self._messages = messages

            def to_messages(self):
                """TODO: Описать функцию to_messages."""
                return self._messages

        return MockPromptValue(self.messages)


class ConversationalRetrievalChain:
    """Класс ConversationalRetrievalChain.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    def __init__(self, **kwargs):
        """TODO: Описать функцию __init__."""

    @classmethod
    def from_llm(cls, llm, retriever, **kwargs):
        """TODO: Описать функцию from_llm.
        
        Args:
            llm: TODO: Описать параметр.
            retriever: TODO: Описать параметр.
        """
        return cls(llm=llm, retriever=retriever, **kwargs)

    async def ainvoke(self, inputs):
        """TODO: Описать функцию ainvoke.
        
        Args:
            inputs: TODO: Описать параметр.
        """
        return {"answer": "Test response", "source_documents": []}


class ChatOpenAI:
    """Класс ChatOpenAI.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    def __init__(self, **kwargs):
        """TODO: Описать функцию __init__."""

    async def ainvoke(self, messages):
        """TODO: Описать функцию ainvoke.
        
        Args:
            messages: TODO: Описать параметр.
        """
        return AIMessage("Test AI response")


class OpenAIEmbeddings:
    """Класс OpenAIEmbeddings.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    def __init__(self, **kwargs):
        """TODO: Описать функцию __init__."""


class SupabaseVectorStore:
    """Класс SupabaseVectorStore.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    def __init__(self, **kwargs):
        """TODO: Описать функцию __init__."""

    def as_retriever(self, **kwargs):
        """TODO: Описать функцию as_retriever."""
        return self

    async def aadd_documents(self, docs):
        """TODO: Описать функцию aadd_documents.
        
        Args:
            docs: TODO: Описать параметр.
        """


def create_client(*args, **kwargs):
    """TODO: Описать функцию create_client."""
    class MockSupabaseClient:
        """Класс MockSupabaseClient.
        
        TODO: Добавить описание класса.
        
        Attributes:
            TODO: Описать атрибуты класса.
        """
        def table(self, *args, **kwargs):
            """TODO: Описать функцию table."""
            return self

        def select(self, *args, **kwargs):
            """TODO: Описать функцию select."""
            return self

        def limit(self, *args, **kwargs):
            """TODO: Описать функцию limit."""
            return self

        def execute(self, *args, **kwargs):
            """TODO: Описать функцию execute."""
            return []

    return MockSupabaseClient()


class AssistantMessage(BaseModel):
    """Модель сообщения в диалоге с ассистентом"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str = Field(description="Роль отправителя: 'user' или 'assistant'")
    content: str = Field(description="Содержимое сообщения")
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Дополнительный контекст"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Метаданные сообщения"
    )


class AssistantResponse(BaseModel):
    """Модель ответа от ассистента"""

    message: AssistantMessage
    sources: List[Document] = Field(
        default_factory=list, description="Источники информации"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Уверенность в ответе")
    reasoning_steps: List[str] = Field(
        default_factory=list, description="Шаги рассуждений"
    )

    class Config:
        """Класс Config.
        
        TODO: Добавить описание класса.
        
        Attributes:
            TODO: Описать атрибуты класса.
        """
        arbitrary_types_allowed = True


class AssistantConfig(BaseModel):
    """Конфигурация ассистента"""

    role: str = Field(description="Роль ассистента")
    name: str = Field(description="Имя ассистента")
    description: str = Field(description="Описание функциональности")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Температура для генерации"
    )
    max_tokens: int = Field(
        default=2000, ge=1, le=4000, description="Максимальное количество токенов"
    )
    system_prompt: str = Field(description="Системный промпт для ассистента")
    vector_store_config: Dict[str, Any] = Field(default_factory=dict)


class BaseAIAssistant(ABC):
    """
    Базовый класс для всех AI-ассистентов
    Обеспечивает общую функциональность: диалог, векторный поиск, обработка ошибок
    """

    def __init__(self, config: AssistantConfig, supabase_url: str, supabase_key: str):
        """
        Инициализация базового ассистента

        Args:
            config: Конфигурация ассистента
            supabase_url: URL Supabase проекта
            supabase_key: API ключ Supabase
        """
        self.config = config
        self.logger = self._setup_logger()

        # Инициализация клиентов
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            openai_api_key=self._get_openai_api_key(),
        )

        self.embeddings = OpenAIEmbeddings(openai_api_key=self._get_openai_api_key())

        # Инициализация Supabase
        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Инициализация векторного хранилища
        self.vector_store = self._init_vector_store()

        # История диалогов
        self.conversation_history: List[AssistantMessage] = []

        # Создание цепочки разговоров
        self.qa_chain = self._create_conversational_chain()

        self.logger.info(
            "Инициализирован ассистент",
            extra={"assistant_name": config.name, "role": config.role},
        )

    def _setup_logger(self) -> logging.Logger:
        """Настройка логгера для ассистента"""
        logger = logging.getLogger(f"AIAssistant.{self.config.role}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    @abstractmethod
    def _get_openai_api_key(self) -> str:
        """Получение API ключа OpenAI (должен быть реализован в наследниках)"""

    def _init_vector_store(self) -> Optional[SupabaseVectorStore]:
        """Инициализация векторного хранилища для поиска знаний"""
        try:
            # Проверяем доступность Supabase
            tables = (
                self.supabase.table("knowledge_base").select("*").limit(1).execute()
            )

            return SupabaseVectorStore(
                embedding=self.embeddings,
                client=self.supabase,
                table_name="knowledge_base",
                query_name="match_knowledge_base",
            )
        except Exception as e:
            self.logger.warning(
                "Не удалось инициализировать векторное хранилище",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "role": self.config.role,
                },
            )
            return None

    def _create_conversational_chain(self) -> Optional[ConversationalRetrievalChain]:
        """Создание цепочки разговоров с RAG"""
        if not self.vector_store:
            return None

        prompt = ChatPromptTemplate.from_messages(
            [("system", self.config.system_prompt), ("human", "{question}")]
        )

        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            memory=None,  # Будем управлять историей вручную
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 5, "similarity_threshold": 0.7}
            ),
            return_source_documents=True,
            verbose=True,
        )

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> AssistantResponse:
        """
        Обработка запроса пользователя

        Args:
            query: Запрос пользователя
            context: Дополнительный контекст
            user_id: ID пользователя для сохранения истории

        Returns:
            AssistantResponse: Ответ ассистента
        """
        start_time = datetime.now()

        try:
            # Добавляем сообщение пользователя в историю
            user_message = AssistantMessage(role="user", content=query, context=context)
            self.conversation_history.append(user_message)

            # Подготавливаем контекст для ассистента
            enhanced_context = self._prepare_context(context or {})

            # Получаем ответ
            response = await self._get_response(query, enhanced_context)

            # Создаем ответ ассистента
            assistant_message = AssistantMessage(
                role="assistant",
                content=response["answer"],
                context=enhanced_context,
                metadata={
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "sources_count": len(response.get("source_documents", [])),
                    "confidence": response.get("confidence", 0.0),
                },
            )

            self.conversation_history.append(assistant_message)

            # Сохраняем историю в базу данных
            if user_id:
                await self._save_conversation(user_id, user_message, assistant_message)

            # Ограничиваем размер истории (последние 50 сообщений)
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-50:]

            return AssistantResponse(
                message=assistant_message,
                sources=response.get("source_documents", []),
                confidence=response.get("confidence", 0.8),
            )

        except Exception as e:
            self.logger.error(
                "Ошибка при обработке запроса",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "role": self.config.role,
                },
                exc_info=True,
            )
            error_message = AssistantMessage(
                role="assistant",
                content=f"Извините, произошла ошибка при обработке вашего запроса: {str(e)}",
                metadata={"error": str(e), "error_type": type(e).__name__},
            )

            return AssistantResponse(message=error_message, sources=[], confidence=0.0)

    def _prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка контекста для ассистента"""
        enhanced_context = context.copy()

        # Добавляем информацию о роли
        enhanced_context["role"] = self.config.role
        enhanced_context["assistant_name"] = self.config.name

        # Добавляем последние сообщения из истории (ограниченно)
        recent_history = (
            self.conversation_history[-10:] if self.conversation_history else []
        )
        enhanced_context["conversation_history"] = [
            {"role": msg.role, "content": msg.content} for msg in recent_history
        ]

        return enhanced_context

    async def _get_response(
        self, query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Получение ответа от LLM с использованием RAG"""
        if self.qa_chain:
            # Используем RAG-цепочку
            result = await self.qa_chain.ainvoke(
                {
                    "question": query,
                    "chat_history": [
                        (msg.role, msg.content)
                        for msg in self.conversation_history[
                            -10:-1
                        ]  # Исключаем текущее сообщение
                    ],
                }
            )

            return {
                "answer": result["answer"],
                "source_documents": result.get("source_documents", []),
                "confidence": 0.9,
            }
        else:
            # Fallback: используем только LLM без векторного поиска
            response = await self.llm.ainvoke([HumanMessage(content=query)])

            return {
                "answer": response.content,
                "source_documents": [],
                "confidence": 0.7,
            }

    async def _save_conversation(
        self, user_id: str, user_msg: AssistantMessage, assistant_msg: AssistantMessage
    ):
        """Сохранение диалога в базу данных"""
        try:
            conversation_data = {
                "user_id": user_id,
                "assistant_role": self.config.role,
                "user_message": user_msg.dict(),
                "assistant_message": assistant_msg.dict(),
                "timestamp": datetime.now().isoformat(),
            }

            self.supabase.table("conversations").insert(conversation_data).execute()

        except Exception as e:
            self.logger.warning(
                "Не удалось сохранить диалог в базу данных",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "role": self.config.role,
                },
            )

    async def add_knowledge(self, documents: List[Dict[str, Any]], user_id: str):
        """
        Добавление новых знаний в базу ассистента

        Args:
            documents: Список документов для добавления
            user_id: ID пользователя, добавляющего знания
        """
        try:
            # Создаем Document объекты
            docs = []
            for doc_data in documents:
                doc = Document(
                    page_content=doc_data["content"],
                    metadata={
                        "source": doc_data.get("source", "user_input"),
                        "user_id": user_id,
                        "role": self.config.role,
                        "added_at": datetime.now().isoformat(),
                        **doc_data.get("metadata", {}),
                    },
                )
                docs.append(doc)

            # Добавляем в векторное хранилище
            if self.vector_store:
                await self.vector_store.aadd_documents(docs)

                # Также сохраняем в Supabase для резервного копирования
                for doc in docs:
                    doc_record = {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "user_id": user_id,
                        "role": self.config.role,
                    }
                    self.supabase.table("knowledge_base").insert(doc_record).execute()

                self.logger.info(
                    "Добавлено документов в базу знаний",
                    extra={"documents_count": len(docs), "role": self.config.role},
                )

        except Exception as e:
            self.logger.error(
                "Ошибка при добавлении знаний",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "role": self.config.role,
                },
                exc_info=True,
            )
            raise

    def get_conversation_history(self, limit: int = 50) -> List[AssistantMessage]:
        """Получение истории диалогов"""
        return self.conversation_history[-limit:]

    def clear_conversation_history(self):
        """Очистка истории диалогов"""
        self.conversation_history.clear()
        self.logger.info("История диалогов очищена")

    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики использования ассистента"""
        return {
            "role": self.config.role,
            "name": self.config.name,
            "total_messages": len(self.conversation_history),
            "vector_store_configured": self.vector_store is not None,
            "qa_chain_configured": self.qa_chain is not None,
            "config": self.config.dict(),
        }

    def __str__(self) -> str:
        return f"{self.config.name} ({self.config.role})"

    def __repr__(self) -> str:
        return f"BaseAIAssistant(role='{self.config.role}', name='{self.config.name}')"
