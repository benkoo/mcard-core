const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const net = require('net');
const dotenv = require('dotenv');
const MCardServiceClinic = require('./mcard_service_clinic');
const axios = require('axios'); // Added axios import

class MCardServiceProxy {
    // Private static instance holder
    static #instance = null;

    // Private constructor to prevent direct instantiation
    constructor(options = {}) {
        // Default configuration with more robust defaults
        this.config = {
            pythonPath: 'python3',
            serverScript: path.join(__dirname, 'server.py'),
            envPath: path.join(__dirname, '..', '.env'),
            host: this._getConfigValue('host'),
            port: this._getConfigValue('port'),
            apiKey: this._getConfigValue('apiKey'),
            dbPath: this._getConfigValue('dbPath'),
            maxStartupAttempts: 3,
            startupTimeout: 10000
        };

        // Override default config with provided options
        this.config = { ...this.config, ...options };

        // Validate database path
        if (!MCardServiceClinic.validateDatabasePath(this.config.dbPath)) {
            throw new Error('Invalid database path');
        }

        // Load environment variables
        this.loadEnvFile();

        // Server process reference
        this.serverProcess = null;

        // Server startup status
        this.isServerRunning = false;

        // Store the instance
        MCardServiceProxy.#instance = this;

        // Flag to track test completion
        this.isTestCompleted = false;
    }

    // Static method to get the singleton instance
    static getInstance(options = {}) {
        if (!MCardServiceProxy.#instance) {
            MCardServiceProxy.#instance = new MCardServiceProxy(options);
        }
        return MCardServiceProxy.#instance;
    }

    // Ensure only one instance can be created
    static reset() {
        if (MCardServiceProxy.#instance) {
            // Ensure server is stopped before resetting
            try {
                MCardServiceProxy.#instance.stopServer();
            } catch (error) {
                console.warn('Error stopping server during reset:', error);
            }
            MCardServiceProxy.#instance = null;
        }
    }

    // Expose methods for easier testing
    static async startServer(options = {}) {
        const instance = this.getInstance(options);
        return await instance.startServer();
    }

    static async stopServer() {
        const instance = this.getInstance();
        return await instance.stopServer();
    }

    loadEnvFile() {
        if (fs.existsSync(this.config.envPath)) {
            dotenv.config({ path: this.config.envPath });
        }
    }

    // Validate API key using MCardServiceClinic
    validateApiKey(apiKey) {
        return MCardServiceClinic.validateApiKey(apiKey);
    }

    // Validate port number using MCardServiceClinic
    validatePortNumber(port = this.config.port) {
        return MCardServiceClinic.validatePortNumber(port);
    }

    // Validate database path using MCardServiceClinic
    validateDatabasePath(dbPath = this.config.dbPath) {
        // Check if path is null or empty
        if (!dbPath || typeof dbPath !== 'string' || dbPath.trim() === '') {
            return false;
        }

        // Check for valid file extensions
        const validExtensions = ['.db', '.sqlite', '.sqlite3'];
        const hasValidExtension = validExtensions.some(ext => dbPath.toLowerCase().endsWith(ext));
        
        if (!hasValidExtension) {
            return false;
        }

        // Optional: You could add additional checks like path length, valid characters, etc.
        return true;
    }

    // Check network connectivity using MCardServiceClinic
    async checkNetworkConnectivity() {
        return await MCardServiceClinic.checkNetworkConnectivity();
    }

    // Comprehensive server status check
    async status() {
        try {
            // Validate API key
            const apiKey = process.env.MCARD_API_KEY;
            if (!this.validateApiKey(apiKey)) {
                return false;
            }

            // Validate port number
            if (!this.validatePortNumber()) {
                return false;
            }

            // Validate database path
            if (!this.validateDatabasePath()) {
                return false;
            }

            // Check network connectivity
            const networkConnected = await this.checkNetworkConnectivity();
            if (!networkConnected) {
                console.warn('Network not connected');
                return false;
            }

            // Attempt to connect to server health endpoint
            const healthCheckUrl = `http://${this.config.host}:${this.config.port}/health`;
            const response = await axios.get(healthCheckUrl, {
                timeout: 2000,
                headers: { 'X-API-Key': apiKey }
            });

            this.isServerRunning = response.status === 200;
            return this.isServerRunning;
        } catch (error) {
            console.error('Server status check failed:', error.message);
            this.isServerRunning = false;
            return false;
        }
    }

