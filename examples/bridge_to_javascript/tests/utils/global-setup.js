const { TestEnvironment } = require('./test-utils');

module.exports = async () => {
    try {
        await TestEnvironment.getGlobalInstance();
    } catch (error) {
        console.error('❌ Global setup failed:', error);
        throw error;
    }
};
