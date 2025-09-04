/**
 * Jest configuration for React frontend testing
 */
module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Test patterns
  testMatch: [
    '<rootDir>/frontend/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/frontend/src/**/?(*.)(spec|test).{js,jsx,ts,tsx}',
    '<rootDir>/tests/frontend/**/*.{js,jsx,ts,tsx}'
  ],
  
  // Module resolution
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/frontend/src/$1',
    '^@components/(.*)$': '<rootDir>/frontend/src/components/$1',
    '^@pages/(.*)$': '<rootDir>/frontend/src/pages/$1',
    '^@hooks/(.*)$': '<rootDir>/frontend/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/frontend/src/utils/$1',
    '^@api/(.*)$': '<rootDir>/frontend/src/api/$1',
    '^@store/(.*)$': '<rootDir>/frontend/src/store/$1',
    '^@types/(.*)$': '<rootDir>/frontend/src/types/$1',
    '\\.(css|less|scss)$': 'identity-obj-proxy',
    '\\.(png|jpg|jpeg|gif|svg)$': '<rootDir>/tests/frontend/__mocks__/fileMock.js'
  },
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/tests/frontend/setup/setupTests.js'
  ],
  
  // Transform configuration
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }],
        '@babel/preset-typescript'
      ],
      plugins: [
        '@babel/plugin-proposal-class-properties',
        '@babel/plugin-proposal-object-rest-spread'
      ]
    }]
  },
  
  // Ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(axios|@testing-library|@hookform)/)'
  ],
  
  // Module directories
  moduleDirectories: [
    'node_modules',
    '<rootDir>/frontend/src',
    '<rootDir>/tests/frontend'
  ],
  
  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'frontend/src/**/*.{js,jsx,ts,tsx}',
    '!frontend/src/**/*.d.ts',
    '!frontend/src/index.js',
    '!frontend/src/reportWebVitals.js',
    '!frontend/src/**/*.stories.{js,jsx,ts,tsx}',
    '!frontend/src/**/__tests__/**',
    '!frontend/src/**/node_modules/**'
  ],
  
  coverageDirectory: '<rootDir>/coverage/frontend',
  
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary'
  ],
  
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output
  verbose: true,
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Restore mocks after each test
  restoreMocks: true,
  
  // Error handling
  errorOnDeprecated: true,
  
  // Globals
  globals: {
    'process.env.NODE_ENV': 'test'
  },
  
  // Watch plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],
  
  // Reporters
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: 'test-results/frontend',
      outputName: 'junit.xml',
      suiteName: 'Frontend Tests'
    }]
  ]
};