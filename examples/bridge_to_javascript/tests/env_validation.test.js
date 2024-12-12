const dotenv = require('dotenv');
const fs = require('fs');
const axios = require('axios'); // Import axios
const MCardServiceProxy = require('../src/mcard_service_proxy'); // Import the service

let mcardService;

describe('Environment Variable Validation', () => {
    beforeAll(async () => {
        console.log('Starting test setup...');
        const envFilePath = '.env';
        if (!fs.existsSync(envFilePath)) {
            throw new Error(`Environment file not found: ${envFilePath}`);
        }
        dotenv.config({ path: envFilePath });
        console.log('Environment variables loaded');
        console.log('API Key present:', !!process.env.MCARD_API_KEY);
        console.log('API Port:', process.env.MCARD_API_PORT);
        console.log('DB Path:', process.env.MCARD_DB_PATH);
        
        mcardService = MCardServiceProxy.getInstance();  // Use getInstance instead of new
        console.log('Starting server...');
        try {
            await mcardService.startServer();
            console.log('Server start command completed');
            
            // Wait for server output
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Server startup timeout'));
                }, 5000);
    
                if (!mcardService.serverProcess) {
                    console.error('Server process is null, cannot access stdout');
                    reject(new Error('Server process is null'));
                    return;
                }
    
                if (!mcardService.serverProcess.stdout) {
                    console.error('Server process stdout is null');
                    reject(new Error('Server process stdout is null'));
                    return;
                }
    
                mcardService.serverProcess.stdout.on('data', (data) => {
                    console.log(`Server stdout: ${data}`);
                    clearTimeout(timeout);
                    resolve();
                });
    
                if (!mcardService.serverProcess.stderr) {
                    console.error('Server process stderr is null');
                    reject(new Error('Server process stderr is null'));
                    return;
                }
    
                mcardService.serverProcess.stderr.on('data', (data) => {
                    console.error(`Server stderr: ${data}`);
                });
    
                if (!mcardService.serverProcess.on) {
                    console.error('Server process on method is null');
                    reject(new Error('Server process on method is null'));
                    return;
                }
    
                mcardService.serverProcess.on('error', (error) => {
                    console.error('Server process error:', error);
                    clearTimeout(timeout);
                    reject(error);
                });
    
                mcardService.serverProcess.on('exit', (code) => {
                    if (code !== 0) {
                        console.error(`Server process exited with code ${code}`);
                        clearTimeout(timeout);
                        reject(new Error(`Server process exited with code ${code}`));
                    }
                });
            });
        } catch (error) {
            console.error('Error starting server:', error);
            throw error;
        }
        console.log('Server started, waiting for initialization...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        console.log('Server should be ready now');
    });

    afterAll(async () => {
        await mcardService.stopServer(); // Stop the server after tests
    });

    test('Environment variables should be defined and valid after initialization', async () => {
        expect(process.env.MCARD_DB_PATH).toBeDefined();
        expect(process.env.MCARD_DB_PATH).not.toBe('');
        expect(fs.existsSync(process.env.MCARD_DB_PATH)).toBe(true); // Check if the path exists
        expect(process.env.MCARD_API_KEY).toBeDefined();
        expect(process.env.MCARD_API_KEY).not.toBe('');
        expect(process.env.MCARD_API_PORT).toBeDefined();
        expect(parseInt(process.env.MCARD_API_PORT)).toBeGreaterThan(0);
        expect(parseInt(process.env.MCARD_API_PORT)).toBeLessThan(65536);
    });


    test('Configuration values should be accessible from the server', async () => {
        const response = await axios.get('http://localhost:5320/config', {
            headers: {
                'X-API-Key': process.env.MCARD_API_KEY
            }
        });
        const { api_key, api_port, db_path } = response.data;
    
        // Validate the values returned from the server
        expect(api_key).toBeDefined();
        expect(api_key).not.toBe('');
        expect(api_port).toBeDefined();
        expect(parseInt(api_port)).toBeGreaterThan(0);
        expect(parseInt(api_port)).toBeLessThan(65536);
        expect(db_path).toBeDefined();
        expect(db_path).not.toBe('');
        expect(fs.existsSync(db_path)).toBe(true);
    });

});
