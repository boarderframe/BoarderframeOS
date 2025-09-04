# MCP-UI Design System

A comprehensive, accessible, and beautiful component library for building MCP (Model Context Protocol) server interfaces with focus on reusability and seamless integration.

## Features

### 🎨 Design System Foundation
- **Color Tokens**: Semantic color system with light/dark mode support
- **Typography Scale**: Consistent type system with 9 size variants
- **Spacing System**: 4px-based grid for consistent layouts
- **Animation Library**: Smooth transitions and micro-interactions
- **Shadow System**: 5-level elevation system for depth

### 🧩 Component Library

#### Core Components
- **Button**: 8 variants, 5 sizes, loading states, icons support
- **Card**: Container component with header/footer sections
- **Input**: Form inputs with validation states and password visibility
- **Modal**: Accessible dialogs with focus management
- **Badge**: Status indicators with removable option
- **Toast**: Non-intrusive notifications with auto-dismiss

#### E-commerce Components
- **ProductCard**: Product display with ratings, pricing, and actions
- **ShoppingCart**: Full cart management with quantity controls
- **ProductGrid**: Responsive product layouts
- **PriceDisplay**: Formatted pricing with discounts

#### Kroger-Specific Components
- **LocationFinder**: Store locator with map integration
- **OrderTracker**: Real-time order status updates
- **AccountManager**: User profile and preferences
- **SearchInterface**: Advanced product search with filters

### 🌓 Theme System
- **Light/Dark Mode**: Automatic system preference detection
- **Custom Themes**: Brand customization through CSS variables
- **Persistent Preferences**: LocalStorage-based theme persistence
- **Smooth Transitions**: Graceful theme switching animations

### 📡 MCP-UI Protocol Integration
- **PostMessage Bridge**: Secure cross-origin communication
- **Event System**: Typed message handlers
- **Request/Response**: Promise-based async communication
- **State Sync**: Real-time data synchronization

## Installation

```bash
npm install @mcp-ui/design-system
# or
yarn add @mcp-ui/design-system
```

## Quick Start

### 1. Import Styles
```css
/* In your main CSS file */
@import '@mcp-ui/design-system/styles.css';
```

### 2. Setup Theme Provider
```tsx
import { ThemeProvider } from '@mcp-ui/design-system';

function App() {
  return (
    <ThemeProvider defaultTheme="system">
      <YourApp />
    </ThemeProvider>
  );
}
```

### 3. Use Components
```tsx
import { Button, Card, ProductCard, toast } from '@mcp-ui/design-system';

function MyComponent() {
  return (
    <Card>
      <ProductCard
        product={product}
        onAddToCart={(product) => {
          toast.success(`${product.name} added to cart`);
        }}
      />
      <Button variant="primary" size="lg">
        Checkout
      </Button>
    </Card>
  );
}
```

## PostMessage Communication

### Setup Bridge
```tsx
import { useMCPBridge, MCPMessages } from '@mcp-ui/design-system';

function MyComponent() {
  const { sendMessage, onMessage } = useMCPBridge();

  useEffect(() => {
    // Listen for cart updates
    const unsubscribe = onMessage(MCPMessages.CART_UPDATE, (message) => {
      console.log('Cart updated:', message.payload);
    });

    return unsubscribe;
  }, []);

  const handleAddToCart = (product) => {
    sendMessage(MCPMessages.CART_ADD, { product });
  };
}
```

### Security Configuration
```tsx
import { mcpBridge } from '@mcp-ui/design-system';

// Set allowed origins for security
mcpBridge.setAllowedOrigins([
  'https://kroger.com',
  'https://api.kroger.com'
]);

// Set target origin for postMessage
mcpBridge.setTargetOrigin('https://kroger.com');
```

## Accessibility Features

All components follow WCAG 2.1 AA standards:

- ✅ **Keyboard Navigation**: Full keyboard support
- ✅ **Screen Reader Support**: Proper ARIA labels and roles
- ✅ **Focus Management**: Visible focus indicators
- ✅ **Color Contrast**: AA compliant color ratios
- ✅ **Reduced Motion**: Respects prefers-reduced-motion
- ✅ **Form Validation**: Clear error messages and states

## Performance Optimizations

- **Tree Shaking**: Import only what you need
- **Lazy Loading**: Components load on demand
- **Memoization**: Optimized re-renders
- **Code Splitting**: Automatic chunk optimization
- **CSS-in-JS**: Styled-components for optimal bundle size
- **Virtual Scrolling**: Efficient list rendering

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- iOS Safari 14+
- Chrome Android 90+

## Design Tokens

### Colors
```tsx
import { colors } from '@mcp-ui/design-system';

// Brand colors
colors.brand.primary[500]  // #2196f3
colors.brand.secondary[500] // #9c27b0

// Semantic colors
colors.semantic.success.main // #2e7d32
colors.semantic.error.main   // #d32f2f

// Kroger brand colors
colors.kroger.blue   // #0063a4
colors.kroger.orange // #ff6900
```

### Typography
```tsx
import { typography } from '@mcp-ui/design-system';

// Font sizes
typography.fontSize.base // 1rem (16px)
typography.fontSize['2xl'] // 1.5rem (24px)

// Font weights
typography.fontWeight.medium // 500
typography.fontWeight.bold   // 700

// Variants
typography.variants.h1
typography.variants.body1
```

### Spacing
```tsx
import { spacing } from '@mcp-ui/design-system';

// Scale
spacing.scale[4]  // 16px
spacing.scale[8]  // 32px

// Component spacing
spacing.component.button.paddingX // 16px
spacing.component.card.padding    // 16px
```

## Component Variants

### Button Variants
- `primary`: Main CTA buttons
- `secondary`: Secondary actions
- `success`: Positive actions
- `danger`: Destructive actions
- `warning`: Caution actions
- `ghost`: Minimal style
- `link`: Text-only style
- `outline`: Border-only style

### Card Variants
- `default`: Standard card with border
- `elevated`: Card with shadow
- `outlined`: Prominent border
- `ghost`: No border or shadow

### Badge Variants
- `default`: Neutral gray
- `primary`: Brand blue
- `secondary`: Brand purple
- `success`: Green for positive
- `warning`: Yellow for caution
- `error`: Red for issues
- `info`: Blue for information

## Best Practices

### 1. Component Composition
```tsx
// Good: Compose smaller components
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>

// Avoid: Monolithic components
<BigComplexComponent {...everything} />
```

### 2. Event Handling
```tsx
// Good: Use MCP bridge for cross-origin
const { sendMessage } = useMCPBridge();
sendMessage(MCPMessages.CART_ADD, payload);

// Avoid: Direct parent access
window.parent.postMessage(data, '*');
```

### 3. Theme Usage
```tsx
// Good: Use theme-aware components
<Button variant="primary">Click</Button>

// Avoid: Hard-coded colors
<button style={{ background: '#2196f3' }}>Click</button>
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](./LICENSE) for details.