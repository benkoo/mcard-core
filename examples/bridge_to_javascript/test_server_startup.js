const { spawn } = require('child_process');
const MCardServiceProxy = require('./src/mcard_service_proxy');

async function killExistingProcesses() {
    return new Promise((resolve, reject) => {
        const killProcess = spawn('pkill', ['-f', 'python']);
        
        killProcess.on('close', (code) => {
            console.log(`Killed existing processes. Exit code: ${code}`);
            resolve();
        });
        
        killProcess.on('error', (err) => {
            console.error('Error killing processes:', err);
            reject(err);
        });
    });
}

async function testServerStartup() {
    // Kill any existing Python processes
    await killExistingProcesses();

    // Set test environment variables
    process.env.NODE_ENV = 'test';
    process.env.MCARD_API_KEY = 'valid_test_key';
    process.env.PORT = '0'; // Use dynamic port selection
    process.env.MCARD_STORE_PATH = './data/mcard.db';

    // Create an instance of MCardServiceProxy
    const mcardService = MCardServiceProxy.getInstance();

    try {
        console.log('Attempting to start server...');
        const serverStarted = await mcardService.startServer();
        
        if (serverStarted) {
            console.log('Server started successfully!');
            
            // Optional: Add a health check or status check
            const serverStatus = await mcardService.status();
            console.log('Server status:', serverStatus);

            // Wait a bit to ensure server is running
            await new Promise(resolve => setTimeout(resolve, 5000));

            // Stop the server
            await mcardService.stopServer();
            console.log('Server stopped successfully.');
        } else {
            console.error('Failed to start server');
        }
    } catch (error) {
        console.error('Error during server startup:', error);
    }
}

testServerStartup().catch(console.error);
