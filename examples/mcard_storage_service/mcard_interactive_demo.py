#!/usr/bin/env python3
"""
MCard Interactive Demonstration CLI

This script provides an interactive CLI to demonstrate the core capabilities 
of the MCard content-addressable storage system.
"""

import os
import sys
import json
import argparse
from typing import Optional, List, Dict, Any
import asyncio

# Ensure MCard core is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcard import MCard
from mcard.infrastructure.persistence.store import MCardStore
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard import ContentTypeInterpreter
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineType
from mcard.infrastructure.persistence.facade import DatabaseConfig
from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure import config

class MCardInteractiveCLI:
    async def initialize(self):
        """Initialize the storage."""
        await self.storage.initialize()

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize MCard Storage with optional custom database path
        
        Args:
            db_path (Optional[str]): Path to SQLite database. 
                                     Defaults to in-memory database if not provided.
        """
        # Set the database path in the global configuration
        if db_path:
            sqlite_config = SQLiteConfig(
                db_path=db_path,
                max_connections=5,
                timeout=5.0,
                check_same_thread=False,
                max_content_size=10 * 1024 * 1024  # 10MB
            )
        else:
            sqlite_config = SQLiteConfig(
                db_path=":memory:",
                max_connections=5,
                timeout=5.0,
                check_same_thread=False,
                max_content_size=10 * 1024 * 1024  # 10MB
            )
            
        db_config = DatabaseConfig(engine_config=sqlite_config)
        config.load_config(db_config)  # Set global config
        self.storage = MCardStore()  # Get singleton instance
        self.content_interpreter = ContentTypeInterpreter()

    async def create_card(self, content: str, content_type: Optional[str] = None) -> MCard:
        """
        Create a new MCard with given content
        
        Args:
            content (str): Content to be stored
            content_type (Optional[str]): Optional content type hint
        
        Returns:
            MCard: The created card
        """
        card = MCard(content=content)
        
        # Optional content type detection and setting
        if content_type:
            card.content_type = content_type
        else:
            detected_type = self.content_interpreter.analyze(content)
            card.content_type = detected_type

        try:
            await self.storage.save(card)
        except Exception as e:
            if "already exists" in str(e):
                # If card already exists, retrieve it
                return await self.storage.get(card.hash)
            raise
        return card

    async def get_card(self, content_hash: str) -> Optional[MCard]:
        """
        Retrieve a card by its content hash
        
        Args:
            content_hash (str): Hash of the card to retrieve
        
        Returns:
            Optional[MCard]: Retrieved card or None
        """
        return await self.storage.get(content_hash)

    async def list_cards(self, limit: int = 10) -> List[MCard]:
        """
        List recent cards
        
        Args:
            limit (int): Number of cards to retrieve
        
        Returns:
            List[MCard]: List of recent cards
        """
        return await self.storage.list(limit=limit)

    async def search_cards(self, query: str) -> List[MCard]:
        """
        Search cards by content
        
        Args:
            query (str): Search query
        
        Returns:
            List[MCard]: Matching cards
        """
        all_cards = await self.storage.list()
        return [
            card for card in all_cards 
            if query.lower() in str(card.content).lower()
        ]

    def analyze_card(self, card: MCard) -> Dict[str, Any]:
        """
        Analyze card metadata and content
        
        Args:
            card (MCard): Card to analyze
        
        Returns:
            Dict[str, Any]: Analysis results
        """
        return {
            "content_hash": card.hash,
            "content_type": self.content_interpreter.analyze(card.content),
            "time_claimed": str(card.g_time),
            "content_length": len(str(card.content))
        }

async def run_demo(cli):
    print("\nMCard Interactive Demonstration")
    
    try:
        # Initialize storage
        await cli.initialize()
        
        # Create a card
        print("\nCreating card...")
        card = await cli.create_card("Hello, World!", "text/plain")
        print(f"Created card with hash: {card.hash}")
        
        # List cards
        print("\nListing cards...")
        cards = await cli.list_cards(limit=5)
        for card in cards:
            print(f"Hash: {card.hash[:8]}..., Content: {str(card.content)[:30]}")
        
        # Search cards
        print("\nSearching for 'Hello'...")
        results = await cli.search_cards("Hello")
        for card in results:
            print(f"Found: {str(card.content)}")
            
    finally:
        # Cleanup
        await cli.storage.close()
        print("\nDemo completed.")

def main():
    parser = argparse.ArgumentParser(description="MCard Interactive Demonstration")
    parser.add_argument('--db', help='Path to SQLite database', default=':memory:')
    args = parser.parse_args()

    cli = MCardInteractiveCLI(db_path=args.db)
    asyncio.run(run_demo(cli))

if __name__ == '__main__':
    main()
