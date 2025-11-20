# [NEXUS IDENTITY] ID: -3774406727551664283 | DATE: 2025-11-19

import pytest

from src.ai.agents.ai_issue_classifier import AIIssueClassifier


@pytest.mark.asyncio
async def test_classify_issue_slow_query_pattern():
    classifier = AIIssueClassifier()

    issue = {
        "type": "slow_query",
        "sql": "SELECT * FROM large_table",
        "duration_ms": 15000,
        "severity": "critical",
        "context": "Report generation",
    }

    result = await classifier.classify_issue(issue)

    assert result.category == "sql_performance"
    assert result.auto_fix_available is True
    assert result.confidence > 0.5


@pytest.mark.asyncio
async def test_classify_issue_memory_leak_context():
    classifier = AIIssueClassifier()

    issue = {
        "type": "performance_issue",
        "duration_ms": 1000,
        "severity": "medium",
        "context": "Possible memory leak detected in long running job",
    }

    result = await classifier.classify_issue(issue)

    assert result.category in {"memory_leak", "sql_performance"}
    assert isinstance(result.similar_cases, int)
