from mcard.infrastructure.persistence.store import MCardStore
from mcard.domain.models.card import MCard
import sys
import json
import asyncio
import os
from datetime import datetime
from typing import Optional, Any, List

def serialize_datetime(dt: Optional[Any]) -> Optional[str]:
    """Safely serialize datetime objects to ISO format strings."""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return None

def decode_content(content: Any) -> Optional[str]:
    """Safely decode content to string."""
    if content is None:
        return None
    if isinstance(content, bytes):
        return content.decode('utf-8')
    if isinstance(content, str):
        return content
    return str(content)

def serialize_card(card: Any) -> Optional[dict]:
    """Safely serialize a card object to a dictionary."""
    if not card:
        return None
    try:
        return {
            "hash": str(card.hash) if hasattr(card, 'hash') else None,
            "content": decode_content(card.content) if hasattr(card, 'content') else None,
            "g_time": serialize_datetime(card.g_time) if hasattr(card, 'g_time') else None,
            "created_at": None,  # Not supported in core MCard
            "updated_at": None,  # Not supported in core MCard
        }
    except Exception as e:
        print(json.dumps({"error": f"Failed to serialize card: {str(e)}", "data": None}), flush=True)
        return None

async def get_paginated_cards(store: MCardStore, offset: int = 0, limit: int = 10) -> List[dict]:
    """Get paginated cards with proper offset and limit handling."""
    try:
        # Get all cards first to determine total count
        all_cards = await store.list()
        total_count = len(all_cards)
        
        # Calculate effective offset and limit
        start = min(offset, total_count)
        end = min(start + limit, total_count)
        
        # Get the paginated subset
        paginated_cards = await store.list(offset=start, limit=end - start)
        return [serialize_card(card) for card in paginated_cards if card]
    except Exception as e:
        print(json.dumps({"error": f"Failed to get paginated cards: {str(e)}", "data": None}), flush=True)
        return []

async def delete_card(store: MCardStore, hash: str) -> bool:
    """Delete a card."""
    try:
        # Delete the card
        await store.delete(hash)
        # Force a small delay to ensure deletion is processed
        await asyncio.sleep(0.1)
        # Verify deletion
        deleted_card = await store.get(hash)
        if deleted_card is not None:
            print(json.dumps({"error": "Failed to delete card", "data": False}), flush=True)
            return False
        return True
    except Exception as e:
        print(json.dumps({"error": f"Failed to delete card: {str(e)}", "data": False}), flush=True)
        return False

async def cleanup_database():
    """Clean up the database by removing all cards."""
    try:
        store = MCardStore()
        await store.initialize()
        cards = await store.list()
        for card in cards:
            try:
                await delete_card(store, card.hash)
            except Exception:
                pass  # Ignore errors during cleanup
        await store.close()
    except Exception:
        pass  # Ignore errors during cleanup

async def main():
    store = None
    try:
        # Clean up database before starting
        await cleanup_database()

        # Initialize fresh store
        store = MCardStore()
        await store.initialize()
        print("ready", flush=True)

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                    
                command = json.loads(line)
                result = None
                
                if command["command"] == "list":
                    result = await get_paginated_cards(
                        store,
                        offset=command["data"].get("offset", 0),
                        limit=command["data"].get("limit", 10)
                    )
                elif command["command"] == "get":
                    card = await store.get(command["data"]["hash"])
                    result = serialize_card(card)
                elif command["command"] == "save":
                    try:
                        content = command["data"]["content"]
                        if isinstance(content, str):
                            content = content.encode('utf-8')
                        card = MCard(content=content)
                        
                        # Try to get existing card first
                        existing = await store.get(card.hash)
                        if existing:
                            result = serialize_card(existing)
                        else:
                            await store.save(card)
                            result = serialize_card(card)
                    except Exception as e:
                        if "already exists" in str(e):
                            # If card already exists, return it
                            existing = await store.get(card.hash)
                            result = serialize_card(existing)
                        else:
                            raise
                elif command["command"] == "delete":
                    success = await delete_card(store, command["data"]["hash"])
                    if not success:
                        raise Exception(f"Failed to delete card {command['data']['hash']}")
                    result = None  # Return null on successful deletion
                
                print(json.dumps({"error": None, "data": result}), flush=True)
                
            except Exception as e:
                print(json.dumps({"error": str(e), "data": None}), flush=True)

    except Exception as e:
        print(json.dumps({"error": f"Fatal error: {str(e)}", "data": None}), flush=True)
        sys.exit(1)
    finally:
        # Always try to close the store
        if store:
            try:
                await store.close()
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main())
