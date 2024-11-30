"""Card provisioning application."""
from typing import Optional, List, Union
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore
from mcard.domain.models.hashing_protocol import HashingService
from mcard.domain.models.exceptions import StorageError
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class CardProvisioningApp:
    """Application for provisioning and managing cards."""
    
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

    async def create_card(self, content: Union[str, bytes]) -> MCard:
        """Create a new card with the given content.
        
        If content already exists, creates a reference card instead.
        If hash collision is detected, transitions to stronger hash.
        
        Args:
            content: The content to create a card with
            
        Returns:
            MCard: The created card
            
        Raises:
            ValueError: If content is invalid
            RuntimeError: If transitioning to stronger hash fails
            StorageError: If card cannot be saved after max retries
        """
        if not content:
            raise ValueError("Content cannot be empty")
            
        # Convert content to bytes if it's a string
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        # Get hash for the content
        content_hash = await self.hashing_service.hash_content(content)
        
        # Check if content already exists
        if await self.has_hash_for_content(content):
            # Get the original card to check for collision
            original_card = await self.store.get(content_hash)
                
            # Verify content match to distinguish between collision and duplicate
            original_content = original_card.content
            if isinstance(original_content, str):
                original_content = original_content.encode('utf-8')
                
            if original_content != content:
                # Hash collision detected - transition to stronger hash
                try:
                    logger.warning(f"Hash collision detected - attempting to transition to stronger hash")
                    logger.warning(f"Current hash: {content_hash} (algorithm: {self.hashing_service.settings.algorithm})")
                    
                    # Get new hash service and verify it's stronger
                    next_service = await self.hashing_service.next_level_hash()
                    if not next_service:
                        logger.error("No stronger hash algorithm available")
                        raise RuntimeError("No stronger hash algorithm available")
                        
                    # Atomically update hashing service
                    old_service = self.hashing_service
                    self.hashing_service = next_service
                    logger.info(f"Upgraded from {old_service.settings.algorithm} to {next_service.settings.algorithm}")
                    
                    # Get new hash with stronger algorithm
                    new_hash = await self.hashing_service.hash_content(content)
                    logger.info(f"New hash with stronger algorithm: {new_hash}")
                    
                    # Create and save card with stronger hash
                    card = MCard(content=content)
                    card.hash = new_hash
                    
                    max_retries = 3
                    retry_delay = 0.1  # 100ms
                    
                    for attempt in range(max_retries):
                        try:
                            await self.store.save(card)
                            logger.info(f"Successfully saved card with new hash after collision")
                            break
                        except StorageError as e:
                            if "already exists" in str(e) and attempt < max_retries - 1:
                                # Hash collision with new algorithm, try next level
                                logger.warning(f"Hash collision with new algorithm, trying next level")
                                next_service = await self.hashing_service.next_level_hash()
                                if not next_service:
                                    raise RuntimeError("No stronger hash algorithm available")
                                self.hashing_service = next_service
                                new_hash = await self.hashing_service.hash_content(content)
                                card.hash = new_hash
                                await asyncio.sleep(retry_delay * (attempt + 1))
                            else:
                                raise
                    
                    # Create detailed collision event
                    collision_event = {
                        'event_type': 'collision',
                        'original_hash': content_hash,
                        'original_content_length': len(original_content),
                        'original_time': original_card.g_time,
                        'new_hash': new_hash, 
                        'new_content_length': len(content),
                        'old_algorithm': old_service.settings.algorithm,
                        'new_algorithm': next_service.settings.algorithm,
                        'collision_details': {
                            'content_diff_length': abs(len(content) - len(original_content)),
                            'content_similarity': self._calculate_similarity(content, original_content)
                        }
                    }
                    
                    # Save collision event with new hash service
                    collision_event_content = json.dumps(collision_event).encode('utf-8')
                    collision_event_card = MCard(content=collision_event_content)
                    collision_event_card.hash = await self.hashing_service.hash_content(collision_event_content)
                    
                    # Save collision event with retry logic
                    for attempt in range(max_retries):
                        try:
                            await self.store.save(collision_event_card)
                            break
                        except StorageError as e:
                            if "already exists" in str(e) and attempt < max_retries - 1:
                                # Generate new hash for collision event
                                collision_event_card.hash = await self.hashing_service.hash_content(
                                    collision_event_content + str(attempt).encode('utf-8')
                                )
                                await asyncio.sleep(retry_delay * (attempt + 1))
                            else:
                                raise
                    
                    # Emit collision event if event bus exists
                    if self.event_bus:
                        await self.event_bus.emit(
                            CollisionEvent(
                                original_hash=content_hash,
                                new_hash=new_hash,
                                old_algorithm=old_service.settings.algorithm,
                                new_algorithm=next_service.settings.algorithm
                            )
                        )
                    
                    return card
                except Exception as e:
                    # Restore original hash service on failure
                    self.hashing_service = old_service
                    raise RuntimeError(f"Failed to transition to stronger hash: {str(e)}")
            else:
                # Content is identical - create reference card
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
                
                # Create duplicate event card with retry logic
                duplicate_event_card = MCard(content=duplicate_event_content)
                duplicate_event_card.hash = await self.hashing_service.hash_content(duplicate_event_content)
                
                max_retries = 3
                retry_delay = 0.1  # 100ms
                
                for attempt in range(max_retries):
                    try:
                        await self.store.save(duplicate_event_card)
                        break
                    except StorageError as e:
                        if "already exists" in str(e) and attempt < max_retries - 1:
                            # Generate new hash for duplicate event
                            duplicate_event_card.hash = await self.hashing_service.hash_content(
                                duplicate_event_content + str(attempt).encode('utf-8')
                            )
                            await asyncio.sleep(retry_delay * (attempt + 1))
                        else:
                            raise
                
                # Emit duplicate content event if event bus exists
                if self.event_bus:
                    await self.event_bus.emit(
                        DuplicateContentEvent(
                            content_hash=content_hash,
                            reference_hash=duplicate_event_card.hash
                        )
                    )
                return duplicate_event_card
        
        # Create new card for unique content
        card = MCard(content=content)
        card.hash = content_hash
        
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                await self.store.save(card)
                break
            except StorageError as e:
                if "already exists" in str(e) and attempt < max_retries - 1:
                    # Generate new hash for card
                    card.hash = await self.hashing_service.hash_content(content + str(attempt).encode('utf-8'))
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    raise
        
        return card

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

    async def list_provisioned_cards(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List all provisioned cards with optional pagination.
        
        Args:
            limit: Maximum number of cards to return
            offset: Number of cards to skip
            
        Returns:
            List of MCard instances
        """
        return await self.store.get_all(limit=limit, offset=offset)

    async def decommission_card(self, hash_str: str) -> None:
        """Decommission (delete) a card by its hash.
        
        Args:
            hash_str: Hash string identifying the card to delete
        """
        await self.store.delete(hash_str)

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
