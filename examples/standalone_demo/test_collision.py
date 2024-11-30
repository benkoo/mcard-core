"""
Simple script to test collision detection in MCard.
"""
import os

def create_test_files():
    # Create directory if it doesn't exist
    test_dir = "sample_data/collisions/test"
    os.makedirs(test_dir, exist_ok=True)

    # Create two files with identical content
    content = "This is a test content that will create a collision!"
    
    with open(os.path.join(test_dir, "identical1.txt"), "w") as f:
        f.write(content)
    
    with open(os.path.join(test_dir, "identical2.txt"), "w") as f:
        f.write(content)

    print("Created test files with identical content in:", test_dir)

if __name__ == "__main__":
    create_test_files()
