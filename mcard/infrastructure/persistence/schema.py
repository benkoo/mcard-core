"""
Schema manager for database operations.
This module implements a deliberately simple, single-table database design for the MCard application.
All card data is stored in a single 'card' table for simplicity, maintainability, and performance.

The schema consists of:
- A 'card' table with columns:
  - id: INTEGER PRIMARY KEY - Auto-incrementing primary key
  - hash: TEXT - Hash identifier for the card
  - content: TEXT - Card content
  - g_time: TEXT - Global timestamp with timezone information
  - metadata: TEXT - JSON-encoded metadata associated with the card
- An index on g_time for efficient time-based queries
- An index on hash for efficient hash-based queries

This single-table design was chosen to:
1. Simplify database maintenance and backups
2. Reduce complexity in schema management
3. Minimize potential for data inconsistencies
4. Optimize for the core use case of storing and retrieving cards
"""

from typing import Optional, Dict, Any, Type, Union, List, Tuple
from enum import Enum
import logging
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass

from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.database_engine_config import EngineType

logger = logging.getLogger(__name__)

class ColumnType(Enum):
    """Supported column types across different databases."""
    TEXT = "TEXT"  # For strings and ISO format datetime strings
    BLOB = "BLOB"  # For binary data
    INTEGER = "INTEGER"  # For integers
    FLOAT = "FLOAT"  # For floating point numbers
    BOOLEAN = "BOOLEAN"  # For boolean values
    TIMESTAMP = "TIMESTAMP"  # For database native timestamps
    JSON = "JSON"  # For JSON data


@dataclass
class ColumnDefinition:
    """Definition of a database column."""
    name: str
    type: ColumnType
    primary_key: bool = False
    nullable: bool = True
    unique: bool = False
    default: Any = None
    index: bool = False
    comment: Optional[str] = None


@dataclass
class TableDefinition:
    """Definition of a database table."""
    name: str
    columns: list[ColumnDefinition]
    indexes: Optional[Dict[str, list[str]]] = None  # index_name -> column_names
    comment: Optional[str] = None


class SchemaManager:
    """Singleton class for managing the card database schema.
    Implements a single-table design pattern for storing all card-related data.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the schema manager."""
        if not self._initialized:
            self._initialized = True
            self._tables = None  # Initialize tables on first use
            self._schema_handlers = {
                EngineType.SQLITE: SQLiteSchemaHandler()
                # Add more handlers for different databases
                # EngineType.POSTGRES: PostgresSchemaHandler(),
                # EngineType.MONGODB: MongoDBSchemaHandler(),
            }

    def _define_tables(self) -> Dict[str, TableDefinition]:
        """Define the database schema.
        
        This implementation deliberately uses a single-table design for simplicity and maintainability.
        All card-related data is stored in the 'card' table with the following structure:
        - id: INTEGER PRIMARY KEY - Auto-incrementing primary key
        - hash: TEXT - Hash identifier for the card
        - content: TEXT - Card content
        - g_time: TEXT - Global timestamp with timezone information
        """
        self._tables = {
            "card": TableDefinition(
                name="card",
                columns=[
                    ColumnDefinition(
                        name="id",
                        type=ColumnType.INTEGER,
                        primary_key=True,
                        nullable=False,
                        comment="Auto-incrementing primary key"
                    ),
                    ColumnDefinition(
                        name="hash",
                        type=ColumnType.TEXT,
                        nullable=False,
                        unique=True,
                        index=True,
                        comment="Hash identifier for the card"
                    ),
                    ColumnDefinition(
                        name="content",
                        type=ColumnType.TEXT,
                        nullable=False,
                        comment="Card content"
                    ),
                    ColumnDefinition(
                        name="g_time",
                        type=ColumnType.TEXT,
                        nullable=False,
                        index=True,
                        comment="Global timestamp in ISO 8601 format with timezone and microsecond precision (e.g., '2023-12-25T13:45:30.123456+00:00')"
                    )
                ],
                indexes={
                    "idx_card_g_time": ["g_time"],
                    "idx_card_hash": ["hash"]
                },
                comment="Single table storing all card data including content and timestamps"
            )
        }
        return self._tables

    def get_table_definition(self, table_name: str) -> TableDefinition:
        """Get the definition of a specific table."""
        if self._tables is None:
            self._tables = self._define_tables()
        if table_name not in self._tables:
            raise ValueError(f"Table {table_name} not defined in schema")
        return self._tables[table_name]

    def get_schema_handler(self, engine_type: EngineType) -> 'BaseSchemaHandler':
        """Get the schema handler for a specific database type."""
        if engine_type not in self._schema_handlers:
            raise ValueError(f"No schema handler available for {engine_type}")
        return self._schema_handlers[engine_type]

    async def initialize_schema(self, engine_type: EngineType = EngineType.SQLITE, connection: Optional[Any] = None) -> bool:
        """
        Initialize the database schema for the specified engine type.
        
        Args:
            engine_type (EngineType): The type of database engine to initialize.
            connection (Optional[Any]): Optional database connection. If not provided, 
                                        a new connection will be created.
        
        Returns:
            bool: True if schema initialization was successful, False otherwise.
        """
        try:
            # Ensure tables are defined
            if self._tables is None:
                self._define_tables()
            
            # Get the appropriate schema handler
            schema_handler = self.get_schema_handler(engine_type)
            
            # If no connection is provided, raise an error
            if connection is None:
                raise ValueError("Database connection is required for schema initialization")
            
            # Initialize schema using the schema handler
            await schema_handler.initialize_schema(connection, self._tables)
            
            return True
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False


