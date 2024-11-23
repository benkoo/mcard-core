"""
MCardCollection: A class for managing a collection of MCards sorted by time_claimed.
"""
from typing import List, Optional
from datetime import datetime
from .core import MCard
from .storage import MCardStorage


class MCardCollection:
    """
    A class that manages a collection of MCards, ensuring they are always sorted by time_claimed.
    """
    def __init__(self, storage: MCardStorage):
        """
        Initialize the collection with a storage instance.
        
        Args:
            storage (MCardStorage): The storage instance to load cards from
        """
        self.storage = storage
        self._cards: List[MCard] = []
        self._load_cards()

    def _load_cards(self) -> None:
        """Load all cards from storage and sort them by time_claimed."""
        self._cards = self.storage.get_all()
        self._sort_cards()

    def _sort_cards(self) -> None:
        """Sort the cards by time_claimed."""
        self._cards.sort(key=lambda x: x.time_claimed)

    def add_card(self, card: MCard) -> bool:
        """
        Add a card to the collection and storage.
        
        Args:
            card (MCard): The card to add
            
        Returns:
            bool: True if the card was added, False if it already existed
        """
        # Try to save to storage first
        if not self.storage.save(card):
            return False
        
        # Add to in-memory collection and sort
        self._cards.append(card)
        self._sort_cards()
        return True

    def get_all_cards(self) -> List[MCard]:
        """
        Get all cards in time_claimed order.
        
        Returns:
            List[MCard]: List of all cards sorted by time_claimed
        """
        return self._cards.copy()  # Return a copy to prevent external modification

    def get_card_by_hash(self, content_hash: str) -> Optional[MCard]:
        """
        Get a card by its content hash.
        
        Args:
            content_hash (str): The content hash to look for
            
        Returns:
            Optional[MCard]: The card if found, None otherwise
        """
        for card in self._cards:
            if card.content_hash == content_hash:
                return card
        return None

    def compare_cards_temporal_order(self, card1: MCard, card2: MCard) -> int:
        """
        Compare two cards based on their temporal order.
        
        Args:
            card1 (MCard): First card to compare
            card2 (MCard): Second card to compare
            
        Returns:
            int: -1 if card1 is earlier, 0 if same time, 1 if card1 is later
        """
        if card1.time_claimed < card2.time_claimed:
            return -1
        elif card1.time_claimed > card2.time_claimed:
            return 1
        return 0

    def get_cards_in_timerange(self, start_time: datetime, end_time: datetime) -> List[MCard]:
        """
        Get all cards within a specified time range.
        
        Args:
            start_time (datetime): Start of the time range (inclusive)
            end_time (datetime): End of the time range (inclusive)
            
        Returns:
            List[MCard]: List of cards within the time range, sorted by time_claimed
        """
        return [
            card for card in self._cards 
            if start_time <= card.time_claimed <= end_time
        ]

    def remove_card(self, content_hash: str) -> bool:
        """
        Remove a card from both storage and collection.
        
        Args:
            content_hash (str): Hash of the card to remove
            
        Returns:
            bool: True if the card was removed, False if not found
        """
        # Try to delete from storage first
        if not self.storage.delete(content_hash):
            return False
        
        # Remove from in-memory collection
        self._cards = [card for card in self._cards if card.content_hash != content_hash]
        return True

    def refresh(self) -> None:
        """Reload all cards from storage and resort."""
        self._load_cards()
