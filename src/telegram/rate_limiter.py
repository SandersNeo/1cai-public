"""
Rate limiter для Telegram бота
Ограничение запросов на пользователя
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import asyncio


class RateLimiter:
    """Rate limiter с памятью в Redis/памяти"""
    
    def __init__(self, max_per_minute: int = 10, max_per_day: int = 100):
        self.max_per_minute = max_per_minute
        self.max_per_day = max_per_day
        
        # В памяти (для простоты, потом можно в Redis)
        self.minute_events: Dict[int, list] = defaultdict(list)
        self.day_events: Dict[int, int] = defaultdict(int)
        self.day_reset: Dict[int, datetime] = {}
    
    async def check_limit(self, user_id: int, is_premium: bool = False) -> Tuple[bool, str]:
        """
        Проверка лимитов
        Returns: (allowed, message)
        """
        if is_premium:
            return True, ""
        
        now = datetime.now()
        
        # Проверка дневного лимита
        if user_id in self.day_reset:
            if now - self.day_reset[user_id] > timedelta(days=1):
                # Сброс счетчика
                self.day_requests[user_id] = 0
                self.day_reset[user_id] = now
        else:
            self.day_reset[user_id] = now
        
        if self.day_events[user_id] >= self.max_per_day:
            return False, (
                f"❌ Вы достигли дневного лимита ({self.max_per_day} запросов)\n\n"
                "💎 Попробуйте Premium для безлимитных запросов: /premium"
            )
        
        # Проверка минутного лимита
        minute_ago = now - timedelta(minutes=1)
        
        # Очистка старых запросов
        self.minute_events[user_id] = [
            req_time for req_time in self.minute_events[user_id]
            if req_time > minute_ago
        ]
        
        if len(self.minute_events[user_id]) >= self.max_per_minute:
            return False, (
                f"⏰ Слишком много запросов!\n"
                f"Подождите минуту. Лимит: {self.max_per_minute} запросов/мин"
            )
        
        # Регистрация запроса
        self.minute_events[user_id].append(now)
        self.day_events[user_id] += 1
        
        return True, ""
    
    def get_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        requests_today = self.day_events.get(user_id, 0)
        
        return {
            "requests_today": requests_today,
            "limit_today": self.max_per_day,
            "requests_total": requests_today  # TODO: из БД
        }


