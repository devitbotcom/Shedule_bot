import logging
from messenger.gateway import MessengerGateway

logger = logging.getLogger(__name__)


class ViberAdapter(MessengerGateway):
    """Viber REST adapter — P2, deferred pending API verification."""

    def send(self, contact_id: str, message: str) -> None:
        raise NotImplementedError("ViberAdapter — deferred to P2")

    def health_check(self) -> bool:
        logger.warning("ViberAdapter is P2 — not implemented")
        return False
