// Set environment variables for tests
process.env.MCARD_API_KEY = process.env.MCARD_API_KEY || 'test_api_key';
process.env.MCARD_API_PORT = process.env.MCARD_API_PORT || '5320';

const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');

// Configuration object
const config = {
    // Server configuration
    server: {
        apiKey: process.env.MCARD_API_KEY,
        port: parseInt(process.env.MCARD_API_PORT, 10),
        pythonPath: path.join(__dirname, '../../.venv/bin/python'),
        serverScript: path.join(__dirname, '../../src/server.py'),
        healthCheckRetries: 10,
        healthCheckDelay: 1000,
        healthEndpoint: '/health'
    },
    
    // Client configuration
    client: {
        defaultConfig: {
            apiKey: process.env.MCARD_API_KEY,
            baseUrl: `http://127.0.0.1:${process.env.MCARD_API_PORT}`
        },
        invalidConfig: {
            apiKey: 'invalid_key',
            baseUrl: `http://127.0.0.1:${process.env.MCARD_API_PORT}`
        }
    },
    
    // Test suite configuration
    testSuite: {
        cleanup: {
            enabled: true,
            maxRetries: 3,
            retryDelay: 1000
        }
    },
    
    // Test data configuration
    testData: {
        testDataDir: path.join(__dirname, '../test-data'),
        maxFileSize: 5 * 1024 * 1024, // 5MB
        defaultBatchSize: 100
    }
};

let serverProcess = null;

// Check if server is already running on the port
async function isServerRunning() {
    try {
        const response = await axios.get(`${config.client.defaultConfig.baseUrl}${config.server.healthEndpoint}`, {
            headers: { 'X-API-Key': config.server.apiKey }
        });
        return response.status === 200;
    } catch (error) {
        return false;
    }
}

// Kill any existing server process on the port
async function killExistingServer() {
    try {
        const findProcess = spawn('lsof', ['-i', `:${config.server.port}`]);
        findProcess.stdout.on('data', async (data) => {
            const lines = data.toString().split('\n');
            for (const line of lines) {
                const parts = line.trim().split(/\s+/);
                if (parts.length > 1) {
                    const pid = parts[1];
                    try {
                        process.kill(parseInt(pid, 10), 'SIGKILL');
                    } catch (err) {
                        // Ignore errors if process is already gone
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error finding/killing process:', error);
    }

    // Wait a bit to ensure the port is released
    await new Promise(resolve => setTimeout(resolve, config.testSuite.cleanup.retryDelay));
}

// Wait for server to be ready
async function waitForServer(retries = config.server.healthCheckRetries, delay = config.server.healthCheckDelay) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await axios.get(`${config.client.defaultConfig.baseUrl}${config.server.healthEndpoint}`, {
                headers: { 'X-API-Key': config.server.apiKey }
            });
            if (response.status === 200) {
                return true;
            }
        } catch (error) {
            // Ignore errors and continue retrying
        }
        await new Promise(resolve => setTimeout(resolve, delay));
    }
    return false;
}

// Start the server
async function startServer() {
    console.log('Checking for existing server...');
    const serverRunning = await isServerRunning();
    
    if (serverRunning) {
        console.log('Existing server found, stopping it...');
        await killExistingServer();
    }

    if (serverProcess) {
        console.log('Stopping existing server process...');
        await stopServer();
    }

    return new Promise(async (resolve, reject) => {
        console.log(`Starting server with Python: ${config.server.pythonPath}`);
        console.log(`Server script path: ${config.server.serverScript}`);
        
        try {
            // Set environment variables for the server
            const env = {
                ...process.env,
                MCARD_API_KEY: config.server.apiKey,
                MCARD_API_PORT: config.server.port.toString(),
                PYTHONPATH: path.join(__dirname, '../..')
            };

            // Start server process in a new process group
            serverProcess = spawn(config.server.pythonPath, [config.server.serverScript], { 
                detached: true,
                stdio: ['ignore', 'pipe', 'pipe'],
                env
            });
            
            // Handle immediate spawn errors
            serverProcess.on('error', (error) => {
                console.error(`Failed to start server: ${error.message}`);
                serverProcess = null;
                reject(error);
            });

            // Handle process exit
            serverProcess.on('close', (code) => {
                if (code !== 0 && code !== null) {
                    console.error(`Server process exited with code ${code}`);
                }
                serverProcess = null;
            });

            // Capture stdout for debugging
            if (serverProcess.stdout) {
                serverProcess.stdout.on('data', (data) => {
                    console.log(`Server output: ${data}`);
                });
            }

            // Capture stderr for debugging
            if (serverProcess.stderr) {
                serverProcess.stderr.on('data', (data) => {
                    console.error(`Server error: ${data}`);
                });
            }

            // Wait for server to be ready
            console.log('Waiting for server to be ready...');
            const serverReady = await waitForServer();
            if (!serverReady) {
                throw new Error('Server failed to start within the timeout period');
            }
            console.log('Server is ready!');
            resolve();
        } catch (error) {
            console.error(`Error spawning server process: ${error.message}`);
            if (serverProcess) {
                try {
                    process.kill(-serverProcess.pid);
                } catch (killError) {
                    console.error('Error killing server process:', killError);
                }
                serverProcess = null;
            }
            reject(error);
        }
    });
}

// Stop the server
async function stopServer() {
    return new Promise((resolve) => {
        if (!serverProcess) {
            console.log('No server process to stop');
            resolve();
            return;
        }

        console.log('Stopping server...');
        
        const cleanup = () => {
            serverProcess = null;
            console.log('Server stopped successfully');
            resolve();
        };

        try {
            // Try graceful shutdown first
            process.kill(-serverProcess.pid);
            serverProcess.on('close', cleanup);
            
            // Force kill after timeout
            setTimeout(() => {
                if (serverProcess) {
                    try {
                        process.kill(-serverProcess.pid, 'SIGKILL');
                    } catch (error) {
                        // Process might already be gone
                    }
                    cleanup();
                }
            }, 5000);
        } catch (error) {
            console.error('Error stopping server:', error);
            cleanup();
        }
    });
}

// Initialize server before tests
beforeAll(async () => {
    try {
        await startServer();
    } catch (error) {
        console.error('Failed to start server:', error);
        throw error;
    }
});

// Cleanup after tests
afterAll(async () => {
    await stopServer();
});

module.exports = {
    config,
    startServer,
    stopServer,
    isServerRunning,
    killExistingServer
};
