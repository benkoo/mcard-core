const { spawn } = require('child_process');
const path = require('path');

// Order of test execution
const testFiles = [
    // Core functionality tests first
    'client.test.js',           // Basic CRUD and core functionality
    'initialization.test.js',   // Client initialization tests
    
    // Feature-specific tests
    'basic-operations.test.js', // Basic operations
    'content-types.test.js',    // Content type handling
    'validation.test.js',       // Input validation and boundaries
    
    // Advanced tests
    'error-handling.test.js',   // Error handling scenarios
    'concurrency.test.js',      // Concurrent operations
    'performance.test.js',      // Performance tests
    
    // Utility tests last
    'utils.test.js'            // Utility function tests
];

// Helper function to run a single test file
function runTest(testFile) {
    return new Promise((resolve, reject) => {
        console.log(`\n🧪 Running ${testFile}...`);
        console.log('━'.repeat(50));
        
        const jest = spawn('npx', ['jest', testFile, '--colors'], {
            stdio: 'inherit',
            cwd: path.join(__dirname)
        });

        jest.on('close', (code) => {
            if (code === 0) {
                console.log('━'.repeat(50));
                console.log(`✅ ${testFile} completed successfully\n`);
                resolve();
            } else {
                reject(new Error(`Test ${testFile} failed with code ${code}`));
            }
        });

        jest.on('error', (err) => {
            reject(err);
        });
    });
}

// Run all tests in sequence
async function runAllTests() {
    console.log('\n🚀 Starting MCardClient Test Suite');
    console.log('═'.repeat(50));
    
    const startTime = Date.now();
    let passedTests = 0;
    let failedTests = [];

    for (const testFile of testFiles) {
        try {
            await runTest(testFile);
            passedTests++;
        } catch (error) {
            failedTests.push({ file: testFile, error: error.message });
            console.error(`\n❌ ${testFile} failed:`, error.message);
        }
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log('═'.repeat(50));
    console.log('\n📊 Test Suite Summary');
    console.log('───────────────────');
    console.log(`Duration: ${duration}s`);
    console.log(`Passed: ${passedTests}/${testFiles.length}`);
    
    if (failedTests.length > 0) {
        console.log('\n❌ Failed Tests:');
        failedTests.forEach(({ file, error }) => {
            console.log(`  • ${file}: ${error}`);
        });
        process.exit(1);
    } else {
        console.log('\n✨ All tests completed successfully!\n');
    }
}

// Run the test suite
runAllTests();
