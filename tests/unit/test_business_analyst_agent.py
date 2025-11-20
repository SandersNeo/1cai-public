# [NEXUS IDENTITY] ID: -7610062127114210714 | DATE: 2025-11-19

from pathlib import Path

import pytest

docx_mod = pytest.importorskip("docx")
Document = docx_mod.Document

from src.ai.agents.business_analyst_agent_extended import \
    BusinessAnalystAgentExtended


@pytest.mark.asyncio
async def test_extract_requirements_from_file_docx(tmp_path: Path):
    doc_path = tmp_path / "requirements.docx"
    document = Document()
    document.add_paragraph(
        "Система должна позволять менеджеру создавать заказ клиента."
    )
    document.add_paragraph("Время отклика не должно превышать 3 секунд.")
    document.save(doc_path)

    agent = BusinessAnalystAgentExtended()
    result = await agent.extract_requirements_from_file(doc_path)

    assert result["functional_requirements"]
    assert result["summary"]["total_requirements"] >= 1
    assert result["summary"]["llm_used"] is False


@pytest.mark.asyncio
async def test_extract_requirements_llm_fallback():
    agent = BusinessAnalystAgentExtended()
    text = "Система должна отправлять уведомления. Обязательно хранить журнал действий."
    result = await agent.extract_requirements(text, "tz")

    assert result["summary"]["total_requirements"] >= 1
    assert result["summary"]["llm_used"] is False
