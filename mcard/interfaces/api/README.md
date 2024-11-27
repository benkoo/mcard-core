# MCard API

This is a FastAPI application for managing MCard content. It provides endpoints to create, retrieve, and list cards with various filters.

## Features
- **Create Card**: Add new cards with content and automatically compute a hash.
- **Retrieve Card**: Fetch a card using its unique hash.
- **List Cards**: List all cards with optional filters for time range and pagination.
- **Remove Card**: Given its hash,remove a card.

## Configuration
- The application loads settings from environment variables, including database paths, hashing algorithms, and the API key.
- The MCard API class must use the `mcard.domain.models.config.AppSettings` class, which uses the `config.py` implementation to load parameters from the environment, ensuring consistency and security in configuration management.
- Environment variables:
  - `MCARD_MANAGER_DB_PATH`: Path to the database file.
  - `MCARD_MANAGER_DATA_SOURCE`: Data source for the application.
  - `MCARD_MANAGER_POOL_SIZE`: Connection pool size.
  - `MCARD_MANAGER_TIMEOUT`: Timeout for database operations.
  - `MCARD_MANAGER_HASH_ALGORITHM`: Hashing algorithm to use.
  - `MCARD_MANAGER_CUSTOM_MODULE`: Custom module for hashing.
  - `MCARD_MANAGER_CUSTOM_FUNCTION`: Custom function for hashing.
  - `MCARD_MANAGER_CUSTOM_HASH_LENGTH`: Length of the custom hash.
  - `MCARD_API_KEY`: API key for authentication.

## Logging
- Logs are configured to be written to `mcard_api.log` and the console.
- The logging level is set to `DEBUG` for detailed information.

## Running the Application
1. Ensure all necessary environment variables are set as outlined in the Configuration section.
2. Run the FastAPI application using the command:
   ```bash
   uvicorn mcard.interfaces.api.mcard_api:app --reload
   ```
3. Access the API documentation at `http://localhost:8000/docs`.

## Testing
- To run the tests for the FastAPI application, use the following command:
  ```bash
  pytest tests/interfaces/api/test_mcard_api.py
  ```

## Security
- The API key is required for accessing certain endpoints and is verified against the environment variable `MCARD_API_KEY`.

## Dependencies
- FastAPI
- Pydantic
- Other internal modules for configuration and services.

For more detailed information, refer to the source code and the API documentation.
