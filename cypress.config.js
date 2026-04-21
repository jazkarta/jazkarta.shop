const { defineConfig } = require('cypress')

module.exports = defineConfig({
  projectId: '5awy1r',
  e2e: {
    baseUrl: 'http://localhost:8080/Plone',
    specPattern: 'cypress/e2e/**/*.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/e2e.js',
  },
  env: {
    SITE_OWNER_NAME: 'admin',
    SITE_OWNER_PASSWORD: 'admin',
  },
})
