# [NEXUS IDENTITY] ID: -2966874279956874591 | DATE: 2025-11-19

import pytest

from src.ai.agents.ai_issue_classifier_ml import MLIssueClassifier


@pytest.mark.asyncio
async def test_rule_based_classification_when_model_not_loaded():
    classifier = MLIssueClassifier()
    classifier.model_loaded = False  # гарантируем rule‑based режим

    result = await classifier.classify_issue(
        title="Ошибка в проде, сервер не работает",
        description="Критичная ошибка, prod down, нужно срочно починить",
    )

    assert result["type"] in {"bug", "feature", "task", "question"}
    assert result["priority"] in {"low", "medium", "high", "critical"}
    assert "confidence" in result
    assert "classifier" in result
