const { config, startServer, stopServer } = require('./config/test-config');
const MCardClient = require('../src/client');

// Global test setup
beforeAll(async () => {
    // Server will be started by test-config.js
    global.testClient = new MCardClient(config.client.defaultConfig);
});

// Global test teardown
afterAll(async () => {
    // Server will be stopped by test-config.js
    delete global.testClient;
});
