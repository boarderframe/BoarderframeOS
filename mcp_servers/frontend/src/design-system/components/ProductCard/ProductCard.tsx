import React, { forwardRef } from 'react';
import { cn } from '../../utils/cn';
import { Card } from '../Card/Card';
import { Button } from '../Button/Button';
import { Badge } from '../Badge/Badge';

/**
 * ProductCard Component
 * Display product information with image, price, and actions
 * Optimized for e-commerce and Kroger products
 * 
 * @example
 * <ProductCard
 *   product={{
 *     id: '123',
 *     name: 'Organic Bananas',
 *     brand: 'Kroger',
 *     price: 2.99,
 *     originalPrice: 3.99,
 *     image: '/banana.jpg',
 *     rating: 4.5,
 *     reviews: 234,
 *     inStock: true,
 *     tags: ['Organic', 'Fresh']
 *   }}
 *   onAddToCart={handleAddToCart}
 *   onViewDetails={handleViewDetails}
 * />
 */

export interface Product {
  id: string;
  name: string;
  brand?: string;
  description?: string;
  price: number;
  originalPrice?: number;
  currency?: string;
  image: string;
  images?: string[];
  rating?: number;
  reviews?: number;
  inStock?: boolean;
  quantity?: number;
  unit?: string;
  tags?: string[];
  promotion?: string;
  nutritionInfo?: Record<string, any>;
}

export interface ProductCardProps {
  product: Product;
  variant?: 'default' | 'compact' | 'detailed';
  onAddToCart?: (product: Product) => void;
  onViewDetails?: (product: Product) => void;
  onFavorite?: (product: Product) => void;
  isFavorite?: boolean;
  showActions?: boolean;
  className?: string;
}

export const ProductCard = forwardRef<HTMLDivElement, ProductCardProps>(
  (
    {
      product,
      variant = 'default',
      onAddToCart,
      onViewDetails,
      onFavorite,
      isFavorite = false,
      showActions = true,
      className,
    },
    ref
  ) => {
    const discount = product.originalPrice
      ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
      : 0;

    const formatPrice = (price: number) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: product.currency || 'USD',
      }).format(price);
    };

    const renderRating = () => {
      if (!product.rating) return null;
      
      return (
        <div className="flex items-center gap-1">
          <div className="flex">
            {[...Array(5)].map((_, i) => (
              <svg
                key={i}
                className={cn(
                  'w-4 h-4',
                  i < Math.floor(product.rating!) ? 'text-yellow-400' : 'text-gray-300'
                )}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
          <span className="text-sm text-gray-600">
            {product.rating} {product.reviews && `(${product.reviews})`}
          </span>
        </div>
      );
    };

    if (variant === 'compact') {
      return (
        <Card
          ref={ref}
          className={cn('overflow-hidden hover:shadow-lg transition-shadow', className)}
          interactive
        >
          <div className="relative">
            <img
              src={product.image}
              alt={product.name}
              className="w-full h-32 object-cover"
              loading="lazy"
            />
            {discount > 0 && (
              <Badge className="absolute top-2 left-2" variant="danger">
                -{discount}%
              </Badge>
            )}
            {onFavorite && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFavorite(product);
                }}
                className="absolute top-2 right-2 p-1 bg-white rounded-full shadow-md hover:shadow-lg transition-shadow"
                aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
              >
                <svg
                  className={cn('w-5 h-5', isFavorite ? 'text-red-500' : 'text-gray-400')}
                  fill={isFavorite ? 'currentColor' : 'none'}
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                  />
                </svg>
              </button>
            )}
          </div>
          <div className="p-3">
            <h3 className="font-medium text-sm text-gray-900 line-clamp-2">{product.name}</h3>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-lg font-bold text-gray-900">{formatPrice(product.price)}</span>
              {product.originalPrice && (
                <span className="text-sm text-gray-500 line-through">
                  {formatPrice(product.originalPrice)}
                </span>
              )}
            </div>
            {showActions && onAddToCart && (
              <Button
                size="sm"
                variant="primary"
                fullWidth
                className="mt-2"
                onClick={() => onAddToCart(product)}
                disabled={!product.inStock}
              >
                {product.inStock ? 'Add to Cart' : 'Out of Stock'}
              </Button>
            )}
          </div>
        </Card>
      );
    }

    return (
      <Card
        ref={ref}
        className={cn('overflow-hidden hover:shadow-lg transition-shadow', className)}
        padding="none"
        interactive={!!onViewDetails}
        onClick={() => onViewDetails?.(product)}
      >
        {/* Image Section */}
        <div className="relative aspect-square overflow-hidden bg-gray-100">
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
          {discount > 0 && (
            <Badge className="absolute top-3 left-3" variant="danger">
              -{discount}%
            </Badge>
          )}
          {product.promotion && (
            <Badge className="absolute top-3 right-3" variant="warning">
              {product.promotion}
            </Badge>
          )}
          {onFavorite && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onFavorite(product);
              }}
              className="absolute top-3 right-3 p-2 bg-white rounded-full shadow-md hover:shadow-lg transition-shadow"
              aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              <svg
                className={cn('w-5 h-5', isFavorite ? 'text-red-500' : 'text-gray-400')}
                fill={isFavorite ? 'currentColor' : 'none'}
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Content Section */}
        <div className="p-4">
          {product.brand && (
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {product.brand}
            </p>
          )}
          <h3 className="mt-1 font-semibold text-gray-900 line-clamp-2">{product.name}</h3>
          
          {product.description && variant === 'detailed' && (
            <p className="mt-2 text-sm text-gray-600 line-clamp-2">{product.description}</p>
          )}

          {renderRating()}

          {/* Tags */}
          {product.tags && product.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {product.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="secondary" size="sm">
                  {tag}
                </Badge>
              ))}
            </div>
          )}

          {/* Price Section */}
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-gray-900">
              {formatPrice(product.price)}
            </span>
            {product.originalPrice && (
              <span className="text-sm text-gray-500 line-through">
                {formatPrice(product.originalPrice)}
              </span>
            )}
            {product.unit && (
              <span className="text-sm text-gray-600">/{product.unit}</span>
            )}
          </div>

          {/* Stock Status */}
          {!product.inStock && (
            <Badge variant="error" className="mt-2">
              Out of Stock
            </Badge>
          )}

          {/* Actions */}
          {showActions && (
            <div className="mt-4 flex gap-2">
              {onAddToCart && (
                <Button
                  variant="primary"
                  size="md"
                  fullWidth
                  onClick={(e) => {
                    e.stopPropagation();
                    onAddToCart(product);
                  }}
                  disabled={!product.inStock}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  Add to Cart
                </Button>
              )}
              {onViewDetails && (
                <Button
                  variant="outline"
                  size="md"
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewDetails(product);
                  }}
                >
                  Details
                </Button>
              )}
            </div>
          )}
        </div>
      </Card>
    );
  }
);

ProductCard.displayName = 'ProductCard';