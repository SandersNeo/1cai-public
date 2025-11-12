# Динамика процессов

| Файл | PNG | Сценарий |
|------|-----|----------|
| `ci-cd-sequence.puml` | ![CI/CD sequence](png/ci-cd-sequence.png) | Последовательность CI/CD: от Git push до деплоя и проверок. |
| `core-data-flow.puml` | ![Core data flow](png/core-data-flow.png) | Главный поток данных между сервисами платформы. |
| `incident-response-activity.puml` | ![Incident response](png/incident-response-activity.png) | Действия команды при инциденте и связь с runbook'ами. |
| `its-scraper-sequence.puml` | ![ITS scraper sequence](png/its-scraper-sequence.png) | Как работает ITS Scraper: очереди, парсеры, хранилища. |
| `quick-analysis-bpmn.puml` | ![Quick analysis BPMN](png/quick-analysis-bpmn.png) | BPMN-диаграмма быстрого анализа конфигурации. |
| `release-bpmn.puml` | ![Release BPMN](png/release-bpmn.png) | BPMN-процесс релиза с контрольными точками. |

Диаграммы полезны для подготовки тренингов, уточнения регламентов и постмортемов. Обновление — правка `.puml` → `make render-uml`.
