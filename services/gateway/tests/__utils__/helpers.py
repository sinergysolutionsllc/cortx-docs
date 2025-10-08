"""
Test helper functions for Gateway service tests
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import httpx


def assert_validation_response_structure(response_data: dict[str, Any]):
    """Assert that response has valid validation response structure"""
    assert "request_id" in response_data
    assert "domain" in response_data
    assert "success" in response_data
    assert "summary" in response_data
    assert "failures" in response_data
    assert "mode_requested" in response_data
    assert "mode_executed" in response_data
    assert "completed_at" in response_data

    # Check summary structure
    summary = response_data["summary"]
    assert "total_records" in summary
    assert "records_processed" in summary
    assert "total_failures" in summary
    assert "processing_time_ms" in summary


def assert_failure_structure(failure: dict[str, Any]):
    """Assert that failure has valid structure"""
    assert "rule_id" in failure
    assert "severity" in failure
    assert "field" in failure
    assert "message" in failure
    assert "value" in failure


def assert_audit_called_with_action(mock_audit_emit: AsyncMock, action: str):
    """Assert that audit was called with specific action"""
    assert mock_audit_emit.called
    call_args = mock_audit_emit.call_args

    if call_args:
        audit_event = call_args[0][0]  # First positional argument
        assert audit_event.action == action


def mock_httpx_response(
    status_code: int = 200,
    json_data: dict[str, Any] = None,
    content: bytes = None,
    headers: dict[str, str] = None,
) -> Mock:
    """Create a mock httpx.Response"""
    if json_data is None:
        json_data = {"status": "ok"}

    if content is None:
        import json

        content = json.dumps(json_data).encode()

    if headers is None:
        headers = {"content-type": "application/json"}

    response = Mock(spec=httpx.Response)
    response.status_code = status_code
    response.content = content
    response.headers = headers
    response.json = Mock(return_value=json_data)

    return response


def mock_async_httpx_client(
    response_status: int = 200, response_data: dict[str, Any] = None
) -> AsyncMock:
    """Create a mock httpx.AsyncClient"""
    if response_data is None:
        response_data = {"status": "ok"}

    mock_client = AsyncMock()
    mock_response = mock_httpx_response(response_status, response_data)

    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    return mock_client


def extract_bearer_token(auth_header: str) -> str:
    """Extract token from Authorization header"""
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return ""


def assert_proxy_headers_forwarded(mock_client: AsyncMock, expected_headers: list[str]):
    """Assert that specific headers were forwarded in proxy request"""
    assert mock_client.request.called
    call_kwargs = mock_client.request.call_args.kwargs

    if "headers" in call_kwargs:
        headers = call_kwargs["headers"]
        for header in expected_headers:
            assert header.lower() in [h.lower() for h in headers.keys()]


def create_multipart_form_data(
    files: dict[str, tuple[str, bytes, str]] = None, data: dict[str, Any] = None
) -> dict[str, Any]:
    """Create multipart form data for testing file uploads"""
    form = {}

    if files:
        for key, (filename, content, content_type) in files.items():
            file_obj = Mock()
            file_obj.filename = filename
            file_obj.read = AsyncMock(return_value=content)
            file_obj.content_type = content_type
            file_obj.file = Mock()
            form[key] = file_obj

    if data:
        form.update(data)

    return form
