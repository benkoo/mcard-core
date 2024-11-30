"""
Schema manager for database operations.
This module implements a deliberately simple, single-table database design for the MCard application.
All card data is stored in a single 'card' table for simplicity, maintainability, and performance.

The schema consists of:
- A 'card' table with columns:
  - id: INTEGER PRIMARY KEY - Auto-incrementing primary key
  - hash: TEXT - Hash identifier for the card
  - content: BLOB - Card content
  - g_time: TEXT - Global timestamp
- An index on g_time for efficient time-based queries
- An index on hash for efficient hash-based queries

This single-table design was chosen to:
1. Simplify database maintenance and backups
2. Reduce complexity in schema management
3. Minimize potential for data inconsistencies
4. Optimize for the core use case of storing and retrieving cards
"""

from typing import Optional, Dict, Any, Type, Union, List
from enum import Enum
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.engine_config import EngineType

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
        - content: BLOB - The actual card content in binary format
        - g_time: TEXT - Global timestamp with timezone information
        """
        return {
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
                        type=ColumnType.BLOB,
                        nullable=False,
                        comment="Card content stored as binary data"
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

    async def initialize_schema(self, engine_type: EngineType, connection: Any) -> None:
        """Initialize the schema for a specific database type."""
        # Force reload tables to get latest schema
        self._tables = self._define_tables()
        handler = self.get_schema_handler(engine_type)
        await handler.initialize_schema(connection, self._tables)


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
    def _generate_table_sql(self, table: TableDefinition) -> tuple[str, list[str]]:
        """Generate SQL statements for table creation and indexes.
        
        Args:
            table: Table definition containing columns and indexes
            
        Returns:
            Tuple of (create table SQL, list of create index SQLs)
        """
        pass


class SQLiteSchemaHandler(BaseSchemaHandler):
    """Schema handler for SQLite database."""

    def get_column_type(self, column_type: ColumnType) -> str:
        """Map generic column types to SQLite types."""
        type_map = {
            ColumnType.TEXT: "TEXT",
            ColumnType.BLOB: "BLOB",
            ColumnType.INTEGER: "INTEGER",
            ColumnType.FLOAT: "REAL",
            ColumnType.BOOLEAN: "INTEGER",  # SQLite doesn't have a boolean type
            ColumnType.TIMESTAMP: "TEXT",  # Store timestamps as ISO format strings
            ColumnType.JSON: "TEXT"  # Store JSON as text
        }
        return type_map[column_type]

    def _build_column_definition(self, column: ColumnDefinition) -> str:
        """Build SQLite column definition string."""
        parts = [
            column.name,
            self.get_column_type(column.type),
            "PRIMARY KEY AUTOINCREMENT" if column.primary_key and column.type == ColumnType.INTEGER else "",
            "NOT NULL" if not column.nullable else "",
            "UNIQUE" if column.unique and not column.primary_key else "",  # Don't add UNIQUE if it's already a primary key
            f"DEFAULT {column.default}" if column.default is not None else "",
            f"/* {column.comment} */" if column.comment else ""
        ]
        return " ".join(part for part in parts if part)

    def _generate_table_sql(self, table: TableDefinition) -> tuple[str, list[str]]:
        """Generate SQL statements for table creation and indexes.
        
        Args:
            table: Table definition containing columns and indexes
            
        Returns:
            Tuple of (create table SQL, list of create index SQLs)
        """
        columns = [self._build_column_definition(col) for col in table.columns]
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table.name} (
                {', '.join(columns)}
            ) /* {table.comment or ''} */
        """
        
        create_index_sqls = []
        if table.indexes:
            for idx_name, idx_columns in table.indexes.items():
                create_index_sql = f"""
                    CREATE INDEX IF NOT EXISTS {idx_name}
                    ON {table.name} ({', '.join(idx_columns)})
                """
                create_index_sqls.append(create_index_sql)
                
        return create_table_sql, create_index_sqls

    async def initialize_schema(self, connection: Any, tables: Dict[str, TableDefinition]) -> None:
        """Initialize schema for the database connection."""
        async with connection.cursor() as cursor:
            for table in tables.values():
                # Check if table exists
                await cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table.name}'")
                if not await cursor.fetchone():
                    # Table doesn't exist, create it
                    create_table_sql, create_index_sqls = self._generate_table_sql(table)
                    await cursor.execute(create_table_sql)
                    for create_index_sql in create_index_sqls:
                        await cursor.execute(create_index_sql)
                    logger.info(f"Created table: {table.name}")
                else:
                    logger.info(f"Table {table.name} already exists, skipping creation")

        await connection.commit()
        logger.info(f"Successfully initialized schema for tables: {', '.join(tables.keys())}")
