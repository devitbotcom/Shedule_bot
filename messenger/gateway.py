from abc import ABC, abstractmethod


class MessengerGateway(ABC):

    @abstractmethod
    def send(self, contact_id: str, message: str) -> None:
        """Send message to contact_id. Raises on failure."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if messenger API is reachable and token is valid."""
