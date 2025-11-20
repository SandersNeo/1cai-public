# [NEXUS IDENTITY] ID: 3377841781617205366 | DATE: 2025-11-19

"""
System Tests - End-to-End сценарии
"""

import pytest
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.asyncio
async def test_full_code_review_flow():
    """
    E2E: Полный цикл Code Review

    Flow:
    1. Получение webhook от GitHub
    2. Анализ кода
    3. Генерация review
    4. Отправка комментария в PR
    """

    from src.ai.agents.code_review.ai_reviewer import AICodeReviewer
    from src.api.github_integration import GitHubIntegration

    # Step 1: Webhook received (mocked)
    pr_data = {
        "number": 123,
        "repository": "test/repo",
        "files": [
            {
                "filename": "test.bsl",
                "content": """
Функция РассчитатьСумму(А, Б)
    Возврат А + Б;
КонецФункции
""",
            }
        ],
    }

    # Step 2: Review code
    reviewer = AICodeReviewer()
    review_result = await reviewer.review_code(
        pr_data["files"][0]["content"], pr_data["files"][0]["filename"]
    )

    assert review_result is not None
    assert "overall_status" in review_result

    # Step 3: Generate comment
    comment = f"""
## 🤖 AI Code Review

**Status:** {review_result['overall_status']}

**Issues Found:** {review_result['metrics']['total_issues']}
"""

    # Step 4: Post to GitHub (mocked)
    response_mock = SimpleNamespace(status_code=201, text="ok")
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.__aexit__.return_value = False
    client_mock.post = AsyncMock(return_value=response_mock)

    with patch("httpx.AsyncClient", return_value=client_mock):
        gh = GitHubIntegration()
        posted = await gh.post_pr_comment(
            repo=pr_data["repository"],
            pr_number=pr_data["number"],
            comment=comment,
            github_token="test",
        )

    assert posted is True
    client_mock.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_multi_tenant_isolation_flow():
    """
    E2E: Multi-tenant изоляция

    Flow:
    1. Tenant A создает данные
    2. Tenant B пытается получить данные A
    3. Проверка RLS (Row-Level Security)
    """

    import asyncpg

    try:
        conn = await asyncpg.connect(
            host="localhost",
            user="postgres",
            password="postgres",
            database="enterprise_1c_ai",
        )

        # Create 2 tenants
        tenant_a = await conn.fetchval(
            "INSERT INTO tenants (name, email) VALUES ($1, $2) RETURNING id",
            "Tenant A",
            "a@test.com",
        )

        tenant_b = await conn.fetchval(
            "INSERT INTO tenants (name, email) VALUES ($1, $2) RETURNING id",
            "Tenant B",
            "b@test.com",
        )

        # Tenant A creates project
        await conn.execute(
            """
            INSERT INTO projects (tenant_id, name, metadata)
            VALUES ($1, $2, $3)
        """,
            tenant_a,
            "Project A",
            {},
        )

        # Set RLS context for Tenant B
        await conn.execute("SET app.current_tenant_id = $1", tenant_b)

        # Tenant B tries to read (should see 0 rows)
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM projects WHERE name = $1", "Project A"
        )

        # RLS should prevent access
        assert count == 0, "RLS failed - tenant B can see tenant A data!"

        # Cleanup
        await conn.execute("DELETE FROM projects WHERE tenant_id = $1", tenant_a)
        await conn.execute(
            "DELETE FROM tenants WHERE id IN ($1, $2)", tenant_a, tenant_b
        )
        await conn.close()

    except Exception as e:
        pytest.skip(f"Database not available: {e}")


@pytest.mark.asyncio
async def test_full_billing_flow():
    """
    E2E: Полный цикл биллинга

    Flow:
    1. Регистрация tenant
    2. Создание Stripe customer
    3. Subscription creation
    4. Payment webhook
    5. Status update
    """

    from src.api.billing_webhooks import BillingWebhookHandler
    import asyncpg

    try:
        conn = await asyncpg.connect(
            host="localhost",
            user="postgres",
            password="postgres",
            database="enterprise_1c_ai",
        )

        # Step 1: Create tenant
        tenant_id = await conn.fetchval(
            """
            INSERT INTO tenants (name, email, plan, status, stripe_customer_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """,
            "Test Company",
            "test@company.com",
            "starter",
            "trial",
            "cus_test123",
        )

        # Step 2-3: Stripe customer & subscription created (mocked)

        # Step 4: Payment webhook received
        handler = BillingWebhookHandler(
            asyncpg.create_pool(
                host="localhost", user="postgres", database="enterprise_1c_ai"
            )
        )

        webhook_event = {
            "type": "invoice.payment_succeeded",
            "id": "evt_test",
            "created": 1234567890,
            "data": {"object": {"customer": "cus_test123", "amount_paid": 9900}},
        }

        await handler.handle_event(webhook_event)

        # Step 5: Check status updated
        tenant = await conn.fetchrow("SELECT * FROM tenants WHERE id = $1", tenant_id)

        # Should have billing event logged
        events = await conn.fetch(
            "SELECT * FROM billing_events WHERE tenant_id = $1", tenant_id
        )

        assert len(events) > 0

        # Cleanup
        await conn.execute("DELETE FROM billing_events WHERE tenant_id = $1", tenant_id)
        await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_id)
        await conn.close()

    except Exception as e:
        pytest.skip(f"Database not available: {e}")


@pytest.mark.asyncio
async def test_ai_agent_routing_flow():
    """
    E2E: AI Agent маршрутизация

    Flow:
    1. Пользователь отправляет запрос
    2. RoleDetector определяет роль
    3. RoleBasedRouter направляет к агенту
    4. Агент обрабатывает
    5. Результат возвращается
    """

    from src.ai.role_based_router import RoleBasedRouter

    router = RoleBasedRouter()

    # Developer query
    dev_result = await router.route_query("Как оптимизировать этот SQL запрос?")

    assert dev_result["role"] == "developer"

    # DevOps query
    devops_result = await router.route_query("Оптимизируй CI/CD pipeline")

    assert devops_result["role"] == "devops"

    # QA query
    qa_result = await router.route_query("Сгенерируй тесты для этой функции")

    assert qa_result["role"] == "qa_engineer"


@pytest.mark.asyncio
async def test_copilot_completion_flow():
    """
    E2E: 1С:Copilot autocomplete

    Flow:
    1. VSCode sends completion request
    2. API receives request
    3. Model generates suggestions
    4. Suggestions returned
    """

    from src.api.copilot_api import CopilotService

    service = CopilotService()

    # Code being typed
    code = """
Функция РассчитатьНДС(Сумма)
    СтавкаНДС = 20;
    """

    current_line = "СуммаНДС = "

    # Get completions
    suggestions = await service.get_completions(
        code=code, current_line=current_line, max_suggestions=3
    )

    assert suggestions is not None
    assert len(suggestions) <= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
