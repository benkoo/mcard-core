const { spawn, spawnSync } = require('child_process');
const axios = require('axios');
require('dotenv').config();

class MCardAPI {
    constructor(config) {
        this.pythonProcess = null;
        this.port = config.port;
        this.baseUrl = `http://localhost:${this.port}`;
        this.headers = { 'X-API-Key': config.api_key };
    }

    async startPythonServer() {
        const pythonPath = '/Users/bkoo/Documents/Development/mcard-core/examples/bridge_to_javascript/venv/bin/python';

        console.log('Starting Python server with:', pythonPath);
        console.log('Current working directory:', process.cwd());
        
        this.pythonProcess = spawn(pythonPath, [
            '-m', 'uvicorn',
            'server:app',
            '--port', this.port.toString(),
            '--reload',
            '--app-dir', './src'
        ], {
            env: {
                ...process.env,
                PYTHONPATH: process.cwd()
            }
        });

        this.pythonProcess.stdout.on('data', (data) => {
            console.log('Python server stdout:', data.toString());
        });

        this.pythonProcess.stderr.on('data', (data) => {
            console.error('Python server stderr:', data.toString());
        });

        // Wait for server to start
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Server startup timeout'));
            }, 5000);

            const checkServer = async () => {
                try {
                    await axios.get(`${this.baseUrl}/health`);
                    clearTimeout(timeout);
                    resolve();
                } catch (error) {
                    if (error.code === 'ECONNREFUSED') {
                        setTimeout(checkServer, 100);
                    } else {
                        clearTimeout(timeout);
                        reject(error);
                    }
                }
            };

            checkServer();
        });
    }

    async createCard(content) {
        const response = await axios.post(`${this.baseUrl}/cards`, { content }, { headers: this.headers });
        return response.data;
    }

    async getCard(hash) {
        const response = await axios.get(`${this.baseUrl}/cards/${hash}`, { headers: this.headers });
        return response.data;
    }

    async listCards(params = {}) {
        const response = await axios.get(`${this.baseUrl}/cards`, { 
            headers: this.headers,
            params 
        });
        return response.data;
    }

    async removeCard(hash) {
        const response = await axios.delete(`${this.baseUrl}/cards/${hash}`, { headers: this.headers });
        return response.data;
    }

    async close() {
        if (this.pythonProcess) {
            this.pythonProcess.kill();
        }
    }
}

async function getConfig() {
    const pythonPath = '/Users/bkoo/Documents/Development/mcard-core/examples/bridge_to_javascript/venv/bin/python';

    const setup = spawnSync(pythonPath, ['src/setup.py'], { encoding: 'utf-8' });
    if (setup.error) {
        throw new Error(`Failed to run setup: ${setup.error}`);
    }
    if (setup.status !== 0) {
        throw new Error(`Setup failed with status ${setup.status}: ${setup.stderr}`);
    }
    return JSON.parse(setup.stdout);
}

async function main() {
    try {
        // Get configuration from Python setup
        const config = await getConfig();
        console.log('Configuration loaded:', config);

        // Initialize API with config from Python
        const api = new MCardAPI(config);
        
        // Start the Python FastAPI server
        console.log('Starting Python FastAPI server...');
        await api.startPythonServer();
        console.log(`MCard API is running on ${api.baseUrl}`);
        
        // Handle shutdown
        process.on('SIGINT', async () => {
            console.log('Shutting down...');
            await api.close();
            process.exit(0);
        });

        // Example usage
        const card = await api.createCard('Hello from JavaScript!');
        console.log('Created card:', card);

        const retrieved = await api.getCard(card.hash);
        console.log('Retrieved card:', retrieved);

        const cards = await api.listCards();
        console.log('All cards:', cards);

        await api.removeCard(card.hash);
        console.log('Card deleted successfully');
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        process.exit(1);
    }
}

main().catch(console.error);
