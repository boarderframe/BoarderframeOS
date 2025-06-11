# BoarderframeOS HQ Metrics Layer Guide

## Overview

The HQ Metrics Layer provides a comprehensive, standardized system for calculating and displaying metrics across Corporate Headquarters. It includes:

- **Unified Metrics Calculation** - Single source of truth for all metrics
- **Standardized Visual Elements** - Consistent colors and icons
- **Reusable Card Components** - Pre-built UI components
- **Real-time Data Integration** - Live data from database and registry
- **Performance Optimization** - Built-in caching and efficient queries

## Architecture

### Core Components

1. **`core/hq_metrics_layer.py`** - Main metrics calculation and rendering engine
   - `MetricsCalculator` - Calculates all metrics from database
   - `CardRenderer` - Renders reusable UI components
   - `BFColors` - Standardized color palette
   - `BFIcons` - Standardized icon set

2. **`core/hq_metrics_integration.py`** - Integration layer for Corporate HQ
   - `HQMetricsIntegration` - High-level API for using metrics
   - Pre-built card generators
   - CSS styling

3. **Database Schema** - Visual metadata storage
   - `departments.configuration` - JSONB with visual settings
   - `divisions.configuration` - JSONB with visual settings
   - `department_registry.metadata` - JSONB with visual settings

## Usage Examples

### 1. Basic Setup

```python
from core.hq_metrics_integration import HQMetricsIntegration, METRICS_CSS

# Initialize the metrics integration
metrics = HQMetricsIntegration()

# Get all metrics (with 30-second caching)
all_metrics = metrics.get_all_metrics()
```

### 2. Dashboard Summary Cards

```python
# Generate dashboard summary cards HTML
summary_html = metrics.get_dashboard_summary_cards()

# Include in your HTML template
html = f"""
{METRICS_CSS}
<div class="dashboard-content">
    {summary_html}
</div>
"""
```

### 3. Agent Metrics

```python
# Get agent-specific metrics
agent_metrics = metrics.get_agents_page_metrics()
print(f"Active Agents: {agent_metrics['active']}")
print(f"Total Agents: {agent_metrics['total']}")

# Generate agent cards
agent_cards_html = metrics.get_agent_cards_html(limit=10, status_filter='online')
```

### 4. Department Cards with Visual Metadata

```python
# Get departments with colors and icons
departments = metrics.get_departments_visual_data()

for dept in departments:
    print(f"{dept['name']}: {dept['icon']} (color: {dept['color']})")

# Generate department cards grouped by division
dept_cards_html = metrics.get_department_cards_html()
```

### 5. Custom Metric Cards

```python
from core.hq_metrics_layer import MetricValue, get_card_renderer

# Create a custom metric
custom_metric = MetricValue(
    value=42,
    label="Custom Metric",
    unit="units",
    trend="up",
    change_percent=15.5,
    color="#10b981",
    icon="fa-chart-line"
)

# Render it
renderer = get_card_renderer()
card_html = renderer.render_metric_card(custom_metric, size='large')
```

## Standardized Colors

```python
from core.hq_metrics_layer import BFColors

# Status colors
BFColors.SUCCESS = "#10b981"   # Green
BFColors.WARNING = "#f59e0b"   # Amber
BFColors.DANGER = "#ef4444"    # Red
BFColors.INFO = "#3b82f6"      # Blue

# Department colors
BFColors.EXECUTIVE = "#6366f1"      # Indigo
BFColors.ENGINEERING = "#06b6d4"    # Cyan
BFColors.OPERATIONS = "#10b981"     # Emerald
BFColors.INFRASTRUCTURE = "#f59e0b" # Amber
```

## Standardized Icons

```python
from core.hq_metrics_layer import BFIcons

# Entity icons
BFIcons.AGENT = "fa-robot"
BFIcons.LEADER = "fa-crown"
BFIcons.DEPARTMENT = "fa-building"
BFIcons.SERVER = "fa-server"

# Status icons
BFIcons.ACTIVE = "fa-check-circle"
BFIcons.INACTIVE = "fa-pause-circle"
BFIcons.WARNING = "fa-exclamation-triangle"
```

## Integration with Corporate HQ

### Step 1: Initialize in `__init__`

```python
from core.hq_metrics_integration import HQMetricsIntegration

class CorporateHQDashboard:
    def __init__(self):
        # ... existing init code ...
        self.metrics_integration = HQMetricsIntegration()
```

### Step 2: Replace Hardcoded Metrics

```python
def generate_dashboard_html(self):
    # Old way (hardcoded)
    # active_agents = 80

    # New way (from metrics layer)
    agent_metrics = self.metrics_integration.get_agents_page_metrics()
    active_agents = agent_metrics['active']
    total_agents = agent_metrics['total']
```

### Step 3: Use Pre-built Cards

```python
def generate_overview_cards(self):
    # Generate all summary cards with one call
    return self.metrics_integration.get_dashboard_summary_cards()
```

## Visual Metadata Structure

Departments and divisions store visual metadata in their configuration:

```json
{
  "visual": {
    "color": "#6366f1",
    "icon": "fa-crown",
    "theme": "executive",
    "accent_color": "#4f46e5",
    "custom_css": {}
  }
}
```

## Populating Visual Metadata

Run the population script to set default colors and icons:

```bash
python populate_visual_metadata.py
```

This will:
1. Run the migration to add visual columns
2. Assign colors and icons based on department names
3. Update the registry with visual metadata

## Performance Considerations

1. **Caching** - 30-second TTL on all metrics
2. **Batch Queries** - Single database round-trip for all metrics
3. **Lazy Loading** - Only calculate requested metrics
4. **Connection Pooling** - Reuse database connections

## Future Enhancements

1. **WebSocket Updates** - Real-time metric updates
2. **Historical Tracking** - Trend analysis over time
3. **Custom Themes** - Department-specific styling
4. **Metric Alerts** - Threshold-based notifications
5. **Export Capabilities** - CSV/JSON export of metrics

## Troubleshooting

### Metrics Not Updating
- Check database connection settings
- Verify PostgreSQL is running on port 5434
- Force refresh with `get_all_metrics(force_refresh=True)`

### Visual Metadata Missing
- Run `populate_visual_metadata.py`
- Check departments.configuration column in database
- Verify migration 007 has been applied

### Performance Issues
- Increase cache TTL if appropriate
- Add database indexes on frequently queried columns
- Use connection pooling for high-traffic scenarios
