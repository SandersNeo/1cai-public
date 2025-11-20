# [NEXUS IDENTITY] ID: -6447429635531186042 | DATE: 2025-11-19

import json
from dataclasses import asdict
from pathlib import Path

from jsonschema import Draft202012Validator

from src.ai.scenario_examples import (
    example_ba_dev_qa_scenario,
    example_dr_rehearsal_scenario,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs" / "architecture" / "SCENARIO_DSL_SCHEMA.json"
EXTERNAL_PLAN_PATH = (
    ROOT / "docs" / "architecture" / "examples" / "scenario_plan_ba_dev_qa.json"
)


def _load_schema():
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _plan_to_dict(plan):
    data = asdict(plan)
    data.setdefault("version", "1.0.0")
    data.setdefault("spec", "scenario-dsl/v1")
    return data


def test_example_scenarios_conform_to_schema():
    schema = _load_schema()
    validator = Draft202012Validator(schema)

    # Внутренние примеры (Python dataclasses)
    for plan in (
        example_ba_dev_qa_scenario("DEMO_FEATURE"),
        example_dr_rehearsal_scenario("vault"),
    ):
        data = _plan_to_dict(plan)
        errors = list(validator.iter_errors(data))
        assert not errors, f"Schema validation errors: {[e.message for e in errors]}"

    # Внешний JSON-пример (как бы из сторонней системы)
    with EXTERNAL_PLAN_PATH.open("r", encoding="utf-8") as f:
        external_data = json.load(f)
    errors = list(validator.iter_errors(external_data))
    assert (
        not errors
    ), f"External ScenarioPlan example violates schema: {[e.message for e in errors]}"
