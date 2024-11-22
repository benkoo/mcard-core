import { MCard } from './core';
import { createHash } from 'crypto';

describe('MCard', () => {
    const validContent = 'Hello World';
    const validHash = '6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba';

    describe('constructor', () => {
        it('should create an MCard with valid data and provided hash', () => {
            const card = new MCard(validContent, validHash);
            
            expect(card.content).toBe(validContent);
            expect(card.contentHash).toBe(validHash);
            expect(card.timeClaimed).toBeInstanceOf(Date);
        });

        it('should create an MCard with auto-generated hash', () => {
            const card = new MCard(validContent);
            const expectedHash = createHash('sha256')
                .update(Buffer.from(validContent))
                .digest('hex');
            
            expect(card.content).toBe(validContent);
            expect(card.contentHash).toBe(expectedHash);
            expect(card.timeClaimed).toBeInstanceOf(Date);
        });

        it('should handle binary content', () => {
            const binaryContent = Buffer.from([1, 2, 3, 4]);
            const card = new MCard(binaryContent);
            
            expect(Buffer.isBuffer(card.content)).toBe(true);
            expect(card.isBinary).toBe(true);
        });
    });

    describe('content hash validation', () => {
        it('should throw error for invalid hash length', () => {
            expect(() => {
                new MCard(validContent, 'abc123');
            }).toThrow('Content hash must be 64 characters long');
        });

        it('should throw error for invalid hex characters', () => {
            expect(() => {
                new MCard(validContent, 'x'.repeat(64));
            }).toThrow('Content hash must contain only hexadecimal characters');
        });

        it('should normalize hash to lowercase', () => {
            const card = new MCard(validContent, validHash.toUpperCase());
            expect(card.contentHash).toBe(validHash.toLowerCase());
        });
    });

    describe('time_claimed handling', () => {
        it('should auto-generate timestamp if not provided', () => {
            const card = new MCard(validContent, validHash);
            expect(card.timeClaimed).toBeInstanceOf(Date);
        });

        it('should accept custom timestamp', () => {
            const customDate = new Date('2024-01-01T12:00:00Z');
            const card = new MCard(validContent, validHash, customDate);
            expect(card.timeClaimed).toBe(customDate);
        });
    });
});
