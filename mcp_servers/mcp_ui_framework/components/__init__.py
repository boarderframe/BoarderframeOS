"""
MCP-UI Framework Component Library
Reusable UI components for MCP servers
"""

from .base import Component, ComponentConfig
from .cards import CardGrid, ProductCard, InfoCard
from .tables import DataTable, TableColumn
from .forms import Form, FormField, FormValidation
from .charts import Chart, ChartType, ChartData
from .widgets import (
    Alert,
    Loading,
    Button,
    Badge,
    Progress,
    Modal,
    Tabs,
    Accordion
)

__all__ = [
    # Base
    "Component",
    "ComponentConfig",
    
    # Cards
    "CardGrid",
    "ProductCard",
    "InfoCard",
    
    # Tables
    "DataTable",
    "TableColumn",
    
    # Forms
    "Form",
    "FormField",
    "FormValidation",
    
    # Charts
    "Chart",
    "ChartType",
    "ChartData",
    
    # Widgets
    "Alert",
    "Loading",
    "Button",
    "Badge",
    "Progress",
    "Modal",
    "Tabs",
    "Accordion"
]