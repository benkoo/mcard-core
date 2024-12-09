const { TestEnvironment } = require('./test-utils');

module.exports = async () => {
    try {
        await TestEnvironment.cleanupGlobalInstance();
    } catch (error) {
        console.error(' Global teardown failed:', error);
        throw error;
    }
};
