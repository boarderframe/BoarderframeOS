import React, { useState } from 'react';

interface Product {
  name: string;
  upc: string;
  brand: string;
  price: number;
  size: string;
  available: boolean;
  delivery?: boolean;
  image?: string;
}

interface ProductCardProps {
  product: Product;
  onAddToCart?: (upc: string, quantity: number) => void;
}

/**
 * ProductCard Component
 * Token-efficient, mobile-responsive product card for grocery shopping
 */
export const ProductCard: React.FC<ProductCardProps> = ({ product, onAddToCart }) => {
  const [isAdded, setIsAdded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  // Parse price
  const priceDollars = Math.floor(product.price);
  const priceCents = Math.round((product.price - priceDollars) * 100)
    .toString()
    .padStart(2, '0');

  // Clean product name (remove redundant brand)
  const cleanName = product.name.replace(/^(Kroger®?|Simple Truth|Private Selection)\s*/i, '');
  const displayName = cleanName.length > 60 ? cleanName.substring(0, 57) + '...' : cleanName;

  // Handle add to cart
  const handleAddToCart = () => {
    if (!product.available || isAdded) return;

    setIsAdded(true);
    
    // Call parent handler
    if (onAddToCart) {
      onAddToCart(product.upc, 1);
    }

    // Emit custom event for MCP integration
    window.dispatchEvent(
      new CustomEvent('mcp:addToCart', {
        detail: { upc: product.upc, quantity: 1 }
      })
    );

    // Reset after animation
    setTimeout(() => setIsAdded(false), 2000);
  };

  // Gradient colors for visual appeal
  const gradients = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  ];
  
  const gradient = product.available 
    ? gradients[product.upc.charCodeAt(0) % gradients.length]
    : 'linear-gradient(135deg, #a8a8a8 0%, #6b6b6b 100%)';

  return (
    <div
      className="product-card"
      data-upc={product.upc}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: 'white',
        borderRadius: '12px',
        boxShadow: isHovered 
          ? '0 4px 12px rgba(0,0,0,0.12)' 
          : '0 2px 8px rgba(0,0,0,0.08)',
        overflow: 'hidden',
        transition: 'transform 0.2s, box-shadow 0.2s',
        transform: isHovered ? 'translateY(-2px)' : 'translateY(0)',
        cursor: 'pointer',
        opacity: product.available ? 1 : 0.8,
      }}
    >
      {/* Product Image/Placeholder */}
      <div
        style={{
          height: '180px',
          background: gradient,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
      >
        {/* Availability Badge */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            background: product.available ? '#10b981' : '#ef4444',
            color: 'white',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {product.available ? 'In Stock' : 'Out of Stock'}
        </div>

        {/* Product Icon */}
        <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
          <path d="M9 2L3 7v13a2 2 0 002 2h14a2 2 0 002-2V7l-6-5z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      </div>

      {/* Product Details */}
      <div style={{ padding: '16px' }}>
        {/* Brand */}
        <div
          style={{
            color: '#666',
            fontSize: '12px',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '4px',
          }}
        >
          {product.brand}
        </div>

        {/* Product Name */}
        <h3
          style={{
            margin: '0 0 8px 0',
            fontSize: '16px',
            fontWeight: 600,
            color: '#222',
            lineHeight: 1.3,
            minHeight: '42px',
          }}
        >
          {displayName}
        </h3>

        {/* Size */}
        <div
          style={{
            color: '#666',
            fontSize: '14px',
            marginBottom: '12px',
          }}
        >
          {product.size}
        </div>

        {/* Price and Action */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
          }}
        >
          {/* Price */}
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '2px' }}>
            <span style={{ fontSize: '14px', color: '#666', fontWeight: 500 }}>$</span>
            <span style={{ fontSize: '24px', fontWeight: 700, color: '#222' }}>
              {priceDollars}
            </span>
            <span style={{ fontSize: '16px', color: '#666', fontWeight: 500 }}>
              .{priceCents}
            </span>
          </div>

          {/* Add to Cart Button */}
          {product.available ? (
            <button
              onClick={handleAddToCart}
              disabled={isAdded}
              style={{
                background: isAdded ? '#059669' : '#10b981',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: isAdded ? 'default' : 'pointer',
                transition: 'background 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
              onMouseEnter={(e) => !isAdded && (e.currentTarget.style.background = '#059669')}
              onMouseLeave={(e) => !isAdded && (e.currentTarget.style.background = '#10b981')}
            >
              {isAdded ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  Added
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="9" cy="21" r="1" />
                    <circle cx="20" cy="21" r="1" />
                    <path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6" />
                  </svg>
                  Add
                </>
              )}
            </button>
          ) : (
            <button
              disabled
              style={{
                background: '#d1d5db',
                color: '#6b7280',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
              Unavailable
            </button>
          )}
        </div>

        {/* Delivery Badge */}
        {product.delivery && product.available && (
          <div
            style={{
              marginTop: '12px',
              paddingTop: '12px',
              borderTop: '1px solid #e5e5e5',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: '#059669',
              fontSize: '13px',
              fontWeight: 500,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="1" y="3" width="15" height="13" />
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
              <circle cx="5.5" cy="18.5" r="2.5" />
              <circle cx="18.5" cy="18.5" r="2.5" />
            </svg>
            Delivery Available
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * ProductGrid Component
 * Responsive grid layout for multiple product cards
 */
export const ProductGrid: React.FC<{ 
  products: Product[]; 
  onAddToCart?: (upc: string, quantity: number) => void;
}> = ({ products, onAddToCart }) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '20px',
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '20px',
      }}
    >
      {products.map((product) => (
        <ProductCard 
          key={product.upc} 
          product={product} 
          onAddToCart={onAddToCart}
        />
      ))}
    </div>
  );
};

/**
 * CompactProductList Component
 * Space-efficient list view for mobile or sidebar
 */
export const CompactProductList: React.FC<{
  products: Product[];
  onAddToCart?: (upc: string, quantity: number) => void;
}> = ({ products, onAddToCart }) => {
  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
      {products.map((product) => (
        <div
          key={product.upc}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '12px',
            background: 'white',
            borderRadius: '8px',
            marginBottom: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            opacity: product.available ? 1 : 0.6,
          }}
        >
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, color: '#222', fontSize: '14px' }}>
              {product.name.length > 50 
                ? product.name.substring(0, 47) + '...' 
                : product.name}
            </div>
            <div style={{ color: '#666', fontSize: '12px', marginTop: '2px' }}>
              {product.brand} • {product.size}
            </div>
          </div>
          <div
            style={{
              fontWeight: 700,
              color: '#222',
              fontSize: '18px',
              margin: '0 16px',
            }}
          >
            ${product.price.toFixed(2)}
          </div>
          {product.available ? (
            <button
              onClick={() => onAddToCart && onAddToCart(product.upc, 1)}
              style={{
                background: '#10b981',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Add
            </button>
          ) : (
            <span
              style={{
                color: '#ef4444',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              Out of Stock
            </span>
          )}
        </div>
      ))}
    </div>
  );
};

export default ProductCard;