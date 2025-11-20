# [NEXUS IDENTITY] ID: -4365017696736944451 | DATE: 2025-11-19

"""
Unit tests for error handling
Best Practices: Test all error scenarios
"""

import pytest
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from src.utils.error_handling import (APIError, ErrorCategory, ErrorCode,
                                      general_exception_handler,
                                      http_exception_handler,
                                      validation_exception_handler)


@pytest.mark.asyncio
async def test_api_error_to_dict():
    """Test APIError conversion to dictionary"""
    error = APIError(
        status_code=400,
        error_code=ErrorCode.INVALID_INPUT,
        message="Invalid input",
        category=ErrorCategory.VALIDATION,
        details={"field": "email"},
        request_id="req-123",
    )

    error_dict = error.to_dict()

    assert "error" in error_dict
    assert error_dict["error"]["code"] == ErrorCode.INVALID_INPUT
    assert error_dict["error"]["message"] == "Invalid input"
    assert error_dict["error"]["category"] == ErrorCategory.VALIDATION
    assert error_dict["error"]["request_id"] == "req-123"


@pytest.mark.asyncio
async def test_http_exception_handler_404():
    """Test HTTP exception handler for 404"""
    request = Request({"type": "http", "method": "GET", "path": "/test"})
    request.state.request_id = "req-123"

    exc = HTTPException(status_code=404, detail="Not found")

    response = await http_exception_handler(request, exc)

    assert response.status_code == 404
    assert response.body is not None
    # Check JSON response structure
    import json

    body = json.loads(response.body)
    assert body["error"]["code"] == ErrorCode.RESOURCE_NOT_FOUND


@pytest.mark.asyncio
async def test_http_exception_handler_401():
    """Test HTTP exception handler for 401"""
    request = Request({"type": "http", "method": "GET", "path": "/test"})
    request.state.request_id = "req-123"

    exc = HTTPException(status_code=401, detail="Unauthorized")

    response = await http_exception_handler(request, exc)

    assert response.status_code == 401
    import json

    body = json.loads(response.body)
    assert body["error"]["code"] == ErrorCode.INVALID_TOKEN
    assert body["error"]["category"] == ErrorCategory.AUTHENTICATION


@pytest.mark.asyncio
async def test_validation_exception_handler():
    """Test validation exception handler"""
    request = Request({"type": "http", "method": "POST", "path": "/test"})
    request.state.request_id = "req-123"

    errors = [
        {
            "loc": ("body", "email"),
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]
    exc = RequestValidationError(errors)

    response = await validation_exception_handler(request, exc)

    assert response.status_code == 422
    import json

    body = json.loads(response.body)
    assert body["error"]["code"] == ErrorCode.INVALID_INPUT
    assert "validation_errors" in body["error"]["details"]


@pytest.mark.asyncio
async def test_general_exception_handler():
    """Test general exception handler"""
    request = Request({"type": "http", "method": "GET", "path": "/test"})
    request.state.request_id = "req-123"

    exc = ValueError("Something went wrong")

    response = await general_exception_handler(request, exc)

    assert response.status_code == 500
    import json

    body = json.loads(response.body)
    assert body["error"]["code"] == ErrorCode.INTERNAL_SERVER_ERROR
    # Should not expose internal error details
    assert "Something went wrong" not in body["error"]["message"]
