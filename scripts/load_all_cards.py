#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import dotenv

# Add the implementations/python directory to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root / "implementations" / "python"))

# Load environment variables from .env file
dotenv.load_dotenv(project_root / ".env")

# Set the data source environment variable if not already set
if "MCARD_DATA_SOURCE" not in os.environ:
    os.environ["MCARD_DATA_SOURCE"] = "data/cards"

from mcard.load_data import main

if __name__ == "__main__":
    main()
