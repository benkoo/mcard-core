"""Create test MCards with various types of content."""
from mcard import MCard, MCardStorage
import json

def create_cards():
    # Initialize storage
    storage = MCardStorage("interpreter.db")
    hashes = []
    
    # 1. Spanish text content
    spanish_content = """
    La inteligencia artificial (IA) es la simulación de procesos de inteligencia humana 
    por parte de máquinas, especialmente sistemas informáticos. Estos procesos incluyen 
    el aprendizaje (la adquisición de información y reglas para el uso de la información), 
    el razonamiento (usando las reglas para llegar a conclusiones aproximadas o definitivas) 
    y la autocorrección.
    """
    card = MCard(content=spanish_content)
    storage.save(card)
    print("\n1. Spanish Text Card")
    print(f"Hash: {card.content_hash}")
    hashes.append(card.content_hash)
    
    # 2. JSON data
    json_content = {
        "user": {
            "id": 12345,
            "name": "John Doe",
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "language": "en-US"
            },
            "activity": {
                "last_login": "2024-02-20T15:30:00Z",
                "total_sessions": 42,
                "favorite_features": ["search", "export", "sharing"]
            }
        }
    }
    card = MCard(content=json.dumps(json_content, indent=2))
    storage.save(card)
    print("\n2. JSON Data Card")
    print(f"Hash: {card.content_hash}")
    hashes.append(card.content_hash)
    
    # 3. French text with some technical content
    french_content = """
    Le développement web moderne utilise plusieurs technologies essentielles:

    Frontend:
    - HTML5 pour la structure
    - CSS3 pour le style
    - JavaScript pour l'interactivité

    Backend:
    - Bases de données SQL et NoSQL
    - APIs RESTful
    - Microservices

    La sécurité est primordiale, notamment:
    - L'authentification
    - Le chiffrement des données
    - La protection contre les injections SQL
    """
    card = MCard(content=french_content)
    storage.save(card)
    print("\n3. French Technical Text Card")
    print(f"Hash: {card.content_hash}")
    hashes.append(card.content_hash)
    
    # 4. Binary content (simple byte sequence)
    binary_content = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + b"Hello, Binary World!"
    card = MCard(content=binary_content)
    storage.save(card)
    print("\n4. Binary Content Card")
    print(f"Hash: {card.content_hash}")
    hashes.append(card.content_hash)
    
    return hashes

if __name__ == "__main__":
    create_cards()
