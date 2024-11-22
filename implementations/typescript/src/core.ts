import { createHash } from 'crypto';

export function getNowWithLocatedZone(): Date {
    return new Date();
}

export class MCard {
    private readonly _content: any;
    private readonly _contentHash: string;
    private readonly _timeClaimed: Date;

    constructor(content: any, contentHash?: string, timeClaimed?: Date) {
        this._content = content;
        this._contentHash = contentHash ? this.validateAndNormalizeHash(contentHash) : this.calculateHash(content);
        this._timeClaimed = timeClaimed || getNowWithLocatedZone();
    }

    private calculateHash(content: string | Buffer): string {
        const hash = createHash('sha256');
        hash.update(typeof content === 'string' ? Buffer.from(content) : content);
        return hash.digest('hex');
    }

    private validateAndNormalizeHash(hash: string): string {
        // Check hash length
        if (hash.length !== 64) {
            throw new Error('Content hash must be 64 characters long');
        }

        // Check if hash contains only valid hexadecimal characters
        if (!/^[0-9a-fA-F]{64}$/.test(hash)) {
            throw new Error('Content hash must contain only hexadecimal characters');
        }

        // Normalize to lowercase
        return hash.toLowerCase();
    }

    get content(): any {
        return this._content;
    }

    get contentHash(): string {
        return this._contentHash;
    }

    get timeClaimed(): Date {
        return this._timeClaimed;
    }

    get isBinary(): boolean {
        return Buffer.isBuffer(this._content);
    }
}
