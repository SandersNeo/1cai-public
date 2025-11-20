# [NEXUS IDENTITY] ID: -7699302782527167215 | DATE: 2025-11-19

import json
from pathlib import Path
from subprocess import check_output

import pytest


@pytest.mark.unit
def test_print_scenario_decisions_cli_runs(tmp_path: Path):
    # Используем готовый пример ScenarioPlan
    from pathlib import Path as P

    repo_root = P(__file__).resolve().parents[2]
    plan_path = (
        repo_root
        / "docs"
        / "architecture"
        / "examples"
        / "scenario_plan_ba_dev_qa.json"
    )
    script_path = repo_root / "scripts" / "cli" / "print_scenario_decisions.py"

    output = check_output(
        ["python", str(script_path), str(plan_path), "A2_non_prod_changes"],
        encoding="utf-8",
    )
    data = json.loads(output)

    assert data["scenario_id"] == "plan-ba-dev-qa-EXTERNAL_DEMO"
    assert data["autonomy"] == "A2_non_prod_changes"
    assert isinstance(data["decisions"], dict)
    assert set(data["decisions"].values()) <= {"auto", "needs_approval", "forbidden"}
