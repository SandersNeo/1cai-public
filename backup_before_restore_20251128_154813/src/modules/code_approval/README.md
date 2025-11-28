# Code Approval Module

## Overview

The Code Approval module provides a human-in-the-loop approval process for AI-generated code. It ensures that all code suggestions are reviewed and approved by a user before being applied to the codebase.

## Architecture

Refactored from `src/api/code_approval.py` into Clean Architecture:

- **Domain**: Pydantic models (`models.py`) for requests (`CodeGenerationRequest`, `CodeApprovalRequest`, etc.).
- **Services**:
  - `CodeApprovalService`: Encapsulates logic for interacting with the `DeveloperAISecure` agent. Handles code generation, preview, approval, rejection, and bulk operations.
- **API**: FastAPI routes (`routes.py`) exposing endpoints.

## Features

- **Code Generation**: Generates code suggestions based on prompts.
- **Preview**: Allows users to preview suggestions before approval.
- **Approval**: Applies approved suggestions to the codebase.
- **Bulk Approval**: Supports approving multiple safe suggestions at once.
- **Rejection**: Allows users to reject suggestions.
- **Pending Suggestions**: Retrieves a list of suggestions waiting for review.

## Usage

The module is exposed via `src.modules.code_approval.api.routes`.
Legacy imports from `src.api.code_approval` are supported via a proxy file.
