#!/usr/bin/env python3
"""Script to load all cards from the data source into the database."""

import sys
from pathlib import Path
import argparse

# Add the project root to the Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

from mcard import config
from mcard.load_data import main as load_data_main

def main():
    """Main function to load all cards."""
    parser = argparse.ArgumentParser(description="Load all cards from data source into database.")
    parser.add_argument("--test", action="store_true", help="Use test database")
    args = parser.parse_args()

    # Load environment variables
    config.load_config()

    # Run the load data main function
    load_data_main(test=args.test)

if __name__ == "__main__":
    main()
