# Инфраструктурный стек 1C AI Stack

Этот каталог содержит артефакты для быстрого развёртывания современной DevOps-инфраструктуры проекта: локальный Kubernetes (kind), Helm chart приложения, Terraform конфигурации и CI/CD pipeline (Jenkins/GitLab).

## 1. Локальный Kubernetes (kind)

- Конфигурация: `kind/cluster.yaml` — создаёт кластер `1cai-devops` с одним control-plane и двумя worker-нодами, пробрасывая порты 8080/8443.
- Запуск:
  ```bash
  kind create cluster --config infrastructure/kind/cluster.yaml
  kubectl cluster-info --context kind-1cai-devops
  ```
- После запуска устанавливаем ingress-nginx, cert-manager, argo-rollouts (по мере необходимости).

## 2. Helm chart

- Каталог: `helm/1cai-stack/`
- Состав:
  - `Chart.yaml` — метаданные чартa.
  - `values.yaml` — настройки API, MCP, observability, secret store (Vault).
  - `templates/` — Deployment/Service/Ingress/ServiceAccount и MCP.
- Деплой в кластер:
  ```bash
  helm upgrade --install 1cai infrastructure/helm/1cai-stack \
    --namespace 1cai --create-namespace \
    -f infrastructure/helm/1cai-stack/values.yaml
  ```

## 3. Observability stack

- Каталог: `helm/observability-stack/` — Prometheus + Loki + Tempo + Grafана + OTEL Collector + Promtail.
- Деплой:
  ```bash
  make helm-observability
  # или напрямую
  helm upgrade --install observability infrastructure/helm/observability-stack \
    --namespace observability --create-namespace \
    -f infrastructure/helm/observability-stack/values.yaml
  ```
- После установки: Grafana доступна через сервис `observability-stack-grafana` (порт 3000). Default пароль — admin/admin (смените через UI). Datasource’ы и дашборды создаются автоматически.
- OTEL Collector — сервис `observability-stack-otel-collector` (порты 4317/4318/9464). Перенастройте приложения на экспорт трейс/метрик через OTLP.

## 4. Terraform

- Файлы: `terraform/providers.tf`, `main.tf`, `variables.tf`, `outputs.tf`.
- Назначение: создавать namespace и устанавливать Helm chart через Terraform (подходит для GitOps пайплайна).
- Пример использования:
  ```bash
  cd infrastructure/terraform
  terraform init
  terraform apply -var="kubeconfig_path=$HOME/.kube/config" -var="kubeconfig_context=kind-1cai-devops"
  ```
- При необходимости добавьте backend (S3/Remote) и отдельные workspace для stage/prod.

## 4. CI/CD

### Jenkins (пример Jenkinsfile)
- Расположение: `jenkins/Jenkinsfile`
- Pipeline включает стадии: `lint`, `tests`, `build-image`, `security-scan`, `deploy-kind`, `deploy-k8s`.
- Требуемые credentials: `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`, `VAULT_TOKEN`, `KUBECONFIG`.

### GitLab CI (пример `.gitlab-ci.yml`)
- Расположение: `gitlab/.gitlab-ci.yml`
- Описывает аналогичный pipeline с использованием GitLab registry и environments.

## 5. Secret Store & Vault

- Значения `values.yaml` предполагают использование HashiCorp Vault (адрес `vault.vault:8200`, роль `1cai-app`).
- Храните Vault token/role в секретах CI (`VAULT_TOKEN`, `VAULT_ROLE_ID`).

## 6. Следующие шаги

- Настроить Argo CD/Flux для GitOps.
- Добавить Terraform модули для managed Kubernetes (EKS/AKS/GKE).
- Подготовить Helm chart для observability стека (`prometheus`, `loki`, `tempo`, `grafana`).
- Автоматизировать создание Vault policies и secrets.
