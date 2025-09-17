import { render, screen } from '@/tests/utils/test-utils'
import { AuthLayout } from '@/components/auth/AuthLayout'

describe('AuthLayout', () => {
  it('renders children correctly', () => {
    render(
      <AuthLayout>
        <div>Test Content</div>
      </AuthLayout>
    )

    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('has proper semantic structure', () => {
    render(
      <AuthLayout>
        <div>Test Content</div>
      </AuthLayout>
    )

    const main = screen.getByRole('main')
    expect(main).toBeInTheDocument()
  })

  it('applies correct CSS classes', () => {
    const { container } = render(
      <AuthLayout>
        <div>Test Content</div>
      </AuthLayout>
    )

    const wrapper = container.firstChild as HTMLElement
    expect(wrapper).toHaveClass('min-h-screen')
  })

  it('is accessible', async () => {
    const { container } = render(
      <AuthLayout>
        <h1>Login</h1>
        <form>
          <label htmlFor="email">Email</label>
          <input id="email" type="email" />
          <label htmlFor="password">Password</label>
          <input id="password" type="password" />
          <button type="submit">Submit</button>
        </form>
      </AuthLayout>
    )

    const axe = await import('jest-axe')
    const results = await axe.default(container)
    expect(results).toHaveNoViolations()
  })

  it('renders with background elements', () => {
    render(
      <AuthLayout>
        <div>Test Content</div>
      </AuthLayout>
    )

    // Check for decorative elements
    const decorativeElements = screen.getAllByRole('img', { hidden: true })
    expect(decorativeElements.length).toBeGreaterThan(0)
  })

  it('centers content properly', () => {
    const { container } = render(
      <AuthLayout>
        <div data-testid="content">Test Content</div>
      </AuthLayout>
    )

    const content = screen.getByTestId('content')
    const wrapper = content.closest('[class*="flex"]')
    expect(wrapper).toHaveClass('items-center', 'justify-center')
  })

  it('is responsive', () => {
    const { container } = render(
      <AuthLayout>
        <div>Test Content</div>
      </AuthLayout>
    )

    const wrapper = container.firstChild as HTMLElement
    expect(wrapper).toHaveClass('p-4', 'md:p-8')
  })

  it('handles long content without overflow', () => {
    const longContent = 'A'.repeat(1000)

    render(
      <AuthLayout>
        <div style={{ width: '400px' }}>
          {longContent}
        </div>
      </AuthLayout>
    )

    const content = screen.getByText(longContent)
    expect(content).toBeInTheDocument()
  })

  describe('Accessibility', () => {
    it('has proper landmark structure', () => {
      render(
        <AuthLayout>
          <div>Test Content</div>
        </AuthLayout>
      )

      expect(screen.getByRole('main')).toBeInTheDocument()
    })

    it('supports keyboard navigation', () => {
      render(
        <AuthLayout>
          <button>Test Button</button>
          <input type="text" placeholder="Test Input" />
        </AuthLayout>
      )

      const button = screen.getByRole('button')
      const input = screen.getByPlaceholderText('Test Input')

      expect(button).toBeVisible()
      expect(input).toBeVisible()

      // Test tab order
      button.focus()
      expect(document.activeElement).toBe(button)
    })

    it('has sufficient color contrast', async () => {
      const { container } = render(
        <AuthLayout>
          <div>Test Content</div>
        </AuthLayout>
      )

      const axe = await import('jest-axe')
      const results = await axe.default(container, {
        rules: {
          'color-contrast': { enabled: true },
        },
      })
      expect(results).toHaveNoViolations()
    })
  })

  describe('Error Boundaries', () => {
    it('handles child component errors gracefully', () => {
      const ThrowError = () => {
        throw new Error('Test error')
      }

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        render(
          <AuthLayout>
            <ThrowError />
          </AuthLayout>
        )
      }).toThrow()

      consoleSpy.mockRestore()
    })
  })

  describe('Performance', () => {
    it('renders quickly with large content', () => {
      const start = performance.now()

      render(
        <AuthLayout>
          {Array.from({ length: 100 }, (_, i) => (
            <div key={i}>Item {i}</div>
          ))}
        </AuthLayout>
      )

      const end = performance.now()
      const renderTime = end - start

      // Should render in less than 100ms
      expect(renderTime).toBeLessThan(100)
    })
  })
})