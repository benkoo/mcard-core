const { spawn } = require('child_process');
const { execSync } = require('child_process');
const path = require('path');

async function startServer() {
    console.log('Starting server...');
    const serverProcess = spawn('python3', ['src/server.py'], {
        cwd: process.cwd(),
        stdio: 'pipe',
        detached: true
    });

    serverProcess.stdout.on('data', (data) => {
        console.log(`Server stdout: ${data}`);
    });

    serverProcess.stderr.on('data', (data) => {
        console.error(`Server stderr: ${data}`);
    });

    // Wait for server to start
    await new Promise(resolve => setTimeout(resolve, 3000));

    return serverProcess;
}

async function runTests() {
    let serverProcess;
    try {
        // Start the server
        serverProcess = await startServer();

        // Run tests
        console.log('Running tests...');
        execSync('npm test tests/client.test.js', { 
            stdio: 'inherit',
            cwd: process.cwd()
        });
    } catch (error) {
        console.error('Test execution failed:', error);
        process.exitCode = 1;
    } finally {
        // Attempt to stop the server
        if (serverProcess) {
            try {
                process.kill(-serverProcess.pid);
            } catch (killError) {
                console.warn('Error killing server process:', killError);
            }
        }
    }
}

runTests();