    _getConfigValue(key, defaultValue) {
        // Centralized method to get configuration values
        switch(key) {
            case 'dbPath':
                return process.env.MCARD_STORE_PATH || 
                       process.env.MCARD_DB_PATH || 
                       defaultValue || 
                       path.join(__dirname, '..', 'data', 'mcard.db');
            
            case 'host':
                return process.env.SERVER_HOST || 'localhost';
            
            case 'port':
                // Ensure port is a valid number
                const portValue = process.env.PORT || defaultValue || null;
                
                // In test environment, try to find an available port
                if (process.env.NODE_ENV === 'test') {
                    // Return null to trigger port finding in _startServer
                    return null;
                }
                
                return portValue;
            
            case 'apiKey':
                return process.env.MCARD_API_KEY || 'default_key';
            
            default:
                return defaultValue;
        }
    }

    async _startServer() {
        return new Promise(async (resolve, reject) => {
            try {
                // Kill any existing server processes first
                await this._killExistingServer();

                // Spawn the server process
                this.serverProcess = spawn(this.config.pythonPath, [
                    this.config.serverScript
                ], {
                    env: process.env,
                    stdio: 'pipe'
                });

                // Capture server output
                this.serverProcess.stdout.on('data', (data) => {
                    console.log('Server stdout:', data.toString().trim());
                });

                this.serverProcess.stderr.on('data', (data) => {
                    console.log('Server stderr:', data.toString().trim());
                });

                // Handle server process exit
                this.serverProcess.on('close', (code, signal) => {
                    // Only log if tests are still running
                    if (!this.isTestCompleted) {
                        console.log(`Server process exited with code ${code} and signal ${signal}`);
                    }
                    this.isServerRunning = false;
                });

                // Wait for server to start and get the actual port
                const serverPort = await this._waitForServerStartup();

                resolve(serverPort);
            } catch (error) {
                console.error('Error starting server:', error);
                reject(error);
            }
        });
    }

