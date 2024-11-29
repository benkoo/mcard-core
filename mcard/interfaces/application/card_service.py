"""
Application service for card management.
"""
from typing import Any, List, Optional
from ..domain.models.card import MCard
from ..domain.models.protocols import CardRepository, ContentTypeService
from ..domain.models.exceptions import ValidationError
from ..domain.services.hashing import get_hashing_service

class CardService:
    """Application service for card management."""

    def __init__(
        self,
        repository: CardRepository,
        content_service: ContentTypeService
    ):
        self._repository = repository
        self._content_service = content_service
        self._hashing_service = get_hashing_service()

    async def _compute_hash(self, content: Any) -> str:
        """Compute hash for the given content."""
        if isinstance(content, bytes):
            content_bytes = content
        else:
            content_bytes = str(content).encode('utf-8')
        return await self._hashing_service.hash_content(content_bytes)

    async def create_card(self, content: Any) -> MCard:
        """Create a new card with proper hash."""
        if not self._content_service.validate_content(content):
            raise ValidationError("Invalid content type")
        
        # Create card with temporary hash first
        card = MCard(content=content)
        
        # Compute real hash
        hash_value = await self._compute_hash(content)
        
        # Create new card with real hash
        card = MCard(content=content, hash=hash_value)
        await self._repository.save(card)
        return card

    async def update_card_content(self, hash: str, new_content: Any) -> MCard:
        """Update a card's content and compute new hash."""
        if not self._content_service.validate_content(new_content):
            raise ValidationError("Invalid content type")

        # Get existing card
        card = await self._repository.get(hash)
        if not card:
            raise ValidationError(f"Card with hash {hash} not found")

        # Compute new hash
        new_hash = await self._compute_hash(new_content)
        
        # Create new card with updated content and hash
        updated_card = MCard(content=new_content, hash=new_hash)
        await self._repository.save(updated_card)
        
        # Delete old card
        await self._repository.delete(hash)
        
        return updated_card

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
