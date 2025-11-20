# [NEXUS IDENTITY] ID: 2733263434009906938 | DATE: 2025-11-19

import json
from pathlib import Path

import pytest

from scripts.ba_integration.sync_artifact import (parse_args, sync_artifact,
                                                  sync_artifact_from_path)


class DummyConnector:
    def __init__(self) -> None:
        self.calls = []

    async def sync(self, artefact, targets):
        self.calls.append((artefact, targets))
        return {"ok": True, "targets": targets}

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_sync_artifact_uses_connector():
    artefact = {"type": "roadmap", "metadata": {"summary": "Sync"}}
    connector = DummyConnector()
    result = await sync_artifact(artefact, ["jira"], connector=connector)
    assert result["ok"] is True
    assert connector.calls[0][1] == ["jira"]


def test_sync_artifact_from_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    artefact_path = tmp_path / "artefact.json"
    artefact_path.write_text(json.dumps({"type": "deck"}), encoding="utf-8")
    connector = DummyConnector()
    monkeypatch.setattr(
        "scripts.ba_integration.sync_artifact.IntegrationConnector",
        lambda: connector,
    )
    result = sync_artifact_from_path(artefact_path, ["confluence"])
    assert result["ok"] is True
    assert connector.calls[0][1] == ["confluence"]


def test_parse_args_defaults():
    args = parse_args(["artefact.json"])
    assert args.artefact.name == "artefact.json"
    assert args.targets == ["jira", "confluence"]
