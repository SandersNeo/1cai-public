# AI Agents

Набор из 8 специализированных AI агентов для разных ролей в разработке.

## Архитектура

Все агенты наследуются от `BaseAgent` и следуют единому интерфейсу:

```python
from src.ai.agents.base_agent import BaseAgent, AgentCapability

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="my_agent",
            capabilities=[AgentCapability.CODE_GENERATION]
        )
    
    async def process(self, input_data: Dict) -> Dict:
        # Implementation
        pass
```

## 8 AI Agents

### 1. Architect Agent
**Файл:** `architect_agent.py`, `architect_agent_extended.py`  
**Capabilities:** Architecture Analysis  
**Функции:**
- Архитектурный анализ системы
- Оценка сложности и рисков
- Рекомендации по паттернам

### 2. Business Analyst Agent
**Файл:** `business_analyst_agent.py`, `business_analyst_agent_extended.py`  
**Capabilities:** Requirements Analysis  
**Функции:**
- Анализ требований
- Генерация технического задания
- Извлечение user stories
- Анализ бизнес-процессов

### 3. Developer Agent
**Файл:** `developer_agent_secure.py`  
**Capabilities:** Code Generation, Code Review  
**Функции:**
- Генерация кода с AI
- Security analysis (SQL injection, XSS, secrets)
- Human approval workflow
- Rule of Two [AB] configuration

### 4. QA Engineer Agent
**Файл:** `qa_engineer_agent.py`, `qa_engineer_agent_extended.py`  
**Capabilities:** Testing  
**Функции:**
- Генерация Vanessa BDD тестов
- Smoke и регрессионные тесты
- Анализ покрытия кода
- Генерация тестовых данных

### 5. DevOps Agent
**Файл:** `devops_agent_secure.py`, `devops_agent_extended.py`  
**Capabilities:** DevOps Automation  
**Функции:**
- Анализ CI/CD логов
- Оптимизация pipeline
- Rule of Two [BC] configuration
- Trusted sources only

### 6. Technical Writer Agent ⭐ NEW
**Файл:** `technical_writer_agent_extended.py`  
**Capabilities:** Documentation  
**Функции:**
- Генерация API документации
- User guides
- Release notes
- Code documentation

### 7. Security Agent ⭐ NEW
**Файл:** `security_agent.py`  
**Capabilities:** Security Audit, Code Review  
**Функции:**
- Vulnerability scanning
- Dependency audit
- Secret detection
- Compliance checking (OWASP, CWE, PCI DSS)

### 8. Project Manager Agent ⭐ NEW
**Файл:** `project_manager_agent.py`  
**Capabilities:** Project Management  
**Функции:**
- Task decomposition
- Effort estimation
- Sprint planning
- Resource allocation
- Risk assessment

## Base Agent Features

Все агенты автоматически получают:

### Prometheus Metrics
```python
# Metrics exported automatically
ai_agent_requests_total{agent_name, capability, status}
ai_agent_processing_duration_seconds{agent_name, capability}
ai_agent_active_tasks{agent_name}
```

### Revolutionary Components Integration
```python
agent.enable_revolutionary_components(
    self_evolving=True,
    self_healing=True,
    predictive_generation=True
)
```

### Audit Logging
```python
agent._log_audit(
    action="code_generated",
    details={"lines": 100},
    user_id="user123"
)
```

## Usage Example

```python
from src.ai.agents import SecurityAgent

# Create agent
agent = SecurityAgent()

# Enable Revolutionary Components
agent.enable_revolutionary_components(
    self_healing=True
)

# Execute
result = await agent.execute(
    input_data={"code": "...", "scan_type": "vulnerability_scan"},
    capability=AgentCapability.SECURITY_AUDIT
)

# Check result
if result["success"]:
    print(result["result"])
```

## Monitoring

Grafana dashboard для агентов:
- `monitoring/grafana/dashboards/ai_agents.json`

Prometheus metrics:
- http://localhost:9090/graph?g0.expr=ai_agent_requests_total

## Security

Agents Rule of Two реализован для:
- **Developer Agent**: [AB] - can process untrusted, can access sensitive
- **DevOps Agent**: [BC] - trusted sources only, can change state
- **Security Agent**: [AB] - can process untrusted, can access sensitive

## Next Steps

1. Migrate existing agents to BaseAgent
2. Add real LLM integration (replace placeholders)
3. Integrate with Revolutionary Components
4. Add more comprehensive tests
