import logging

import requests

from messenger.gateway import MessengerGateway

logger = logging.getLogger(__name__)

_TIMEOUT = 10


class TelegramAdapter(MessengerGateway):

    def __init__(self, token: str) -> None:
        self._token = token

    def _url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self._token}/{method}"

    def send(self, contact_id: str, message: str) -> None:
        try:
            resp = requests.post(
                self._url("sendMessage"),
                json={"chat_id": contact_id, "text": message},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Telegram send failed: {type(exc).__name__}") from None
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram error: {data.get('description', data)}")

    def health_check(self) -> bool:
        try:
            resp = requests.get(self._url("getMe"), timeout=_TIMEOUT)
            resp.raise_for_status()
            return resp.json().get("ok", False)
        except Exception as exc:
            logger.warning("Telegram health check failed: %s", type(exc).__name__)
            return False
