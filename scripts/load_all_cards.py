#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the implementations/python directory to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root / "implementations" / "python"))

# Set the data source environment variable
os.environ["MCARD_DATA_SOURCE"] = "data/cards"

from mcard.load_data import main

if __name__ == "__main__":
    main()
