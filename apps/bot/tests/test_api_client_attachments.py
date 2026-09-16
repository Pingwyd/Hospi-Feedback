"""Tests for attachment fetch and upload query params on the bot API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from bot.api_client import ApiClientError, HospiApiClient


@pytest.mark.asyncio
async def test_fetch_attachment_bytes_uses_bearer_and_preview_path() -> None:
    response = httpx.Response(
        200,
        content=b"png-bytes",
        headers={"content-type": "image/png"},
        request=httpx.Request("GET", "http://api.test/x"),
    )
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.api_client.httpx.AsyncClient", return_value=mock_client):
        client = HospiApiClient(base_url="http://api.test")
        data, content_type = await client.fetch_attachment_bytes(
            token="session-token",
            preview_url="/api/reports/ticket/ABCD1234/attachments/a1",
        )

    assert data == b"png-bytes"
    assert content_type == "image/png"
    mock_client.get.assert_awaited_once()
    call_kwargs = mock_client.get.await_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer session-token"


@pytest.mark.asyncio
async def test_fetch_attachment_bytes_raises_on_404() -> None:
    response = httpx.Response(
        404,
        json={"error": {"code": "not_found", "message": "Attachment not found."}},
        request=httpx.Request("GET", "http://api.test/x"),
    )
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.api_client.httpx.AsyncClient", return_value=mock_client):
        client = HospiApiClient(base_url="http://api.test")
        with pytest.raises(ApiClientError) as exc_info:
            await client.fetch_attachment_bytes(
                token="session-token",
                preview_url="/api/reports/ticket/ABCD1234/attachments/a1",
            )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_fetch_attachment_bytes_passes_quality_query_param() -> None:
    response = httpx.Response(
        200,
        content=b"jpeg-bytes",
        headers={"content-type": "image/jpeg"},
        request=httpx.Request("GET", "http://api.test/x"),
    )
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.api_client.httpx.AsyncClient", return_value=mock_client):
        client = HospiApiClient(base_url="http://api.test")
        await client.fetch_attachment_bytes(
            token="session-token",
            preview_url="/api/reports/ticket/ABCD1234/attachments/a1",
            jpeg_quality=70,
        )

    call_kwargs = mock_client.get.await_args.kwargs
    assert call_kwargs["params"] == {"quality": "70"}


@pytest.mark.asyncio
async def test_fetch_attachment_bytes_surfaces_404_with_quality_param() -> None:
    response = httpx.Response(
        404,
        json={"error": {"code": "not_found", "message": "Attachment not found."}},
        request=httpx.Request("GET", "http://api.test/x"),
    )
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.api_client.httpx.AsyncClient", return_value=mock_client):
        client = HospiApiClient(base_url="http://api.test")
        with pytest.raises(ApiClientError) as exc_info:
            await client.fetch_attachment_bytes(
                token="session-token",
                preview_url="/api/reports/ticket/WRONG123/attachments/a1",
                jpeg_quality=70,
            )
    assert exc_info.value.status_code == 404
    assert mock_client.get.await_args.kwargs["params"] == {"quality": "70"}


@pytest.mark.asyncio
async def test_fetch_attachment_bytes_surfaces_415_with_invalid_quality() -> None:
    response = httpx.Response(
        415,
        json={
            "error": {
                "code": "unsupported_media_type",
                "message": "Unsupported delivery quality.",
            }
        },
        request=httpx.Request("GET", "http://api.test/x"),
    )
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.api_client.httpx.AsyncClient", return_value=mock_client):
        client = HospiApiClient(base_url="http://api.test")
        with pytest.raises(ApiClientError) as exc_info:
            await client.fetch_attachment_bytes(
                token="session-token",
                preview_url="/api/reports/ticket/ABCD1234/attachments/a1",
                jpeg_quality=55,
            )
    assert exc_info.value.status_code == 415


@pytest.mark.asyncio
async def test_upload_attachment_link_to_thread_query() -> None:
    response = httpx.Response(
        201,
        json={
            "id": "a1",
            "file_type": "image/jpeg",
            "uploaded_at": "2026-09-03T12:00:00+00:00",
            "message_id": "m1",
            "preview_url": "/api/reports/ticket/ABCD1234/attachments/a1",
        },
        request=httpx.Request("POST", "http://api.test/x"),
    )
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.api_client.httpx.AsyncClient", return_value=mock_client):
        client = HospiApiClient(base_url="http://api.test")
        result = await client.upload_attachment(
            token="session-token",
            ticket_code="ABCD1234",
            filename="photo.jpg",
            content_type="image/jpeg",
            data=b"jpeg",
            link_to_thread=True,
        )

    assert result["message_id"] == "m1"
    post_url = mock_client.post.await_args.args[0]
    assert post_url.endswith("/attachments?link_to_thread=true")


@pytest.mark.asyncio
async def test_upload_attachments_batch_posts_multipart_to_batch_path() -> None:
    response = httpx.Response(
        201,
        json={
            "message_id": "m-batch",
            "attachments": [
                {"id": "a1", "file_type": "image/jpeg"},
                {"id": "a2", "file_type": "image/jpeg"},
            ],
        },
        request=httpx.Request("POST", "http://api.test/x"),
    )
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.api_client.httpx.AsyncClient", return_value=mock_client):
        client = HospiApiClient(base_url="http://api.test")
        result = await client.upload_attachments_batch(
            token="session-token",
            ticket_code="ABCD1234",
            files=[
                ("one.jpg", b"1", "image/jpeg"),
                ("two.jpg", b"2", "image/jpeg"),
            ],
        )

    assert result["message_id"] == "m-batch"
    assert len(result["attachments"]) == 2
    post_url = mock_client.post.await_args.args[0]
    assert post_url.endswith("/attachments/batch")
    call_kwargs = mock_client.post.await_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer session-token"


@pytest.mark.asyncio
async def test_fetch_telegram_dashboard_stats_uses_bot_secret_and_chat_id() -> None:
    response = httpx.Response(
        200,
        json={"data": {"status_counts": {"new": 1}}},
        request=httpx.Request("GET", "http://api.test/x"),
    )
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.api_client.httpx.AsyncClient", return_value=mock_client):
        client = HospiApiClient(
            base_url="http://api.test",
            bot_service_secret="bot-secret",
        )
        result = await client.fetch_telegram_dashboard_stats(
            telegram_chat_id="123456789",
        )

    assert result["status_counts"]["new"] == 1
    call_kwargs = mock_client.request.await_args.kwargs
    assert call_kwargs["headers"]["X-Bot-Service-Secret"] == "bot-secret"
    assert "telegram_chat_id=123456789" in mock_client.request.await_args.args[1]
