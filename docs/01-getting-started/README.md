# 🎯 Getting Started - Быстрый старт

Добро пожаловать в Enterprise 1C AI Stack!

---

## 📚 Содержание раздела

1. **[README.md](./README.md)** - главная страница проекта (copy from root)
2. **[QUICKSTART.md](./QUICKSTART.md)** - быстрый старт за 5 минут
3. **[START_HERE.md](./START_HERE.md)** - пошаговое руководство для новичков
4. **[DEPLOYMENT_INSTRUCTIONS.md](./DEPLOYMENT_INSTRUCTIONS.md)** - развертывание
5. **[CONTRIBUTING.md](./CONTRIBUTING.md)** - как контрибьютить

---

## ⚡ Быстрый старт (5 минут)

### **Шаг 1: Установка**
```bash
git clone https://github.com/DmitrL-dev/1cai-public
cd enterprise-1c-ai-stack
pip install -r requirements.txt
```

### **Шаг 2: Настройка**
```bash
cp .env.example .env
# Отредактируйте .env
```

### **Шаг 3: Запуск**
```bash
python src/main.py
```

---

## 🎓 Что дальше?

- **Новичок?** → [START_HERE.md](./START_HERE.md)
- **Хочу развернуть?** → [DEPLOYMENT_INSTRUCTIONS.md](./DEPLOYMENT_INSTRUCTIONS.md)
- **Хочу помочь?** → [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Обновить БД?** → `python scripts/run_migrations.py`
- **Нужна no-code автоматизация?** → [n8n Integration](../06-features/n8n-integration.md)
- **Нужен токен?** → [Auth API](../API_REFERENCE.md#-auth-api)
- [Python Setup Guide](python-setup.md)

---

[← Назад к документации](../README.md) | [→ Architecture](../02-architecture/)
