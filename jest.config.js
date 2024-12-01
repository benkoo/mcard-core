/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest/presets/default-esm',
  testEnvironment: 'node',
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  transform: {
    '^.+\\.m?[tj]sx?$': ['ts-jest', {
      useESM: true,
      tsconfig: 'tsconfig.json'
    }]
  },
  testMatch: [
    '**/examples/monadic-cards/__tests__/**/*.test.ts'
  ],
  extensionsToTreatAsEsm: ['.ts'],
  watchPathIgnorePatterns: [
    '<rootDir>/.cursor/',
    '<rootDir>/.windsurf/',
    '<rootDir>/Library/',
    '<rootDir>/go/'
  ],
  modulePathIgnorePatterns: [
    '<rootDir>/.cursor/',
    '<rootDir>/.windsurf/',
    '<rootDir>/Library/',
    '<rootDir>/go/'
  ]
};
