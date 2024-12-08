const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

const ENV_CONTENT = `# Server Configuration
MCARD_API_KEY=dev_key_123
MCARD_API_PORT=5320

# Database Settings
MCARD_DB_PATH=data/mcard.db
MCARD_STORE_MAX_CONNECTIONS=5
MCARD_STORE_TIMEOUT=30.0

# Hash Configuration
MCARD_HASH_ALGORITHM=sha256`;

class TestEnvironment {
    constructor() {
        this.rootDir = path.resolve(__dirname, '../..');
        this.serverProcess = null;
    }

    async setup() {
        await this.createEnvFile();
        await this.startServer();
    }

    async createEnvFile() {
        const envPath = path.join(this.rootDir, '.env');
        await fs.writeFile(envPath, ENV_CONTENT);
    }

    async isServerRunning() {
        try {
            const response = await axios.get('http://127.0.0.1:5320/health', {
                headers: { 'X-API-Key': 'dev_key_123' },
                timeout: 1000
            });
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }

    async startServer() {
        // Kill any existing server process first
        await this.stopServer();

        console.log('🚀 Starting MCard server...');
        
        // Use Python from .venv
        const pythonPath = path.join(process.cwd(), '.venv', 'bin', 'python');
        
        // Start server with detached mode and its own process group
        this.serverProcess = spawn(pythonPath, ['src/server.py'], {
            cwd: process.cwd(),
            detached: true,
            stdio: ['ignore', 'pipe', 'pipe']
        });

        // Handle server output
        this.serverProcess.stdout.on('data', (data) => {
            console.log(`Server stdout: ${data}`);
        });

        this.serverProcess.stderr.on('data', (data) => {
            console.error(`Server stderr: ${data}`);
        });

        console.log('⏳ Waiting for server to start...');
        await this.waitForServer();
    }

    async stopServer() {
        if (this.serverProcess) {
            try {
                // Try graceful shutdown first
                await axios.post('http://localhost:5320/shutdown', null, {
                    headers: { 'X-API-Key': 'dev_key_123' },
                    timeout: 1000
                }).catch(() => {});

                // Kill process group
                process.kill(-this.serverProcess.pid);
            } catch (error) {
                // Ignore errors, server might already be down
            }

            this.serverProcess = null;
            // Wait for port to be released
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    async waitForServer(maxAttempts = 30) {
        for (let i = 0; i < maxAttempts; i++) {
            try {
                await axios.get('http://localhost:5320/health', {
                    headers: { 'X-API-Key': 'dev_key_123' },
                    timeout: 1000
                });
                console.log('✅ Server is ready!');
                return;
            } catch (error) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
        throw new Error('Server failed to start');
    }

    async cleanup() {
        // Delete all cards before stopping the server
        try {
            await axios.delete('http://localhost:5320/cards', {
                headers: { 'X-API-Key': 'dev_key_123' },
                timeout: 1000
            });
        } catch (error) {
            console.warn('Failed to delete cards during cleanup:', error.message);
        }

        await this.stopServer();
    }

    static async getGlobalInstance() {
        if (!TestEnvironment.instance) {
            TestEnvironment.instance = new TestEnvironment();
            await TestEnvironment.instance.setup();
        }
        return TestEnvironment.instance;
    }

    static async cleanupGlobalInstance() {
        if (TestEnvironment.instance) {
            await TestEnvironment.instance.cleanup();
            TestEnvironment.instance = null;
        }
    }
}

module.exports = {
    TestEnvironment
};
