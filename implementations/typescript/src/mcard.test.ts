import { MCard } from './mcard';

describe('MCard', () => {
    const validContent = 'Hello World';
    const validHash = '6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba';

    describe('constructor', () => {
        it('should create an MCard with valid data', () => {
            const card = new MCard(validContent, validHash);
            
            expect(card.content).toBe(validContent);
            expect(card.contentHash).toBe(validHash);
            expect(card.timeclaimed).toBeInstanceOf(Date);
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
            expect(card.timeclaimed).toBeInstanceOf(Date);
        });

        it('should accept custom timestamp', () => {
            const customDate = new Date('2024-01-01T12:00:00Z');
            const card = new MCard(validContent, validHash, customDate);
            expect(card.timeclaimed).toBe(customDate);
        });
    });
});
