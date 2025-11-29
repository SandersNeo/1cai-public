# [NEXUS IDENTITY] ID: 7244191789325133853 | DATE: 2025-11-19

#!/usr/bin/env python3
"""Sync Azure Key Vault secrets into Vault KV."""

from __future__ import annotations

import argparse
import os

import hvac
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Azure Key Vault secrets to Vault")
    parser.add_argument("vault_name", help="Azure Key Vault name")
    parser.add_argument("secrets", nargs="+", help="Secret names in Key Vault")
    parser.add_argument("--vault-path", required=True, help="Vault KV path prefix")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    credential = ClientSecretCredential(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        client_id=os.environ["AZURE_CLIENT_ID"],
        client_secret=os.environ["AZURE_CLIENT_SECRET"],
    )
    keyvault_uri = f"https://{args.vault_name}.vault.azure.net"
    client = SecretClient(vault_url=keyvault_uri, credential=credential)

    vault_client = hvac.Client(url=os.environ["VAULT_ADDR"], token=os.environ["VAULT_TOKEN"])

    for name in args.secrets:
        secret = client.get_secret(name)
        path = f"{args.vault_path}/{name}"
        vault_client.secrets.kv.v2.create_or_update_secret(path=path, secret={"value": secret.value})
        print(f"Synced {name} -> {path}")


if __name__ == "__main__":
    main()
