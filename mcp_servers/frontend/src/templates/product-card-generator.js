/**
 * Product Card Generator for Grocery Shopping MCP Server
 * Generates token-efficient HTML product cards from JSON data
 */

class ProductCardGenerator {
    /**
     * Generate a single product card HTML string
     * @param {Object} product - Product data object
     * @returns {string} HTML string for the product card
     */
    static generateCard(product) {
        // Parse price into dollars and cents
        const price = parseFloat(product.price);
        const priceDollars = Math.floor(price);
        const priceCents = Math.round((price - priceDollars) * 100).toString().padStart(2, '0');
        
        // Determine availability status
        const availabilityColor = product.available ? '#10b981' : '#ef4444';
        const availabilityText = product.available ? 'In Stock' : 'Out of Stock';
        const buttonDisabled = !product.available;
        
        // Generate gradient colors based on availability
        const gradientColors = product.available 
            ? this.getRandomGradient() 
            : 'linear-gradient(135deg, #a8a8a8 0%, #6b6b6b 100%)';
        
        // Delivery badge visibility
        const deliveryDisplay = product.delivery && product.available ? 'flex' : 'none';
        
        return `
<div class="product-card" 
     data-upc="${product.upc}"
     data-product-id="${product.id || product.upc}"
     style="
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        ${!product.available ? 'opacity: 0.8;' : ''}
     "
     onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.12)'"
     onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.08)'">
    
    <div style="
        height: 180px;
        background: ${gradientColors};
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    ">
        <div style="
            position: absolute;
            top: 12px;
            right: 12px;
            background: ${availabilityColor};
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        ">
            ${availabilityText}
        </div>
        
        <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
            <path d="M9 2L3 7v13a2 2 0 002 2h14a2 2 0 002-2V7l-6-5z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
    </div>
    
    <div style="padding: 16px;">
        <div style="
            color: #666;
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        ">
            ${product.brand}
        </div>
        
        <h3 style="
            margin: 0 0 8px 0;
            font-size: 16px;
            font-weight: 600;
            color: #222;
            line-height: 1.3;
            min-height: 42px;
        ">
            ${this.truncateName(product.name)}
        </h3>
        
        <div style="
            color: #666;
            font-size: 14px;
            margin-bottom: 12px;
        ">
            ${product.size}
        </div>
        
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        ">
            <div style="
                display: flex;
                align-items: baseline;
                gap: 2px;
            ">
                <span style="
                    font-size: 14px;
                    color: #666;
                    font-weight: 500;
                ">$</span>
                <span style="
                    font-size: 24px;
                    font-weight: 700;
                    color: #222;
                ">${priceDollars}</span>
                <span style="
                    font-size: 16px;
                    color: #666;
                    font-weight: 500;
                ">.${priceCents}</span>
            </div>
            
            ${buttonDisabled ? `
            <button 
                disabled
                style="
                    background: #d1d5db;
                    color: #6b7280;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: not-allowed;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                ">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                Unavailable
            </button>
            ` : `
            <button 
                class="add-to-cart-btn"
                data-upc="${product.upc}"
                onclick="handleAddToCart(this)"
                style="
                    background: #10b981;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                "
                onmouseover="this.style.background='#059669'"
                onmouseout="this.style.background='#10b981'">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="9" cy="21" r="1"/>
                    <circle cx="20" cy="21" r="1"/>
                    <path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/>
                </svg>
                Add
            </button>
            `}
        </div>
        
        <div style="
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e5e5e5;
            display: ${deliveryDisplay};
            align-items: center;
            gap: 6px;
            color: #059669;
            font-size: 13px;
            font-weight: 500;
        ">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="1" y="3" width="15" height="13"/>
                <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                <circle cx="5.5" cy="18.5" r="2.5"/>
                <circle cx="18.5" cy="18.5" r="2.5"/>
            </svg>
            Delivery Available
        </div>
    </div>
</div>`;
    }
    
