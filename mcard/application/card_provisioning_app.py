"""Card provisioning application."""
from typing import Optional, List, Union
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore
from mcard.domain.models.hashing_protocol import HashingService
from mcard.domain.models.exceptions import StorageError
from mcard.domain.services.hashing import get_hashing_service
import json
import asyncio
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = True  # Ensure log propagation is enabled

# Create file handler
file_handler = logging.FileHandler('mcard_api_test.log')
file_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

# Configure root logger as well
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)

print("Logging configuration executed")
logger.debug('Logging system initialized.')

class CardCreationError(Exception):
    """Base exception for card creation errors."""
    pass

class HashCollisionError(CardCreationError):
    """Raised when a hash collision is detected."""
    pass

class StorageOperationError(CardCreationError):
    """Raised when storage operations fail."""
    pass

class EventCreationError(CardCreationError):
    """Raised when event creation fails."""
    pass

class CardProvisioningApp:
    """Application for provisioning and managing cards."""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # 100ms

    def __init__(self, store: CardStore, hashing_service: Optional[HashingService] = None, event_bus = None):
        """Initialize the card provisioning application.
        
        Args:
            store: Storage backend for cards
            hashing_service: Optional custom hashing service
            event_bus: Optional event bus for emitting events
        """
        self.store = store
        self.hashing_service = hashing_service or get_hashing_service()
        self.event_bus = event_bus
        print('CardProvisioningApp initialized with store and hashing service.')
        logger.debug('CardProvisioningApp initialized with store and hashing service.')

    async def _prepare_content(self, content: Union[str, bytes]) -> bytes:
        """Prepare and validate content for card creation.
        
        Args:
            content: Raw content to prepare
            
        Returns:
            bytes: Prepared content
            
        Raises:
            ValueError: If content is invalid
        """
        if not content:
            raise ValueError("Content cannot be empty")
            
        return content.encode('utf-8') if isinstance(content, str) else content

    async def _create_new_card(self, content: bytes, content_hash: str) -> MCard:
        """Create a new card with unique content.
        
        Args:
            content: Prepared content
            content_hash: Hash of the content
            
        Returns:
            MCard: Created card
            
        Raises:
            StorageOperationError: If card cannot be saved
        """
        try:
            logger.debug(f'Creating new card with hash: {content_hash}')
            card = MCard(content=content)
            card.hash = content_hash
            logger.debug(f'Attempting to save card with hash: {card.hash}')
            await self._save_with_retry(card, content)
            logger.debug(f'Successfully saved card with hash: {card.hash}')
            return card
        except Exception as e:
            logger.error(f'Failed to create new card: {str(e)}')
            raise StorageOperationError(f"Failed to create new card: {str(e)}")

    async def _save_with_retry(self, card: MCard, content: bytes) -> MCard:
        """Save card with retry logic.
        
        Args:
            card: Card to save
            content: Card content for hash generation
            
        Returns:
            MCard: Saved card
            
        Raises:
            StorageOperationError: If card cannot be saved after max retries
        """
        existing_card = await self.store.get(card.hash)
        logger.debug(f'Checking for existing card with hash: {card.hash}, exists: {existing_card is not None}')
        if existing_card:
            return existing_card  # Return existing card if it already exists

        for attempt in range(self.MAX_RETRIES):
            try:
                await self.store.save(card)
                return card
            except StorageError as e:
                if "already exists" in str(e) and attempt < self.MAX_RETRIES - 1:
                    card.hash = await self.hashing_service.hash_content(
                        content + str(attempt).encode('utf-8')
                    )
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    raise StorageOperationError(f"Failed to save card after {attempt + 1} attempts: {str(e)}")

    async def _handle_hash_collision(self, content: bytes, content_hash: str, 
                                   original_card: MCard) -> MCard:
        """Handle hash collision by upgrading hash algorithm.
        
        Args:
            content: New content that caused collision
            content_hash: Original hash that collided
            original_card: Existing card with same hash
            
        Returns:
            MCard: New card with stronger hash
            
        Raises:
            HashCollisionError: If collision cannot be resolved
        """
        try:
            old_service = self.hashing_service
            next_service = await self.hashing_service.next_level_hash()
            
            if not next_service:
                raise HashCollisionError("No stronger hash algorithm available")
                
            self.hashing_service = next_service
            new_hash = await self.hashing_service.hash_content(content)
            
            card = MCard(content=content)
            card.hash = new_hash
            
            try:
                await self._save_with_retry(card, content)
                await self._create_collision_event(content, content_hash, original_card, 
                                                new_hash, old_service, next_service)
                return card
            except Exception as e:
                self.hashing_service = old_service
                raise HashCollisionError(f"Failed to save card with stronger hash: {str(e)}")
                
        except Exception as e:
            self.hashing_service = old_service
            raise HashCollisionError(f"Failed to handle hash collision: {str(e)}")

    async def _handle_duplicate_content(self, content: bytes, content_hash: str, 
                                      original_card: MCard) -> MCard:
        """Handle duplicate content by creating a reference card.
        
        Args:
            content: Duplicate content
            content_hash: Content hash
            original_card: Original card with same content
            
        Returns:
            MCard: Reference card
            
        Raises:
            EventCreationError: If reference card creation fails
        """
        try:
            event_card = await self._create_duplicate_event(content, content_hash, original_card)
            
            if self.event_bus:
                await self.event_bus.emit(
                    DuplicateContentEvent(
                        content_hash=content_hash,
                        reference_hash=event_card.hash
                    )
                )
            
            return event_card
        except Exception as e:
            raise EventCreationError(f"Failed to handle duplicate content: {str(e)}")

    async def create_card(self, content: Union[str, bytes]) -> MCard:
        """Create a new card with the given content.
        
        If content already exists, returns the existing card instead.
        
        Args:
            content: The content to create a card with
            
        Returns:
            MCard: The created or existing card
            
        Raises:
            ValueError: If content is invalid
            CardCreationError: If card creation fails
        """
        try:
            prepared_content = await self._prepare_content(content)
            content_hash = await self.hashing_service.hash_content(prepared_content)
            
            # Check if a card with this content already exists
            existing_card = await self.store.get(content_hash)
            if existing_card:
                return existing_card
            
            # Create new card for unique content
            card = MCard(content=prepared_content.decode('utf-8'))  # Convert bytes back to string for storage
            card.hash = content_hash
            await self.store.save(card)
            return card
            
        except (ValueError, CardCreationError) as e:
            # Re-raise known exceptions
            raise
        except Exception as e:
            # Wrap unknown exceptions
            raise CardCreationError(f"Unexpected error during card creation: {str(e)}")

    async def retrieve_card(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash identifier.
        
        Args:
            hash_str: Hash string identifying the card
            
        Returns:
            MCard if found, None otherwise
        """
        return await self.store.get(hash_str)

    async def has_hash_for_content(self, content: Union[str, bytes]) -> bool:
        """Check if content has duplicates by looking up its hash in the store.
        
        Args:
            content: The content to check for duplicates (string or bytes)
            
        Returns:
            bool: True if duplicates exist, False otherwise
        """
        if not content:
            return False
            
        # Convert content to bytes if it's a string
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        # Get hash for the content
        content_hash = await self.hashing_service.hash_content(content)
        
        # Check if hash exists in store
        existing_card = await self.store.get(content_hash)
        if not existing_card:
            return False
            
        # Hash exists - verify if it's a collision or duplicate
        existing_content = existing_card.content
        if isinstance(existing_content, str):
            existing_content = existing_content.encode('utf-8')
            
        # Return True in both cases - collision detection happens in create_card
        return True

    async def list_cards(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List all provisioned cards with optional pagination.
        
        Args:
            limit: Maximum number of cards to return
            offset: Number of cards to skip
            
        Returns:
            List of MCard instances
        """
        cards, _ = await self.store.list(page_size=limit, page=(offset // limit + 1) if limit and offset else None)
        return cards

    async def list_provisioned_cards(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List all provisioned cards with optional pagination.
        
        Args:
            limit: Maximum number of cards to return
            offset: Number of cards to skip
            
        Returns:
            List of MCard instances
        """
        return await self.store.get_all(limit=limit, offset=offset)

    async def list_cards_by_content(self, content: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List cards with optional content filtering and pagination.
        
        Args:
            content: Optional content string to filter cards by
            limit: Maximum number of cards to return
            offset: Number of cards to skip
            
        Returns:
            List of MCard instances matching the content filter
        """
        if content is None:
            return await self.list_provisioned_cards(limit=limit, offset=offset)
            
        return await self.store.list(content=content, limit=limit, offset=offset)

    async def decommission_card(self, hash_str: str) -> None:
        """Decommission (delete) a card by its hash.
        
        Args:
            hash_str: Hash string identifying the card to delete
        """
        await self.store.delete(hash_str)

    async def delete_all_cards(self) -> None:
        """Delete all cards."""
        await self.store.delete_all()

    async def shutdown(self) -> None:
        """Gracefully shutdown the application and its dependencies."""
        await self.store.close()

    def _calculate_similarity(self, content1: bytes, content2: bytes) -> float:
        """Calculate similarity ratio between two contents.
        
        Uses a simple byte-level comparison for efficiency.
        Returns a value between 0 (completely different) and 1 (identical).
        """
        if not content1 or not content2:
            return 0.0
            
        # Compare first 1KB for efficiency
        sample_size = min(1024, len(content1), len(content2))
        matches = sum(a == b for a, b in zip(content1[:sample_size], content2[:sample_size]))
        return matches / sample_size

    async def _create_collision_event(self, content: bytes, content_hash: str, 
                                   original_card: MCard, new_hash: str, 
                                   old_service: HashingService, next_service: HashingService) -> None:
        """Create a collision event.
        
        Args:
            content: New content that caused collision
            content_hash: Original hash that collided
            original_card: Existing card with same hash
            new_hash: New hash with stronger algorithm
            old_service: Original hashing service
            next_service: New hashing service
        """
        collision_event = {
            'event_type': 'collision',
            'original_hash': content_hash,
            'original_content_length': len(original_card.content),
            'original_time': original_card.g_time,
            'new_hash': new_hash, 
            'new_content_length': len(content),
            'old_algorithm': old_service.settings.algorithm,
            'new_algorithm': next_service.settings.algorithm,
            'collision_details': {
                'content_diff_length': abs(len(content) - len(original_card.content)),
                'content_similarity': self._calculate_similarity(content, original_card.content)
            }
        }
        
        collision_event_content = json.dumps(collision_event).encode('utf-8')
        collision_event_card = MCard(content=collision_event_content)
        collision_event_card.hash = await self.hashing_service.hash_content(collision_event_content)
        
        await self._save_with_retry(collision_event_card, collision_event_content)

    async def _create_duplicate_event(self, content: bytes, content_hash: str, 
                                   original_card: MCard) -> MCard:
        """Create a duplicate event.
        
        Args:
            content: Duplicate content
            content_hash: Content hash
            original_card: Original card with same content
            
        Returns:
            MCard: Duplicate event card
        """
        duplicate_event = {
            "hash": content_hash,
            "g_time": original_card.g_time,
            "content_length": len(content),
            "verification": {
                "content_verified": True,
                "hash_algorithm": self.hashing_service.settings.algorithm
            }
        }
        duplicate_event_content = json.dumps(duplicate_event).encode('utf-8')
        
        duplicate_event_card = MCard(content=duplicate_event_content)
        duplicate_event_card.hash = await self.hashing_service.hash_content(duplicate_event_content)
        
        await self._save_with_retry(duplicate_event_card, duplicate_event_content)
        
        return duplicate_event_card
