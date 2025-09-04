import React, { useState } from 'react';
import {
  ThemeProvider,
  ThemeToggle,
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Input,
  Modal,
  ModalFooter,
  Badge,
  toast,
  ToastContainer,
  ProductCard,
  ShoppingCart,
  useMCPBridge,
  MCPMessages,
  Product,
  CartItem,
} from '../index';

/**
 * Component Showcase
 * Interactive demonstration of all design system components
 */

export const ComponentShowcase: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [favoriteProducts, setFavoriteProducts] = useState<Set<string>>(new Set());
  const { sendMessage } = useMCPBridge();

  // Sample products
  const sampleProducts: Product[] = [
    {
      id: '1',
      name: 'Organic Bananas',
      brand: 'Kroger',
      description: 'Fresh organic bananas, perfect for smoothies',
      price: 2.99,
      originalPrice: 3.99,
      image: 'https://via.placeholder.com/300x300/ffeb3b/000000?text=Bananas',
      rating: 4.5,
      reviews: 234,
      inStock: true,
      unit: 'lb',
      tags: ['Organic', 'Fresh', 'Fruit'],
      promotion: 'Buy 2 Get 1 Free',
    },
    {
      id: '2',
      name: 'Whole Milk',
      brand: 'Simple Truth',
      description: 'Fresh whole milk from grass-fed cows',
      price: 4.49,
      originalPrice: 5.99,
      image: 'https://via.placeholder.com/300x300/e3f2fd/000000?text=Milk',
      rating: 4.8,
      reviews: 567,
      inStock: true,
      unit: 'gal',
      tags: ['Dairy', 'Organic'],
    },
    {
      id: '3',
      name: 'Sourdough Bread',
      brand: 'Bakery Fresh',
      description: 'Artisanal sourdough bread, freshly baked',
      price: 3.99,
      image: 'https://via.placeholder.com/300x300/8d6e63/ffffff?text=Bread',
      rating: 4.2,
      reviews: 89,
      inStock: false,
      unit: 'loaf',
      tags: ['Bakery', 'Fresh'],
    },
  ];

  // Sample cart items
  const sampleCartItems: CartItem[] = [
    {
      id: 'cart-1',
      productId: '1',
      name: 'Organic Bananas',
      brand: 'Kroger',
      price: 2.99,
      originalPrice: 3.99,
      quantity: 2,
      image: 'https://via.placeholder.com/100x100/ffeb3b/000000?text=Bananas',
      unit: 'lb',
      maxQuantity: 10,
    },
    {
      id: 'cart-2',
      productId: '2',
      name: 'Whole Milk',
      brand: 'Simple Truth',
      price: 4.49,
      originalPrice: 5.99,
      quantity: 1,
      image: 'https://via.placeholder.com/100x100/e3f2fd/000000?text=Milk',
      unit: 'gal',
      maxQuantity: 5,
    },
  ];

  const handleAddToCart = (product: Product) => {
    sendMessage(MCPMessages.CART_ADD, { product });
    toast.success(`${product.name} added to cart`);
  };

  const handleViewDetails = (product: Product) => {
    sendMessage(MCPMessages.PRODUCT_DETAILS, { productId: product.id });
    toast.info(`Viewing details for ${product.name}`);
  };

  const handleFavorite = (product: Product) => {
    const newFavorites = new Set(favoriteProducts);
    if (newFavorites.has(product.id)) {
      newFavorites.delete(product.id);
      toast.default(`${product.name} removed from favorites`);
    } else {
      newFavorites.add(product.id);
      toast.success(`${product.name} added to favorites`);
    }
    setFavoriteProducts(newFavorites);
    sendMessage(MCPMessages.PRODUCT_FAVORITE, { 
      productId: product.id, 
      isFavorite: newFavorites.has(product.id) 
    });
  };

  return (
    <ThemeProvider defaultTheme="light">
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Header */}
        <header className="sticky top-0 z-40 bg-white dark:bg-gray-800 shadow-sm">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                MCP-UI Component Showcase
              </h1>
              <div className="flex items-center gap-4">
                <Badge variant="info">v1.0.0</Badge>
                <ThemeToggle className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" />
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8 space-y-12">
          {/* Buttons Section */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Buttons</h2>
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-wrap gap-3">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="success">Success</Button>
                  <Button variant="danger">Danger</Button>
                  <Button variant="warning">Warning</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="link">Link</Button>
                  <Button variant="outline">Outline</Button>
                  <Button loading loadingText="Processing...">Loading</Button>
                  <Button disabled>Disabled</Button>
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Button size="xs">Extra Small</Button>
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                  <Button size="xl">Extra Large</Button>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Input Fields Section */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Input Fields</h2>
            <Card>
              <CardContent className="p-6 space-y-4">
                <Input
                  label="Email Address"
                  type="email"
                  placeholder="Enter your email"
                  helperText="We'll never share your email"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                />
                <Input
                  label="Password"
                  type="password"
                  placeholder="Enter password"
                  required
                />
                <Input
                  label="Error State"
                  error="This field is required"
                  placeholder="Example with error"
                />
                <Input
                  label="Success State"
                  success="Valid input!"
                  placeholder="Example with success"
                />
                <Input
                  label="Disabled"
                  disabled
                  placeholder="Cannot edit"
                />
              </CardContent>
            </Card>
          </section>

          {/* Badges Section */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Badges</h2>
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-wrap gap-2">
                  <Badge>Default</Badge>
                  <Badge variant="primary">Primary</Badge>
                  <Badge variant="secondary">Secondary</Badge>
                  <Badge variant="success">Success</Badge>
                  <Badge variant="warning">Warning</Badge>
                  <Badge variant="error">Error</Badge>
                  <Badge variant="info">Info</Badge>
                  <Badge variant="outline">Outline</Badge>
                  <Badge removable onRemove={() => toast.info('Badge removed')}>
                    Removable
                  </Badge>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge size="xs">Extra Small</Badge>
                  <Badge size="sm">Small</Badge>
                  <Badge size="md">Medium</Badge>
                  <Badge size="lg">Large</Badge>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Cards Section */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Cards</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Default Card</CardTitle>
                  <CardDescription>This is a default card style</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">Card content goes here</p>
                </CardContent>
                <CardFooter>
                  <Button size="sm">Action</Button>
                </CardFooter>
              </Card>

              <Card variant="elevated">
                <CardHeader>
                  <CardTitle>Elevated Card</CardTitle>
                  <CardDescription>Card with shadow elevation</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">Elevated content</p>
                </CardContent>
              </Card>

              <Card variant="outlined">
                <CardHeader>
                  <CardTitle>Outlined Card</CardTitle>
                  <CardDescription>Card with border outline</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">Outlined content</p>
                </CardContent>
              </Card>
            </div>
          </section>

          {/* Product Cards Section */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Product Cards</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sampleProducts.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onAddToCart={handleAddToCart}
                  onViewDetails={handleViewDetails}
                  onFavorite={handleFavorite}
                  isFavorite={favoriteProducts.has(product.id)}
                />
              ))}
            </div>
            <div className="mt-8">
              <h3 className="text-lg font-medium mb-4">Compact Product Cards</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {sampleProducts.map((product) => (
                  <ProductCard
                    key={`compact-${product.id}`}
                    product={product}
                    variant="compact"
                    onAddToCart={handleAddToCart}
                    onFavorite={handleFavorite}
                    isFavorite={favoriteProducts.has(product.id)}
                  />
                ))}
              </div>
            </div>
          </section>

          {/* Shopping Cart Section */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Shopping Cart</h2>
            <div className="max-w-2xl">
              <ShoppingCart
                onCheckout={(items) => {
                  toast.success(`Proceeding to checkout with ${items.length} items`);
                }}
              />
            </div>
          </section>

          {/* Modal Section */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Modals</h2>
            <Card>
              <CardContent className="p-6">
                <div className="flex gap-3">
                  <Button onClick={() => setModalOpen(true)}>Open Modal</Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      toast.success('Success notification!');
                    }}
                  >
                    Show Success Toast
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => {
                      toast.error('Error notification!');
                    }}
                  >
                    Show Error Toast
                  </Button>
                  <Button
                    variant="warning"
                    onClick={() => {
                      toast.warning('Warning notification!');
                    }}
                  >
                    Show Warning Toast
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Toast Notifications Section */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Toast Notifications</h2>
            <Card>
              <CardContent className="p-6">
                <p className="text-gray-600 mb-4">
                  Click the buttons above to see different toast notifications
                </p>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => {
                      toast.info('Info notification with action', {
                        action: {
                          label: 'Undo',
                          onClick: () => console.log('Undo clicked'),
                        },
                      });
                    }}
                  >
                    Toast with Action
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      toast.default('Persistent notification', {
                        duration: 0, // Won't auto-dismiss
                      });
                    }}
                  >
                    Persistent Toast
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>
        </main>

        {/* Modal */}
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Example Modal"
          description="This is a demonstration of the modal component"
          size="md"
        >
          <div className="space-y-4">
            <p className="text-gray-600">
              Modals are perfect for displaying important information or collecting user input
              without navigating away from the current page.
            </p>
            <Input
              label="Example Input"
              placeholder="Type something..."
              helperText="This input is inside a modal"
            />
          </div>
          <ModalFooter>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                setModalOpen(false);
                toast.success('Modal action completed!');
              }}
            >
              Confirm
            </Button>
          </ModalFooter>
        </Modal>

        {/* Toast Container */}
        <ToastContainer toasts={[]} position="top-right" />
      </div>
    </ThemeProvider>
  );
};