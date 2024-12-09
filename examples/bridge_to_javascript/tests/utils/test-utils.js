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
        console.log('🔧 Setting up test environment...');
        await this.createEnvFile();
        
        // Ensure server is stopped first
        await this.stopServer();
        
        // Start server with multiple attempts
        await this.startServerWithRetry();
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

    async startServerWithRetry(maxRetries = 3) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`🚀 Server Startup Attempt ${attempt}/${maxRetries}`);
                await this.startServer();
                
                // Verify server is truly running
                const isRunning = await this.isServerRunning();
                if (isRunning) {
                    console.log('✅ Server successfully started and verified');
                    return;
                }
            } catch (error) {
                console.error(`❌ Server startup attempt ${attempt} failed:`, error.message);
                
                // Stop server to clean up resources
                await this.stopServer();
                
                // Wait a bit before retrying
                await new Promise(resolve => setTimeout(resolve, 2000 * attempt));
            }
        }
        
        throw new Error(`Failed to start server after ${maxRetries} attempts`);
    }

    async waitForServer(maxAttempts = 30) {
        console.log('🕒 Waiting for server to start...');
        for (let i = 0; i < maxAttempts; i++) {
            try {
                console.log(`Attempt ${i + 1}: Checking server health...`);
                const response = await axios.get('http://localhost:5320/health', {
                    headers: { 'X-API-Key': 'dev_key_123' },
                    timeout: 2000
                });
                
                if (response.status === 200) {
                    console.log('✅ Server is running successfully!');
                    return true;
                }
            } catch (error) {
                console.log(`Attempt ${i + 1} failed:`, error.message);
                // Exponential backoff
                await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
            }
        }
        
        console.error('❌ Server failed to start after maximum attempts');
        throw new Error('Server did not start within the expected time');
    }

    async startServer() {
        console.log('🚀 Attempting to start MCard server...');
        
        // Kill any existing server process first
        await this.stopServer();

        // Try multiple Python paths
        const pythonPaths = [
            'python3',
            'python',
            '/usr/local/bin/python3',
            '/usr/bin/python3',
            path.join(process.cwd(), '.venv', 'bin', 'python')
        ];

        let pythonPath = null;
        for (const tryPath of pythonPaths) {
            try {
                const { stdout } = await this.execShell(`which ${tryPath}`);
                if (stdout.trim()) {
                    pythonPath = tryPath;
                    break;
                }
            } catch (error) {
                console.log(`Path ${tryPath} not found`);
                continue;
            }
        }

        if (!pythonPath) {
            throw new Error('No suitable Python interpreter found');
        }

        console.log(`Using Python interpreter: ${pythonPath}`);

        // Create data directory if it doesn't exist
        const dataDir = path.join(process.cwd(), 'data');
        try {
            await fs.mkdir(dataDir, { recursive: true });
        } catch (error) {
            console.warn('Could not create data directory:', error);
        }

        // Start server with detached mode and its own process group
        this.serverProcess = spawn(pythonPath, ['src/server.py'], {
            cwd: process.cwd(),
            detached: true,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
        });

        // Handle server output
        this.serverProcess.stdout.on('data', (data) => {
            console.log(`Server stdout: ${data}`);
        });

        this.serverProcess.stderr.on('data', (data) => {
            console.error(`Server stderr: ${data}`);
        });

        // Set a timeout for server startup
        const startupTimeout = new Promise((_, reject) => {
            setTimeout(() => {
                reject(new Error('Server startup timeout'));
            }, 30000); // 30 seconds timeout
        });

        try {
            // Race between server startup and timeout
            await Promise.race([
                this.waitForServer(),
                startupTimeout
            ]);
        } catch (error) {
            console.error('Server startup failed:', error);
            await this.stopServer();
            throw error;
        }
    }

    async stopServer() {
        console.log('🛑 Attempting to stop server...');
        
        // Attempt to gracefully terminate the server process
        if (this.serverProcess) {
            try {
                // Check if the process is still running before attempting to kill
                try {
                    process.kill(this.serverProcess.pid, 0);
                } catch (err) {
                    console.log('Server process already terminated');
                    this.serverProcess = null;
                    return;
                }

                // Send SIGTERM to allow graceful shutdown
                process.kill(this.serverProcess.pid, 'SIGTERM');
                
                // Wait a short time for graceful shutdown
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // If still running, force kill
                try {
                    process.kill(this.serverProcess.pid, 'SIGKILL');
                } catch (err) {
                    // Ignore if process is already dead
                    if (err.code !== 'ESRCH') {
                        console.error('Error force killing server:', err);
                    }
                }
            } catch (error) {
                // Only log if it's not a "No such process" error
                if (error.code !== 'ESRCH') {
                    console.error('Error stopping server:', error);
                }
            }
            
            this.serverProcess = null;
        }
        
        // Attempt to clear any lingering server ports
        try {
            await this.killPortProcess(5320);
        } catch (error) {
            console.error('Error killing port process:', error);
        }
    }

    async killPortProcess(port) {
        return new Promise((resolve, reject) => {
            const { exec } = require('child_process');
            
            // Find and kill any process using the specified port
            exec(`lsof -ti:${port} | xargs kill -9`, (error, stdout, stderr) => {
                if (error && error.code !== 1) {
                    reject(error);
                } else {
                    resolve();
                }
            });
        });
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

    // Add a helper method to execute shell commands
    async execShell(cmd) {
        return new Promise((resolve, reject) => {
            const { exec } = require('child_process');
            exec(cmd, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve({ stdout, stderr });
                }
            });
        });
    }
}

module.exports = {
    TestEnvironment
};
