import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import fs from 'fs';
import path from 'path';

let dbInstance: any = null;

export async function getDb() {
  const dbPath = process.env.MCARD_MANAGER_DB_PATH || './data/monadic_cards.db';
  const absoluteDbPath = path.resolve(dbPath);
  
  // Return existing instance if available
  if (dbInstance) {
    return dbInstance;
  }

  // Ensure data directory exists with proper permissions
  const dataDir = path.dirname(absoluteDbPath);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true, mode: 0o755 });
  }

  // If database exists but has wrong permissions, fix them
  if (fs.existsSync(absoluteDbPath)) {
    fs.chmodSync(absoluteDbPath, 0o644);
  }

  // Open or create the database
  dbInstance = await open({
    filename: absoluteDbPath,
    driver: sqlite3.Database
  });

  // Enable foreign keys
  await dbInstance.exec('PRAGMA foreign_keys = ON');

  // Create table if it doesn't exist
  await dbInstance.exec(`
    CREATE TABLE IF NOT EXISTS cards (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      hash TEXT UNIQUE NOT NULL,
      content TEXT NOT NULL,
      content_type TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  `);

  return dbInstance;
}

export async function closeDb() {
  if (dbInstance) {
    await dbInstance.close();
    dbInstance = null;
  }
}
