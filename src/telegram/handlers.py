# [NEXUS IDENTITY] ID: 6122309749347960075 | DATE: 2025-11-19

"""
Telegram Bot Handlers
Обработчики команд и сообщений
"""

import os
import tempfile
from pathlib import Path

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from src.ai.orchestrator import get_orchestrator
from src.services.ocr_service import DocumentType, get_ocr_service
from src.services.speech_to_text_service import get_stt_service
from src.telegram.config import config
from src.telegram.formatters import TelegramFormatter
from src.telegram.rate_limiter import RateLimiter
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger
router = Router()

# Services
# orchestrator is now accessed via get_orchestrator()
formatter = TelegramFormatter()
rate_limiter = RateLimiter(
    max_per_minute=config.max_requests_per_minute,
    max_per_day=config.max_requests_per_day,
)


def is_premium_user(user_id: int) -> bool:
    """Проверка Premium статуса"""
    return user_id in (config.premium_user_ids or set())


async def check_rate_limit(message: Message) -> bool:
    """Проверка rate limit с автоответом"""
    user_id = message.from_user.id
    is_premium = is_premium_user(user_id)

    allowed, error_msg = await rate_limiter.check_limit(user_id, is_premium)

    if not allowed:
        await message.reply(error_msg, parse_mode=ParseMode.MARKDOWN)

    return allowed


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    user_name = message.from_user.first_name

    welcome = f"""👋 Привет, **{user_name}**!

Я — AI-помощник для 1С разработчиков.

Могу:
🔍 Искать код по смыслу (не только по тексту!)
💻 Генерировать BSL код
🔗 Анализировать зависимости
💡 Отвечать на вопросы о вашей конфигурации
🎤 Понимать голосовые сообщения!

**Попробуйте:**
• `/search расчет НДС`
• Или просто спросите: "Где мы работаем с документами?"
• 🎤 Или отправьте голосовое сообщение!

Полный список команд: /help

🚀 **Начнем?**
"""

    await message.reply(welcome, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = formatter.format_help()
    await message.reply(help_text, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("search"))
async def cmd_search(message: Message):
    """Команда /search - семантический поиск"""

    # Rate limiting
    if not await check_rate_limit(message):
        return

    # Извлечение запроса
    query = message.text.replace("/search", "").strip()

    if not query:
        await message.reply(
            "❓ Укажите запрос для поиска\n\n" "Пример: `/search расчет НДС`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Typing indicator
    await message.answer("🔍 Ищу...")

    try:
        # Поиск через orchestrator
        result = await get_orchestrator().process_query(
            query,
            context={
                "type": "semantic_search",
                "user_id": message.from_user.id,
                "limit": 10,
            },
        )

        # Форматирование
        response = formatter.format_search_results(result)

        await message.reply(response, parse_mode=ParseMode.MARKDOWN)

        logger.info("Search completed", extra={"user_id": message.from_user.id})

    except Exception as e:
        logger.error(
            "Search error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": message.from_user.id if message.from_user else None,
            },
            exc_info=True,
        )
        await message.reply(
            formatter.format_error(str(e)), parse_mode=ParseMode.MARKDOWN
        )


@router.message(Command("generate"))
async def cmd_generate(message: Message):
    """Команда /generate - генерация кода"""

    if not config.enable_code_generation:
        await message.reply("❌ Генерация кода временно отключена")
        return

    # Rate limiting
    if not await check_rate_limit(message):
        return

    # Извлечение описания
    description = message.text.replace("/generate", "").strip()

    if not description:
        await message.reply(
            "❓ Опишите, что нужно сгенерировать\n\n"
            "Пример: `/generate функция расчета скидки по объему`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Typing indicator
    await message.answer("💻 Генерирую код...")

    try:
        # Генерация через orchestrator
        result = await get_orchestrator().process_query(
            f"Создай функцию: {description}",
            context={
                "type": "code_generation",
                "user_id": message.from_user.id,
                "description": description,
            },
        )

        # Форматирование
        response = formatter.format_generated_code(result)

        await message.reply(response, parse_mode=ParseMode.MARKDOWN)

        logger.info("Code generated", extra={"user_id": message.from_user.id})

    except Exception as e:
        logger.error(
            "Generation error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": message.from_user.id if message.from_user else None,
            },
            exc_info=True,
        )
        await message.reply(
            formatter.format_error(str(e)), parse_mode=ParseMode.MARKDOWN
        )


@router.message(Command("deps"))
async def cmd_dependencies(message: Message):
    """Команда /deps - анализ зависимостей"""

    if not config.enable_dependency_analysis:
        await message.reply("❌ Анализ зависимостей временно отключен")
        return

    # Rate limiting
    if not await check_rate_limit(message):
        return

    # Парсинг аргументов: /deps <модуль> <функция>
    args = message.text.replace("/deps", "").strip().split()

    if len(args) < 2:
        await message.reply(
            "❓ Укажите модуль и функцию\n\n"
            "Пример: `/deps РасчетыСервер РассчитатьНДС`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    module_name = args[0]
    function_name = " ".join(args[1:])

    # Typing indicator
    await message.answer("🔗 Анализирую зависимости...")

    try:
        # Анализ через orchestrator
        result = await get_orchestrator().process_query(
            f"Покажи зависимости функции {function_name} в модуле {module_name}",
            context={
                "type": "dependency_analysis",
                "user_id": message.from_user.id,
                "module_name": module_name,
                "function_name": function_name,
            },
        )

        # Форматирование
        response = formatter.format_dependencies(result)

        await message.reply(response, parse_mode=ParseMode.MARKDOWN)

        logger.info("Dependencies analyzed", extra={"user_id": message.from_user.id})

    except Exception as e:
        logger.error(
            "Dependencies error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": message.from_user.id if message.from_user else None,
            },
            exc_info=True,
        )
        await message.reply(
            formatter.format_error(str(e)), parse_mode=ParseMode.MARKDOWN
        )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда /stats - статистика"""
    user_id = message.from_user.id

    stats = rate_limiter.get_stats(user_id)
    stats["is_premium"] = is_premium_user(user_id)

    response = formatter.format_stats(stats)
    await message.reply(response, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("premium"))
async def cmd_premium(message: Message):
    """Команда /premium - информация о Premium"""
    response = formatter.format_premium_info()
    await message.reply(response, parse_mode=ParseMode.MARKDOWN)


@router.message(F.voice)
async def handle_voice(message: Message):
    """Обработка голосовых сообщений 🎤"""

    # Rate limiting
    if not await check_rate_limit(message):
        return

    voice = message.voice

    await message.answer("🎤 Распознаю голос...")

    try:
        # Получаем сервис STT
        stt_service = get_stt_service()

        # Скачиваем голосовое сообщение
        voice_file = await message.bot.get_file(voice.file_id)

        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
            await message.bot.download_file(voice_file.file_path, tmp_file)
            tmp_path = tmp_file.name

        try:
            # Распознаем речь
            transcription = await stt_service.transcribe(
                tmp_path,
                language="ru",
                prompt="1С, БСП, конфигурация, модуль, функция, процедура",
            )

            text = transcription["text"].strip()

            if not text:
                await message.reply(
                    "🤔 Не удалось распознать речь. Попробуйте еще раз."
                )
                return

            # Показываем что распознали
            await message.reply(
                f'✅ Распознано:\n_"{text}"_\n\n🤔 Обрабатываю запрос...',
                parse_mode=ParseMode.MARKDOWN,
            )

            # Обрабатываем как обычный текст через orchestrator
            result = await get_orchestrator().process_query(
                text,
                context={
                    "type": "voice_query",
                    "user_id": message.from_user.id,
                    "original_format": "voice",
                },
            )

            # Определяем тип ответа
            if result.get("type") == "search_results":
                response = formatter.format_search_results(result)
            elif result.get("type") == "code":
                response = formatter.format_generated_code(result)
            else:
                response = result.get("answer", "Не могу найти ответ 😔")

            await message.reply(response, parse_mode=ParseMode.MARKDOWN)

            logger.info(
                "Voice message processed",
                extra={
                    "user_id": message.from_user.id,
                    "text_preview": text[:50] if len(text) > 50 else text,
                },
            )

        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(
                    "Failed to delete temp file",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "tmp_path": tmp_path if "tmp_path" in locals() else None,
                    },
                )

    except Exception as e:
        logger.error(
            "Voice handling error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": message.from_user.id if message.from_user else None,
            },
            exc_info=True,
        )
        await message.reply(
            "❌ Ошибка обработки голосового сообщения\n\n"
            "Попробуйте написать текстом или /help",
            parse_mode=ParseMode.MARKDOWN,
        )


@router.message(F.photo)
async def handle_photo(message: Message):
    """Обработка фотографий - OCR распознавание документов 📸"""

    # Rate limiting
    if not await check_rate_limit(message):
        return

    # Получаем фото наилучшего качества
    photo = message.photo[-1]

    await message.answer("📸 Распознаю документ через OCR...")

    try:
        # Получаем OCR сервис
        ocr_service = get_ocr_service()

        # Скачиваем фото
        photo_file = await message.bot.get_file(photo.file_id)

        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            await message.bot.download_file(photo_file.file_path, tmp_file)
            tmp_path = tmp_file.name

        try:
            # Определяем тип документа из caption (если есть)
            caption = message.caption or ""
            doc_type = DocumentType.AUTO

            if "договор" in caption.lower() or "contract" in caption.lower():
                doc_type = DocumentType.CONTRACT
            elif "счет" in caption.lower() or "invoice" in caption.lower():
                doc_type = DocumentType.INVOICE
            elif "накладная" in caption.lower() or "waybill" in caption.lower():
                doc_type = DocumentType.WAYBILL
            elif "акт" in caption.lower():
                doc_type = DocumentType.ACT

            # Показываем предварительное время
            estimate = ocr_service.estimate_processing_time(tmp_path)
            if estimate > 5:
                await message.answer(
                    f"⏱️ Примерное время обработки: ~{estimate} секунд\n"
                    f"Пожалуйста, подождите..."
                )

            # OCR распознавание
            ocr_result = await ocr_service.process_image(
                tmp_path, document_type=doc_type
            )

            if not ocr_result.text:
                await message.reply(
                    "🤔 Не удалось распознать текст на изображении.\n\n"
                    "Возможные причины:\n"
                    "• Плохое качество фото\n"
                    "• Слишком мелкий текст\n"
                    "• Нестандартный формат\n\n"
                    "Попробуйте сделать фото еще раз с лучшим освещением."
                )
                return

            # Формируем ответ
            response = "✅ **Документ распознан!**\n\n"
            response += f"📊 Уверенность: {ocr_result.confidence*100:.1f}%\n"
            response += f"📝 Символов: {len(ocr_result.text)}\n\n"

            # Если есть структурированные данные
            if ocr_result.structured_data:
                response += "**Извлечено:**\n"

                for key, value in ocr_result.structured_data.items():
                    if value and key != "raw_response":
                        response += f"• {key}: {value}\n"

                response += "\n"

            # Показываем первые 500 символов текста
            text_preview = ocr_result.text[:500]
            if len(ocr_result.text) > 500:
                text_preview += "..."

            response += f"**Распознанный текст:**\n```\n{text_preview}\n```\n\n"

            # Подсказки по использованию
            response += "💡 **Что дальше?**\n"
            response += "• Скопируйте текст для использования\n"
            response += "• Задайте вопрос по документу\n"
            response += "• Попросите создать документ 1С на основе данных\n"

            await message.reply(response, parse_mode=ParseMode.MARKDOWN)

            logger.info(
                "OCR processed",
                extra={
                    "user_id": message.from_user.id,
                    "text_length": len(ocr_result.text),
                    "confidence": round(ocr_result.confidence, 2),
                },
            )

        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(
                    "Failed to delete temp file",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "tmp_path": tmp_path if "tmp_path" in locals() else None,
                    },
                )

    except Exception as e:
        logger.error(
            "OCR handling error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": message.from_user.id if message.from_user else None,
            },
            exc_info=True,
        )
        await message.reply(
            "❌ Ошибка обработки изображения\n\n"
            "Попробуйте:\n"
            "• Отправить фото еще раз\n"
            "• Использовать другой формат (JPG, PNG)\n"
            "• Написать текстом или /help",
            parse_mode=ParseMode.MARKDOWN,
        )


@router.message(F.document)
async def handle_document(message: Message):
    """Обработка файлов (.bsl, .os, .pdf)"""

    # Rate limiting
    if not await check_rate_limit(message):
        return

    document = message.document

    # Проверка: PDF для OCR или BSL для анализа
    if document.file_name.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        # OCR обработка
        await message.answer("📄 Распознаю документ через OCR...")

        try:
            ocr_service = get_ocr_service()

            # Скачиваем файл
            doc_file = await message.bot.get_file(document.file_id)

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=Path(document.file_name).suffix
            ) as tmp_file:
                await message.bot.download_file(doc_file.file_path, tmp_file)
                tmp_path = tmp_file.name

            try:
                # OCR
                ocr_result = await ocr_service.process_image(tmp_path)

                # Аналогично обработке фото
                response = f"✅ **Файл распознан: {document.file_name}**\n\n"
                response += f"📊 Уверенность: {ocr_result.confidence*100:.1f}%\n"
                response += f"📝 Символов: {len(ocr_result.text)}\n\n"

                text_preview = ocr_result.text[:500]
                if len(ocr_result.text) > 500:
                    text_preview += "..."

                response += f"**Текст:**\n```\n{text_preview}\n```"

                await message.reply(response, parse_mode=ParseMode.MARKDOWN)

            finally:
                os.unlink(tmp_path)

        except Exception as e:
            logger.error(
                "OCR document error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": message.from_user.id if message.from_user else None,
                },
                exc_info=True,
            )
            await message.reply(
                "❌ Ошибка обработки документа\n\n" "Попробуйте другой файл или формат",
                parse_mode=ParseMode.MARKDOWN,
            )

        return

    # BSL файлы
    if not document.file_name.endswith((".bsl", ".os", ".txt")):
        await message.reply(
            "❌ Поддерживаются файлы:\n"
            "• .bsl, .os, .txt - для анализа кода\n"
            "• .pdf, .jpg, .png - для OCR распознавания"
        )
        return

    await message.answer("📄 Анализирую BSL код...")

    try:
        # TODO: Скачать файл и проанализировать
        await message.reply(
            "✅ Файл получен!\n\n"
            "🚧 Анализ BSL файлов в разработке...\n"
            "Скоро будет доступно: code review, поиск проблем, рефакторинг",
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        logger.error(
            "File handling error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": message.from_user.id if message.from_user else None,
            },
            exc_info=True,
        )
        await message.reply(formatter.format_error(str(e)))


@router.message(F.text)
async def handle_text(message: Message):
    """Обработка обычного текста (естественные вопросы)"""

    # Игнорируем команды
    if message.text.startswith("/"):
        return

    # Rate limiting
    if not await check_rate_limit(message):
        return

    query = message.text.strip()

    if len(query) < 5:
        await message.reply("❓ Задайте более конкретный вопрос или используйте /help")
        return

    await message.answer("🤔 Думаю...")

    try:
        # Обработка естественного запроса
        result = await get_orchestrator().process_query(
            query, context={"type": "natural_query", "user_id": message.from_user.id}
        )

        # Определяем тип ответа
        if result.get("type") == "search_results":
            response = formatter.format_search_results(result)
        elif result.get("type") == "code":
            response = formatter.format_generated_code(result)
        else:
            # Общий текстовый ответ
            response = result.get("answer", "Не могу найти ответ 😔")

        await message.reply(response, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(
            "Text handling error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": message.from_user.id if message.from_user else None,
            },
            exc_info=True,
        )
        await message.reply(
            "🤔 Не совсем понял вопрос. Попробуйте:\n\n"
            "• `/search <что ищете>`\n"
            "• `/generate <что создать>`\n"
            "• `/help` — список команд",
            parse_mode=ParseMode.MARKDOWN,
        )
