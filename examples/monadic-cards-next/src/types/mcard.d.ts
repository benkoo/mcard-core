// Type definitions for MCard

export {
  EngineType,
  EngineConfig,
  DatabaseConfig,
  HashingSettings,
  Card,
  CardContent,
  MCardStore,
  ListCardsOptions
} from '../lib/types';

// Type guards for content types
export const isImageContent = (contentType?: string): boolean => 
  contentType?.startsWith('image/') ?? false;

export const isTextContent = (contentType?: string): boolean => 
  contentType === 'text/plain';

export const isJsonContent = (contentType?: string): boolean => 
  contentType === 'application/json';

export const isPdfContent = (contentType?: string): boolean => 
  contentType === 'application/pdf';

export const isBinaryContent = (contentType?: string): boolean => 
  contentType ? !isTextContent(contentType) && !isImageContent(contentType) : false;

// Error types
export { StorageError, HashingError, ConfigurationError, CardNotFoundError, DuplicateCardError } from '../lib/errors';
