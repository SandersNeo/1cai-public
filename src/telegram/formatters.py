# [NEXUS IDENTITY] ID: 2676020175565852118 | DATE: 2025-11-19

"""
Форматирование ответов для Telegram
Markdown formatting, code blocks, красивый вывод
"""

from typing import Dict


class TelegramFormatter:
    """Форматирование ответов для Telegram"""

    @staticmethod
    def format_search_results(results: Dict) -> str:
        """Форматирование результатов поиска"""
        if not results or not results.get("results"):
            return "🔍 Ничего не найдено. Попробуйте другой запрос."

        items = results.get("results", [])
        count = len(items)

        # Заголовок
        text = f"✨ **Найдено: {count} результатов**\n\n"

        # Показываем топ-5 результатов
        for i, item in enumerate(items[:5], 1):
            name = item.get("name", "Unknown")
            module = item.get("module", "")
            score = item.get("score", 0)
            description = item.get("description", "")

            text += f"**{i}. {name}**\n"

            if module:
                text += f"📁 `{module}`\n"

            if description:
                # Ограничиваем длину описания
                desc_short = (
                    description[:150] + "..." if len(description) > 150 else description
                )
                text += f"💬 {desc_short}\n"

            if score:
                text += f"🎯 Релевантность: {score:.1%}\n"

            text += "\n"

        # Если результатов больше 5
        if count > 5:
            text += f"_...и ещё {count - 5} результатов_\n\n"

        # Подсказка
        text += "💡 Хотите увидеть код? Используйте /show <номер>"

        return text

    @staticmethod
    def format_code(code: str, language: str = "bsl") -> str:
        """Форматирование кода с syntax highlighting"""
        # Telegram поддерживает markdown code blocks
        return f"```{language}\n{code}\n```"

    @staticmethod
    def format_generated_code(result: Dict) -> str:
        """Форматирование сгенерированного кода"""
        code = result.get("code", "")
        explanation = result.get("explanation", "")
        function_name = result.get("function_name", "")

        text = f"✨ **Сгенерирован код**\n\n"

        if function_name:
            text += f"📝 Функция: `{function_name}`\n\n"

        if explanation:
            text += f"💡 **Описание:**\n{explanation}\n\n"

        text += f"**Код:**\n{TelegramFormatter.format_code(code)}\n\n"

        text += "⚠️ _Не забудьте проверить и протестировать код перед использованием!_"

        return text

    @staticmethod
    def format_dependencies(result: Dict) -> str:
        """Форматирование анализа зависимостей"""
        function_name = result.get("function", "")
        module_name = result.get("module", "")

        text = f"🔗 **Анализ зависимостей**\n\n"
        text += f"📌 Функция: `{function_name}`\n"
        text += f"📁 Модуль: `{module_name}`\n\n"

        # Используемые функции
        uses = result.get("uses", [])
        if uses:
            text += f"**Использует ({len(uses)}):**\n"
            for func in uses[:10]:
                text += f"  → `{func}`\n"
            if len(uses) > 10:
                text += f"  _...и ещё {len(uses) - 10}_\n"
            text += "\n"

        # Где используется
        used_by = result.get("used_by", [])
        if used_by:
            text += f"**Используется в ({len(used_by)}):**\n"
            for func in used_by[:10]:
                text += f"  ← `{func}`\n"
            if len(used_by) > 10:
                text += f"  _...и ещё {len(used_by) - 10}_\n"
            text += "\n"

        # Граф (если есть)
        if result.get("graph_url"):
            text += f"📊 [Визуализация графа]({result['graph_url']})\n"

        return text

    @staticmethod
    def format_error(error: str) -> str:
        """Форматирование ошибки"""
        return f"❌ **Ошибка:**\n\n{error}\n\n💡 Попробуйте переформулировать запрос или используйте /help"

    @staticmethod
    def format_help() -> str:
        """Справка по командам"""
        return """🤖 **1C AI Assistant**

**Команды:**

🔍 `/search <запрос>` — семантический поиск кода
Пример: `/search расчет НДС`

💻 `/generate <описание>` — генерация BSL кода  
Пример: `/generate функция для расчета скидки`

🔗 `/deps <модуль> <функция>` — анализ зависимостей
Пример: `/deps РасчетыСервер РассчитатьНДС`

📊 `/stats` — ваша статистика
🎁 `/premium` — информация о Premium
❓ `/help` — эта справка

**Естественные запросы:**
Просто напишите вопрос, и я постараюсь помочь!

Пример: "Где в коде мы работаем с налогами?"

**Подсказки:**
• Используйте конкретные термины
• Можете отправлять BSL файлы для анализа
• 🎤 Можете отправлять голосовые сообщения!
• Premium дает безлимитные запросы

🚀 Начните с `/search` или просто задайте вопрос!
"""

    @staticmethod
    def format_stats(stats: Dict) -> str:
        """Форматирование статистики пользователя"""
        requests_today = stats.get("requests_today", 0)
        requests_total = stats.get("requests_total", 0)
        limit_today = stats.get("limit_today", 100)
        is_premium = stats.get("is_premium", False)

        text = "📊 **Ваша статистика**\n\n"

        if is_premium:
            text += "⭐ **Premium аккаунт** — безлимит!\n\n"
        else:
            text += f"📈 Запросов сегодня: {requests_today}/{limit_today}\n"
            remaining = max(0, limit_today - requests_today)
            text += f"✅ Осталось: {remaining}\n\n"

        text += f"📊 Всего запросов: {requests_total}\n"

        if not is_premium and requests_today >= limit_today * 0.8:
            text += f"\n⚠️ Вы использовали {requests_today}/{limit_today} запросов!\n"
            text += "💎 Попробуйте Premium для безлимитных запросов: /premium"

        return text

    @staticmethod
    def format_premium_info() -> str:
        """Информация о Premium"""
        return """💎 **Premium возможности**

**Расширенные функции:**
✅ Повышенный лимит запросов
✅ Приоритетная обработка
✅ Расширенный анализ кода
✅ API для интеграции
✅ Экспорт результатов
✅ Дополнительные AI агенты

**Интересует Premium доступ?**
Создайте [Issue на GitHub](https://github.com/DmitrL-dev/1cai-public/issues) с описанием ваших задач.

Мы обсудим возможности интеграции для вашего случая.
"""
