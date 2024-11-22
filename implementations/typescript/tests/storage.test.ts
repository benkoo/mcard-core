import fs from 'fs';
import { MCard } from '../src/mcard';
import { MCardStorage } from '../src/storage';

describe('MCardStorage', () => {
    const TEST_DB = 'test_mcards.db';
    let storage: MCardStorage;

    // Test data
    const textContent = 'Hello World';
    const textHash = '6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba';
    const binaryContent = Buffer.from('Binary Data');
    const binaryHash = '4d6f7c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c';
    const numberContent = 12345;
    const numberHash = '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5';

    beforeEach(() => {
        storage = new MCardStorage(TEST_DB);
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
            await storage.save(card);

            // Retrieve and verify
            const retrieved = await storage.get(textHash);
            expect(retrieved).not.toBeNull();
            if (retrieved) {
                expect(retrieved.content).toBe(textContent);
                expect(retrieved.contentHash).toBe(textHash);
                expect(retrieved.timeclaimed).toBeInstanceOf(Date);
            }
        });

        it('should save and retrieve binary content', async () => {
            // Create and save
            const card = new MCard(binaryContent, binaryHash, new Date());
            await storage.save(card);

            // Retrieve and verify
            const retrieved = await storage.get(binaryHash);
            expect(retrieved).not.toBeNull();
            if (retrieved) {
                expect(Buffer.isBuffer(retrieved.content)).toBe(true);
                expect(retrieved.content).toEqual(binaryContent);
                expect(retrieved.contentHash).toBe(binaryHash);
            }
        });

        it('should save and retrieve numeric content', async () => {
            // Create and save
            const card = new MCard(numberContent, numberHash, new Date());
            await storage.save(card);

            // Retrieve and verify
            const retrieved = await storage.get(numberHash);
            expect(retrieved).not.toBeNull();
            if (retrieved) {
                expect(parseInt(retrieved.content as string)).toBe(numberContent);
                expect(retrieved.contentHash).toBe(numberHash);
            }
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
            await Promise.all(cards.map(card => storage.save(card)));

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
            await storage.save(card);

            // Verify it exists
            const exists = await storage.get(textHash);
            expect(exists).not.toBeNull();

            // Delete and verify
            const deleted = await storage.delete(textHash);
            expect(deleted).toBe(true);
            
            const retrieved = await storage.get(textHash);
            expect(retrieved).toBeNull();
        });

        it('should return false when deleting non-existent cards', async () => {
            const deleted = await storage.delete('nonexistent'.padEnd(64, '0'));
            expect(deleted).toBe(false);
        });
    });
});
