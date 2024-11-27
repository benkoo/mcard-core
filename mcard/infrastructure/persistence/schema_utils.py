import sqlite3
import logging

def initialize_schema(connection: sqlite3.Connection):
    """
    Initialize the database schema.

    This method creates the necessary tables with the specified schema. The `g_time` column is
    a string representing the global time when the card was claimed, with microsecond precision.
    The `hash` column is a cryptographic hash computed from the card content.
    """
    logging.debug("Initializing database schema.")
    connection.execute(
        '''
        CREATE TABLE IF NOT EXISTS card (
            hash TEXT PRIMARY KEY,
            content BLOB NOT NULL,
            g_time TEXT NOT NULL
        )
        '''
    )
    logging.debug("Database schema initialized.")
