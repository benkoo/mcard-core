"""
Configuration management for the MCard CRUD app.
"""

import os
from pathlib import Path

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DB_PATH = os.getenv('MCARD_DB_PATH', str(BASE_DIR / 'data' / 'db' / 'MCardStore.db'))
DB_MAX_CONNECTIONS = int(os.getenv('MCARD_DB_MAX_CONNECTIONS', '5'))
DB_TIMEOUT = float(os.getenv('MCARD_DB_TIMEOUT', '5.0'))
MAX_CONTENT_SIZE = int(os.getenv('MCARD_MAX_CONTENT_SIZE', str(10 * 1024 * 1024)))  # 10MB default

# Flask configuration
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev')  # Change in production
CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY', 'dev')   # Change in production
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
PORT = int(os.getenv('FLASK_PORT', '5050'))

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = str(BASE_DIR / 'app.log')
