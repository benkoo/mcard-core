# Standalone MCard Loader

This directory contains a simple executable script that demonstrates the loading and unloading of content into an MCard store.

## Overview

The script loads content from the `sample_data` directory into the MCard store. It is configured to use the `.env` file for setting up the environment variables required by the `MCardSetup` class.

## How It Works

1. **Loading Data**: The script reads files from the `sample_data` directory and loads them into the MCard store. The configuration for the database path, maximum connections, timeout, and other settings are read from the `.env` file.

2. **Unloading Data**: After loading, the script demonstrates the ability to unload (remove) the MCards from the store, showcasing the full cycle of data management.

## Configuration

- Ensure that the `.env` file is present and correctly configured with the necessary environment variables such as `MCARD_STORE_PATH`, `MCARD_HASH_ALGORITHM`, etc.

## Running the Script

To execute the script, navigate to this directory and run the following command:

```bash
python3 simple_app.py
```

This will load all content from the `sample_data` directory into the MCard store and then remove them to demonstrate both loading and unloading capabilities.