    /**
     * Generate a grid of product cards
     * @param {Array} products - Array of product objects
     * @returns {string} HTML string for the product grid
     */
    static generateGrid(products) {
        const cards = products.map(product => this.generateCard(product)).join('\n');
        
        return `
<div style="
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
">
    ${cards}
</div>

<script>
function handleAddToCart(button) {
    const upc = button.getAttribute('data-upc');
    const card = button.closest('.product-card');
    
    // Visual feedback
    button.innerHTML = \`
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
        </svg>
        Added
    \`;
    button.style.background = '#059669';
    
    // Call MCP endpoint
    if (window.mcpClient) {
        window.mcpClient.addToCart({
            upc: upc,
            quantity: 1
        });
    }
    
    // Emit custom event for integration
    window.dispatchEvent(new CustomEvent('mcp:addToCart', {
        detail: { upc, quantity: 1 }
    }));
    
    // Reset button after delay
    setTimeout(() => {
        button.innerHTML = \`
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="9" cy="21" r="1"/>
                <circle cx="20" cy="21" r="1"/>
                <path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/>
            </svg>
            Add
        \`;
        button.style.background = '#10b981';
    }, 2000);
}
</script>`;
    }
    
    /**
     * Generate a compact list view of products
     * @param {Array} products - Array of product objects
     * @returns {string} HTML string for the compact list
     */
    static generateCompactList(products) {
        const items = products.map(product => {
            const price = parseFloat(product.price);
            const available = product.available;
            
            return `
<div style="
    display: flex;
    align-items: center;
    padding: 12px;
    background: white;
    border-radius: 8px;
    margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ${!available ? 'opacity: 0.6;' : ''}
">
    <div style="flex: 1;">
        <div style="font-weight: 600; color: #222; font-size: 14px;">
            ${this.truncateName(product.name, 50)}
        </div>
        <div style="color: #666; font-size: 12px; margin-top: 2px;">
            ${product.brand} • ${product.size}
        </div>
    </div>
    <div style="
        font-weight: 700;
        color: #222;
        font-size: 18px;
        margin: 0 16px;
    ">
        $${price.toFixed(2)}
    </div>
    ${available ? `
    <button 
        data-upc="${product.upc}"
        onclick="handleAddToCart(this)"
        style="
            background: #10b981;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
        ">
        Add
    </button>
    ` : `
    <span style="
        color: #ef4444;
        font-size: 12px;
        font-weight: 600;
    ">Out of Stock</span>
    `}
</div>`;
        }).join('\n');
        
        return `
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    ${items}
</div>`;
    }
    
    /**
     * Truncate product name for display
     * @param {string} name - Product name
     * @param {number} maxLength - Maximum length (default: 60)
     * @returns {string} Truncated name
     */
    static truncateName(name, maxLength = 60) {
        // Remove brand from name if it's redundant
        const cleanName = name.replace(/^(Kroger®?|Simple Truth|Private Selection)\s*/i, '');
        
        if (cleanName.length <= maxLength) {
            return cleanName;
        }
        
        return cleanName.substring(0, maxLength - 3) + '...';
    }
    
    /**
     * Get a random gradient for product cards
     * @returns {string} CSS gradient string
     */
    static getRandomGradient() {
        const gradients = [
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
            'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)'
        ];
        
        return gradients[Math.floor(Math.random() * gradients.length)];
    }
    
    /**
     * Generate a complete HTML page with product cards
     * @param {Array} products - Array of product objects
     * @param {string} title - Page title
     * @returns {string} Complete HTML document
     */
    static generateFullPage(products, title = 'Product Catalog') {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #222;
            margin-bottom: 30px;
            font-size: 28px;
        }
    </style>
</head>
<body>
    <h1>${title}</h1>
    ${this.generateGrid(products)}
</body>
</html>`;
    }
}

// Export for use in Node.js/CommonJS environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProductCardGenerator;
}

// Export for ES6 modules
export default ProductCardGenerator;