import logging
from messenger.gateway import MessengerGateway

logger = logging.getLogger(__name__)


class TelegramAdapter(MessengerGateway):
    """Telegram REST adapter — implemented in S003."""

    def send(self, contact_id: str, message: str) -> None:
        raise NotImplementedError("TelegramAdapter.send — implemented in Sprint 003")

    def health_check(self) -> bool:
        logger.warning("TelegramAdapter not yet implemented (S003)")
        return False
