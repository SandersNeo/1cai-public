# [NEXUS IDENTITY] ID: -858150394946314802 | DATE: 2025-11-19


import pytest

from src.ai.agents.tech_log_analyzer import (
    TechLogAnalyzer,
    TechLogEvent,
    PerformanceIssue,
)


@pytest.mark.asyncio
async def test_analyze_performance_with_slow_query_and_lock():
    analyzer = TechLogAnalyzer()

    # Один медленный SQL и одна долгая блокировка
    events = [
        TechLogEvent(
            timestamp=(
                analyzer._determine_severity.__self__.__class__.__mro__[0]  # type: ignore[attr-defined]
                if False
                else analyzer.__class__.__mro__[0].__mro__[0]
            ),  # заглушка, не используется
            duration_ms=6000,
            event_type="DBMSSQL",
            process="rphost",
            user="User1",
            application="1CV8",
            event="Query",
            context="Report",
            sql="SELECT * FROM sales",
        ),
        TechLogEvent(
            timestamp=(
                analyzer.__class__.__mro__[0].__mro__[0]  # заглушка, не используется
                if False
                else analyzer.__class__.__mro__[0].__mro__[0]
            ),
            duration_ms=1000,
            event_type="TLOCK",
            process="rphost",
            user="User2",
            application="1CV8",
            event="Lock",
            context="Document.Write",
        ),
    ]

    log_data = {"events": events}

    result = await analyzer.analyze_performance(log_data)

    # Есть хотя бы одна performance issue по медленному запросу
    issues = result["performance_issues"]
    assert any(i.issue_type == "slow_query" for i in issues)
    # Анализ вернул summary с подсчётом критичных проблем
    assert "summary" in result
    assert isinstance(result["summary"]["total_issues"], int)


@pytest.mark.asyncio
async def test_generate_ai_recommendations_for_slow_query_issue():
    analyzer = TechLogAnalyzer()

    issues = [
        PerformanceIssue(
            issue_type="slow_query",
            severity="critical",
            description="Slow SQL",
            location="SELECT * FROM ...",
            metric_value=15000,
            threshold=3000,
            occurrences=10,
            recommendation="Use SQL Optimizer",
            auto_fix_available=True,
        )
    ]

    recs = await analyzer._generate_ai_recommendations(issues)

    assert recs, "Ожидаем хотя бы одну AI‑рекомендацию"
    sql_rec = next((r for r in recs if r["category"] == "SQL Performance"), None)
    assert sql_rec is not None
    assert "use_sql_optimizer" in sql_rec["action"]
