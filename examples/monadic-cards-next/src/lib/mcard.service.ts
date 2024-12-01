import { 
  Card, 
  ListCardsOptions, 
  MCardStore,
} from './types';
import {
  StorageError,
  ConfigurationError,
  CardNotFoundError,
  DuplicateCardError
} from './errors';
import { MCardStore as MCardStoreImpl } from './mcard.store';
import AsyncLock from 'async-lock';

export class MCardService {
  private static _instance: MCardService | null = null;
  private static _lock = new AsyncLock();
  private _store: MCardStore | null = null;
  private _isInitialized = false;

  private constructor() {}

  public static async getInstance(): Promise<MCardService> {
    if (!MCardService._instance) {
      await MCardService._lock.acquire('singleton', async () => {
        if (!MCardService._instance) {
          const instance = new MCardService();
          try {
            instance._store = await MCardStoreImpl.getInstance();
            await instance.initialize();
            MCardService._instance = instance;
          } catch (error) {
            console.error('Failed to initialize MCardService:', error);
            throw new ConfigurationError('Failed to initialize MCard service');
          }
        }
      });
    }
    return MCardService._instance!;
  }

  public async initialize(): Promise<void> {
    if (this._isInitialized) {
      return;
    }

    try {
      if (!this._store) {
        this._store = await MCardStoreImpl.getInstance();
      }
      await this._store.initialize();
      this._isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize MCard service:', error);
      throw new ConfigurationError(`Failed to initialize MCard service: ${error}`);
    }
  }

  public async close(): Promise<void> {
    if (this._store) {
      try {
        await this._store.close();
        this._isInitialized = false;
        MCardService._instance = null;
      } catch (error) {
        console.error('Error closing MCard service:', error);
        throw new StorageError('Failed to close MCard service');
      }
    }
  }

  public async listCards(options?: ListCardsOptions): Promise<Card[]> {
    if (!this._store) {
      throw new ConfigurationError('Service not initialized');
    }
    try {
      return await this._store.list(options?.limit, options?.offset);
    } catch (error) {
      console.error('Error listing cards:', error);
      throw new StorageError('Failed to list cards');
    }
  }

  public async getCard(hash: string): Promise<Card | null> {
    if (!this._store) {
      throw new ConfigurationError('Service not initialized');
    }
    try {
      const card = await this._store.get(hash);
      if (!card) {
        throw new CardNotFoundError(hash);
      }
      return card;
    } catch (error) {
      if (error instanceof CardNotFoundError) {
        return null;
      }
      console.error('Error getting card:', error);
      throw new StorageError(`Failed to get card: ${hash}`);
    }
  }

  public async createCard(content: string | Buffer, contentType?: string): Promise<Card> {
    if (!this._store) {
      throw new ConfigurationError('Service not initialized');
    }
    try {
      return await this._store.save({ content, content_type: contentType });
    } catch (error) {
      if (error instanceof DuplicateCardError) {
        // If card exists, try to get it
        const hash = error.message.match(/hash (\w+)/)?.[1];
        if (hash) {
          const existingCard = await this.getCard(hash);
          if (existingCard) {
            return existingCard;
          }
        }
        throw error;
      }
      console.error('Error creating card:', error);
      throw new StorageError('Failed to create card');
    }
  }

  public async deleteCard(hash: string): Promise<void> {
    if (!this._store) {
      throw new ConfigurationError('Service not initialized');
    }
    try {
      await this._store.delete(hash);
    } catch (error) {
      if (error instanceof CardNotFoundError) {
        // Card already deleted or doesn't exist
        return;
      }
      console.error('Error deleting card:', error);
      throw new StorageError(`Failed to delete card: ${hash}`);
    }
  }

  public isInitialized(): boolean {
    return this._isInitialized && !!this._store;
  }
}

// Create a singleton instance
let mcardServiceInstance: MCardService | null = null;

export const getMCardService = async (): Promise<MCardService> => {
  if (!mcardServiceInstance) {
    mcardServiceInstance = await MCardService.getInstance();
  }
  return mcardServiceInstance;
};

// Ensure cleanup on process exit
const cleanup = async () => {
  if (mcardServiceInstance) {
    try {
      await mcardServiceInstance.close();
      mcardServiceInstance = null;
    } catch (error) {
      console.error('Error during cleanup:', error);
    }
  }
};

process.on('beforeExit', cleanup);
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);