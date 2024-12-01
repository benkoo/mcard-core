export enum EngineType {
  SQLITE = 'sqlite',
  POSTGRES = 'postgres',
  MEMORY = 'memory'
}

export interface EngineConfig {
  engine_type: EngineType;
  database: string;
  max_connections?: number;
  timeout?: number;
  engine_options?: Record<string, any>;
}

export interface DatabaseConfig {
  engine: EngineConfig;
  hashing?: HashingSettings;
}

export interface HashingSettings {
  algorithm?: string;
  salt?: string;
  iterations?: number;
}

export interface Card {
  hash: string;
  content: string;
  content_type?: string;
  g_time: string;
  created_at: string;
  updated_at: string;
}

export interface CardContent {
  content: string | Buffer;
  content_type?: string;
}

export interface ListCardsOptions {
  limit?: number;
  offset?: number;
}
