# 1C Git Synchronization Module

## Purpose
This module is responsible for two-way synchronization between the 1C:Enterprise platform and a Git repository (Gitea).

## Architecture (Clean Architecture)
- **Domain**: `models.py` defines `GitCommit` and `SyncStatus`.
- **Services**: `service.py` contains the business logic for checking changes, exporting configuration, and pushing to Git.
- **API**: (Planned) REST endpoints to trigger sync manually.
- **Repositories**: (Planned) Abstraction for Git command line or API interactions.

## Usage
Run the service as a standalone process or container:
```bash
python src/modules/git_sync/service.py
```

## Configuration
Environment variables:
- `GIT_SERVER_URL`: URL of the Gitea server.
- `GIT_USER`: Username for Git authentication.
- `GIT_PASSWORD`: Password for Git authentication.
