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

    async waitForServer(retries = 30, delay = 1000) {
        for (let i = 0; i < retries; i++) {
            if (await this.isServerRunning()) {
                console.log('✅ Server is ready!');
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, delay));
            process.stdout.write('.');
        }
        throw new Error('Server failed to start within the timeout period');
    }

    async startServer() {
        if (await this.isServerRunning()) {
            console.log('Server is already running, restarting...');
            // Try to kill any existing server process
            try {
                const response = await axios.post('http://127.0.0.1:5320/shutdown', null, {
                    headers: { 'X-API-Key': 'dev_key_123' },
                    timeout: 1000
                });
            } catch (error) {
                // Ignore errors, server might already be down
            }
            // Wait a bit for the server to fully shut down
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        console.log('🚀 Starting MCard server...');
        
        const pythonPath = path.join(this.rootDir, '.venv', 'bin', 'python');
        const serverScript = path.join(this.rootDir, 'src', 'server.py');

        this.serverProcess = spawn(pythonPath, [serverScript], {
            env: {
                ...process.env,
                PYTHONPATH: this.rootDir
            }
        });

        this.serverProcess.stdout.on('data', (data) => {
            console.log(`Server stdout: ${data}`);
        });

        this.serverProcess.stderr.on('data', (data) => {
            console.error(`Server stderr: ${data}`);
        });

        this.serverProcess.on('error', (error) => {
            console.error('Failed to start server:', error);
            throw error;
        });

        console.log('⏳ Waiting for server to start...');
        await this.waitForServer();
    }

    async cleanup() {
        if (this.serverProcess) {
            // Try graceful shutdown first
            try {
                await axios.post('http://127.0.0.1:5320/shutdown', null, {
                    headers: { 'X-API-Key': 'dev_key_123' },
                    timeout: 1000
                });
                // Wait for the server to shut down gracefully
                await new Promise(resolve => setTimeout(resolve, 2000));
            } catch (error) {
                // Ignore errors, server might already be down
            }

            // Force kill if still running
            if (this.serverProcess) {
                this.serverProcess.kill('SIGKILL');
                this.serverProcess = null;
                // Wait a bit to ensure the port is released
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
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
