from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


BULKSMSBD_CODE_MESSAGES: dict[str, str] = {
    "202": "SMS Submitted Successfully",
    "1002": "Sender ID is invalid or disabled",
    "1003": "Required SMS fields are missing",
    "1005": "SMS provider internal error",
    "1006": "SMS balance validity is not available",
    "1007": "Insufficient SMS balance",
    "1011": "SMS user ID was not found",
    "1012": "Masking SMS must be sent in Bengali",
    "1013": "Sender ID has no gateway for this API key",
    "1014": "Sender type name was not found for this API key",
    "1015": "Sender ID has no valid gateway for this API key",
    "1016": "Sender type active price info was not found",
    "1017": "Sender type price info was not found",
    "1018": "Account owner is disabled",
    "1019": "Sender type price is disabled",
    "1020": "Parent account was not found",
    "1021": "Parent active sender type price was not found",
    "1032": "Server IP is not whitelisted in BulkSMSBD",
}


@dataclass(frozen=True)
class BulkSmsResult:
    success: bool
    provider_code: str | None
    provider_message: str
    raw_response: str | dict[str, Any]
    recipients: list[str]
    dry_run: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BulkSmsBalanceResult:
    success: bool
    provider_code: str | None
    provider_message: str
    raw_response: str | dict[str, Any]
    balance: str | None
    dry_run: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_bd_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("00880"):
        digits = digits[2:]
    if digits.startswith("880"):
        normalized = digits
    elif digits.startswith("0"):
        normalized = f"88{digits}"
    elif digits.startswith("1") and len(digits) == 10:
        normalized = f"880{digits}"
    else:
        normalized = digits

    if not validate_bd_phone(normalized):
        raise ValueError("Invalid Bangladeshi mobile number")
    return normalized


def validate_bd_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("00880"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = f"88{digits}"
    if digits.startswith("1") and len(digits) == 10:
        digits = f"880{digits}"
    return bool(re.fullmatch(r"8801[3-9]\d{8}", digits))


class BulkSmsBdClient:
    def __init__(
        self,
        api_key: str | None,
        sender_id: str | None,
        base_url: str = "https://bulksmsbd.net/api/",
        timeout: int = 15,
        enabled: bool = False,
        dry_run: bool = True,
    ) -> None:
        self.api_key = api_key
        self.sender_id = sender_id
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.enabled = enabled
        self.dry_run = dry_run

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.sender_id)

    def send_sms(self, number: str, message: str) -> BulkSmsResult:
        return self.send_bulk_same_message([number], message)

    def send_bulk_same_message(self, numbers: list[str], message: str) -> BulkSmsResult:
        recipients = self._normalize_numbers(numbers)
        body = self._validate_message(message)
        if self._should_dry_run():
            logger.info("BulkSMSBD dry run: %s recipient(s), message=%s", len(recipients), self._mask_message(body))
            return BulkSmsResult(True, "DRY_RUN", "Dry run: SMS was not sent", {}, recipients, True)
        if not self.configured:
            return BulkSmsResult(False, None, "BulkSMSBD API key or sender ID is not configured", {}, recipients, False)

        return self._post_send(
            "smsapi",
            {
                "api_key": self.api_key,
                "type": "text",
                "number": ",".join(recipients),
                "senderid": self.sender_id,
                "message": body,
            },
            recipients,
        )

    def send_many_raw(self, messages: str) -> BulkSmsResult:
        raw_messages = self._validate_message(messages, max_length=10000)
        if self._should_dry_run():
            logger.info("BulkSMSBD many-to-many dry run: message payload length=%s", len(raw_messages))
            return BulkSmsResult(True, "DRY_RUN", "Dry run: many-to-many SMS was not sent", {}, [], True)
        if not self.configured:
            return BulkSmsResult(False, None, "BulkSMSBD API key or sender ID is not configured", {}, [], False)

        # TODO: Verify BulkSMSBD's exact `messages` serialization with a real provider sample before building objects here.
        return self._post_send(
            "smsapimany",
            {"api_key": self.api_key, "senderid": self.sender_id, "messages": raw_messages},
            [],
        )

    def get_balance(self) -> BulkSmsBalanceResult:
        if not self.api_key:
            return BulkSmsBalanceResult(False, None, "BulkSMSBD API key is not configured", {}, None, False)

        try:
            response = httpx.get(
                f"{self.base_url}getBalanceApi",
                params={"api_key": self.api_key},
                timeout=self.timeout,
            )
        except httpx.TimeoutException:
            return BulkSmsBalanceResult(False, None, "SMS provider timeout", {}, None, False)
        except httpx.HTTPError as exc:
            return BulkSmsBalanceResult(False, None, f"SMS provider unavailable: {exc}", {}, None, False)

        raw = response.text.strip()
        if response.status_code != 200:
            return BulkSmsBalanceResult(False, None, f"SMS provider HTTP {response.status_code}", raw, None, False)
        code = self._extract_code(raw)
        if code and code != "202":
            return BulkSmsBalanceResult(False, code, BULKSMSBD_CODE_MESSAGES.get(code, "SMS provider returned an error"), raw, None, False)
        return BulkSmsBalanceResult(True, code, "Balance check successful", raw, raw, False)

    def _post_send(self, endpoint: str, data: dict[str, Any], recipients: list[str]) -> BulkSmsResult:
        try:
            response = httpx.post(f"{self.base_url}{endpoint}", data=data, timeout=self.timeout)
        except httpx.TimeoutException:
            return BulkSmsResult(False, None, "SMS provider timeout", {}, recipients, False)
        except httpx.HTTPError as exc:
            return BulkSmsResult(False, None, f"SMS provider unavailable: {exc}", {}, recipients, False)

        raw = response.text.strip()
        if response.status_code != 200:
            return BulkSmsResult(False, None, f"SMS provider HTTP {response.status_code}", raw, recipients, False)
        code = self._extract_code(raw)
        success = code == "202"
        return BulkSmsResult(
            success,
            code,
            self._provider_message(code, raw),
            raw,
            recipients,
            False,
        )

    def _should_dry_run(self) -> bool:
        if not self.enabled or self.dry_run:
            return True
        return False

    @staticmethod
    def _normalize_numbers(numbers: list[str]) -> list[str]:
        if not numbers:
            raise ValueError("At least one recipient is required")
        recipients = [normalize_bd_phone(number) for number in numbers]
        return list(dict.fromkeys(recipients))

    @staticmethod
    def _validate_message(message: str, max_length: int = 918) -> str:
        body = (message or "").strip()
        if not body:
            raise ValueError("SMS message is required")
        if len(body) > max_length:
            raise ValueError(f"SMS message is too long. Maximum length is {max_length} characters")
        return body

    @staticmethod
    def _extract_code(raw_response: str) -> str | None:
        text = (raw_response or "").strip()
        match = re.search(r"\b(202|10\d{2})\b", text)
        return match.group(1) if match else None

    @staticmethod
    def _provider_message(code: str | None, raw_response: str) -> str:
        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            error_message = str(payload.get("error_message") or "").strip()
            success_message = str(payload.get("success_message") or "").strip()
            if error_message:
                return error_message
            if success_message:
                return success_message
        if code in BULKSMSBD_CODE_MESSAGES:
            return BULKSMSBD_CODE_MESSAGES[code]
        if "success" in raw_response.lower() or "submitted" in raw_response.lower():
            return "SMS submitted successfully"
        return "SMS provider returned an unknown response"

    @staticmethod
    def _mask_message(message: str) -> str:
        return re.sub(r"\b\d{4,8}\b", "****", message)[:160]
