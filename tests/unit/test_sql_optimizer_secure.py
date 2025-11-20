# [NEXUS IDENTITY] ID: -6221341441176095839 | DATE: 2025-11-19

from datetime import timedelta

from src.ai.sql_optimizer_secure import SQLOptimizerSecure


def test_optimize_query_blocks_injection():
    optimizer = SQLOptimizerSecure()
    sql = "SELECT * FROM users WHERE name = 'admin' OR '1'='1'"

    result = optimizer.optimize_query(sql)

    assert result.get("blocked") is True
    assert "SQL injection" in result.get("error", "")


def test_optimize_query_returns_token_for_safe_select(monkeypatch):
    optimizer = SQLOptimizerSecure()

    def fake_optimize(sql: str) -> str:
        return "SELECT id FROM users"

    def fake_safety(sql: str):
        return {
            "safe_for_auto_execute": True,
            "has_dangerous_ops": False,
            "is_read_only": True,
            "operations": ["SELECT"],
            "requires_dba_approval": False,
            "warning": None,
        }

    monkeypatch.setattr(optimizer, "_optimize_with_ai", fake_optimize)
    monkeypatch.setattr(optimizer, "_analyze_query_safety", fake_safety)

    result = optimizer.optimize_query("SELECT id FROM users")

    assert result["success"] is True
    assert result["token"] in optimizer._pending_queries
    assert result["can_execute"] is True


def test_execute_approved_query_expiration(monkeypatch):
    optimizer = SQLOptimizerSecure()

    def fake_optimize(sql: str) -> str:
        return "SELECT id FROM users"

    def fake_safety(sql: str):
        return {
            "safe_for_auto_execute": True,
            "has_dangerous_ops": False,
            "is_read_only": True,
            "operations": ["SELECT"],
            "requires_dba_approval": False,
            "warning": None,
        }

    monkeypatch.setattr(optimizer, "_optimize_with_ai", fake_optimize)
    monkeypatch.setattr(optimizer, "_analyze_query_safety", fake_safety)

    res = optimizer.optimize_query("SELECT id FROM users")
    token = res["token"]

    # искусственно устарим запись
    optimizer._pending_queries[token]["created_at"] -= timedelta(minutes=31)

    exec_res = optimizer.execute_approved_query(token, approved_by_user="dba")

    assert exec_res["blocked"] is True
    assert "expired" in exec_res["error"]
