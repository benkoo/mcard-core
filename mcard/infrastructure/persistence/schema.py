"""
Schema manager for database operations.
Provides a centralized place for defining and managing database schemas across different database types.
"""

from typing import Optional, Dict, Any, Type, Union
from enum import Enum
import logging
import sqlite3
import aiosqlite
from dataclasses import dataclass
from abc import ABC, abstractmethod

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
    """
    Singleton class for managing database schemas.
    Provides a centralized place for defining and managing database schemas.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._tables = self._define_tables()
            self._schema_handlers = {
                EngineType.SQLITE: SQLiteSchemaHandler()
                # Add more handlers for different databases
                # EngineType.POSTGRES: PostgresSchemaHandler(),
                # EngineType.MONGODB: MongoDBSchemaHandler(),
            }

    def _define_tables(self) -> Dict[str, TableDefinition]:
        """Define all database tables and their schemas."""
        return {
            "card": TableDefinition(
                name="card",
                columns=[
                    ColumnDefinition(
                        name="hash",
                        type=ColumnType.TEXT,
                        primary_key=True,
                        nullable=False,
                        comment="Unique hash identifier for the card"
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
                    "idx_card_g_time": ["g_time"]
                },
                comment="Stores card data with content and global timestamp"
            )
            # Add more table definitions as needed
        }

    def get_table_definition(self, table_name: str) -> TableDefinition:
        """Get the definition of a specific table."""
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
            "PRIMARY KEY" if column.primary_key else "",
            "NOT NULL" if not column.nullable else "",
            "UNIQUE" if column.unique else "",
            f"DEFAULT {column.default}" if column.default is not None else "",
            f"/* {column.comment} */" if column.comment else ""
        ]
        return " ".join(part for part in parts if part)

    async def initialize_schema(self, connection: Union[sqlite3.Connection, aiosqlite.Connection], tables: Dict[str, TableDefinition]) -> None:
        """Initialize SQLite schema."""
        try:
            if isinstance(connection, aiosqlite.Connection):
                await self._initialize_schema_async(connection, tables)
            else:
                self._initialize_schema_sync(connection, tables)
        except (sqlite3.Error, Exception) as e:
            raise StorageError(f"Failed to initialize schema: {str(e)}")

    def _initialize_schema_sync(self, connection: sqlite3.Connection, tables: Dict[str, TableDefinition]) -> None:
        """Initialize schema for synchronous connection."""
        cursor = connection.cursor()
        
        # Set pragmas for better performance and reliability
        cursor.execute("PRAGMA busy_timeout = 5000")
        cursor.execute("PRAGMA journal_mode=WAL")
        
        for table in tables.values():
            # Create table
            columns = [self._build_column_definition(col) for col in table.columns]
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table.name} (
                    {', '.join(columns)}
                ) /* {table.comment or ''} */
            """
            cursor.execute(create_table_sql)

            # Create indexes
            if table.indexes:
                for idx_name, idx_columns in table.indexes.items():
                    create_index_sql = f"""
                        CREATE INDEX IF NOT EXISTS {idx_name}
                        ON {table.name} ({', '.join(idx_columns)})
                    """
                    cursor.execute(create_index_sql)

        connection.commit()
        logger.info(f"Successfully initialized schema for tables: {', '.join(tables.keys())}")

    async def _initialize_schema_async(self, connection: aiosqlite.Connection, tables: Dict[str, TableDefinition]) -> None:
        """Initialize schema for asynchronous connection."""
        async with connection.cursor() as cursor:
            # Set pragmas for better performance and reliability
            await cursor.execute("PRAGMA busy_timeout = 5000")
            await cursor.execute("PRAGMA journal_mode=WAL")
            
            for table in tables.values():
                # Create table
                columns = [self._build_column_definition(col) for col in table.columns]
                create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS {table.name} (
                        {', '.join(columns)}
                    ) /* {table.comment or ''} */
                """
                await cursor.execute(create_table_sql)

                # Create indexes
                if table.indexes:
                    for idx_name, idx_columns in table.indexes.items():
                        create_index_sql = f"""
                            CREATE INDEX IF NOT EXISTS {idx_name}
                            ON {table.name} ({', '.join(idx_columns)})
                        """
                        await cursor.execute(create_index_sql)

            await connection.commit()
            logger.info(f"Successfully initialized schema for tables: {', '.join(tables.keys())}")
