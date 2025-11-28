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
