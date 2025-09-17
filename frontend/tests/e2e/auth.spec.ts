import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.context().clearCookies()
    await page.goto('/')
  })

  test.describe('Login', () => {
    test('should display login form', async ({ page }) => {
      await page.goto('/auth/login')

      // Check form elements
      await expect(page.locator('input[name="email"]')).toBeVisible()
      await expect(page.locator('input[name="password"]')).toBeVisible()
      await expect(page.locator('button[type="submit"]')).toBeVisible()

      // Check form labels
      await expect(page.locator('text=Email')).toBeVisible()
      await expect(page.locator('text=Password')).toBeVisible()
    })

    test('should login with valid credentials', async ({ page }) => {
      await page.goto('/auth/login')

      // Fill login form
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="password"]', 'password123')

      // Submit form
      await page.click('button[type="submit"]')

      // Should redirect to dashboard
      await page.waitForURL('/dashboard')
      await expect(page.locator('text=Dashboard')).toBeVisible()
    })

    test('should show error with invalid credentials', async ({ page }) => {
      await page.goto('/auth/login')

      // Fill login form with invalid credentials
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="password"]', 'wrongpassword')

      // Submit form
      await page.click('button[type="submit"]')

      // Should show error message
      await expect(page.locator('text=Invalid credentials')).toBeVisible()
      await expect(page).toHaveURL('/auth/login')
    })

    test('should validate required fields', async ({ page }) => {
      await page.goto('/auth/login')

      // Try to submit without filling fields
      await page.click('button[type="submit"]')

      // Should show validation errors
      await expect(page.locator('text=Email is required')).toBeVisible()
      await expect(page.locator('text=Password is required')).toBeVisible()
    })

    test('should validate email format', async ({ page }) => {
      await page.goto('/auth/login')

      // Fill invalid email
      await page.fill('input[name="email"]', 'invalid-email')
      await page.fill('input[name="password"]', 'password123')

      // Submit form
      await page.click('button[type="submit"]')

      // Should show email validation error
      await expect(page.locator('text=Please enter a valid email')).toBeVisible()
    })

    test('should toggle password visibility', async ({ page }) => {
      await page.goto('/auth/login')

      const passwordInput = page.locator('input[name="password"]')
      const toggleButton = page.locator('[data-testid="password-toggle"]')

      // Initially password should be hidden
      await expect(passwordInput).toHaveAttribute('type', 'password')

      // Click toggle button
      await toggleButton.click()

      // Password should be visible
      await expect(passwordInput).toHaveAttribute('type', 'text')

      // Click toggle button again
      await toggleButton.click()

      // Password should be hidden again
      await expect(passwordInput).toHaveAttribute('type', 'password')
    })
  })

  test.describe('Registration', () => {
    test('should display registration form', async ({ page }) => {
      await page.goto('/auth/register')

      // Check form elements
      await expect(page.locator('input[name="name"]')).toBeVisible()
      await expect(page.locator('input[name="email"]')).toBeVisible()
      await expect(page.locator('input[name="password"]')).toBeVisible()
      await expect(page.locator('input[name="confirmPassword"]')).toBeVisible()
      await expect(page.locator('button[type="submit"]')).toBeVisible()
    })

    test('should register with valid data', async ({ page }) => {
      await page.goto('/auth/register')

      // Fill registration form
      await page.fill('input[name="name"]', 'Test User')
      await page.fill('input[name="email"]', 'newuser@example.com')
      await page.fill('input[name="password"]', 'password123')
      await page.fill('input[name="confirmPassword"]', 'password123')

      // Submit form
      await page.click('button[type="submit"]')

      // Should show success message or redirect to verification page
      await expect(
        page.locator('text=Registration successful')
      ).toBeVisible()
    })

    test('should validate password confirmation', async ({ page }) => {
      await page.goto('/auth/register')

      // Fill form with mismatched passwords
      await page.fill('input[name="name"]', 'Test User')
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="password"]', 'password123')
      await page.fill('input[name="confirmPassword"]', 'differentpassword')

      // Submit form
      await page.click('button[type="submit"]')

      // Should show password mismatch error
      await expect(page.locator('text=Passwords do not match')).toBeVisible()
    })

    test('should validate password strength', async ({ page }) => {
      await page.goto('/auth/register')

      const passwordInput = page.locator('input[name="password"]')

      // Test weak password
      await passwordInput.fill('123')
      await expect(page.locator('text=Password too weak')).toBeVisible()

      // Test medium password
      await passwordInput.fill('password')
      await expect(page.locator('text=Password strength: Medium')).toBeVisible()

      // Test strong password
      await passwordInput.fill('Password123!')
      await expect(page.locator('text=Password strength: Strong')).toBeVisible()
    })
  })

  test.describe('Logout', () => {
    test('should logout successfully', async ({ page }) => {
      // Login first
      await page.goto('/auth/login')
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="password"]', 'password123')
      await page.click('button[type="submit"]')
      await page.waitForURL('/dashboard')

      // Logout
      await page.click('[data-testid="user-menu"]')
      await page.click('text=Logout')

      // Should redirect to home page
      await page.waitForURL('/')
      await expect(page.locator('text=Login')).toBeVisible()
    })
  })

  test.describe('Protected Routes', () => {
    test('should redirect to login when accessing protected route', async ({ page }) => {
      // Try to access protected route without authentication
      await page.goto('/dashboard')

      // Should redirect to login
      await page.waitForURL('/auth/login')
      await expect(page.locator('text=Please log in to continue')).toBeVisible()
    })

    test('should remember intended destination after login', async ({ page }) => {
      // Try to access protected route
      await page.goto('/dashboard/users')

      // Should redirect to login
      await page.waitForURL(/\/auth\/login/)

      // Login
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="password"]', 'password123')
      await page.click('button[type="submit"]')

      // Should redirect to originally requested page
      await page.waitForURL('/dashboard/users')
    })
  })

  test.describe('Session Management', () => {
    test('should persist session across page reloads', async ({ page }) => {
      // Login
      await page.goto('/auth/login')
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="password"]', 'password123')
      await page.click('button[type="submit"]')
      await page.waitForURL('/dashboard')

      // Reload page
      await page.reload()

      // Should still be authenticated
      await expect(page.locator('text=Dashboard')).toBeVisible()
      await expect(page).toHaveURL('/dashboard')
    })

    test('should handle token expiration gracefully', async ({ page }) => {
      // This test would require setting up a way to simulate token expiration
      // For now, we'll skip the implementation details
      test.skip()
    })
  })

  test.describe('Accessibility', () => {
    test('login form should be accessible', async ({ page }) => {
      await page.goto('/auth/login')

      // Check for proper labels and form associations
      const emailInput = page.locator('input[name="email"]')
      const passwordInput = page.locator('input[name="password"]')

      await expect(emailInput).toHaveAttribute('aria-label')
      await expect(passwordInput).toHaveAttribute('aria-label')

      // Check for proper form validation announcements
      await page.click('button[type="submit"]')
      await expect(page.locator('[role="alert"]')).toBeVisible()
    })

    test('should support keyboard navigation', async ({ page }) => {
      await page.goto('/auth/login')

      // Tab through form elements
      await page.keyboard.press('Tab') // Email input
      await expect(page.locator('input[name="email"]')).toBeFocused()

      await page.keyboard.press('Tab') // Password input
      await expect(page.locator('input[name="password"]')).toBeFocused()

      await page.keyboard.press('Tab') // Submit button
      await expect(page.locator('button[type="submit"]')).toBeFocused()

      // Submit with Enter key
      await page.keyboard.press('Enter')
    })
  })

  test.describe('Mobile Experience', () => {
    test.use({ viewport: { width: 375, height: 667 } })

    test('should work on mobile devices', async ({ page }) => {
      await page.goto('/auth/login')

      // Check that form is properly sized for mobile
      const form = page.locator('form')
      const formBox = await form.boundingBox()
      expect(formBox?.width).toBeLessThanOrEqual(375)

      // Fill and submit form
      await page.fill('input[name="email"]', 'test@example.com')
      await page.fill('input[name="password"]', 'password123')
      await page.click('button[type="submit"]')

      await page.waitForURL('/dashboard')
      await expect(page.locator('text=Dashboard')).toBeVisible()
    })
  })
})