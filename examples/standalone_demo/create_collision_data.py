#!/usr/bin/env python3
"""
Create test data for hash collision demonstration.
This includes:
1. MD5 collision examples
2. SHA-1 collision (Shattered PDFs)
3. Random data with high collision probability for MD5
"""

import os
import hashlib
import requests
from pathlib import Path

def create_md5_collision_files():
    """Create two different files with the same MD5 hash."""
    print("\nCreating MD5 collision test files...")
    
    # These two strings have the same MD5 hash but different content
    # Source: https://crypto.stackexchange.com/questions/1434/are-there-two-known-strings-which-have-the-same-md5-hash-value
    str1 = "4dc968ff0ee35c209572d4777b721587d36fa7b21bdc56b74a3dc0783e7b9518afbfa200a8284bf36e8e4b55b35f427593d849676da0d1555d8360fb5f07fea2"
    str2 = "4dc968ff0ee35c209572d4777b721587d36fa7b21bdc56b74a3dc0783e7b9518afbfa202a8284bf36e8e4b55b35f427593d849676da0d1d55d8360fb5f07fea2"
    
    collision_dir = Path("sample_data/collisions/md5")
    collision_dir.mkdir(parents=True, exist_ok=True)
    
    # Write the strings to files
    with open(collision_dir / "file1.txt", "w") as f:
        f.write(str1)
    with open(collision_dir / "file2.txt", "w") as f:
        f.write(str2)
    
    # Verify they have the same MD5 hash
    hash1 = hashlib.md5(str1.encode()).hexdigest()
    hash2 = hashlib.md5(str2.encode()).hexdigest()
    
    print(f"File 1 MD5: {hash1}")
    print(f"File 2 MD5: {hash2}")
    print(f"Collision verified: {hash1 == hash2}")
    print(f"Files created in {collision_dir}")

def download_shattered_pdfs():
    """Download the SHA-1 collision PDFs (Shattered attack)."""
    print("\nDownloading SHA-1 collision PDFs (Shattered)...")
    
    # URLs for the Shattered PDFs
    urls = [
        "https://shattered.io/static/shattered-1.pdf",
        "https://shattered.io/static/shattered-2.pdf"
    ]
    
    collision_dir = Path("sample_data/collisions/sha1")
    collision_dir.mkdir(parents=True, exist_ok=True)
    
    for i, url in enumerate(urls, 1):
        output_file = collision_dir / f"shattered-{i}.pdf"
        if not output_file.exists():
            print(f"Downloading shattered-{i}.pdf...")
            response = requests.get(url)
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {output_file}")
            else:
                print(f"Failed to download shattered-{i}.pdf")
        else:
            print(f"File {output_file} already exists")
    
    # Verify SHA-1 hashes
    if all(f.exists() for f in collision_dir.glob("shattered-*.pdf")):
        hashes = []
        for i in range(1, 3):
            with open(collision_dir / f"shattered-{i}.pdf", "rb") as f:
                content = f.read()
                sha1_hash = hashlib.sha1(content).hexdigest()
                hashes.append(sha1_hash)
                print(f"Shattered-{i}.pdf SHA-1: {sha1_hash}")
        print(f"Collision verified: {hashes[0] == hashes[1]}")

def create_high_probability_collisions():
    """Create files with high probability of collision in MD5."""
    print("\nCreating high probability collision test files...")
    
    collision_dir = Path("sample_data/collisions/probability")
    collision_dir.mkdir(parents=True, exist_ok=True)
    
    # Create 1000 small files with random data
    # Due to the birthday paradox, there's a good chance of MD5 collisions
    num_files = 1000
    file_size = 128  # bytes
    
    print(f"Creating {num_files} random files...")
    for i in range(num_files):
        with open(collision_dir / f"random_{i:04d}.bin", "wb") as f:
            f.write(os.urandom(file_size))
    
    print(f"Files created in {collision_dir}")

def main():
    """Create all collision test data."""
    print("Creating collision test data...")
    
    # Create MD5 collision files
    create_md5_collision_files()
    
    # Download SHA-1 collision PDFs
    download_shattered_pdfs()
    
    # Create high probability collision files
    create_high_probability_collisions()
    
    print("\nCollision test data creation completed!")

if __name__ == "__main__":
    main()
