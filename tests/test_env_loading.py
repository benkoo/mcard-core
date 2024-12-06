import os
from dotenv import load_dotenv
import unittest
from mcard.config_constants import *

class TestExampleEnvLoading(unittest.TestCase):
    def setUp(self):
        # Store original environment variables
        self.original_env = {
            ENV_DB_PATH: os.environ.get(ENV_DB_PATH),
            ENV_DB_MAX_CONNECTIONS: os.environ.get(ENV_DB_MAX_CONNECTIONS),
            ENV_DB_TIMEOUT: os.environ.get(ENV_DB_TIMEOUT),
            ENV_HASH_ALGORITHM: os.environ.get(ENV_HASH_ALGORITHM),
            ENV_HASH_CUSTOM_MODULE: os.environ.get(ENV_HASH_CUSTOM_MODULE),
            ENV_HASH_CUSTOM_FUNCTION: os.environ.get(ENV_HASH_CUSTOM_FUNCTION),
            ENV_HASH_CUSTOM_LENGTH: os.environ.get(ENV_HASH_CUSTOM_LENGTH),
        }
        
        # Clear relevant environment variables
        for key in self.original_env:
            if key in os.environ:
                del os.environ[key]
                
        # Load environment variables from example.env
        load_dotenv(dotenv_path='example.env', override=True)

    def tearDown(self):
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_env_variables(self):
        # Test if environment variables are loaded correctly
        self.assertEqual(os.getenv(ENV_DB_PATH), DEFAULT_DB_PATH)
        self.assertEqual(os.getenv(ENV_DB_MAX_CONNECTIONS), str(DEFAULT_POOL_SIZE))
        self.assertEqual(os.getenv(ENV_DB_TIMEOUT), str(DEFAULT_TIMEOUT))
        self.assertEqual(os.getenv(ENV_HASH_ALGORITHM), DEFAULT_HASH_ALGORITHM)
        self.assertEqual(os.getenv(ENV_HASH_CUSTOM_MODULE), DEFAULT_HASH_CUSTOM_MODULE)
        self.assertEqual(os.getenv(ENV_HASH_CUSTOM_FUNCTION), DEFAULT_HASH_CUSTOM_FUNCTION)
        self.assertEqual(int(os.getenv(ENV_HASH_CUSTOM_LENGTH)), DEFAULT_HASH_CUSTOM_LENGTH)


if __name__ == '__main__':
    unittest.main()
