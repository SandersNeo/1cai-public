# [NEXUS IDENTITY] ID: 1339118493824722792 | DATE: 2025-11-19

import asyncio

from src.ai.agents.business_analyst_agent_extended import BPMNGenerator


def test_mermaid_sanitizes_steps():
    generator = BPMNGenerator()
    malicious_steps = [
        "Valid [Step] --> HACK",
        "Second\nLine<script>alert(1)</script>",
    ]

    result = asyncio.run(generator.generate_bpmn(".".join(malicious_steps)))
    mermaid = result["mermaid"]

    assert " --> HACK" not in mermaid
    assert "<script" not in mermaid
    assert mermaid.count("-->") == len(malicious_steps)


def test_bpmn_elements_escape_html():
    generator = BPMNGenerator()
    description = "Шаг: <script>alert(1)</script>"

    result = asyncio.run(generator.generate_bpmn(description))
    elements = result["bpmn"]["elements"]

    assert elements[0]["name"] == "Шаг: &lt;script&gt;alert(1)&lt;/script&gt;"
    assert elements[0]["raw_name"] == "Шаг: <script>alert(1)</script>"
