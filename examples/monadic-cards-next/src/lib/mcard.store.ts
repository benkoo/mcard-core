import { spawn, ChildProcess } from 'child_process';
import { join } from 'path';
import { Card } from './types';

export class StorageError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'StorageError';
  }
}

export class MCardStore {
  private static instance: MCardStore;
  private pythonProcess: ChildProcess | null = null;
  private initialized = false;
  private initPromise: Promise<void> | null = null;
  private commandQueue: Promise<any> = Promise.resolve();

  private constructor() {}

  static getInstance(): MCardStore {
    if (!MCardStore.instance) {
      MCardStore.instance = new MCardStore();
    }
    return MCardStore.instance;
  }

  isInitialized(): boolean {
    return this.initialized;
  }

  async initialize(): Promise<void> {
    if (this.initPromise) {
      return this.initPromise;
    }

    this.initPromise = new Promise<void>((resolve, reject) => {
      try {
        const scriptPath = join(process.cwd(), 'src', 'lib', 'mcard_store.py');
        this.pythonProcess = spawn('python3', [scriptPath], {
          env: {
            ...process.env,
            PYTHONPATH: process.env.PYTHONPATH || '',
            MCARD_DATA_DIR: process.env.MCARD_DATA_DIR || join(process.cwd(), 'data'),
            MCARD_DB_PATH: process.env.MCARD_DB_PATH || join(process.cwd(), 'data', 'cards.db'),
          },
        });

        if (!this.pythonProcess.stdin || !this.pythonProcess.stdout) {
          throw new Error('Failed to create Python process streams');
        }

        this.pythonProcess.stderr?.on('data', (data) => {
          console.error(`Python Error: ${data}`);
        });

        this.pythonProcess.on('error', (error) => {
          console.error('Python process error:', error);
          this.initialized = false;
          reject(error);
        });

        this.pythonProcess.on('exit', (code) => {
          if (code !== 0 && code !== null) {
            console.error(`Python process exited with code ${code}`);
            this.initialized = false;
          }
        });

        // Wait for ready signal
        this.pythonProcess.stdout.once('data', (data) => {
          const response = data.toString().trim();
          if (response === 'ready') {
            this.initialized = true;
            resolve();
          } else {
            reject(new Error(`Unexpected initialization response: ${response}`));
          }
        });

      } catch (error) {
        this.initialized = false;
        reject(error);
      }
    });

    return this.initPromise;
  }

  private async sendCommand<T>(command: string, data?: any): Promise<T> {
    if (!this.initialized || !this.pythonProcess?.stdin || !this.pythonProcess?.stdout) {
      throw new StorageError('Store not initialized');
    }

    // Queue the command to prevent race conditions
    return new Promise((resolve, reject) => {
      this.commandQueue = this.commandQueue.then(async () => {
        return new Promise<T>((innerResolve, innerReject) => {
          const responseHandler = (data: Buffer) => {
            try {
              const response = data.toString().trim();
              if (!response) {
                return; // Skip empty responses
              }
              
              const result = JSON.parse(response);
              if (result.error) {
                innerReject(new StorageError(result.error));
              } else {
                innerResolve(result.data as T);
              }
            } catch (error) {
              innerReject(new StorageError(`Failed to parse response: ${error}`));
            }
          };

          this.pythonProcess!.stdout!.once('data', responseHandler);

          const commandObj = {
            command,
            data: data || {},
          };

          this.pythonProcess!.stdin!.write(JSON.stringify(commandObj) + '\n');
        });
      }).then(resolve).catch(reject);
    });
  }

  async save(card: Partial<Card>): Promise<Card> {
    return this.sendCommand<Card>('save', card);
  }

  async get(hash: string): Promise<Card | null> {
    return this.sendCommand<Card | null>('get', { hash });
  }

  async list(offset: number = 0, limit: number = 10): Promise<Card[]> {
    // Ensure offset and limit are non-negative integers
    const validOffset = Math.max(0, Math.floor(offset));
    const validLimit = Math.max(1, Math.floor(limit));
    
    return this.sendCommand<Card[]>('list', { 
      offset: validOffset, 
      limit: validLimit 
    });
  }

  async delete(hash: string): Promise<void> {
    return this.sendCommand<void>('delete', { hash });
  }

  async clear(): Promise<void> {
    return this.sendCommand<void>('clear');
  }

  async close(): Promise<void> {
    if (this.pythonProcess) {
      this.pythonProcess.kill();
      this.pythonProcess = null;
    }
    this.initialized = false;
    this.initPromise = null;
    this.commandQueue = Promise.resolve();
  }
}
