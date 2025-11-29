# [NEXUS IDENTITY] ID: -4326263936345997538 | DATE: 2025-11-19

#!/usr/bin/env python3
"""Sync selected AWS Secrets Manager entries into Vault KV."""

from __future__ import annotations

import argparse
import json
import os

import boto3
import hvac


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync AWS secrets to Vault")
    parser.add_argument("secrets", nargs="+", help="AWS Secrets Manager ARNs or names")
    parser.add_argument(
        "--vault-path",
        required=True,
        help="Vault KV path prefix (e.g. secret/data/1cai/aws)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    session = boto3.session.Session()
    client = session.client("secretsmanager")

    vault_client = hvac.Client(url=os.environ["VAULT_ADDR"], token=os.environ["VAULT_TOKEN"])

    for secret in args.secrets:
        response = client.get_secret_value(SecretId=secret)
        payload = response.get("SecretString") or response.get("SecretBinary", b"").decode()
        data = json.loads(payload)

        name = secret.split(":")[-1].split("/")[-1]
        vault_path = f"{args.vault_path}/{name}"
        print(f"Sync {secret} -> {vault_path}")
        vault_client.secrets.kv.v2.create_or_update_secret(path=vault_path, secret=data)


if __name__ == "__main__":
    main()
