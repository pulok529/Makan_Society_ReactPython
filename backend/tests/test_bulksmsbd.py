from __future__ import annotations

import httpx
import pytest

from app.modules.messaging.bulksmsbd import BulkSmsBdClient, normalize_bd_phone, validate_bd_phone


def test_normalize_bd_phone_accepts_common_formats() -> None:
    assert normalize_bd_phone("01712345678") == "8801712345678"
    assert normalize_bd_phone("+8801712345678") == "8801712345678"
    assert normalize_bd_phone("8801712345678") == "8801712345678"


def test_invalid_phone_rejection() -> None:
    assert not validate_bd_phone("12345")
    with pytest.raises(ValueError):
        normalize_bd_phone("12345")


def test_provider_code_mapping_insufficient_balance() -> None:
    client = BulkSmsBdClient("key", "sender", enabled=True, dry_run=False)
    assert client._provider_message("1007", "1007") == "Insufficient SMS balance"


def test_dry_run_send_does_not_call_provider() -> None:
    client = BulkSmsBdClient(None, None, enabled=False, dry_run=True)
    result = client.send_sms("01712345678", "Hello")
    assert result.success is True
    assert result.dry_run is True
    assert result.recipients == ["8801712345678"]


def test_successful_mocked_provider_response_202(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args, **kwargs):
        return httpx.Response(200, text="202")

    monkeypatch.setattr(httpx, "post", fake_post)
    client = BulkSmsBdClient("key", "sender", enabled=True, dry_run=False)
    result = client.send_sms("01712345678", "Hello")
    assert result.success is True
    assert result.provider_code == "202"


def test_insufficient_balance_response_1007(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args, **kwargs):
        return httpx.Response(200, text="1007")

    monkeypatch.setattr(httpx, "post", fake_post)
    client = BulkSmsBdClient("key", "sender", enabled=True, dry_run=False)
    result = client.send_sms("01712345678", "Hello")
    assert result.success is False
    assert result.provider_code == "1007"
    assert result.provider_message == "Insufficient SMS balance"


def test_timeout_network_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "post", fake_post)
    client = BulkSmsBdClient("key", "sender", enabled=True, dry_run=False)
    result = client.send_sms("01712345678", "Hello")
    assert result.success is False
    assert result.provider_message == "SMS provider timeout"


def test_bulk_same_message_validates_every_number() -> None:
    client = BulkSmsBdClient("key", "sender", enabled=False, dry_run=True)
    with pytest.raises(ValueError):
        client.send_bulk_same_message(["01712345678", "123"], "Hello")
