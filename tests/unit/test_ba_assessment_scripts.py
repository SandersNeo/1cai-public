# [NEXUS IDENTITY] ID: -4463638147250294504 | DATE: 2025-11-19

import json
from pathlib import Path

from scripts.ba_assessment.generate_forms import generate_assessment
from scripts.ba_scenarios.sync_templates import sync_templates
from src.ai.knowledge.ba_knowledge import BAKnowledgeBase


def _write_snapshot(tmp_path: Path, collector: str, payload: dict) -> None:
    collector_dir = tmp_path / collector / "20250101"
    collector_dir.mkdir(parents=True, exist_ok=True)
    (collector_dir / f"{collector}_snapshot.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def test_generate_assessment_uses_latest_snapshot(tmp_path: Path):
    job_payload = {
        "collector": "job_market",
        "records": [
            {"platform": "hh.ru", "skills": ["1C", "Power BI"]},
            {"platform": "linkedin", "skills": ["SQL", "Power BI"]},
        ],
    }
    conf_payload = {
        "collector": "conference_digest",
        "records": [
            {
                "event": "Analyst Days",
                "topic": "AI & BA",
                "link": "https://example.com",
            },
        ],
    }
    _write_snapshot(tmp_path, "job_market", job_payload)
    _write_snapshot(tmp_path, "conference_digest", conf_payload)

    output_path = tmp_path / "assessment.md"
    generate_assessment(input_dir=tmp_path, output_path=output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "Power BI" in content
    assert "Analyst Days" in content


def test_sync_templates_updates_catalog_and_template(tmp_path: Path):
    job_payload = {
        "collector": "job_market",
        "records": [
            {"platform": "hh.ru", "skills": ["BPMN"]},
        ],
    }
    usage_payload = {
        "collector": "internal_usage",
        "records": [
            {"feature": "discovery_run_session", "timestamp": "2025-01-01T00:00:00Z"},
        ],
    }
    _write_snapshot(tmp_path, "job_market", job_payload)
    _write_snapshot(tmp_path, "internal_usage", usage_payload)

    template_path = tmp_path / "template.md"
    template_path.write_text("# Template\n", encoding="utf-8")
    catalog_path = tmp_path / "generated" / "catalog.json"

    sync_templates(
        input_dir=tmp_path,
        template_path=template_path,
        catalog_output=catalog_path,
    )

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert catalog["tracks"]
    assert catalog["tracks"][0]["skills"]

    template_content = template_path.read_text(encoding="utf-8")
    assert "Последнее обновление" in template_content


def test_ba_knowledge_base_reads_snapshots(tmp_path: Path):
    job_payload = {
        "collector": "job_market",
        "records": [
            {"platform": "hh.ru", "skills": ["SQL", "Power BI"]},
            {"platform": "hh.ru", "skills": ["Power BI"]},
        ],
    }
    conf_payload = {
        "collector": "conference_digest",
        "records": [
            {
                "event": "BA Summit",
                "topic": "Generative AI",
                "link": "https://example.com",
            },
        ],
    }
    usage_payload = {
        "collector": "internal_usage",
        "records": [
            {
                "feature": "discovery_run_session",
                "count": 10,
                "timestamp": "2025-01-01T00:00:00Z",
            }
        ],
    }
    _write_snapshot(tmp_path, "job_market", job_payload)
    _write_snapshot(tmp_path, "conference_digest", conf_payload)
    _write_snapshot(tmp_path, "internal_usage", usage_payload)

    kb = BAKnowledgeBase(base_dir=tmp_path)
    top_skills = kb.get_top_market_skills()
    topics = kb.get_conference_topics()
    usage = kb.get_usage_highlights()

    assert top_skills and top_skills[0]["skill"] == "Power BI"
    assert topics and topics[0]["event"] == "BA Summit"
    assert usage and usage[0]["feature"] == "discovery_run_session"
