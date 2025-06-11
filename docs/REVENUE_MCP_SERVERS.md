# Revenue-Focused MCP Servers

This document describes the new MCP servers implemented to enhance BoarderframeOS with revenue generation capabilities.

## Overview

Three new MCP servers have been added to the ecosystem:

1. **Payment Server** - Handles payments, subscriptions and billing operations
2. **Analytics Server** - Tracks business KPIs and provides analytics functionality
3. **Customer Server** - Manages customer data, subscriptions and interactions

These servers work together with the existing infrastructure to enable revenue generation and business operations for the BoarderframeOS platform.

## Payment Server

**Purpose**: Process payments, manage subscriptions, and handle billing operations.

**Key Features**:
- Stripe integration for payment processing
- Subscription management (creation, updates, cancellation)
- Usage-based billing calculations
- Invoice generation
- Payment webhooks for third-party integrations

**Endpoints**:
- `/health` - Health check endpoint
- `/payment` - Process individual payments
- `/subscription` - Create and manage subscriptions
- `/invoice` - Generate invoices
- `/webhook` - Handle payment processor webhooks
- `/stats` - Payment statistics

**Configuration**:
```yaml
payment:
  dependencies:
    - httpx
    - fastapi
    - pydantic
  enabled: true
  features:
    stripe_integration: true
    subscription_management: true
    usage_based_billing: true
    invoice_generation: true
    payment_webhooks: true
  health_endpoint: http://localhost:8006/health
  path: mcp/payment_server.py
  port: 8006
  startup_script: mcp/payment_server.py
```

## Analytics Server

**Purpose**: Track business metrics, calculate KPIs, and provide business insights.

**Key Features**:
- Customer acquisition cost calculation
- Customer lifetime value tracking
- Churn rate monitoring
- Revenue per agent analysis
- API usage metrics
- Business dashboard data

**Endpoints**:
- `/health` - Health check endpoint
- `/track` - Track an analytics event
- `/metrics/customer-acquisition` - Get customer acquisition cost
- `/metrics/lifetime-value` - Get customer lifetime value
- `/metrics/churn` - Get churn rate
- `/metrics/revenue-per-agent` - Get revenue generated per agent
- `/metrics/api-usage` - Get API usage metrics
- `/kpi` - Calculate specific KPIs
- `/dashboard-data` - Get data for analytics dashboard

**Configuration**:
```yaml
analytics:
  dependencies:
    - httpx
    - fastapi
    - pydantic
    - numpy
    - pandas
  enabled: true
  features:
    customer_acquisition_cost: true
    customer_lifetime_value: true
    churn_rate: true
    revenue_per_agent: true
    api_usage_metrics: true
  health_endpoint: http://localhost:8007/health
  path: mcp/analytics_server.py
  port: 8007
  startup_script: mcp/analytics_server.py
```

## Customer Server

**Purpose**: Manage customer relationships, interactions, and subscription information.

**Key Features**:
- Customer database management
- Customer interaction tracking
- Subscription status monitoring
- Customer analytics integration
- Payment system integration

**Endpoints**:
- `/health` - Health check endpoint
- `/customers` - CRUD operations for customers
- `/interactions` - Track and manage customer interactions
- `/customers/{customer_id}/subscription` - Get subscription details
- `/stats` - Customer statistics

**Configuration**:
```yaml
customer:
  dependencies:
    - httpx
    - fastapi
    - pydantic
  enabled: true
  features:
    customer_management: true
    subscription_tracking: true
    interaction_logging: true
  health_endpoint: http://localhost:8008/health
  path: mcp/customer_server.py
  port: 8008
  startup_script: mcp/customer_server.py
```

## Database Schema Extensions

The following tables have been added to the database schema:

### Revenue Transactions
```sql
CREATE TABLE IF NOT EXISTS revenue_transactions (
    id TEXT PRIMARY KEY,
    customer_id TEXT,
    amount DECIMAL(10,2),
    currency TEXT,
    product TEXT,
    agent_id TEXT,  -- Which agent generated this revenue
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Customers
```sql
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    stripe_customer_id TEXT,
    subscription_status TEXT,
    monthly_value DECIMAL(10,2),
    created_by_agent TEXT
)
```

### API Usage
```sql
CREATE TABLE IF NOT EXISTS api_usage (
    customer_id TEXT,
    endpoint TEXT,
    tokens_used INTEGER,
    cost DECIMAL(10,4),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Agent Integration

The revenue-focused MCP servers are integrated with the following agents:

- **Solomon** (Chief of Staff) - Analyzes business health, tracks KPIs, makes revenue-focused decisions
- **David** (CEO) - Provides strategic leadership, resource allocation, and P&L management
- **Eve** (Evolver) - Considers profit metrics in agent evolution and fitness calculations

## Starting the Servers

The servers can be started individually or together with the system startup script:

```bash
# Start all servers
python startup.py

# Start individual servers
python mcp/payment_server.py
python mcp/analytics_server.py
python mcp/customer_server.py
```

Or using the MCP server launcher:

```bash
python mcp/server_launcher.py --servers payment analytics customer
```
