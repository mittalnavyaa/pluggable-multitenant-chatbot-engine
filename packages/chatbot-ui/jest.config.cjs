// packages/chatbot-ui/jest.config.cjs

/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jest-environment-jsdom',
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.json' }]
  },
  moduleNameMapper: {
    '\\?raw$': '<rootDir>/src/tests/raw-mock.js'
  }
};