class BaseSchemaHandler(ABC):
    """Base class for database-specific schema handlers."""
    
    @abstractmethod
    async def initialize_schema(self, connection: Any, tables: Dict[str, TableDefinition]) -> None:
        """Initialize the schema for this database type."""
        pass

    @abstractmethod
    def get_column_type(self, column_type: ColumnType) -> str:
        """Get the database-specific column type."""
        pass

    @abstractmethod
    def _build_column_definition(self, column: ColumnDefinition) -> str:
        """Build database-specific column definition string."""
        pass

    @abstractmethod
    def _generate_table_sql(self, table: TableDefinition) -> tuple[str, Dict[str, str]]:
        """Generate SQL statements for table creation and indexes.
        
        Args:
            table: Table definition containing columns and indexes
            
        Returns:
            Tuple of (create table SQL, dictionary of index names to index SQL)
        """
        pass


class SQLiteSchemaHandler(BaseSchemaHandler):
    """SQLite-specific schema handler."""
    
    def get_column_type(self, column_type: ColumnType) -> str:
        """Map column types to SQLite types."""
        type_mapping = {
            ColumnType.TEXT: "TEXT",
            ColumnType.BLOB: "BLOB",
            ColumnType.INTEGER: "INTEGER",
            ColumnType.FLOAT: "REAL",
            ColumnType.BOOLEAN: "INTEGER",  # SQLite uses 0/1 for boolean
            ColumnType.TIMESTAMP: "TEXT",  # SQLite stores timestamps as text
            ColumnType.JSON: "TEXT"  # JSON stored as text
        }
        return type_mapping.get(column_type, "TEXT")

    def _build_column_definition(self, column: ColumnDefinition) -> str:
        """Build SQLite column definition."""
        parts = [column.name, self.get_column_type(column.type)]
        
        if column.primary_key:
            parts.append("PRIMARY KEY AUTOINCREMENT")
        
        if not column.nullable:
            parts.append("NOT NULL")
        
        if column.unique:
            parts.append("UNIQUE")
        
        if column.default is not None:
            parts.append(f"DEFAULT {column.default}")
        
        return " ".join(parts)

    def _generate_table_sql(self, table: TableDefinition) -> tuple[str, Dict[str, str]]:
        """
        Generate SQL statements for table creation and indexes.
        
        Args:
            table: Table definition containing columns and indexes
            
        Returns:
            Tuple of (create table SQL, dictionary of index names to index SQL)
        """
        # Build column definitions
        column_defs = [self._build_column_definition(col) for col in table.columns]
        
        # Construct table creation SQL
        table_sql = f"CREATE TABLE IF NOT EXISTS {table.name} (\n"
        table_sql += ",\n".join(column_defs)
        table_sql += "\n)"
        
        # Generate index SQLs
        index_sqls = {}
        if table.indexes:
            for index_name, index_columns in table.indexes.items():
                # Construct index SQL
                index_cols_str = ", ".join(index_columns)
                index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table.name} ({index_cols_str})"
                index_sqls[index_name] = index_sql
        
        return table_sql, index_sqls

    async def initialize_schema(self, connection: Any, tables: Dict[str, TableDefinition]) -> None:
        """Initialize the SQLite schema."""
        try:
            # Log the start of schema initialization
            logger.debug(f"Starting SQLite schema initialization for tables: {list(tables.keys())}")
            
            # Ensure the connection is an aiosqlite connection
            if not hasattr(connection, 'execute'):
                logger.error(f"Invalid connection type: {type(connection)}")
                raise ValueError("Connection must be an aiosqlite connection")
            
            # Process each table definition
            for table_name, table_def in tables.items():
                logger.debug(f"Processing table: {table_name}")
                
                # Generate table creation SQL
                table_sql, index_sqls = self._generate_table_sql(table_def)
                logger.debug(f"Table creation SQL: {table_sql}")
                
                try:
                    # Create table
                    await connection.execute(table_sql)
                    logger.info(f"Initialized table {table_name} in SQLite database")
                    
                    # Create indexes
                    for index_name, index_sql in index_sqls.items():
                        logger.debug(f"Index SQL: {index_sql}")
                        await connection.execute(index_sql)
                        logger.debug(f"Created index {index_name}")
                
                except sqlite3.OperationalError as e:
                    logger.error(f"Error initializing table {table_name}: {e}")
                    # Don't raise here to continue with other tables
            
            # Commit the transaction
            await connection.commit()
            logger.info("SQLite schema initialization completed successfully")
        
        except Exception as e:
            logger.error(f"Comprehensive schema initialization error: {e}", exc_info=True)
            raise
