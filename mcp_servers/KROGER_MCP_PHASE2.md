# Kroger MCP Server Phase 2 - Production Implementation

## Architecture Overview

Phase 2 of the Kroger MCP Server implements a production-ready shopping assistant with enterprise-grade features including OAuth 2.0 authentication, real-time cart management, and advanced API integration.

### System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web UI]
        MCP[MCP Client]
    end
    
    subgraph "API Gateway"
        FAST[FastAPI Server]
        AUTH[OAuth Handler]
        WS[WebSocket Manager]
    end
    
    subgraph "Service Layer"
        KAS[Kroger API Service]
        CACHE[Cache Service]
        SESSION[Session Manager]
        CART[Cart Service]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        REDIS[(Redis Cache)]
        QUEUE[Task Queue]
    end
    
    subgraph "External Services"
        KROGER[Kroger API]
        OAUTH[Kroger OAuth]
    end
    
    UI --> FAST
    MCP --> FAST
    FAST --> AUTH
    FAST --> WS
    AUTH --> SESSION
    FAST --> KAS
    KAS --> KROGER
    AUTH --> OAUTH
    SESSION --> PG
    KAS --> CACHE
    CACHE --> REDIS
    CART --> PG
    CART --> QUEUE
```

## Key Features

### 1. Enhanced Authentication System

#### OAuth 2.0 Authorization Code Flow
- **Secure user authentication** via Kroger's OAuth system
- **Token management** with automatic refresh
- **Session persistence** across requests
- **Multi-device support** with session synchronization

#### User Session Management
```python
# Session lifecycle
1. User initiates login → OAuth redirect
2. Authorization code received → Exchange for tokens
3. Session created with secure ID
4. Tokens stored encrypted in database
5. Automatic refresh before expiration
```

### 2. Advanced API Integration

#### Cart Management
- **Real-time cart synchronization** with Kroger backend
- **Persistent cart storage** across sessions
- **Smart quantity management** with inventory checks
- **Price tracking** and savings calculation

#### Location Services
- **Store finder** with geolocation support
- **Service filtering** (pharmacy, fuel, etc.)
- **Real-time availability** checks
- **Distance calculation** and routing

#### Digital Coupons
- **Automatic coupon discovery**
- **One-click clipping** to account
- **Savings tracking** and analytics
- **Expiration notifications**

### 3. Data Models

#### Core Entities

```python
# User Session
- session_id: Unique identifier
- user_id: Kroger user ID
- access_token: OAuth access token
- refresh_token: OAuth refresh token
- expires_at: Token expiration
- user_data: Profile information

# Cart Item
- product_id: Kroger UPC
- quantity: Item count
- price: Current price
- savings: Discount amount

# Digital Coupon
- coupon_id: Unique identifier
- discount_value: Dollar or percentage off
- applicable_products: Product list
- expiration_date: Valid until
```

### 4. Enhanced MCP Tools

#### Shopping Tools
| Tool | Description | UI Component |
|------|-------------|--------------|
| `search_products_advanced` | Advanced search with filters | Product grid with sorting |
| `manage_cart` | Full cart CRUD operations | Interactive cart view |
| `digital_coupons` | Browse and clip coupons | Coupon browser |
| `store_locator_advanced` | Find stores with services | Interactive map |

#### User Tools
| Tool | Description | UI Component |
|------|-------------|--------------|
| `user_profile` | Profile management | Profile editor |
| `order_history` | View past orders | Order timeline |
| `shopping_lists` | List management | List organizer |
| `meal_planner` | Meal planning | Weekly planner |

## API Endpoints

### Authentication Endpoints
```
GET  /auth/login          - Initiate OAuth flow
GET  /auth/callback       - OAuth callback handler
GET  /auth/logout         - Invalidate session
POST /auth/refresh        - Refresh access token
```

### Shopping Endpoints
```
POST /tools/search_products_advanced
POST /tools/manage_cart
POST /tools/digital_coupons
GET  /cart/{session_id}
PUT  /cart/{session_id}/items
```

### User Endpoints
```
GET  /profile/{session_id}
PUT  /profile/{session_id}
GET  /orders/{session_id}
GET  /lists/{session_id}
```

## Security Features

### Token Security
- **Encrypted storage** of OAuth tokens
- **Automatic rotation** before expiration
- **Secure session IDs** using cryptographic randomness
- **HTTPS-only** cookie flags

### Rate Limiting
- **Per-user limits**: 60 requests/minute
- **API quota management**: Track Kroger API usage
- **Graceful degradation**: Cache fallback on limits
- **DDoS protection**: Request throttling

### Data Protection
- **PII encryption** at rest
- **Secure communication** via TLS
- **GDPR compliance** with data deletion
- **Audit logging** for security events

## Performance Optimization

### Caching Strategy
```python
# Multi-tier caching
1. Browser cache: Static assets (1 hour)
2. Redis cache: Product data (5 minutes)
3. Database cache: User preferences (1 day)
4. CDN: UI components (1 week)
```

### Database Optimization
- **Connection pooling** for concurrent requests
- **Index optimization** on frequent queries
- **Prepared statements** for security
- **Read replicas** for scaling

### API Optimization
- **Batch requests** to Kroger API
- **Parallel processing** for independent calls
- **Response compression** with gzip
- **Field filtering** to reduce payload

## Deployment Configuration

### Environment Variables
```bash
# Required
KROGER_CLIENT_ID=your_client_id
KROGER_CLIENT_SECRET=your_client_secret
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://localhost:6379

