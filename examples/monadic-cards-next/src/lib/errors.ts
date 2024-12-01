export class StorageError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'StorageError';
  }
}

export class CardNotFoundError extends Error {
  constructor(hash: string) {
    super(`Card with hash ${hash} not found`);
    this.name = 'CardNotFoundError';
  }
}

export class ConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationError';
  }
}
