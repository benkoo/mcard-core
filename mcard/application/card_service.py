"""
Application service for card management.
"""
from typing import Any, List, Optional
from ..domain.models.card import MCard
from ..domain.models.protocols import CardRepository, ContentTypeService
from ..domain.models.exceptions import ValidationError

class CardService:
    """Application service for card management."""

    def __init__(
        self,
        repository: CardRepository,
        content_service: ContentTypeService
    ):
        self._repository = repository
        self._content_service = content_service

    async def create_card(self, content: Any) -> MCard:
        """Create a new card."""
        if not self._content_service.validate_content(content):
            raise ValidationError("Invalid content type")
        
        card = MCard(content=content)
        await self._repository.save(card)
        return card

    async def get_card(self, hash: str) -> Optional[MCard]:
        """Retrieve a card by its hash."""
        return await self._repository.get(hash)

    async def get_all_cards(self) -> List[MCard]:
        """Retrieve all cards."""
        return await self._repository.get_all()

    async def delete_card(self, hash: str) -> None:
        """Delete a card by its hash."""
        await self._repository.delete(hash)

    def get_content_type(self, content: Any) -> str:
        """Get content type for the given content."""
        return self._content_service.detect_type(content)
