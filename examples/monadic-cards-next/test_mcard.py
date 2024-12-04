import asyncio
from mcard.domain.models.card import MCard
from mcard.domain.services.hashing import get_hashing_service
from mcard.infrastructure.persistence.memory_store import MemoryCardStore

async def main():
    try:
        # Initialize store
        store = MemoryCardStore()
        print("Store initialized successfully")
        
        # Initialize hashing service
        hashing_service = get_hashing_service()
        
        # Create test cards
        test_contents = [
            "Hello World! This is a test card.",
            "This is another test card with different content.",
            "A third test card to make sure pagination works.",
            "Fourth test card with some numbers: 1234567890",
            "Fifth test card with special characters: !@#$%^&*()",
        ]
        
        for content in test_contents:
            try:
                hash_value = await hashing_service.hash_content(content.encode('utf-8'))
                card = MCard(
                    content=content,
                    hash=hash_value
                )
                await store.save(card)
                print(f"Created new card: {card.hash}")
            except Exception as e:
                print(f"Error creating card: {e}")
        
        # List all cards
        try:
            cards = await store.list(limit=10, offset=0)
            print(f"\nFound {len(cards)} cards:")
            for card in cards:
                print(f"- {card.hash}: {card.content}")
        except Exception as e:
            print(f"Error listing cards: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
