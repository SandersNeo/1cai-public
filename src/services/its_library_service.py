"""
Сервис для работы с библиотекой 1С ИТС
Извлечение документации, примеров кода и best practices
Версия: 2.1.0

Улучшения:
- Retry logic для HTTP запросов
- Улучшена обработка ошибок
- Structured logging
- Input validation
"""

import os
import re
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ITSLibraryService:
    """Сервис для работы с библиотекой 1С ИТС"""
    
    # URL библиотеки ИТС
    ITS_BASE_URL = "https://its.1c.ru"
    # URL авторизации (правильный URL из login.1c.ru)
    ITS_LOGIN_URL = "https://login.1c.ru/login?service=https%3A%2F%2Fits.1c.ru%2Flogin%2F%3Faction%3Daftercheck%26provider%3Dlogin"
    
    # Возможные URL для входа (резервные)
    ITS_LOGIN_URLS = [
        "https://login.1c.ru/login?service=https%3A%2F%2Fits.1c.ru%2Flogin%2F%3Faction%3Daftercheck%26provider%3Dlogin",
        "https://its.1c.ru/db/metod8dev",
        "https://its.1c.ru/auth",
        "https://its.1c.ru/login"
    ]
    
    def __init__(self, username: str, password: str):
        """
        Инициализация сервиса ИТС
        
        Args:
            username: Имя пользователя ИТС
            password: Пароль ИТС
        """
        # Input validation
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        
        self.username = username
        self.password = password
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Для синхронных запросов используем Client
        self.session = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            headers=self.base_headers
        )
        self.authenticated = False
        
    async def authenticate(self) -> bool:
        """
        Авторизация в библиотеке ИТС
        
        Returns:
            True если авторизация успешна
        """
        try:
            # Используем правильный URL авторизации
            logger.info(
                "Авторизация через ITS",
                extra={"its_login_url": self.ITS_LOGIN_URL}
            )
            login_response = self.session.get(self.ITS_LOGIN_URL)
            
            if login_response.status_code != 200:
                logger.error(
                    "Не удалось получить страницу входа",
                    extra={"status_code": login_response.status_code}
                )
                return False
            
            # Пробуем найти форму входа
            logger.info("Поиск формы авторизации...")
            if await self._try_login_from_page(login_response.text, self.ITS_LOGIN_URL):
                self.authenticated = True
                logger.info("Авторизация успешна!")
                return True
            
            # Если стандартный метод не сработал, пробуем резервные URL
            for login_url in self.ITS_LOGIN_URLS[1:]:  # Пропускаем первый (уже использовали)
                try:
                    logger.info(
                        "Попытка авторизации через резервный URL",
                        extra={"login_url": login_url}
                    )
                    response = self.session.get(login_url)
                    
                    if response.status_code == 200:
                        if await self._try_login_from_page(response.text, login_url):
                            self.authenticated = True
                            logger.info("Авторизация успешна через резервный URL")
                            return True
                except Exception as e:
                    logger.debug(
                        "Ошибка для резервного URL",
                        extra={
                            "login_url": login_url,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                    continue
            
            # Если стандартные методы не сработали, пробуем прямую авторизацию
            logger.info("Попытка прямой авторизации...")
            return await self._try_direct_auth()
            
        except Exception as e:
            logger.error(
                "Ошибка авторизации в ИТС",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return False
    
    async def _try_login_from_page(self, html_content: str, base_url: str) -> bool:
        """Попытка авторизации на основе HTML страницы"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Ищем все формы
            forms = soup.find_all('form')
            
            for form in forms:
                # Ищем поля для входа (для login.1c.ru обычно 'login' и 'password')
                username_input = (form.find('input', {'name': 'login'}) or 
                                form.find('input', {'name': 'username'}) or
                                form.find('input', {'name': re.compile(r'user|login|name', re.I)}) or
                                form.find('input', {'id': re.compile(r'user|login|name', re.I)}))
                
                password_input = form.find('input', {'type': 'password'})
                
                if username_input and password_input:
                    # Находим action формы (для login.1c.ru обычно action="/login" или полный URL)
                    action = form.get('action', '')
                    
                    if action:
                        # Если action начинается с /, это относительный путь
                        if action.startswith('/'):
                            # Для login.1c.ru используем базовый URL
                            if 'login.1c.ru' in base_url:
                                action_url = urljoin('https://login.1c.ru', action)
                            else:
                                action_url = urljoin(base_url, action)
                        elif action.startswith('http'):
                            action_url = action
                        else:
                            action_url = urljoin(base_url, action)
                    else:
                        # Если action не указан, используем текущий URL
                        action_url = base_url
                    
                    # Формируем данные для входа
                    # Для login.1c.ru используются поля 'login' и 'password'
                    login_field_name = username_input.get('name', 'login')
                    password_field_name = password_input.get('name', 'password')
                    
                    login_data = {
                        login_field_name: self.username,
                        password_field_name: self.password
                    }
                    
                    # Добавляем скрытые поля формы (CSRF токены и т.д.)
                    for hidden_input in form.find_all('input', {'type': 'hidden'}):
                        name = hidden_input.get('name')
                        value = hidden_input.get('value', '')
                        if name:
                            login_data[name] = value
                    
                    # Отправляем запрос
                    logger.debug(
                        "Попытка авторизации",
                        extra={
                            "action_url": action_url,
                            "login_field_name": login_field_name,
                            "has_password": bool(self.password)
                        }
                    )
                    
                    response = self.session.post(action_url, data=login_data, follow_redirects=True)
                    
                    # Проверяем успешность
                    if response.status_code in [200, 302]:
                        # Проверяем, что мы авторизованы
                        response_lower = response.text.lower()
                        response_url_lower = str(response.url).lower()
                        
                        # Индикаторы успешной авторизации
                        success_indicators = [
                            'logout', 'выход', 'профиль', 'profile', 
                            'its.1c.ru/db', 'its.1c.ru/login', 
                            self.username.lower()
                        ]
                        
                        if any(indicator in response_lower or indicator in response_url_lower 
                               for indicator in success_indicators):
                            logger.info("Авторизация успешна (по индикаторам в ответе)")
                            return True
                        
                        # Проверяем cookies (Bitrix использует различные cookies)
                        cookies_to_check = [
                            'BITRIX_SM_LOGIN', 'auth', 'session', 
                            '1C_SESSION', 'ITS_AUTH'
                        ]
                        
                        for cookie_name in cookies_to_check:
                            if self.session.cookies.get(cookie_name):
                                logger.info(
                                    "Авторизация успешна (найден cookie)",
                                    extra={"cookie_name": cookie_name}
                                )
                                return True
                        
                        # Проверяем редирект на защищённую страницу
                        response_url_str = str(response.url)
                        if 'its.1c.ru' in response_url_str and 'login' not in response_url_str:
                            logger.info("Авторизация успешна (редирект на защищённую страницу)")
                            return True
            
            return False
            
        except Exception as e:
            logger.error(
                "Ошибка при попытке входа",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return False
    
    async def _try_direct_auth(self) -> bool:
        """Прямая авторизация через стандартные эндпоинты"""
        try:
            # Пробуем стандартные эндпоинты авторизации Bitrix
            auth_endpoints = [
                '/user/auth/login',
                '/auth/login',
                '/login',
                '/db/login'
            ]
            
            for endpoint in auth_endpoints:
                try:
                    auth_url = urljoin(self.ITS_BASE_URL, endpoint)
                    
                    # Пробуем разные форматы данных
                    auth_data_variants = [
                        {'username': self.username, 'password': self.password},
                        {'login': self.username, 'password': self.password},
                        {'user': self.username, 'pass': self.password},
                        {'LOGIN': self.username, 'PASSWORD': self.password}
                    ]
                    
                    for auth_data in auth_data_variants:
                        try:
                            # Пробуем POST с form data
                            response = self.session.post(auth_url, data=auth_data, follow_redirects=True)
                            
                            if response.status_code in [200, 302]:
                                # Проверяем cookies
                                if self.session.cookies.get('BITRIX_SM_LOGIN') or self.session.cookies.get('auth'):
                                    self.authenticated = True
                                    logger.info(
                                        "Авторизация успешна",
                                        extra={"auth_url": auth_url}
                                    )
                                    return True
                                
                                # Пробуем JSON
                                response = self.session.post(auth_url, json=auth_data, follow_redirects=True)
                                if response.status_code in [200, 302]:
                                    if self.session.cookies.get('BITRIX_SM_LOGIN'):
                                        self.authenticated = True
                                        return True
                        except (httpx.HTTPError, httpx.RequestError, Exception):
                            continue
                except (httpx.HTTPError, httpx.RequestError, Exception):
                    continue
            
            return False
            
        except Exception as e:
            logger.error(
                "Ошибка прямой авторизации",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return False
    
    async def get_configuration_documentation(
        self,
        config_name: str
    ) -> Dict[str, Any]:
        """
        Получение документации по конфигурации
        
        Args:
            config_name: Название конфигурации (erp, ut, zup, buh, holding)
            
        Returns:
            Словарь с документацией
        """
        if not self.authenticated:
            auth_result = await self.authenticate()
            if not auth_result:
                return {"error": "Не удалось авторизоваться в ИТС"}
        
        try:
            # Маппинг конфигураций на ID контента в ИТС
            config_content_ids = {
                "erp": "78/1",
                "ut": "78/2",
                "zup": "78/3",
                "buh": "78/4",
                "holding": "78/5",
                "buhbit": "78/4",
                "do": "78/6",
                "ka": "78/7"
            }
            
            content_id = config_content_ids.get(config_name.lower())
            if not content_id:
                return {"error": f"Конфигурация {config_name} не найдена в ИТС"}
            
            # ИТС использует hash-based routing (#content:78:1)
            # Прямой URL с hash работает и возвращает HTML со всем контентом
            hash_id = content_id.replace('/', ':')
            page_url = f"{self.ITS_BASE_URL}/db/metod8dev#content:{hash_id}"
            
            # Получаем страницу документации
            logger.debug(
                "Получение страницы",
                extra={"page_url": page_url}
            )
            response = self.session.get(page_url)
            
            if response.status_code != 200:
                logger.error(
                    "Не удалось получить документацию",
                    extra={"status_code": response.status_code, "page_url": page_url}
                )
                return {"error": f"HTTP {response.status_code}"}
            
            logger.info(
                "Получена страница",
                extra={"page_size_bytes": len(response.text), "page_url": page_url}
            )
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлекаем информацию
            documentation = {
                "config_name": config_name,
                "title": self._extract_title(soup),
                "description": self._extract_description(soup),
                "modules": self._extract_modules(soup),
                "best_practices": self._extract_best_practices(soup),
                "code_examples": self._extract_code_examples(soup),
                "api_reference": self._extract_api_reference(soup),
                "extracted_at": datetime.now().isoformat()
            }
            
            logger.info(
                "Извлечена документация",
                extra={"config_name": config_name}
            )
            return documentation
            
        except Exception as e:
            logger.error(
                "Ошибка получения документации",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "config_name": config_name if 'config_name' in locals() else None
                },
                exc_info=True
            )
            return {"error": str(e)}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлечение заголовка"""
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            return title_elem.get_text(strip=True)
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлечение описания"""
        # Ищем описания в различных местах
        description = ""
        
        # Пробуем найти блок описания
        desc_blocks = soup.find_all(['p', 'div'], class_=re.compile(r'description|about|info', re.I))
        for block in desc_blocks:
            text = block.get_text(strip=True)
            if len(text) > 50:  # Более-менее содержательный текст
                description += text + "\n"
        
        return description.strip()
    
    def _extract_modules(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлечение информации о модулях"""
        modules = []
        
        # Вариант 1: Ищем блоки с информацией о модулях по классам
        module_sections = soup.find_all(['div', 'section'], class_=re.compile(r'module|module-info|content', re.I))
        
        # Вариант 2: Ищем ссылки на модули
        module_links = soup.find_all('a', href=re.compile(r'module|модуль', re.I))
        
        # Вариант 3: Ищем упоминания модулей в тексте
        all_text = soup.get_text()
        module_patterns = [
            r'Общий\s+Модуль\s+(\w+)',
            r'Модуль\s+(\w+)',
            r'Модуль\s+Объекта\s+(\w+)',
            r'Модуль\s+Формы\s+(\w+)'
        ]
        
        found_modules = set()
        for pattern in module_patterns:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                found_modules.add(match.group(1) if match.lastindex else match.group(0))
        
        # Извлекаем информацию о найденных модулях
        for module_name in list(found_modules)[:50]:  # Ограничиваем
            # Ищем контекст вокруг упоминания модуля
            module_context = self._find_module_context(soup, module_name)
            
            if module_context:
                modules.append({
                    "name": module_name,
                    "description": module_context.get("description", ""),
                    "code_examples": module_context.get("code_examples", [])
                })
        
        # Добавляем модули из ссылок
        for link in module_links[:20]:
            link_text = link.get_text(strip=True)
            if link_text and len(link_text) > 3:
                modules.append({
                    "name": link_text,
                    "description": "",
                    "code_examples": [],
                    "source": "link"
                })
        
        logger.info(
            "Найдено модулей",
            extra={"modules_count": len(modules)}
        )
        return modules
    
    def _find_module_context(self, soup: BeautifulSoup, module_name: str) -> Optional[Dict[str, Any]]:
        """Поиск контекста упоминания модуля"""
        try:
            # Ищем текст с упоминанием модуля
            all_text_elements = soup.find_all(text=re.compile(module_name, re.I))
            
            if not all_text_elements:
                return None
            
            # Берем первый найденный элемент
            text_elem = all_text_elements[0]
            parent = text_elem.parent
            
            # Ищем описание в родительском элементе
            description = ""
            code_examples = []
            
            # Ищем параграфы рядом
            for sibling in parent.find_next_siblings(['p', 'div'])[:3]:
                text = sibling.get_text(strip=True)
                if text and len(text) > 50:
                    description += text + " "
            
            # Ищем код рядом
            for code_block in parent.find_all_next(['pre', 'code'])[:3]:
                code = code_block.get_text(strip=True)
                if code and len(code) > 20:
                    code_examples.append(code)
            
            return {
                "description": description.strip(),
                "code_examples": code_examples
            }
        except (httpx.HTTPError, httpx.RequestError, Exception):
            return None
    
    def _extract_best_practices(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлечение best practices"""
        practices = []
        
        # Вариант 1: Ищем блоки с best practices по классам
        practice_sections = soup.find_all(['div', 'section'], 
                                         class_=re.compile(r'practice|best-practice|recommendation|tip|note', re.I))
        
        # Вариант 2: Ищем упоминания best practices в тексте
        all_text = soup.get_text()
        practice_keywords = [
            r'рекомендуется',
            r'не рекомендуется',
            r'лучше всего',
            r'следует',
            r'важно',
            r'обратите внимание',
            r'best practice',
            r'good practice'
        ]
        
        found_practices = []
        for keyword in practice_keywords:
            pattern = f'({keyword}[^.!?]*[.!?])'
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                text = match.group(0).strip()
                if len(text) > 20 and len(text) < 500:
                    found_practices.append(text)
        
        # Обрабатываем найденные практики
        for i, practice_text in enumerate(found_practices[:30]):  # Ограничиваем
            practices.append({
                "title": practice_text[:100],
                "description": practice_text,
                "category": self._detect_category(practice_text)
            })
        
        # Обрабатываем секции
        for section in practice_sections:
            title_elem = section.find(['h3', 'h4', 'strong', 'b'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            desc_elem = section.find('p')
            description = desc_elem.get_text(strip=True) if desc_elem else section.get_text(strip=True)[:500]
            
            if title or description:
                practices.append({
                    "title": title or "Best Practice",
                    "description": description,
                    "category": self._detect_category(description)
                })
        
        logger.info(
            "Найдено best practices",
            extra={"practices_count": len(practices)}
        )
        return practices
    
    def _extract_code_examples(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлечение примеров кода"""
        examples = []
        
        # Ищем блоки кода (расширенный поиск)
        code_selectors = [
            ('pre', {}),
            ('code', {}),
            ('div', {'class': re.compile(r'code|example|sample', re.I)}),
            ('div', {'class': re.compile(r'bsl|1c', re.I)}),
            ('textarea', {}),
            ('div', {'style': re.compile(r'monospace|fixed', re.I)})
        ]
        
        code_blocks = []
        for selector, attrs in code_selectors:
            found = soup.find_all(selector, attrs)
            code_blocks.extend(found)
        
        # Убираем дубликаты
        seen_codes = set()
        for i, code_block in enumerate(code_blocks):
            code = code_block.get_text(strip=True)
            
            # Проверяем что это похоже на код BSL
            if code and len(code) > 30:
                # Проверяем признаки BSL кода
                if any(keyword in code.lower() for keyword in ['функция', 'процедура', 'переменная', 'возврат', 'если', 'цикл']):
                    # Проверяем что это не дубликат
                    code_hash = hash(code[:500])
                    if code_hash not in seen_codes:
                        seen_codes.add(code_hash)
                        
                        # Ищем описание перед блоком кода
                        prev_elem = code_block.find_previous(['p', 'div', 'li', 'td'])
                        description = prev_elem.get_text(strip=True)[:200] if prev_elem else ""
                        
                        # Ищем заголовок секции
                        section_header = None
                        for header in code_block.find_all_previous(['h1', 'h2', 'h3', 'h4'])[:1]:
                            section_header = header.get_text(strip=True)
                            break
                        
                        examples.append({
                            "id": f"example_{len(examples)+1}",
                            "code": code[:5000],  # Ограничиваем длину
                            "description": description,
                            "section": section_header,
                            "language": "bsl"
                        })
                        
                        if len(examples) >= 50:  # Ограничиваем количество
                            break
        
        logger.info(
            "Найдено примеров кода",
            extra={"examples_count": len(examples)}
        )
        return examples
    
    def _extract_api_reference(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлечение справочной информации по API"""
        api_refs = []
        
        # Ищем таблицы с методами/функциями
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            
            # Проверяем заголовки
            headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
            
            if any(keyword in ' '.join(headers).lower() for keyword in ['метод', 'функция', 'method', 'function']):
                # Это таблица с API
                for row in rows[1:]:
                    cells = [td.get_text(strip=True) for td in row.find_all('td')]
                    if len(cells) >= 2:
                        api_refs.append({
                            "name": cells[0],
                            "description": cells[1] if len(cells) > 1 else "",
                            "parameters": cells[2] if len(cells) > 2 else "",
                            "return_type": cells[3] if len(cells) > 3 else ""
                        })
        
        return api_refs
    
    def _detect_category(self, text: str) -> str:
        """Определение категории best practice"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['производительность', 'performance', 'оптимизация', 'optimization']):
            return "performance"
        elif any(keyword in text_lower for keyword in ['безопасность', 'security', 'безопасный', 'safe']):
            return "security"
        elif any(keyword in text_lower for keyword in ['ошибка', 'error', 'исключение', 'exception']):
            return "error_handling"
        else:
            return "general"
    
    def _parse_api_response(self, api_data: Dict, config_name: str) -> Dict[str, Any]:
        """Парсинг JSON ответа от API ИТС"""
        try:
            # Структура ответа может быть разной
            documentation = {
                "config_name": config_name,
                "title": api_data.get("title", ""),
                "content": api_data.get("content", ""),
                "modules": [],
                "best_practices": [],
                "code_examples": [],
                "extracted_at": datetime.now().isoformat()
            }
            
            # Парсим HTML из content если есть
            if api_data.get("content"):
                soup = BeautifulSoup(api_data["content"], 'html.parser')
                documentation["modules"] = self._extract_modules(soup)
                documentation["best_practices"] = self._extract_best_practices(soup)
                documentation["code_examples"] = self._extract_code_examples(soup)
            
            return documentation
            
        except Exception as e:
            logger.error(
                "Ошибка парсинга API ответа",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {"error": str(e)}
    
    async def load_all_configurations_docs(self) -> Dict[str, Any]:
        """
        Загрузка документации для всех конфигураций
        
        Returns:
            Словарь с документацией по всем конфигурациям
        """
        if not self.authenticated:
            auth_result = await self.authenticate()
            if not auth_result:
                return {"error": "Не удалось авторизоваться в ИТС"}
        
        configurations = ["erp", "ut", "zup", "buh", "holding", "buhbit", "do", "ka"]
        results = {}
        
        for config_name in configurations:
            logger.info(
                "Загрузка документации",
                extra={"config_name": config_name}
            )
            doc = await self.get_configuration_documentation(config_name)
            results[config_name] = doc
        
        return results


def get_its_service(username: str = None, password: str = None) -> ITSLibraryService:
    """
    Получение экземпляра сервиса ИТС
    
    Args:
        username: Имя пользователя (из env если не указано)
        password: Пароль (из env если не указано)
        
    Returns:
        Экземпляр ITSLibraryService
    """
    username = username or os.getenv("ITS_USERNAME", "its_rrpk")
    password = password or os.getenv("ITS_PASSWORD", "RRPK_2022")
    
    return ITSLibraryService(username, password)

