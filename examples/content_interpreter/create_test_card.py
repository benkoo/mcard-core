"""Create a test MCard with sample content."""
from mcard import MCard, MCardStorage

def main():
    # Initialize storage
    storage = MCardStorage("interpreter.db")
    
    # Create a test card with some interesting content
    content = """
    Machine Learning (ML) is a subset of artificial intelligence that focuses on developing 
    systems that can learn and improve from experience without being explicitly programmed. 
    It uses algorithms and statistical models to analyze and draw insights from patterns in data.
    
    Key concepts include:
    1. Supervised Learning
    2. Unsupervised Learning
    3. Reinforcement Learning
    4. Deep Learning
    
    ML has numerous applications in:
    - Image and Speech Recognition
    - Natural Language Processing
    - Recommendation Systems
    - Autonomous Vehicles
    """
    
    card = MCard(content=content)
    storage.save(card)
    
    print(f"Created card with hash: {card.content_hash}")
    return card.content_hash

if __name__ == "__main__":
    main()
