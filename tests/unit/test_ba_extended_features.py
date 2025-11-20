# [NEXUS IDENTITY] ID: -2625091860944473855 | DATE: 2025-11-19


import pytest

from src.ai.agents.business_analyst_agent_extended import \
    BusinessAnalystAgentExtended


@pytest.mark.asyncio
async def test_generate_process_model_basic():
    agent = BusinessAnalystAgentExtended()
    description = "Менеджер создаёт заказ. Бухгалтер проверяет оплату."

    result = await agent.generate_process_model(description)

    assert result["bpmn"]["metadata"]["steps"] >= 2
    assert result["metadata"]["ba_feature"] == "BA-03"
    assert "mermaid" in result


@pytest.mark.asyncio
async def test_design_kpi_blueprint_contains_sql():
    agent = BusinessAnalystAgentExtended()

    result = await agent.design_kpi_blueprint("Новая программа лояльности")

    assert result["ba_feature"] == "BA-04"
    assert result["kpis"]
    assert any("SELECT" in kpi["sql_draft"] for kpi in result["kpis"])


@pytest.mark.asyncio
async def test_build_traceability_and_risks_marks_uncovered():
    agent = BusinessAnalystAgentExtended()
    requirements = [
        {"id": "FR-001", "title": "Создание заказа"},
        {"id": "FR-002", "title": "Печать счёта"},
    ]
    test_cases = [{"id": "TC-1", "requirement_ids": ["FR-001"]}]

    result = await agent.build_traceability_and_risks(requirements, test_cases)

    assert result["ba_feature"] == "BA-05"
    trace = result["traceability"]
    assert trace["coverage_summary"]["total_requirements"] == 2
    assert "FR-002" in trace["uncovered_requirements"]
    assert any(r["requirement_id"] == "FR-002" for r in result["risk_register"])


@pytest.mark.asyncio
async def test_plan_and_sync_integrations_safe_offline():
    agent = BusinessAnalystAgentExtended()

    result = await agent.plan_and_sync_integrations(
        "BA summary",
        "Описание инициативы",
        targets=["jira", "confluence"],
    )

    assert result["ba_feature"] == "BA-06"
    assert "results" in result
    assert all("target" in r and "status" in r for r in result["results"])


def test_build_enablement_plan_structure():
    agent = BusinessAnalystAgentExtended()

    result = agent.build_enablement_plan("Scenario Hub")

    assert result["ba_feature"] == "BA-07"
    assert result["feature_name"] == "Scenario Hub"
    assert result["modules"]
    assert any(m["id"] == "howto" for m in result["modules"])
