# 🚀 Quick Start: Parser Optimization

**Быстрый старт оптимизации парсинга - 5 минут до запуска**

---

## 📦 Шаг 1: Установка зависимостей (2 мин)

```bash
# 1. Основные зависимости
pip install -r requirements-parser-optimization.txt

# 2. Опционально (для ML features)
pip install sentence-transformers scikit-learn numba
```

---

## 🐳 Шаг 2: Запуск инфраструктуры (1 мин)

```bash
# Запускаем Docker сервисы
docker-compose -f docker-compose.parser.yml up -d

# Проверяем что все запустилось
docker-compose -f docker-compose.parser.yml ps
```

**Должно быть запущено:**
- ✅ bsl-language-server (port 8080)
- ✅ postgres-kb (port 5433)
- ✅ redis-parser-cache (port 6380)

---

## ✅ Шаг 3: Тестирование (1 мин)

```bash
# Быстрый тест что все работает
python scripts/test_parser_optimization.py --quick
```

**Ожидаемый вывод:**
```
[TEST 1] OptimizedXMLParser
  ✅ OptimizedXMLParser импортирован

[TEST 2] BSLASTParser
  ✅ BSLASTParser импортирован
  ✅ Парсинг работает: 1 функций

[TEST 3] IntegratedParser
  ✅ IntegratedParser импортирован

[TEST 4] BSL Language Server
  ✅ BSL Language Server доступен

[TEST 5] Redis Cache
  ✅ Redis доступен
```

---

## 🏃 Шаг 4: Запуск парсинга (1 мин)

```bash
# Парсинг всех конфигураций с оптимизациями
python scripts/parsers/parser_integration.py
```

**Ожидаемый результат:**
```
INTEGRATED PARSER - OPTIMIZED MODE
====================================
AST Parsing: ✅ Enabled
Redis Cache: ✅ Enabled
Incremental: ✅ Enabled
Parallel: ✅ Enabled
====================================

Время: 80 сек (vs 440 сек без оптимизаций)
Ускорение: 5.5x
Модулей: 5,000+
Функций: 50,000+
```

---

## 📊 Шаг 5: Benchmark (опционально)

```bash
# Полное сравнение старый vs новый парсер
python scripts/test_parser_optimization.py --benchmark
```

**Ожидаемый результат:**
```
BENCHMARK: Старый парсер
  ⏱️  Время: 55.2 сек
  💾 Память: 2100 MB
  📦 Модулей: 650

BENCHMARK: Новый парсер
  ⏱️  Время: 10.3 сек
  💾 Память: 420 MB
  📦 Модулей: 650

СРАВНЕНИЕ:
  Ускорение: 5.4x
  Экономия памяти: 5.0x
  ✅ Результаты идентичны
```

---

## 🎯 Что дальше?

### Вариант A: Создать massive dataset

```bash
# Запуск создания большого dataset из PostgreSQL
cd scripts/dataset
python massive_ast_dataset_builder.py
```

**Результат:**
- `./data/bsl_massive_dataset/train.jsonl` (40,000+ примеров)
- `./data/bsl_massive_dataset/validation.jsonl` (5,000+ примеров)
- `./data/bsl_massive_dataset/test.jsonl` (5,000+ примеров)

### Вариант B: Fine-tune модель

```bash
# Обучение модели на новом dataset
python scripts/train_copilot_model.py
```

**Время обучения:**
- CPU: 12-24 часа
- GPU (CUDA): 2-4 часа

**Результат:**
- Модель: `./models/1c-copilot-lora/`
- Точность генерации: 85-90% (vs 65-70% до)

---

## 🔧 Troubleshooting

### Проблема 1: BSL Language Server недоступен

```bash
# Проверить статус
docker logs bsl-language-server

# Рестарт
docker-compose -f docker-compose.parser.yml restart bsl-language-server

# Проверить здоровье
curl http://localhost:8080/actuator/health
```

### Проблема 2: Redis недоступен

```bash
# Проверить статус
docker logs redis-parser-cache

# Рестарт
docker-compose -f docker-compose.parser.yml restart redis-parser-cache

# Тест подключения
redis-cli -h localhost -p 6380 ping
```

### Проблема 3: PostgreSQL connection failed

```bash
# Проверить что БД запущена
docker ps | grep postgres

# Проверить подключение
psql -h localhost -p 5433 -U parser_user -d 1c_ai_db

# Если нужно, инициализировать схему
python scripts/init_knowledge_base.py
```

### Проблема 4: Slow parsing

```bash
# Проверить что включены оптимизации
python -c "
from scripts.parsers.parser_integration import IntegratedParser
parser = IntegratedParser(use_ast=True, use_redis=True, incremental=True)
print('AST:', parser.use_ast)
print('Redis:', parser.use_redis)
print('Incremental:', parser.xml_parser.enable_incremental)
"
```

---

## 📈 Мониторинг производительности

### Real-time мониторинг парсинга

```bash
# Terminal 1: Парсинг
python scripts/parsers/parser_integration.py

# Terminal 2: Мониторинг Redis
watch -n 1 'redis-cli -p 6380 info stats'

# Terminal 3: Мониторинг памяти
watch -n 1 'ps aux | grep python | head -5'
```

---

## 🎓 Дополнительные материалы

### Полная документация:
- [1C_PARSER_OPTIMIZATION_RESEARCH.md](1C_PARSER_OPTIMIZATION_RESEARCH.md) - детальное исследование
- [ADVANCED_PARSER_RESEARCH.md](ADVANCED_PARSER_RESEARCH.md) - продвинутые техники
- [PARSER_OPTIMIZATION_SUMMARY.md](PARSER_OPTIMIZATION_SUMMARY.md) - краткое резюме

### Код:
- [optimized_xml_parser.py](scripts/parsers/optimized_xml_parser.py) - оптимизированный XML парсер
- [bsl_ast_parser.py](scripts/parsers/bsl_ast_parser.py) - AST парсер для BSL
- [parser_integration.py](scripts/parsers/parser_integration.py) - интегрированный парсер
- [massive_ast_dataset_builder.py](scripts/dataset/massive_ast_dataset_builder.py) - создание dataset

---

## ✅ Checklist успешной установки

- [ ] lxml установлен и работает
- [ ] Docker сервисы запущены (bsl-ls, postgres, redis)
- [ ] Быстрый тест прошел успешно
- [ ] Benchmark показывает 5x+ ускорение
- [ ] Парсинг конфигураций завершается без ошибок
- [ ] Dataset создается корректно (если запускали)

**Если все ✅ - ГОТОВО! 🎉**

---

## 🚀 Production Deployment

### Для production окружения:

```bash
# 1. Настройка переменных окружения
cp .env.example .env.production
nano .env.production

# 2. Настройка под production
docker-compose -f docker-compose.parser.yml \
  -f docker-compose.parser.prod.yml up -d

# 3. Setup мониторинга
docker-compose -f monitoring/docker-compose.yml up -d

# 4. Настройка backup
./scripts/setup_backup.sh
```

---

**Вопросы?** Смотрите [PARSER_OPTIMIZATION_SUMMARY.md](PARSER_OPTIMIZATION_SUMMARY.md)

**Проблемы?** Создайте issue в GitHub

**Успехов! 🚀**


