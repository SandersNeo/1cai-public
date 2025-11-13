# AI Agents

Набор специализованных агентов, которые выполняют роли в 1C AI Stack: архитекторы, разработчики, QA, DevOps, бизнес-аналитики и др.

## Категории
| Агент | Файл | Описание |
|-------|------|----------|
| Архитектор | `architect_agent_extended.py` | Анализ архитектуры, выдача рекомендаций. |
| Бизнес-аналитик | `business_analyst_agent.py`, `business_analyst_agent_extended.py` | Работа с требованиями, оценка влияния. |
| Разработчик | `developer_agent_secure.py` | Генерация/рефакторинг кода с проверками безопасности. |
| QA | `qa_engineer_agent.py`, `qa_engineer_agent_extended.py` | Планирование тестов и анализ результатов. |
| DevOps | `devops_agent_secure.py`, `devops_agent_extended.py` | Инфраструктурные сценарии, пайплайны. |
| Code Review | `code_review/` (см. отдельный README) | Проверки кода: best practices, security, автофиксы. |
| SQL Optimizer | `sql_optimizer.py`, `sql_optimizer_secure.py` | Рекомендации по оптимизации SQL (см. secure версию в корне `ai/`). |
| Tech Logs | `tech_log_analyzer.py`, `ras_monitor*.py` | Мониторинг технических логов и RAS. |
| Performance | `performance_analyzer.py` | Анализ производительности, узких мест. |
| ITS Knowledge | `its_knowledge_integrator.py` | Интеграция знаний ITS.

Дополнительно:
- `ai_issue_classifier.py`, `ai_issue_classifier_ml.py` — классификация задач/инцидентов.
- `technology_selector.py`, `onec_server_optimizer.py` — подбор технологий и оптимизация серверов 1С.

## Связанные разделы
- [docs/03-ai-agents/README.md](../../../docs/03-ai-agents/README.md)
- [docs/research/alkoleft_todo.md](../../../docs/research/alkoleft_todo.md)
- [docs/research/ba_agent_roadmap.md](../../../docs/research/ba_agent_roadmap.md)
