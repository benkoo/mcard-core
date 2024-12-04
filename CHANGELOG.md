# Changelog

## [Unreleased]

### Added
- New `AsyncPersistenceWrapper` class to replace `AsyncSQLiteWrapper`
  - Database-agnostic persistence layer
  - Support for multiple database engines
  - Proper implementation of the `CardStore` protocol
- New `BaseStore` abstract class for database engines
  - Template for all database engine implementations
  - Standardized interface for database operations
- New reusable setup module in `mcard/infrastructure/setup.py`
  - Configurable database settings
  - Support for different engine types
  - Configuration overrides
  - Async context manager support
  - Built-in content interpreter
- Comprehensive test suite for setup module
  - In-memory database testing
  - File-based database testing
  - Configuration override testing
  - Invalid engine handling
  - Context manager usage
  - Content interpreter functionality
  - Multiple instance testing

### Changed
- Refactored persistence layer to use new architecture
  - Moved from direct SQL operations to engine-specific implementations
  - Updated all tests to use `AsyncPersistenceWrapper`
  - Improved separation of concerns between API and persistence layers
- Updated SQLite implementation
  - Now inherits from `BaseStore`
  - Proper handling of card hashes
  - Better error handling and validation
- Moved demo setup code to core infrastructure
  - More reusable and configurable
  - Better organized as part of core functionality

### Removed
- `AsyncSQLiteWrapper` and related code
  - Removed direct SQL-related features from wrapper
  - Delegated database operations to engine layer
- Old setup code from examples directory
  - Functionality moved to core infrastructure
  - Better organized and more maintainable

### Fixed
- Hash computation and storage
  - Now properly computes and stores hashes in database
  - Fixed NOT NULL constraint issues
- Database schema handling
  - Better validation of required fields
  - Proper handling of nullable constraints

## [0.2.0] - Previous Release
[Previous release notes...]
