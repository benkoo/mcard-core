import os
from dotenv import load_dotenv
import unittest
from mcard.config_constants import *

class TestExampleEnvLoading(unittest.TestCase):
    def setUp(self):
        # Load environment variables from example.env
        load_dotenv(dotenv_path='example.env')

    def test_env_variables(self):
        # Test if environment variables are loaded correctly
        self.assertEqual(os.getenv(ENV_DB_PATH), DEFAULT_DB_PATH)
        self.assertEqual(int(os.getenv(ENV_DB_MAX_CONNECTIONS)), DEFAULT_POOL_SIZE)
        self.assertEqual(float(os.getenv(ENV_DB_TIMEOUT)), DEFAULT_TIMEOUT)
        self.assertEqual(os.getenv(ENV_HASH_ALGORITHM), DEFAULT_HASH_ALGORITHM)
        self.assertEqual(os.getenv(ENV_HASH_CUSTOM_MODULE), DEFAULT_HASH_CUSTOM_MODULE)
        self.assertEqual(os.getenv(ENV_HASH_CUSTOM_FUNCTION), DEFAULT_HASH_CUSTOM_FUNCTION)
        self.assertEqual(int(os.getenv(ENV_HASH_CUSTOM_LENGTH)), DEFAULT_HASH_CUSTOM_LENGTH)
        self.assertEqual(int(os.getenv(ENV_API_PORT)), DEFAULT_API_PORT)

if __name__ == '__main__':
    unittest.main()