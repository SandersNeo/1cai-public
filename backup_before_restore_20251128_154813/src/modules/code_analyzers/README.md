# Code Analyzers Module

## Overview

The Code Analyzers module provides static analysis capabilities for various programming languages (Python, TypeScript, JavaScript). It detects potential issues, security vulnerabilities, and calculates code quality metrics.

## Architecture

Refactored from `src/api/code_analyzers.py` into Clean Architecture:

- **Domain**: Pydantic models (`models.py`) for analysis results (`AnalysisResult`, `AnalysisIssue`).
- **Services**:
  - `CodeAnalyzerService`: Facade service providing a unified interface.
  - `analyzers/`: Language-specific analyzer implementations:
    - `PythonAnalyzer`: Checks for bare excepts, print usage, eval/exec, secrets.
    - `TypeScriptAnalyzer`: Checks for `any` types, console.log, imports.
    - `JavaScriptAnalyzer`: Checks for `var`, `==`, `eval`.

## Features

- **Static Analysis**: Regex-based pattern matching for common issues.
- **Metrics**: Calculates complexity, maintainability, security, and performance scores.
- **Security Checks**: Detects hardcoded secrets and dangerous functions (eval/exec).
- **Best Practices**: Enforces language-specific best practices (e.g., `===` in JS, type safety in TS).

## Usage

The module is exposed via `src.modules.code_analyzers.services.analyzer_service`.
Legacy imports from `src.api.code_analyzers` are supported via a proxy file.

```python
from src.modules.code_analyzers.services.analyzer_service import CodeAnalyzerService

service = CodeAnalyzerService()
result = service.analyze_python(code_string)
```