# Optional
KROGER_REDIRECT_URI=http://localhost:9011/auth/callback
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn
MAX_REQUESTS_PER_MINUTE=60
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 9011

CMD ["python", "kroger_mcp_server_phase2.py"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  kroger-mcp:
    build: .
    ports:
      - "9011:9011"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db/kroger
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=kroger

  redis:
    image: redis:7-alpine
```

## Testing Strategy

### Unit Tests
```python
# Test authentication flow
def test_oauth_flow():
    - Mock OAuth redirect
    - Verify state generation
    - Test token exchange
    - Validate session creation

# Test cart operations
def test_cart_management():
    - Add items to cart
    - Update quantities
    - Remove items
    - Calculate totals
```

### Integration Tests
```python
# Test Kroger API integration
def test_kroger_api():
    - Product search
    - Store lookup
    - Cart synchronization
    - Coupon retrieval
```

### Load Tests
```bash
# Using locust for load testing
locust -f load_tests.py --host=http://localhost:9011
- 100 concurrent users
- 1000 requests/second
- 95th percentile < 200ms
```

## Monitoring & Observability

### Metrics Collection
- **Prometheus metrics** for system health
- **Custom metrics** for business KPIs
- **API latency** tracking
- **Error rate** monitoring

### Logging
```python
# Structured logging
logger.info("cart_updated", {
    "session_id": session_id,
    "item_count": len(items),
    "total_value": total,
    "timestamp": datetime.utcnow()
})
```

### Alerting
- **Uptime monitoring** with health checks
- **Error threshold** alerts
- **API quota** warnings
- **Security event** notifications

## Usage Examples

### 1. User Authentication
```python
# Initiate login
GET /auth/login
→ Redirects to Kroger OAuth

# After authorization
GET /auth/callback?code=xxx&state=yyy
→ Creates session, returns session_id
```

### 2. Product Search
```python
POST /tools/search_products_advanced
{
    "query": "organic milk",
    "session_id": "xxx",
    "filters": {
        "brand": "Simple Truth",
        "max_price": 10
    },
    "sort": "price_low"
}
```

### 3. Cart Management
```python
POST /tools/manage_cart
{
    "session_id": "xxx",
    "action": "add",
    "product_id": "0001111041700",
    "quantity": 2
}
```

### 4. Digital Coupons
```python
POST /tools/digital_coupons
{
    "session_id": "xxx",
    "category": "dairy"
}
```

## Troubleshooting

### Common Issues

#### OAuth Errors
```
Problem: "Invalid redirect URI"
Solution: Ensure KROGER_REDIRECT_URI matches app settings

Problem: "Token expired"
Solution: Automatic refresh should handle this, check refresh_token validity
```

#### API Rate Limits
```
Problem: "429 Too Many Requests"
Solution: Implement exponential backoff, use caching layer
```

#### Database Connection
```
Problem: "Connection pool exhausted"
Solution: Increase pool size, optimize query performance
```

## Future Enhancements

### Phase 3 Roadmap
1. **Machine Learning Integration**
   - Personalized product recommendations
   - Price prediction models
   - Shopping pattern analysis

2. **Advanced Features**
   - Voice shopping interface
   - Barcode scanning support
   - Recipe integration
   - Nutritional tracking

3. **Platform Expansion**
   - Mobile app support
   - Smart home integration
   - Third-party marketplace

4. **Enterprise Features**
   - Multi-account management
   - Bulk ordering
   - Invoice generation
   - Analytics dashboard

## Support & Resources

- **API Documentation**: [Kroger Developer Portal](https://developer.kroger.com/)
- **MCP Protocol**: [MCP Specification](https://modelcontextprotocol.io/)
- **Issue Tracking**: GitHub Issues
- **Community**: Discord Server

## License

This implementation is provided as-is for educational and development purposes. Ensure compliance with Kroger's API terms of service and data privacy regulations when deploying to production.