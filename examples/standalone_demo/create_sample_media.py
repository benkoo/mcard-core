#!/usr/bin/env python3
"""
Create sample media files for MCard demo.
"""

import os
from PIL import Image
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_sample_image(filename, size=(300, 200), format='PNG'):
    """Create a sample image with random colors."""
    # Create random color data
    data = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    
    # Create image from array
    img = Image.fromarray(data)
    
    # Save in specified format
    img.save(filename, format=format)
    print(f"Created {format} image: {filename}")

def create_sample_pdf(filename):
    """Create a sample PDF file."""
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawString(100, 750, "Sample PDF Document")
    c.drawString(100, 700, "Created for MCard Demo")
    c.save()
    print(f"Created PDF: {filename}")

def create_sample_mov(filename):
    """Create a minimal MOV file."""
    # This creates a very basic MOV file header
    with open(filename, 'wb') as f:
        # Write minimal MOV header
        f.write(bytes.fromhex('0000001C667479706D703432000000006D703432697336766964656F'))
        # Add some dummy video data
        f.write(os.urandom(1024))  # Random data to simulate video content
    print(f"Created MOV file: {filename}")

def main():
    # Create media directory if it doesn't exist
    media_dir = "sample_data/media"
    os.makedirs(media_dir, exist_ok=True)
    
    # Create PNG image
    create_sample_image(os.path.join(media_dir, "sample.png"), format='PNG')
    
    # Create JPG image
    create_sample_image(os.path.join(media_dir, "sample.jpg"), format='JPEG')
    
    # Create PDF
    create_sample_pdf(os.path.join(media_dir, "sample.pdf"))
    
    # Create MOV file
    create_sample_mov(os.path.join(media_dir, "sample.mov"))

if __name__ == '__main__':
    main()
