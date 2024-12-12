// Track test failures globally
global.testsFailed = false;

// Set the flag to true if any test fails
jasmine.getEnv().addReporter({
    specDone: function(result) {
        if (result.status === 'failed') {
            global.testsFailed = true;
        }
    }
});
