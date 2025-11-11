#!/usr/bin/env python3
"""Check AWS Budgets and send Slack alert if forecast exceeds threshold."""

from __future__ import annotations

import json
import os
from typing import Any

import boto3
import requests

BUDGET_NAMES = os.environ.get("AWS_BUDGET_NAMES", "").split(",")
WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


def notify(text: str) -> None:
    if not WEBHOOK_URL:
        return
    resp = requests.post(WEBHOOK_URL, json={"text": text}, timeout=10)
    resp.raise_for_status()


def check_budget(budgets_client: Any, account_id: str, budget_name: str) -> None:
    response = budgets_client.describe_budget(AccountId=account_id, BudgetName=budget_name)
    budget = response["Budget"]
    actual = float(budget["CalculatedSpend"]["ActualSpend"]["Amount"])
    forecast = float(budget["CalculatedSpend"].get("ForecastedSpend", {"Amount": 0})["Amount"])
    limit = float(budget["BudgetLimit"]["Amount"])

    if forecast > limit:
        notify(f"*AWS Budget Alert* `{budget_name}` forecast ${forecast:.2f} exceeds limit ${limit:.2f}")
    else:
        notify(f"AWS budget `{budget_name}` OK. Actual ${actual:.2f}, forecast ${forecast:.2f}, limit ${limit:.2f}")


def main() -> None:
    account_id = os.environ["AWS_ACCOUNT_ID"]
    budgets_client = boto3.client("budgets")
    names = [name.strip() for name in BUDGET_NAMES if name.strip()]
    if not names:
        raise RuntimeError("AWS_BUDGET_NAMES must list at least one budget")
    for name in names:
        check_budget(budgets_client, account_id, name)


if __name__ == "__main__":
    main()
