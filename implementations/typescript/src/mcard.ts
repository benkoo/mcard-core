export function getNowWithLocatedZone(): Date {
    return new Date();
}

export class MCard {
    readonly content: any;
    readonly contentHash: string;
    readonly timeclaimed: Date;

    constructor(
        content: any,
        contentHash: string,
        timeclaimed?: Date
    ) {
        this.content = content;
        this.contentHash = this.validateAndNormalizeHash(contentHash);
        this.timeclaimed = timeclaimed || getNowWithLocatedZone();
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
}
