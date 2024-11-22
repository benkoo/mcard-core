import fs from 'fs';
import { MCard } from './core';
import { MCardStorage } from './storage';

describe('MCardStorage', () => {
    const TEST_DB = 'test_mcards.db';
    let storage: MCardStorage;

    // Test data
    const textContent = 'Hello World';
    const textHash = '6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba';
    const binaryContent = Buffer.from([1, 2, 3, 4]);
    const binaryHash = '9cdc9050cecf59530c8f8e4c398ccb2b5c7e1f20c8c76605d9f70a87bc966c4c';
    const numberContent = 42;
    const numberHash = '73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049';

    beforeEach(async () => {
        // Remove test database if it exists
        if (fs.existsSync(TEST_DB)) {
            fs.unlinkSync(TEST_DB);
        }
        storage = new MCardStorage(TEST_DB);
        // Wait a bit for database initialization
        await new Promise(resolve => setTimeout(resolve, 100));
    });

    afterEach(() => {
        storage.close();
        if (fs.existsSync(TEST_DB)) {
            fs.unlinkSync(TEST_DB);
        }
    });

    describe('save and get', () => {
        it('should save and retrieve text content', async () => {
            // Create and save
            const card = new MCard(textContent, textHash, new Date());
            storage.save(card);

            // Retrieve and verify
            const retrieved = await storage.get(textHash);
            expect(retrieved).not.toBeNull();
            expect(retrieved?.content).toBe(textContent);
            expect(retrieved?.contentHash).toBe(textHash);
            expect(retrieved?.timeClaimed).toBeInstanceOf(Date);
        });

        it('should save and retrieve binary content', async () => {
            // Create and save
            const card = new MCard(binaryContent, binaryHash, new Date());
            storage.save(card);

            // Retrieve and verify
            const retrieved = await storage.get(binaryHash);
            expect(retrieved).not.toBeNull();
            expect(Buffer.isBuffer(retrieved?.content)).toBe(true);
            expect(retrieved?.content).toEqual(binaryContent);
            expect(retrieved?.contentHash).toBe(binaryHash);
        });

        it('should save and retrieve numeric content', async () => {
            // Create and save
            const card = new MCard(numberContent, numberHash, new Date());
            storage.save(card);

            // Retrieve and verify
            const retrieved = await storage.get(numberHash);
            expect(retrieved).not.toBeNull();
            expect(parseInt(retrieved?.content as string)).toBe(numberContent);
            expect(retrieved?.contentHash).toBe(numberHash);
        });
    });

    describe('getAll', () => {
        it('should retrieve all stored cards', async () => {
            // Create and save multiple cards
            const cards = [
                new MCard(textContent, textHash),
                new MCard(binaryContent, binaryHash),
                new MCard(numberContent, numberHash)
            ];
            cards.forEach(card => storage.save(card));

            // Retrieve all and verify
            const retrieved = await storage.getAll();
            expect(retrieved.length).toBe(3);
            
            const hashes = new Set(retrieved.map(card => card.contentHash));
            expect(hashes).toEqual(new Set([textHash, binaryHash, numberHash]));
        });
    });

    describe('delete', () => {
        it('should delete existing cards', async () => {
            // Create and save
            const card = new MCard(textContent, textHash);
            storage.save(card);

            // Verify it exists
            const retrieved = await storage.get(textHash);
            expect(retrieved).not.toBeNull();

            // Delete and verify
            expect(await storage.delete(textHash)).toBe(true);
            const deletedRetrieved = await storage.get(textHash);
            expect(deletedRetrieved).toBeNull();
        });

        it('should return false when deleting non-existent cards', async () => {
            expect(await storage.delete('nonexistent')).toBe(false);
        });
    });

    describe('update', () => {
        it('should update existing cards', async () => {
            // Create and save initial card
            const initialTime = new Date();
            const card = new MCard(textContent, textHash, initialTime);
            storage.save(card);

            // Update with new time
            const newTime = new Date(initialTime.getTime() + 1000);
            const updatedCard = new MCard(textContent, textHash, newTime);
            storage.save(updatedCard);

            // Retrieve and verify
            const retrieved = await storage.get(textHash);
            expect(retrieved).not.toBeNull();
            expect(retrieved?.timeClaimed.getTime()).toBe(newTime.getTime());
        });
    });
});
