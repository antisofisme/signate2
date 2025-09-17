import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use

  // Launch browser for setup
  const browser = await chromium.launch()
  const page = await browser.newPage()

  try {
    console.log('🚀 Starting E2E test setup...')

    // Wait for the application to be ready
    await page.goto(baseURL || 'http://localhost:3000')
    await page.waitForSelector('body', { timeout: 30000 })

    // Setup test data if needed
    await setupTestData(page)

    // Create authenticated session state
    await createAuthenticatedState(page)

    console.log('✅ E2E test setup completed')
  } catch (error) {
    console.error('❌ E2E test setup failed:', error)
    throw error
  } finally {
    await browser.close()
  }
}

async function setupTestData(page: any) {
  // Here you can set up test data in your backend
  // For example, create test users, tenants, etc.
  console.log('📋 Setting up test data...')

  // You might make API calls here to set up test data
  // or use a test database seeding mechanism
}

async function createAuthenticatedState(page: any) {
  console.log('🔐 Creating authenticated session state...')

  try {
    // Navigate to login page
    await page.goto('/auth/login')

    // Fill in test user credentials
    await page.fill('[name="email"]', 'test@example.com')
    await page.fill('[name="password"]', 'password123')

    // Submit login form
    await page.click('button[type="submit"]')

    // Wait for successful login (redirect to dashboard)
    await page.waitForURL('/dashboard', { timeout: 10000 })

    // Save authenticated state
    await page.context().storageState({ path: 'tests/e2e/auth-state.json' })

    console.log('✅ Authenticated session state saved')
  } catch (error) {
    console.log('ℹ️ Could not create authenticated state (this is normal if auth is not set up yet)')
    // Don't fail the setup if authentication is not available yet
  }
}

export default globalSetup