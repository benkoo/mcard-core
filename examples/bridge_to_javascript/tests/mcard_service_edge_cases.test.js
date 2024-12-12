const MCardServiceProxy = require('../src/mcard_service_proxy');

describe('MCardServiceProxy Edge Cases and Error Handling', () => {
    let mcardService;

    beforeEach(() => {
        // Reset the singleton instance before each test
        jest.resetModules();
        mcardService = MCardServiceProxy.getInstance();
    });

    afterEach(async () => {
        // Ensure server is stopped after each test
        try {
            await mcardService.stopServer();
        } catch (error) {
            // Ignore errors during stopServer
            console.warn('Error during stopServer:', error);
        }
    });

    // Configuration Validation Tests
    describe('Configuration Validation', () => {
        test('should handle invalid configuration gracefully', () => {
            // Test with invalid configuration values
            expect(() => {
                mcardService._validateConfig({
                    port: -1,  // Invalid port
                    apiKey: '',  // Empty API key
                    dbPath: '/nonexistent/path'  // Non-existent path
                });
            }).toThrow();
        });

        test('should use default values when configuration is incomplete', () => {
            const partialConfig = {
                port: undefined,
                apiKey: null
            };
            
            const resolvedConfig = mcardService._getResolvedConfig(partialConfig);
            
            expect(resolvedConfig.port).toBeDefined();
            expect(resolvedConfig.apiKey).toBeDefined();
        });

        // New test for configuration resolution with more edge cases
        test('should handle complex configuration scenarios', () => {
            // Test various configuration scenarios
            const scenarios = [
                { input: {}, expectedApiKey: 'default_key', expectedPort: 5320 },
                { input: { port: 0 }, expectedPort: 0 },
                { input: { apiKey: '' }, expectedApiKey: 'default_key' }
            ];

            scenarios.forEach(scenario => {
                const resolvedConfig = mcardService._getResolvedConfig(scenario.input);
                
                if (scenario.expectedApiKey) {
                    expect(resolvedConfig.apiKey).toBe(scenario.expectedApiKey);
                }
                
                if (scenario.expectedPort !== undefined) {
                    expect(resolvedConfig.port).toBe(scenario.expectedPort);
                }
            });
        });
    });

    // Server Management Edge Cases
    describe('Server Management Edge Cases', () => {
        test('should handle multiple server start attempts', async () => {
            // Start server first time
            await mcardService.startServer();
            
            // Try starting server again
            await expect(mcardService.startServer()).resolves.not.toThrow();
        }, 10000);  // Increased timeout

        test('should handle server stop when not running', async () => {
            // Ensure server is not running
            await expect(mcardService.stopServer()).resolves.not.toThrow();
            
            // Try stopping server again
            await expect(mcardService.stopServer()).resolves.not.toThrow();
        }, 10000);  // Increased timeout

        test('should check server status correctly', async () => {
            // Verify server is not running initially
            expect(mcardService.isServerRunning).toBe(false);

            // Start the server
            await mcardService.startServer();

            // Check server status
            expect(mcardService.isServerRunning).toBe(true);
            expect(mcardService.serverPort).toBeGreaterThan(0);

            // Stop the server
            await mcardService.stopServer();

            // Verify server is stopped
            expect(mcardService.isServerRunning).toBe(false);
            expect(mcardService.serverPort).toBeNull();
        }, 10000);  // Increased timeout
    });

    // Error Handling in Card Operations
    describe('Card Operation Error Handling', () => {
        test('should throw error for invalid card creation', async () => {
            // Validate content type
            await expect(mcardService._createCard(null)).rejects.toThrow('Card content cannot be null or undefined');
            await expect(mcardService._createCard({})).rejects.toThrow('Card content must be a string');
            await expect(mcardService._createCard('')).rejects.toThrow('Card content cannot be an empty string');
        });

        test('should handle card retrieval with invalid hash', async () => {
            // Start server first
            await mcardService.startServer();

            // Invalid hash scenarios
            await expect(mcardService._retrieveCard(null)).rejects.toThrow('Card hash cannot be null or undefined');
            await expect(mcardService._retrieveCard('')).rejects.toThrow('Card hash cannot be an empty string');
            await expect(mcardService._retrieveCard('invalid-hash')).rejects.toThrow('Invalid card hash format');
        });

        test('should handle large content creation', async () => {
            // Start server first
            await mcardService.startServer();

            // Create a large content string (1MB + 1 byte)
            const largeContent = 'x'.repeat(1024 * 1024 + 1);
            await expect(mcardService._createCard(largeContent)).rejects.toThrow('Card content is too large');
        });
    });

    // Singleton Behavior
    describe('Singleton Behavior', () => {
        test('should always return the same instance', () => {
            const instance1 = MCardServiceProxy.getInstance();
            const instance2 = MCardServiceProxy.getInstance();
            
            expect(instance1).toBe(instance2);
        });

        // New test for instance reset
        test('should allow resetting the singleton', () => {
            const originalInstance = MCardServiceProxy.getInstance();
            MCardServiceProxy.reset();
            const newInstance = MCardServiceProxy.getInstance();
            
            expect(newInstance).not.toBe(originalInstance);
        });
    });

    // Network and Connectivity Tests
    describe('Network Connectivity', () => {
        test('should validate network connectivity', async () => {
            const isConnected = await mcardService._checkNetworkConnectivity();
            expect(isConnected).toBe(true);
        });

        // New test for network connectivity error handling
        test('should handle network connectivity errors gracefully', async () => {
            // Mock the checkNetworkConnectivity method to simulate an error
            const originalMethod = mcardService.checkNetworkConnectivity;
            mcardService.checkNetworkConnectivity = jest.fn().mockRejectedValue(new Error('Network error'));

            const isConnected = await mcardService._checkNetworkConnectivity();
            expect(isConnected).toBe(false);

            // Restore the original method
            mcardService.checkNetworkConnectivity = originalMethod;
        });
    });

    // Configuration Value Retrieval Tests
    describe('Configuration Value Retrieval', () => {
        test('should retrieve configuration values correctly', () => {
            const configKeys = ['dbPath', 'host', 'port', 'apiKey'];
            
            configKeys.forEach(key => {
                const value = mcardService._getConfigValue(key);
                expect(value).toBeDefined();
            });
        });

        test('should handle unknown configuration keys', () => {
            const unknownKey = 'unknownConfigKey';
            const defaultValue = 'defaultTestValue';
            
            const value = mcardService._getConfigValue(unknownKey, defaultValue);
            expect(value).toBe(defaultValue);
        });
    });
});
