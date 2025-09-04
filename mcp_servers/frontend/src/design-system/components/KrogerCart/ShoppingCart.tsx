import React, { useState, useEffect } from 'react';
import { cn } from '../../utils/cn';
import { Button } from '../Button/Button';
import { Badge } from '../Badge/Badge';
import { Card } from '../Card/Card';
import { useMCPBridge, MCPMessages } from '../../utils/postMessageBridge';
import { toast } from '../Toast/Toast';

/**
 * Shopping Cart Component for Kroger
 * Full-featured cart management with MCP integration
 */

export interface CartItem {
  id: string;
  productId: string;
  name: string;
  brand?: string;
  price: number;
  originalPrice?: number;
  quantity: number;
  image: string;
  unit?: string;
  maxQuantity?: number;
  savings?: number;
}

export interface ShoppingCartProps {
  className?: string;
  onCheckout?: (items: CartItem[]) => void;
  editable?: boolean;
  showSummary?: boolean;
}

export const ShoppingCart: React.FC<ShoppingCartProps> = ({
  className,
  onCheckout,
  editable = true,
  showSummary = true,
}) => {
  const [items, setItems] = useState<CartItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [promoCode, setPromoCode] = useState('');
  const [appliedPromo, setAppliedPromo] = useState<string | null>(null);
  const { sendMessage, sendRequest, onMessage } = useMCPBridge();

  // Load cart data
  useEffect(() => {
    loadCart();

    // Listen for cart updates
    const unsubscribe = onMessage(MCPMessages.CART_UPDATE, (message) => {
      setItems(message.payload.items || []);
    });

    return unsubscribe;
  }, []);

  const loadCart = async () => {
    try {
      setIsLoading(true);
      const data = await sendRequest<{ items: CartItem[] }>(MCPMessages.DATA_REQUEST, {
        type: 'cart',
      });
      setItems(data.items);
    } catch (error) {
      toast.error('Failed to load cart');
    } finally {
      setIsLoading(false);
    }
  };

  const updateQuantity = async (itemId: string, quantity: number) => {
    if (quantity < 1) {
      removeItem(itemId);
      return;
    }

    const item = items.find(i => i.id === itemId);
    if (item && item.maxQuantity && quantity > item.maxQuantity) {
      toast.warning(`Maximum quantity is ${item.maxQuantity}`);
      return;
    }

    try {
      await sendRequest(MCPMessages.CART_UPDATE, {
        itemId,
        quantity,
      });
      
      setItems(prev =>
        prev.map(item =>
          item.id === itemId ? { ...item, quantity } : item
        )
      );
      
      toast.success('Cart updated');
    } catch (error) {
      toast.error('Failed to update quantity');
    }
  };

  const removeItem = async (itemId: string) => {
    try {
      await sendRequest(MCPMessages.CART_REMOVE, { itemId });
      setItems(prev => prev.filter(item => item.id !== itemId));
      toast.success('Item removed from cart');
    } catch (error) {
      toast.error('Failed to remove item');
    }
  };

  const clearCart = async () => {
    try {
      await sendRequest(MCPMessages.CART_CLEAR);
      setItems([]);
      toast.success('Cart cleared');
    } catch (error) {
      toast.error('Failed to clear cart');
    }
  };

  const applyPromoCode = async () => {
    if (!promoCode.trim()) return;

    try {
      const result = await sendRequest<{ success: boolean; discount?: number }>(
        MCPMessages.ACTION_EXECUTE,
        {
          action: 'applyPromo',
          code: promoCode,
        }
      );

      if (result.success) {
        setAppliedPromo(promoCode);
        toast.success(`Promo code applied! Saved ${result.discount || 0}%`);
      } else {
        toast.error('Invalid promo code');
      }
    } catch (error) {
      toast.error('Failed to apply promo code');
    }
  };

  const handleCheckout = () => {
    if (items.length === 0) {
      toast.warning('Your cart is empty');
      return;
    }

    sendMessage(MCPMessages.CART_CHECKOUT, {
      items,
      promoCode: appliedPromo,
      total: total,
    });

    onCheckout?.(items);
  };

  // Calculate totals
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const savings = items.reduce(
    (sum, item) =>
      sum + (item.originalPrice ? (item.originalPrice - item.price) * item.quantity : 0),
    0
  );
  const tax = subtotal * 0.08; // 8% tax
  const total = subtotal + tax;

  const formatPrice = (price: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <Card className={cn('text-center p-8', className)}>
        <svg
          className="mx-auto h-12 w-12 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Your cart is empty</h3>
        <p className="text-gray-600">Add items to get started</p>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Cart Items */}
      <Card>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              Shopping Cart ({items.length} items)
            </h2>
            {editable && (
              <Button variant="ghost" size="sm" onClick={clearCart}>
                Clear Cart
              </Button>
            )}
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {items.map((item) => (
            <div key={item.id} className="p-4 flex gap-4">
              <img
                src={item.image}
                alt={item.name}
                className="w-20 h-20 object-cover rounded-lg"
              />
              
              <div className="flex-1">
                <div className="flex justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">{item.name}</h3>
                    {item.brand && (
                      <p className="text-sm text-gray-500">{item.brand}</p>
                    )}
                    <div className="mt-1 flex items-baseline gap-2">
                      <span className="font-semibold text-gray-900">
                        {formatPrice(item.price)}
                      </span>
                      {item.originalPrice && (
                        <span className="text-sm text-gray-500 line-through">
                          {formatPrice(item.originalPrice)}
                        </span>
                      )}
                      {item.unit && (
                        <span className="text-sm text-gray-600">/{item.unit}</span>
                      )}
                    </div>
                  </div>
                  
                  {editable && (
                    <button
                      onClick={() => removeItem(item.id)}
                      className="text-gray-400 hover:text-red-600"
                      aria-label="Remove item"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>

                <div className="mt-2 flex items-center gap-2">
                  {editable ? (
                    <div className="flex items-center border border-gray-300 rounded-md">
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        className="p-1 hover:bg-gray-100"
                        aria-label="Decrease quantity"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                        </svg>
                      </button>
                      <span className="px-3 py-1 min-w-[3rem] text-center">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        className="p-1 hover:bg-gray-100"
                        aria-label="Increase quantity"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-600">Qty: {item.quantity}</span>
                  )}
                  
                  <span className="ml-auto font-semibold text-gray-900">
                    {formatPrice(item.price * item.quantity)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Promo Code */}
      {editable && (
        <Card className="p-4">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Enter promo code"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Button onClick={applyPromoCode} disabled={!promoCode.trim()}>
              Apply
            </Button>
          </div>
          {appliedPromo && (
            <div className="mt-2 flex items-center gap-2">
              <Badge variant="success">
                Promo applied: {appliedPromo}
              </Badge>
              <button
                onClick={() => {
                  setAppliedPromo(null);
                  setPromoCode('');
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Remove
              </button>
            </div>
          )}
        </Card>
      )}

      {/* Order Summary */}
      {showSummary && (
        <Card className="p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Order Summary</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Subtotal</span>
              <span className="text-gray-900">{formatPrice(subtotal)}</span>
            </div>
            {savings > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-green-600">Savings</span>
                <span className="text-green-600">-{formatPrice(savings)}</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Estimated Tax</span>
              <span className="text-gray-900">{formatPrice(tax)}</span>
            </div>
            <div className="pt-2 border-t border-gray-200">
              <div className="flex justify-between font-semibold text-lg">
                <span>Total</span>
                <span>{formatPrice(total)}</span>
              </div>
            </div>
          </div>
          
          {editable && (
            <Button
              variant="primary"
              size="lg"
              fullWidth
              className="mt-4"
              onClick={handleCheckout}
            >
              Proceed to Checkout
            </Button>
          )}
        </Card>
      )}
    </div>
  );
};