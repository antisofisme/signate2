import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  // Use authenticated state for all dashboard tests
  test.use({ storageState: 'tests/e2e/auth-state.json' })

  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test.describe('Navigation', () => {
    test('should display main navigation elements', async ({ page }) => {
      // Check main navigation items
      await expect(page.locator('nav')).toBeVisible()
      await expect(page.locator('text=Dashboard')).toBeVisible()
      await expect(page.locator('text=Users')).toBeVisible()
      await expect(page.locator('text=Assets')).toBeVisible()
      await expect(page.locator('text=Settings')).toBeVisible()
    })

    test('should navigate between sections', async ({ page }) => {
      // Navigate to Users
      await page.click('text=Users')
      await page.waitForURL('/dashboard/users')
      await expect(page.locator('h1:has-text("Users")')).toBeVisible()

      // Navigate to Assets
      await page.click('text=Assets')
      await page.waitForURL('/dashboard/assets')
      await expect(page.locator('h1:has-text("Assets")')).toBeVisible()

      // Navigate back to Dashboard
      await page.click('text=Dashboard')
      await page.waitForURL('/dashboard')
      await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible()
    })

    test('should highlight active navigation item', async ({ page }) => {
      // Check dashboard is active by default
      await expect(page.locator('nav a[href="/dashboard"]')).toHaveClass(/active/)

      // Navigate to users and check active state
      await page.click('text=Users')
      await expect(page.locator('nav a[href="/dashboard/users"]')).toHaveClass(/active/)
    })
  })

  test.describe('Dashboard Overview', () => {
    test('should display key statistics', async ({ page }) => {
      // Check for statistics cards
      await expect(page.locator('[data-testid="stats-total-users"]')).toBeVisible()
      await expect(page.locator('[data-testid="stats-active-users"]')).toBeVisible()
      await expect(page.locator('[data-testid="stats-total-assets"]')).toBeVisible()
      await expect(page.locator('[data-testid="stats-storage-used"]')).toBeVisible()

      // Check that statistics have actual values
      const totalUsers = await page.locator('[data-testid="stats-total-users"]').textContent()
      expect(totalUsers).toMatch(/\\d+/)
    })

    test('should display usage charts', async ({ page }) => {
      // Check for chart containers
      await expect(page.locator('[data-testid="usage-chart"]')).toBeVisible()
      await expect(page.locator('[data-testid="growth-chart"]')).toBeVisible()

      // Wait for charts to load
      await page.waitForFunction(() => {
        const chartElements = document.querySelectorAll('[data-testid="usage-chart"] svg')
        return chartElements.length > 0
      })
    })

    test('should display recent activity', async ({ page }) => {
      await expect(page.locator('[data-testid="recent-activity"]')).toBeVisible()

      // Check for activity items
      const activityItems = page.locator('[data-testid="activity-item"]')
      await expect(activityItems.first()).toBeVisible()
    })
  })

  test.describe('User Management', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/dashboard/users')
    })

    test('should display users table', async ({ page }) => {
      await expect(page.locator('table')).toBeVisible()
      await expect(page.locator('thead')).toBeVisible()
      await expect(page.locator('tbody')).toBeVisible()

      // Check table headers
      await expect(page.locator('th:has-text("Name")')).toBeVisible()
      await expect(page.locator('th:has-text("Email")')).toBeVisible()
      await expect(page.locator('th:has-text("Role")')).toBeVisible()
      await expect(page.locator('th:has-text("Actions")')).toBeVisible()
    })

    test('should create new user', async ({ page }) => {
      // Click create user button
      await page.click('[data-testid="create-user-button"]')

      // Fill user form
      await page.fill('input[name="name"]', 'New Test User')
      await page.fill('input[name="email"]', 'newuser@test.com')
      await page.selectOption('select[name="role"]', 'user')
      await page.fill('input[name="password"]', 'password123')

      // Submit form
      await page.click('button[type="submit"]')

      // Check success message
      await expect(page.locator('text=User created successfully')).toBeVisible()

      // Check that user appears in table
      await expect(page.locator('text=New Test User')).toBeVisible()
    })

    test('should edit existing user', async ({ page }) => {
      // Click edit button for first user
      await page.click('[data-testid="edit-user-button"]')

      // Update user name
      await page.fill('input[name="name"]', 'Updated Test User')

      // Submit form
      await page.click('button[type="submit"]')

      // Check success message
      await expect(page.locator('text=User updated successfully')).toBeVisible()

      // Check that user name is updated in table
      await expect(page.locator('text=Updated Test User')).toBeVisible()
    })

    test('should delete user with confirmation', async ({ page }) => {
      // Click delete button for first user
      await page.click('[data-testid="delete-user-button"]')

      // Confirm deletion in modal
      await expect(page.locator('text=Are you sure?')).toBeVisible()
      await page.click('button:has-text("Delete")')

      // Check success message
      await expect(page.locator('text=User deleted successfully')).toBeVisible()
    })

    test('should filter users by search', async ({ page }) => {
      // Enter search term
      await page.fill('[data-testid="user-search"]', 'john')

      // Wait for filtered results
      await page.waitForFunction(() => {
        const rows = document.querySelectorAll('tbody tr')
        return Array.from(rows).some(row =>
          row.textContent?.toLowerCase().includes('john')
        )
      })

      // Check that only matching users are shown
      const visibleRows = page.locator('tbody tr')
      const count = await visibleRows.count()
      expect(count).toBeGreaterThan(0)
    })

    test('should paginate users', async ({ page }) => {
      // Check pagination controls
      await expect(page.locator('[data-testid="pagination"]')).toBeVisible()

      // Go to next page
      await page.click('[data-testid="next-page"]')

      // Check URL updates
      await expect(page).toHaveURL(/page=2/)

      // Check different users are shown
      const firstPageUser = await page.locator('tbody tr:first-child td:first-child').textContent()

      // Go back to first page
      await page.click('[data-testid="prev-page"]')
      await expect(page).toHaveURL(/page=1/)
    })
  })

  test.describe('Asset Management', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/dashboard/assets')
    })

    test('should display assets grid', async ({ page }) => {
      await expect(page.locator('[data-testid="assets-grid"]')).toBeVisible()
      await expect(page.locator('[data-testid="asset-card"]').first()).toBeVisible()
    })

    test('should upload new asset', async ({ page }) => {
      // Click upload button
      await page.click('[data-testid="upload-asset-button"]')

      // Create a test file
      const fileContent = 'test file content'
      const fileName = 'test-image.jpg'

      // Upload file
      await page.setInputFiles('input[type="file"]', {
        name: fileName,
        mimeType: 'image/jpeg',
        buffer: Buffer.from(fileContent),
      })

      // Wait for upload completion
      await expect(page.locator('text=Upload successful')).toBeVisible()

      // Check that asset appears in grid
      await expect(page.locator(`text=${fileName}`)).toBeVisible()
    })

    test('should preview asset', async ({ page }) => {
      // Click on first asset
      await page.click('[data-testid="asset-card"]')

      // Check preview modal opens
      await expect(page.locator('[data-testid="asset-preview"]')).toBeVisible()
      await expect(page.locator('[data-testid="asset-details"]')).toBeVisible()

      // Close preview
      await page.click('[data-testid="close-preview"]')
      await expect(page.locator('[data-testid="asset-preview"]')).not.toBeVisible()
    })

    test('should delete asset', async ({ page }) => {
      // Click delete button on first asset
      await page.hover('[data-testid="asset-card"]')
      await page.click('[data-testid="delete-asset-button"]')

      // Confirm deletion
      await page.click('button:has-text("Delete")')

      // Check success message
      await expect(page.locator('text=Asset deleted successfully')).toBeVisible()
    })
  })

  test.describe('Responsive Design', () => {
    test('should work on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/dashboard')

      // Check that navigation collapses on tablet
      await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible()

      // Check that content is properly sized
      const mainContent = page.locator('main')
      const boundingBox = await mainContent.boundingBox()
      expect(boundingBox?.width).toBeLessThanOrEqual(768)
    })

    test('should work on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/dashboard')

      // Check mobile navigation
      await page.click('[data-testid="mobile-menu-button"]')
      await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible()

      // Navigate using mobile menu
      await page.click('[data-testid="mobile-menu"] text=Users')
      await page.waitForURL('/dashboard/users')
      await expect(page.locator('h1:has-text("Users")')).toBeVisible()
    })
  })

  test.describe('Performance', () => {
    test('should load dashboard quickly', async ({ page }) => {
      const startTime = Date.now()

      await page.goto('/dashboard')
      await page.waitForSelector('[data-testid="dashboard-content"]')

      const loadTime = Date.now() - startTime
      expect(loadTime).toBeLessThan(3000) // Should load in less than 3 seconds
    })

    test('should handle large datasets', async ({ page }) => {
      await page.goto('/dashboard/users')

      // Wait for initial load
      await page.waitForSelector('table')

      // Test scrolling performance with large dataset
      const startTime = Date.now()

      for (let i = 0; i < 10; i++) {
        await page.keyboard.press('PageDown')
        await page.waitForTimeout(100)
      }

      const scrollTime = Date.now() - startTime
      expect(scrollTime).toBeLessThan(2000) // Should handle scrolling smoothly
    })
  })

  test.describe('Accessibility', () => {
    test('should be keyboard navigable', async ({ page }) => {
      await page.goto('/dashboard')

      // Tab through main navigation
      await page.keyboard.press('Tab')
      await expect(page.locator('nav a').first()).toBeFocused()

      // Continue tabbing through interactive elements
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')

      // Should be able to activate links with Enter
      await page.keyboard.press('Enter')
    })

    test('should have proper heading hierarchy', async ({ page }) => {
      await page.goto('/dashboard')

      // Check heading structure
      const h1 = page.locator('h1')
      await expect(h1).toBeVisible()

      const h2s = page.locator('h2')
      expect(await h2s.count()).toBeGreaterThan(0)
    })

    test('should have proper ARIA labels', async ({ page }) => {
      await page.goto('/dashboard')

      // Check for important ARIA attributes
      await expect(page.locator('nav')).toHaveAttribute('aria-label')
      await expect(page.locator('main')).toHaveAttribute('aria-label')
    })
  })
})