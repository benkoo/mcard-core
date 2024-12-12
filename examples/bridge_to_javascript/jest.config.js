module.exports = {
  // Test Environment
  testEnvironment: 'node',
  
  // Test Files
  testMatch: ['**/tests/**/*.test.js'],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/tests/utils/',
    '/tests/config/'
  ],

  // Verbose Output
  verbose: true,

  // Coverage Configuration
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary'
  ],
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/tests/',
    '/coverage/'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },

  // Test Timeouts
  testTimeout: 30000, // 30 seconds for all tests
  slowTestThreshold: 5000, // Mark tests as slow if they take more than 5 seconds

  // Reporter Configuration
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: 'reports',
        outputName: 'junit.xml',
        classNameTemplate: '{classname}',
        titleTemplate: '{title}',
        ancestorSeparator: ' › ',
        usePathForSuiteName: true
      }
    ]
  ],

  // Test Result Processors
  testResultsProcessor: 'jest-sonar-reporter',

  // Other Configuration
  detectOpenHandles: true,
  errorOnDeprecated: true,
  maxConcurrency: 1, // Run tests serially
  maxWorkers: '50%', // Use up to 50% of available cores
  notify: true, // Show desktop notifications for test results
  bail: 0, // Don't fail fast
  cache: true, // Use cache for faster runs
  clearMocks: true, // Clear mocks between tests
  resetMocks: true, // Reset mocks between tests
  restoreMocks: true // Restore mocks between tests
};