    async _waitForServerStartup(maxAttempts = 5, interval = 1000) {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            let serverPort = null;
            let portExtracted = false;

            const serverOutputListener = (data) => {
                const output = data.toString().trim();
                console.log('Server Output:', output);

                // Look for port information in the server output
                const portMatch = output.match(/Port:\s*(\d+)/);
                if (portMatch && !portExtracted) {
                    serverPort = parseInt(portMatch[1], 10);
                    console.log(`Extracted port from server output: ${serverPort}`);
                    portExtracted = true;

                    // Validate and resolve with the port
                    if (serverPort && serverPort > 0) {
                        this.serverProcess.stdout.removeListener('data', serverOutputListener);
                        this.serverProcess.stderr.removeListener('data', serverOutputListener);
                        resolve(serverPort);
                    }
                }
            };

            // Add output listeners to capture port
            this.serverProcess.stdout.on('data', serverOutputListener);
            this.serverProcess.stderr.on('data', serverOutputListener);

            // Timeout to prevent indefinite waiting
            const startupTimeout = setTimeout(() => {
                this.serverProcess.stdout.removeListener('data', serverOutputListener);
                this.serverProcess.stderr.removeListener('data', serverOutputListener);
                reject(new Error('Server startup timeout: Could not extract port'));
            }, maxAttempts * interval);

            // Handle server process exit
            this.serverProcess.on('exit', (code, signal) => {
                clearTimeout(startupTimeout);
                this.serverProcess.stdout.removeListener('data', serverOutputListener);
                this.serverProcess.stderr.removeListener('data', serverOutputListener);
                
                if (code !== 0) {
                    reject(new Error(`Server process exited with code ${code}`));
                }
            });
        });
    }

    async _findAvailablePort(startPort = 0, maxAttempts = 10) {
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            const port = startPort === 0 ? 0 : (startPort + attempt);
            try {
                const isAvailable = await this._checkPortAvailable(port);
                if (isAvailable) {
                    console.log(`Found available port: ${port}`);
                    return port;
                }
            } catch (error) {
                console.error(`Error checking port ${port}:`, error);
            }
        }
        throw new Error(`Could not find an available port after ${maxAttempts} attempts`);
    }

    async _checkPortAvailable(port) {
        return new Promise((resolve, reject) => {
            const server = net.createServer();
            
            server.listen(port, () => {
                server.close(() => {
                    resolve(true);
                });
            });
            
            server.on('error', (err) => {
                if (err.code === 'EADDRINUSE') {
                    resolve(false);
                } else {
                    reject(err);
                }
            });
        });
    }

    async startServer() {
        // Prevent multiple server starts
        if (this.isServerRunning) {
            console.log('Server is already running');
            return true;
        }

        try {
            // Ensure clean configuration
            const configChecks = [
                { 
                    check: MCardServiceClinic.validateApiKey, 
                    value: this._getConfigValue('apiKey'),
                    defaultAction: () => {
                        console.warn('Using default API key');
                        process.env.MCARD_API_KEY = 'default_key';
                    }
                },
                { 
                    check: MCardServiceClinic.validatePortNumber, 
                    value: this._getConfigValue('port'),
                    defaultAction: () => {
                        console.warn('Using dynamic port selection');
                        process.env.PORT = '0';
                    }
                },
                { 
                    check: MCardServiceClinic.validateDatabasePath, 
                    value: this._getConfigValue('dbPath'),
                    defaultAction: () => {
                        const defaultDbPath = path.join(__dirname, '..', 'data', 'mcard.db');
                        console.warn(`Using default database path: ${defaultDbPath}`);
                        process.env.MCARD_STORE_PATH = defaultDbPath;
                    }
                }
            ];

            // Validate and set defaults if needed
            configChecks.forEach(({ check, value, defaultAction }) => {
                if (!check(value)) {
                    defaultAction();
                }
            });

            // Start server and wait for port
            const serverPort = await this._startServer();
            
            // Mark server as running and store port
            this.isServerRunning = true;
            this.serverPort = serverPort;

            console.log(`Server started successfully on port ${serverPort}`);
            return true;
        } catch (error) {
            console.error('Failed to start server:', error);
            this.isServerRunning = false;
            return false;
        }
    }

    async _createCard(content, options = {}) {
        try {
            const payload = {
                content: content,
                metadata: options
            };

            const response = await axios.post(`http://${this.config.host}:${this.serverPort}/cards`, 
                payload, 
                { 
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-API-Key': process.env.MCARD_API_KEY || 'default_key'
                    }
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error creating card:', error.response ? error.response.data : error.message);
            throw error;
        }
    }

    async createCard(content, options = {}) {
        // Ensure server is running before creating card
        await this.startServer();
        
        // If content is an object, assume it's the new structure
        if (typeof content === 'object' && content.content) {
            options = content.metadata || {};
            content = content.content;
        }

        return this._createCard(content, options);
    }

    async _getCard(hash, options = {}) {
        try {
            const response = await axios.get(`http://${this.config.host}:${this.serverPort}/cards/${hash}`, 
                { 
                    headers: { 
                        'X-API-Key': process.env.MCARD_API_KEY || 'default_key'
                    },
                    ...options 
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error retrieving card:', error.response ? error.response.data : error.message);
            throw error;
        }
    }

    async getCard(hash, options = {}) {
        if (!this.isServerRunning) {
            await this.startServer();
        }

        return this._getCard(hash, options);
    }

    async _listCards(options = {}) {
        try {
            const response = await axios.get(`http://${this.config.host}:${this.serverPort}/cards`, 
                { 
                    headers: { 
                        'X-API-Key': process.env.MCARD_API_KEY || 'default_key'
                    },
                    ...options 
                }
            );
            console.log('List Cards Response:', response.data);
            return response.data;
        } catch (error) {
            console.error('Error listing cards:', error.response ? error.response.data : error.message);
            throw error;
        }
    }

    async listCards(options = {}) {
        if (!this.isServerRunning) {
            await this.startServer();
        }

        return this._listCards(options);
    }

    async _deleteAllCards(options = {}) {
        try {
            const response = await axios.delete(`http://${this.config.host}:${this.serverPort}/cards`, 
                { 
                    headers: { 
                        'X-API-Key': process.env.MCARD_API_KEY || 'default_key'
                    },
                    ...options 
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error deleting cards:', error.response ? error.response.data : error.message);
            throw error;
        }
    }

    async deleteAllCards(options = {}) {
        if (!this.isServerRunning) {
            await this.startServer();
        }

        return this._deleteAllCards(options);
    }

    async stopServer() {
        return new Promise((resolve, reject) => {
            if (!this.serverProcess) {
                this.isServerRunning = false;
                this.isTestCompleted = true; // Set test completion flag
                resolve(true);
                return;
            }

            try {
                // Prevent logging after tests
                const stdoutListener = (data) => {};
                const stderrListener = (data) => {};

                this.serverProcess.stdout.on('data', stdoutListener);
                this.serverProcess.stderr.on('data', stderrListener);

                // Handle server process exit
                this.serverProcess.on('exit', (code, signal) => {
                    // Remove listeners to prevent post-test logging
                    this.serverProcess.stdout.removeListener('data', stdoutListener);
                    this.serverProcess.stderr.removeListener('data', stderrListener);

                    this.isServerRunning = false;
                    this.serverProcess = null;
                    this.serverPort = null;

                    if (code !== 0 && code !== null) {
                        reject(new Error(`Server stopped with code ${code}`));
                    } else {
                        this.isTestCompleted = true; // Set test completion flag
                        resolve(true);
                    }
                });

                // Attempt to kill the process
                if (process.platform === 'win32') {
                    exec(`taskkill /pid ${this.serverProcess.pid} /T /F`);
                } else {
                    this.serverProcess.kill('SIGTERM');
                }
            } catch (error) {
                console.warn('Error during server stop:', error);
                this.isServerRunning = false;
                this.serverProcess = null;
                this.isTestCompleted = true; // Set test completion flag
                resolve(true);
            }
        });
    }

    async _killExistingServer() {
        try {
            const serverPort = process.env.PORT || 5320;
            console.log(`Attempting to kill processes on port ${serverPort}`);
            
            // Use a more robust method to kill processes
            const killProcess = spawn('lsof', ['-ti', `:${serverPort}`]);
            
            return new Promise((resolve, reject) => {
                let pidOutput = '';
                
                killProcess.stdout.on('data', (data) => {
                    pidOutput += data.toString().trim();
                });
                
                killProcess.on('close', (code) => {
                    if (pidOutput) {
                        console.log(`Found processes on port ${serverPort}: ${pidOutput}`);
                        const pids = pidOutput.split('\n');
                        
                        // Kill each process individually
                        const killPromises = pids.map(pid => {
                            return new Promise((resolveKill, rejectKill) => {
                                const killCmd = spawn('kill', ['-9', pid]);
                                
                                killCmd.on('close', (killCode) => {
                                    if (killCode === 0) {
                                        console.log(`Successfully killed process ${pid}`);
                                        resolveKill(true);
                                    } else {
                                        console.error(`Failed to kill process ${pid}`);
                                        rejectKill(new Error(`Kill command failed with code ${killCode}`));
                                    }
                                });
                            });
                        });
                        
                        // Wait for all kill attempts to complete
                        Promise.allSettled(killPromises)
                            .then(results => {
                                const failed = results.filter(r => r.status === 'rejected');
                                if (failed.length > 0) {
                                    console.error(`Failed to kill ${failed.length} processes`);
                                    reject(new Error('Some processes could not be killed'));
                                } else {
                                    resolve(true);
                                }
                            });
                    } else {
                        console.log(`No processes found on port ${serverPort}`);
                        resolve(true);
                    }
                });
                
                killProcess.on('error', (err) => {
                    console.error('Error finding processes:', err);
                    reject(err);
                });
            });
        } catch (error) {
            console.error('Unexpected error killing existing server:', error);
            throw error;
        }
    }
}

// Export both the class and a function to get the singleton instance
module.exports = MCardServiceProxy;
module.exports.default = MCardServiceProxy;
module.exports.getMCardServiceProxy = function(options = {}) {
    return MCardServiceProxy.getInstance(options);
};
