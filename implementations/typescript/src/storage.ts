import sqlite3 from 'sqlite3';
import { MCard } from './core';
import { promisify } from 'util';

export class MCardStorage {
    private db: sqlite3.Database;

    constructor(dbPath: string = 'mcards.db') {
        this.db = new sqlite3.Database(dbPath);
        this.initialize().catch(err => {
            console.error('Failed to initialize database:', err);
            throw err;
        });
    }

    private async initialize(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.db.run(`
                CREATE TABLE IF NOT EXISTS mcards (
                    content_hash TEXT PRIMARY KEY,
                    content BLOB NOT NULL,
                    time_claimed DATETIME NOT NULL
                )
            `, (err: Error | null) => {
                if (err) {
                    reject(err);
                } else {
                    resolve();
                }
            });
        });
    }

    async save(mcard: MCard): Promise<void> {
        return new Promise((resolve, reject) => {
            const stmt = this.db.prepare(`
                INSERT OR REPLACE INTO mcards (content_hash, content, time_claimed)
                VALUES (?, ?, ?)
            `);

            // Convert content to Buffer if it's not already
            const content = Buffer.isBuffer(mcard.content)
                ? mcard.content
                : Buffer.from(String(mcard.content), 'utf-8');

            stmt.run(
                mcard.contentHash,
                content,
                mcard.timeClaimed.toISOString(),
                (err: Error | null) => {
                    stmt.finalize();
                    if (err) {
                        reject(err);
                    } else {
                        resolve();
                    }
                }
            );
        });
    }

    async get(contentHash: string): Promise<MCard | null> {
        return new Promise((resolve, reject) => {
            this.db.get(
                `SELECT content_hash, content, time_claimed
                FROM mcards
                WHERE content_hash = ?`,
                [contentHash],
                (err: Error | null, row: any) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    if (!row) {
                        resolve(null);
                        return;
                    }

                    let content: string | Buffer = row.content;
                    if (Buffer.isBuffer(content)) {
                        // Try to convert to string if it looks like text
                        try {
                            const str = content.toString('utf-8');
                            // Check if it contains only printable ASCII characters
                            if (/^[\x20-\x7E]*$/.test(str)) {
                                content = str;
                            }
                        } catch {
                            // Keep as Buffer if conversion fails
                        }
                    }

                    resolve(new MCard(
                        content,
                        row.content_hash,
                        new Date(row.time_claimed)
                    ));
                }
            );
        });
    }

    async getAll(): Promise<MCard[]> {
        return new Promise((resolve, reject) => {
            this.db.all(
                `SELECT content_hash, content, time_claimed
                FROM mcards`,
                [],
                (err: Error | null, rows: any[]) => {
                    if (err) {
                        reject(err);
                        return;
                    }

                    const mcards = rows.map(row => {
                        let content: string | Buffer = row.content;
                        if (Buffer.isBuffer(content)) {
                            // Try to convert to string if it looks like text
                            try {
                                const str = content.toString('utf-8');
                                // Check if it contains only printable ASCII characters
                                if (/^[\x20-\x7E]*$/.test(str)) {
                                    content = str;
                                }
                            } catch {
                                // Keep as Buffer if conversion fails
                            }
                        }

                        return new MCard(
                            content,
                            row.content_hash,
                            new Date(row.time_claimed)
                        );
                    });

                    resolve(mcards);
                }
            );
        });
    }

    async delete(contentHash: string): Promise<boolean> {
        return new Promise((resolve, reject) => {
            this.db.run(
                `DELETE FROM mcards
                WHERE content_hash = ?`,
                [contentHash],
                function(err: Error | null) {
                    if (err) {
                        reject(err);
                        return;
                    }
                    resolve(this.changes > 0);
                }
            );
        });
    }

    close(): void {
        this.db.close();
    }
}
