#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)
POLICY_DIR="$ROOT_DIR/policy"
HELM_DIR="$ROOT_DIR/infrastructure/helm"
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

log() {
  printf '[policy] %s\n' "$*"
}

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[policy] missing dependency: $1" >&2
    exit 1
  fi
}

require conftest
require helm
require semgrep

log "rendering Helm templates for 1cai-stack"
helm template policy-test "$HELM_DIR/1cai-stack" \
  --values "$HELM_DIR/1cai-stack/values.yaml" > "$TEMP_DIR/1cai-stack.yaml"

log "rendering Helm templates for observability-stack"
helm template policy-observability "$HELM_DIR/observability-stack" \
  --values "$HELM_DIR/observability-stack/values.yaml" > "$TEMP_DIR/observability-stack.yaml"

log "running Conftest policies"
conftest test "$TEMP_DIR/1cai-stack.yaml" --policy "$POLICY_DIR/kubernetes"
conftest test "$TEMP_DIR/observability-stack.yaml" --policy "$POLICY_DIR/kubernetes"
conftest test "$ROOT_DIR/infrastructure/kind/cluster.yaml" --policy "$POLICY_DIR/kubernetes"

if [ -d "$ROOT_DIR/infrastructure/terraform" ]; then
  log "validating Terraform format"
  (cd "$ROOT_DIR/infrastructure/terraform" && terraform fmt -check)
fi

log "running Semgrep security profile"
semgrep --config "$ROOT_DIR/security/semgrep.yml" --error --quiet

log "policy checks completed"
