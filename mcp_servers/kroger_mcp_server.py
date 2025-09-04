"""
Kroger MCP Server
A comprehensive FastAPI server implementing Kroger Developer API functionality
including Products, Locations, Cart, and Identity/Loyalty services.

Port: 9004
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import time
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path as FilePath
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode, parse_qs, urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, validator, HttpUrl
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# Import MCP UI Protocol infrastructure  
from mcp_ui_infrastructure import MCPUIService, MCPUIResource


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# FastAPI app initialization with JSON Schema 2020-12 compatibility
app = FastAPI(
    title="Kroger MCP Server",
    description="Comprehensive Kroger Developer API integration for product search, locations, cart management, and user profiles",
    version="1.0.1",  # Bumped version to force schema refresh
    docs_url="/docs",
    redoc_url="/redoc",
    # Ensure compatibility with JSON Schema draft 2020-12 for Claude Opus 4.1
    openapi_version="3.1.0",
    # Disable automatic validation error schema generation
    generate_unique_id_function=lambda route: f"{route.name}"
)

# In-memory artifact cache for Open WebUI compatibility
artifact_cache = {}

# Add rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom OpenAPI schema for Claude Opus 4.1 compatibility
def resolve_ref(ref_path, components):
    """Resolve a $ref path to its actual schema definition"""
    if not ref_path.startswith("#/components/schemas/"):
        return None
    
    schema_name = ref_path.replace("#/components/schemas/", "")
    return components.get("schemas", {}).get(schema_name)


def flatten_schema_refs(schema, components, visited=None):
    """Aggressively flatten all $ref references into inline schemas"""
    if visited is None:
        visited = set()
    
    if isinstance(schema, dict):
        # Handle $ref by replacing it with the actual schema
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path in visited:
                # Circular reference - return a simple type to avoid infinite recursion
                return {"type": "object", "description": "Circular reference resolved"}
            
            visited.add(ref_path)
            resolved_schema = resolve_ref(ref_path, components)
            if resolved_schema:
                # Recursively flatten the resolved schema
                flattened = flatten_schema_refs(resolved_schema, components, visited.copy())
                return flattened
            else:
                # If we can't resolve, return a generic object
                return {"type": "object", "description": "Unresolved reference"}
        
        # Recursively process all other dictionary fields
        flattened = {}
        for key, value in schema.items():
            if key in ["title", "examples", "x-examples", "$schema", "definitions"]:
                # Remove problematic fields that cause JSON Schema 2020-12 issues
                continue
            elif key == "allOf" and isinstance(value, list):
                # Flatten allOf into a merged object when possible
                merged_properties = {}
                merged_required = []
                merged_type = "object"
                
                for item in value:
                    flattened_item = flatten_schema_refs(item, components, visited.copy())
                    if isinstance(flattened_item, dict):
                        if "properties" in flattened_item:
                            merged_properties.update(flattened_item["properties"])
                        if "required" in flattened_item:
                            merged_required.extend(flattened_item["required"])
                        if "type" in flattened_item and flattened_item["type"] != "object":
                            merged_type = flattened_item["type"]
                
                if merged_properties:
                    flattened["type"] = merged_type
                    flattened["properties"] = merged_properties
                    if merged_required:
                        flattened["required"] = list(set(merged_required))
                else:
                    flattened[key] = [flatten_schema_refs(item, components, visited.copy()) for item in value]
            elif key == "anyOf" and isinstance(value, list):
                # For anyOf, keep the structure but flatten each schema
                flattened[key] = [flatten_schema_refs(item, components, visited.copy()) for item in value]
            elif key == "oneOf" and isinstance(value, list):
                # For oneOf, keep the structure but flatten each schema
                flattened[key] = [flatten_schema_refs(item, components, visited.copy()) for item in value]
            elif key == "properties" and isinstance(value, dict):
                # Recursively flatten all properties
                flattened[key] = {k: flatten_schema_refs(v, components, visited.copy()) for k, v in value.items()}
            elif key == "items" and isinstance(value, dict):
                # Flatten array item schema
                flattened[key] = flatten_schema_refs(value, components, visited.copy())
            elif key == "additionalProperties" and isinstance(value, dict):
                # Flatten additional properties schema
                flattened[key] = flatten_schema_refs(value, components, visited.copy())
            elif isinstance(value, dict):
                # Recursively flatten any nested objects
                flattened[key] = flatten_schema_refs(value, components, visited.copy())
            elif isinstance(value, list):
                # Process lists, flattening any dict items
                flattened[key] = [
                    flatten_schema_refs(item, components, visited.copy()) if isinstance(item, dict) else item 
                    for item in value
                ]
            else:
                flattened[key] = value
        
        return flattened
    
    elif isinstance(schema, list):
        # Process lists of schemas
        return [flatten_schema_refs(item, components, visited.copy()) if isinstance(item, dict) else item for item in schema]
    
    return schema


def clean_schema_for_claude(schema):
    """Recursively clean schema for Claude Opus 4.1 and GPT-5 JSON Schema 2020-12 compatibility"""
    if isinstance(schema, dict):
        cleaned = {}
        for key, value in schema.items():
            # Remove all problematic JSON Schema 2020-12 fields
            if key in [
                "title", "examples", "x-examples", "$schema", "definitions",
                "$id", "$comment", "$defs", "const", "contentEncoding", 
                "contentMediaType", "if", "then", "else", "dependentSchemas",
                "dependentRequired", "unevaluatedProperties", "unevaluatedItems",
                "$vocabulary", "$dynamicRef", "$dynamicAnchor", "prefixItems"
            ]:
                continue
            elif key == "format" and value in ["time", "date", "date-time", "duration", "uri-template", "json-pointer", "relative-json-pointer", "regex"]:
                # Replace problematic formats with basic string validation
                cleaned["type"] = "string"
                if value in ["date", "date-time"]:
                    cleaned["pattern"] = r"^\d{4}-\d{2}-\d{2}"
                continue
            elif key in ["anyOf", "oneOf", "allOf"] and isinstance(value, list):
                # COMPLETELY REMOVE anyOf/oneOf/allOf patterns for GPT-5 compatibility
                # Take the first non-null type or just the first type
                non_null_types = [item for item in value if isinstance(item, dict) and item.get("type") != "null"]
                
                if non_null_types:
                    # Use the first non-null type
                    primary_type = non_null_types[0]
                else:
                    # Use the first type regardless
                    primary_type = value[0] if value else {"type": "string"}
                
                if isinstance(primary_type, dict):
                    # Flatten the schema - copy all properties from the primary type
                    for prop_key, prop_value in primary_type.items():
                        if prop_key == "anyOf" or prop_key == "oneOf" or prop_key == "allOf":
                            # Skip nested anyOf/oneOf/allOf
                            continue
                        elif isinstance(prop_value, dict):
                            cleaned[prop_key] = clean_schema_for_claude(prop_value)
                        elif isinstance(prop_value, list):
                            cleaned[prop_key] = [clean_schema_for_claude(item) if isinstance(item, dict) else item for item in prop_value]
                        else:
                            cleaned[prop_key] = prop_value
                    continue
                # Skip this key entirely if we can't process it
                continue
            elif isinstance(value, dict):
                cleaned[key] = clean_schema_for_claude(value)
            elif isinstance(value, list):
                cleaned[key] = [clean_schema_for_claude(item) if isinstance(item, dict) else item for item in value]
            else:
                cleaned[key] = value
        return cleaned
    return schema

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Ensure JSON Schema 2020-12 compatibility
    openapi_schema["openapi"] = "3.1.0"
    
    # Store original components for reference resolution
    original_components = openapi_schema.get("components", {})
    
    # Step 1: Remove problematic schemas entirely
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        # Remove FastAPI validation error schemas that cause issues
        schemas_to_remove = [
            "HTTPValidationError", "ValidationError", 
            "Body_create_cart_cart_post", "Body__",
            # Also remove any schemas that start with Body_ (auto-generated request body schemas)
        ]
        # Get all schema names that match patterns to remove
        all_schema_names = list(openapi_schema["components"]["schemas"].keys())
        for schema_name in all_schema_names:
            if schema_name in schemas_to_remove or schema_name.startswith("Body_"):
                openapi_schema["components"]["schemas"].pop(schema_name, None)
    
    # Step 2: Aggressively flatten all remaining schemas in components
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        flattened_schemas = {}
        for schema_name, schema_def in openapi_schema["components"]["schemas"].items():
            # First flatten all $ref references
            flattened = flatten_schema_refs(schema_def, original_components)
            # Then clean for Claude compatibility
            cleaned = clean_schema_for_claude(flattened)
            flattened_schemas[schema_name] = cleaned
        
        openapi_schema["components"]["schemas"] = flattened_schemas
    
    # Step 3: Flatten and clean all schemas in paths (parameters, request bodies, responses)
    if "paths" in openapi_schema:
        for path, path_methods in openapi_schema["paths"].items():
            for method, operation in path_methods.items():
                # Clean parameter schemas
                if "parameters" in operation:
                    for param in operation["parameters"]:
                        if "schema" in param:
                            flattened = flatten_schema_refs(param["schema"], original_components)
                            param["schema"] = clean_schema_for_claude(flattened)
                
                # Clean request body schemas
                if "requestBody" in operation and "content" in operation["requestBody"]:
                    for content_type, content in operation["requestBody"]["content"].items():
                        if "schema" in content:
                            flattened = flatten_schema_refs(content["schema"], original_components)
                            content["schema"] = clean_schema_for_claude(flattened)
                
                # Clean response schemas
                if "responses" in operation:
                    for response_code, response in operation["responses"].items():
                        # For 422 validation error responses, replace with inline schema
                        if response_code == "422":
                            response["description"] = "Validation Error"
                            response["content"] = {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "detail": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "loc": {
                                                            "type": "array",
                                                            "items": {
                                                                "anyOf": [
                                                                    {"type": "string"},
                                                                    {"type": "integer"}
                                                                ]
                                                            }
                                                        },
                                                        "msg": {"type": "string"},
                                                        "type": {"type": "string"}
                                                    },
                                                    "required": ["loc", "msg", "type"]
                                                }
                                            }
                                        },
                                        "required": ["detail"]
                                    }
                                }
                            }
                        elif "content" in response:
                            for content_type, content in response["content"].items():
                                if "schema" in content:
                                    flattened = flatten_schema_refs(content["schema"], original_components)
                                    content["schema"] = clean_schema_for_claude(flattened)
                        
                        # Also clean response headers if they have schemas
                        if "headers" in response:
                            for header_name, header_def in response["headers"].items():
                                if "schema" in header_def:
                                    flattened = flatten_schema_refs(header_def["schema"], original_components)
                                    header_def["schema"] = clean_schema_for_claude(flattened)
    
    # Step 4: Clean the entire schema recursively one more time to catch any remaining issues
    openapi_schema = clean_schema_for_claude(openapi_schema)
    
    # Step 5: Final validation - ensure no $ref remains anywhere
    def remove_remaining_refs(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                # Replace any remaining $ref with a simple object type
                return {"type": "object", "description": "Reference removed for compatibility"}
            return {k: remove_remaining_refs(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [remove_remaining_refs(item) for item in obj]
        return obj
    
    openapi_schema = remove_remaining_refs(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Configuration
KROGER_BASE_URL = "https://api.kroger.com/v1"
KROGER_AUTH_URL = "https://api.kroger.com/v1/connect/oauth2/token"
KROGER_AUTHORIZE_URL = "https://api.kroger.com/v1/connect/oauth2/authorize"

# Environment variables
KROGER_CLIENT_ID = os.getenv("KROGER_CLIENT_ID", "")
KROGER_CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET", "")
KROGER_REDIRECT_URI = os.getenv("KROGER_REDIRECT_URI", "http://localhost:9004/auth/callback")
KROGER_DEV_MODE = os.getenv("KROGER_DEV_MODE", "false").lower() == "true"

# Default location settings for LLM agent convenience
KROGER_DEFAULT_ZIP_CODE = os.getenv("KROGER_DEFAULT_ZIP_CODE", "43026")
KROGER_DEFAULT_STORE_ID = os.getenv("KROGER_DEFAULT_STORE_ID", "01600966")
KROGER_DEFAULT_RADIUS_MILES = int(os.getenv("KROGER_DEFAULT_RADIUS_MILES", "10"))

# Default fulfillment settings - hardcoded for LLM simplicity
KROGER_DEFAULT_FULFILLMENT = os.getenv("KROGER_DEFAULT_FULFILLMENT", "delivery")
KROGER_DEFAULT_DELIVERY_TYPE = os.getenv("KROGER_DEFAULT_DELIVERY_TYPE", "kroger")
KROGER_FORCE_KROGER_DELIVERY = os.getenv("KROGER_FORCE_KROGER_DELIVERY", "true").lower() == "true"

# Hardcoded user authentication - for LLM cart operations without auth flow
KROGER_USER_ACCESS_TOKEN = os.getenv("KROGER_USER_ACCESS_TOKEN", "")
KROGER_USER_REFRESH_TOKEN = os.getenv("KROGER_USER_REFRESH_TOKEN", "")
KROGER_USER_TOKEN_EXPIRES_AT = os.getenv("KROGER_USER_TOKEN_EXPIRES_AT", "0")
KROGER_HARDCODED_USER_ID = os.getenv("KROGER_HARDCODED_USER_ID", "user_default")

# Token storage and management
token_cache: Dict[str, Dict[str, Any]] = {}
client_credentials_token: Optional[Dict[str, Any]] = None
token_file_path = FilePath(".kroger_tokens.json")
token_refresh_task: Optional[asyncio.Task] = None
token_lock = threading.Lock()

# Rate limiting counters
rate_limit_counters: Dict[str, Dict[str, int]] = {}


# ============================================================================
# Pydantic Models
# ============================================================================

class KrogerError(BaseModel):
    """Standard Kroger API error response"""
    error: str
    error_description: Optional[str] = None


class TokenResponse(BaseModel):
    """OAuth2 token response"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class ProductImage(BaseModel):
    """Product image information"""
    id: Optional[str] = None
    perspective: Optional[str] = None
    featured: Optional[bool] = None
    sizes: List[Dict[str, Union[str, int]]] = []


class ProductItem(BaseModel):
    """Product item with pricing and inventory"""
    itemId: str
    favorite: bool
    fulfillment: Dict[str, Any]
    price: Dict[str, Any]
    size: str
    soldBy: str


class ProductCategory(BaseModel):
    """Product category information"""
    categoryId: str
    name: str


class AisleLocation(BaseModel):
    """Product aisle location in store"""
    bayNumber: Optional[str] = None
    description: Optional[str] = None
    number: Optional[str] = None
    numberOfFacings: Optional[str] = None
    sequenceNumber: Optional[str] = None
    side: Optional[str] = None
    shelfNumber: Optional[str] = None
    shelfPositionInBay: Optional[str] = None


class Product(BaseModel):
    """Complete product information"""
    productId: str
    aisleLocations: List[AisleLocation] = []
    brand: Optional[str] = None
    categories: List[Union[str, ProductCategory]] = []
    description: str
    images: List[ProductImage] = []
    items: List[ProductItem] = []
    itemInformation: Dict[str, Any] = {}
    temperature: Optional[Dict[str, Any]] = None


class ProductSearchResponse(BaseModel):
    """Product search results"""
    data: List[Product]
    meta: Dict[str, Any]


class LocationAddress(BaseModel):
    """Location address information"""
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    county: Optional[str] = None
    state: str
    zipCode: str


class HourDetail(BaseModel):
    """Individual day hour detail"""
    open: Optional[str] = None
    close: Optional[str] = None
    open24: Optional[bool] = None

class LocationHours(BaseModel):
    """Store hours information"""
    monday: Optional[HourDetail] = None
    tuesday: Optional[HourDetail] = None
    wednesday: Optional[HourDetail] = None
    thursday: Optional[HourDetail] = None
    friday: Optional[HourDetail] = None
    saturday: Optional[HourDetail] = None
    sunday: Optional[HourDetail] = None


class LocationDepartment(BaseModel):
    """Store department information"""
    departmentId: str
    name: str


class LocationGeolocation(BaseModel):
    """Store geolocation coordinates"""
    latitude: float
    longitude: float


class Location(BaseModel):
    """Store location information"""
    locationId: str
    chain: str
    address: LocationAddress
    geolocation: LocationGeolocation
    name: str
    phone: Optional[str] = None
    hours: Optional[LocationHours] = None
    departments: List[LocationDepartment] = []


class LocationSearchResponse(BaseModel):
    """Location search results"""
    data: List[Location]
    meta: Dict[str, Any]


class CartItem(BaseModel):
    """Cart item information"""
    itemId: str
    quantity: int
    modifiedTime: str


class Cart(BaseModel):
    """Shopping cart information"""
    cartId: str
    customerId: str
    locationId: str
    items: List[CartItem] = []


class CartResponse(BaseModel):
    """Cart operation response"""
    data: Cart


class UserProfile(BaseModel):
    """User profile information"""
    id: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None


class LoyaltyAccount(BaseModel):
    """Loyalty account information"""
    loyaltyId: str


class IdentityResponse(BaseModel):
    """Identity API response"""
    data: UserProfile


class LoyaltyResponse(BaseModel):
    """Loyalty API response"""
    data: LoyaltyAccount


# Request models
class CartItemRequest(BaseModel):
    """Request to add/update cart item"""
    items: List[Dict[str, Union[str, int]]]


class AuthorizeRequest(BaseModel):
    """Authorization request"""
    scope: str = "profile.compact cart.basic:write"
    response_type: str = "code"


# ============================================================================
# Token-Efficient Artifact System Models
# ============================================================================

class MinimalProduct(BaseModel):
    """Ultra-compact product for LLM efficiency - 90% token reduction"""
    id: str = Field(..., description="Product UPC/ID")
    name: str = Field(..., max_length=50, description="Product name (truncated)")
    price: float = Field(..., description="Current price")
    artifact_id: str = Field(..., description="Reference to HTML artifact")
    summary: str = Field(..., max_length=100, description="1-line description")


class ArtifactMetadata(BaseModel):
    """Metadata for pre-rendered artifacts"""
    artifact_id: str = Field(..., description="UUID")
    artifact_type: str = Field(..., description="Type: product_card, product_grid, etc.")
    created_at: float = Field(..., description="Timestamp")
    expires_at: float = Field(..., description="TTL expiration")
    content_hash: str = Field(..., description="SHA256 of content")
    size_bytes: int = Field(..., description="Size of HTML content")
    product_ids: List[str] = Field(..., description="Associated products")


# ============================================================================
# MCP UI Protocol Models (Reusable Infrastructure)
# ============================================================================

class MCPUIResource(BaseModel):
    """MCP UI Protocol Resource - Reusable across all MCP servers"""
    uri: str = Field(..., description="Resource URI with ui:// scheme")
    mimeType: str = Field(..., description="MIME type (text/html, text/uri-list, etc)")
    content: str = Field(..., description="Resource content (HTML, URL, etc)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class MCPUIResponse(BaseModel):
    """Base MCP UI Protocol Response - Reusable across all MCP servers"""
    ui_resources: Dict[str, MCPUIResource] = Field(..., description="UI resources keyed by URI")
    content: Optional[Any] = Field(default=None, description="Additional response data")

class ArtifactSearchResponse(BaseModel):
    """Token-efficient search response with MCP UI Protocol support"""
    query: str = Field(..., description="Original search term")
    count: int = Field(..., description="Number of results")
    products: List[MinimalProduct] = Field(..., description="Minimal product data")
    ui_resources: Dict[str, MCPUIResource] = Field(..., description="MCP UI Protocol resources")
    expires_in: int = Field(..., description="Seconds until UI resources expire")
    artifact_html: Optional[str] = Field(None, description="HTML artifact for Open WebUI rendering")
    display_instructions: Optional[str] = Field(None, description="Instructions for LLM to display artifacts")


# ============================================================================
# Token Persistence & Background Refresh Management
# ============================================================================

def load_tokens_from_file() -> Dict[str, Any]:
    """Load tokens from persistent storage file"""
    try:
        if token_file_path.exists():
            with open(token_file_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data.get('user_tokens', {}))} user tokens from file")
                return data
    except Exception as e:
        logger.error(f"Failed to load tokens from file: {e}")
    
    return {"user_tokens": {}, "client_credentials": None}


def save_tokens_to_file(user_tokens: Dict[str, Any], client_token: Optional[Dict[str, Any]] = None) -> None:
    """Save tokens to persistent storage file with thread safety"""
    try:
        with token_lock:
            # Prepare data for saving (remove sensitive details from logs)
            data = {
                "user_tokens": user_tokens,
                "client_credentials": client_token,
                "last_updated": time.time()
            }
            
            # Atomic write using temporary file
            temp_file = token_file_path.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic move to final location
            temp_file.replace(token_file_path)
            
            logger.info("Successfully saved tokens to persistent storage")
    except Exception as e:
        logger.error(f"Failed to save tokens to file: {e}")


def is_token_expired(token_info: Dict[str, Any], buffer_minutes: int = 5) -> bool:
    """Check if token is expired or will expire soon"""
    expires_at = token_info.get("expires_at", 0)
    buffer_seconds = buffer_minutes * 60
    return expires_at <= time.time() + buffer_seconds


async def background_token_refresh():
    """Background task to refresh tokens before they expire"""
    logger.info("Starting background token refresh task")
    
    while True:
        try:
            # Check every 60 seconds
            await asyncio.sleep(60)
            
            # Check client credentials token
            global client_credentials_token
            if client_credentials_token and is_token_expired(client_credentials_token, 10):
                logger.info("Refreshing client credentials token in background")
                try:
                    await get_client_credentials_token()
                except Exception as e:
                    logger.error(f"Background refresh failed for client credentials: {e}")
            
            # Check user tokens
            tokens_to_refresh = []
            for user_id, token_info in token_cache.items():
                if is_token_expired(token_info, 10) and token_info.get("refresh_token"):
                    tokens_to_refresh.append((user_id, token_info))
            
            # Refresh user tokens that are expiring
            for user_id, token_info in tokens_to_refresh:
                logger.info(f"Refreshing user token in background for user {user_id}")
                try:
                    await refresh_user_token(token_info["refresh_token"], user_id)
                except Exception as e:
                    logger.error(f"Background refresh failed for user {user_id}: {e}")
            
            # Save tokens if any were updated
            if client_credentials_token or token_cache:
                save_tokens_to_file(token_cache, client_credentials_token)
                
        except Exception as e:
            logger.error(f"Error in background token refresh: {e}")


async def background_artifact_cleanup():
    """Background task to clean up expired artifacts every 5 minutes"""
    logger.info("Starting background artifact cleanup task")
    
    while True:
        try:
            # Run cleanup every 5 minutes (300 seconds)
            await asyncio.sleep(300)
            
            # Clean up expired artifacts
            cleaned = await artifact_service.cleanup_expired_artifacts()
            
            if cleaned > 0:
                logger.info(f"Background cleanup: removed {cleaned} expired artifacts")
                
        except Exception as e:
            logger.error(f"Error in background artifact cleanup: {e}")


def migrate_env_tokens():
    """Migrate tokens from environment variables to file storage"""
    migrated = False
    
    # Check for hardcoded user tokens in env
    if KROGER_USER_ACCESS_TOKEN and KROGER_USER_REFRESH_TOKEN:
        expires_at = float(KROGER_USER_TOKEN_EXPIRES_AT or "0")
        
        user_token = {
            "access_token": KROGER_USER_ACCESS_TOKEN,
            "token_type": "Bearer",
            "expires_at": expires_at,
            "refresh_token": KROGER_USER_REFRESH_TOKEN,
            "scope": "profile.compact cart.basic:write",
            "source": "env_migration"
        }
        
        token_cache[KROGER_HARDCODED_USER_ID] = user_token
        migrated = True
        logger.info(f"Migrated hardcoded user token from .env for user {KROGER_HARDCODED_USER_ID}")
    
    if migrated:
        save_tokens_to_file(token_cache, client_credentials_token)
        logger.info("Token migration from .env completed")


# ============================================================================
# Authentication & Token Management
# ============================================================================

async def get_client_credentials_token() -> str:
    """Get or refresh client credentials token for public API access with persistence"""
    global client_credentials_token
    
    # In development mode without credentials, return dummy token
    if KROGER_DEV_MODE and (not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET):
        logger.warning("Running in development mode with dummy token")
        return "dev_mode_dummy_token"
    
    # Check if token exists and is valid
    if (client_credentials_token and 
        not is_token_expired(client_credentials_token, 5)):
        return client_credentials_token["access_token"]
    
    # Request new token
    auth_data = {
        "grant_type": "client_credentials",
        "scope": "product.compact"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                KROGER_AUTH_URL,
                data=auth_data,
                auth=(KROGER_CLIENT_ID, KROGER_CLIENT_SECRET),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Token request failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to authenticate with Kroger API"
                )
            
            token_data = response.json()
            client_credentials_token = {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"],
                "expires_at": time.time() + token_data["expires_in"],
                "scope": token_data.get("scope", "product.compact"),
                "obtained_at": time.time()
            }
            
            # Save to persistent storage
            save_tokens_to_file(token_cache, client_credentials_token)
            
            logger.info("Successfully obtained and saved client credentials token")
            return client_credentials_token["access_token"]
            
        except httpx.RequestError as e:
            logger.error(f"Network error during token request: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Network error connecting to Kroger API"
            )


async def refresh_user_token(refresh_token: str, user_id: str) -> Dict[str, Any]:
    """Refresh user access token using refresh token with persistence"""
    auth_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                KROGER_AUTH_URL,
                data=auth_data,
                auth=(KROGER_CLIENT_ID, KROGER_CLIENT_SECRET),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed for user {user_id}: {response.status_code} - {response.text}")
                
                # If refresh fails, try to fall back to env tokens for hardcoded user
                if user_id == KROGER_HARDCODED_USER_ID and KROGER_USER_ACCESS_TOKEN:
                    logger.warning(f"Refresh failed for hardcoded user, attempting fallback to env tokens")
                    # Check if env token is still valid
                    env_expires_at = float(KROGER_USER_TOKEN_EXPIRES_AT or "0")
                    if env_expires_at > time.time() + 300:
                        fallback_token = {
                            "access_token": KROGER_USER_ACCESS_TOKEN,
                            "token_type": "Bearer",
                            "expires_at": env_expires_at,
                            "refresh_token": KROGER_USER_REFRESH_TOKEN,
                            "scope": "profile.compact cart.basic:write",
                            "source": "env_fallback"
                        }
                        token_cache[user_id] = fallback_token
                        save_tokens_to_file(token_cache, client_credentials_token)
                        logger.info(f"Successfully fell back to env token for user {user_id}")
                        return fallback_token
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh authentication token and no valid fallback available"
                )
            
            token_data = response.json()
            new_token = {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"],
                "expires_at": time.time() + token_data["expires_in"],
                "refresh_token": token_data.get("refresh_token", refresh_token),
                "scope": token_data.get("scope"),
                "refreshed_at": time.time()
            }
            
            # Update cache and save to file
            token_cache[user_id] = new_token
            save_tokens_to_file(token_cache, client_credentials_token)
            
            logger.info(f"Successfully refreshed and saved token for user {user_id}")
            return new_token
            
        except httpx.RequestError as e:
            logger.error(f"Network error during token refresh: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Network error connecting to Kroger API"
            )


async def get_user_token(user_id: str) -> str:
    """Get valid user access token, refreshing if necessary with robust fallback"""
    # Check if user exists in token cache
    if user_id not in token_cache:
        # For hardcoded user, try to migrate from env variables first
        if user_id == KROGER_HARDCODED_USER_ID and KROGER_USER_ACCESS_TOKEN:
            logger.info("Migrating hardcoded user token from environment")
            expires_at = float(KROGER_USER_TOKEN_EXPIRES_AT or "0")
            
            hardcoded_token = {
                "access_token": KROGER_USER_ACCESS_TOKEN,
                "token_type": "Bearer",
                "expires_at": expires_at,
                "refresh_token": KROGER_USER_REFRESH_TOKEN,
                "scope": "profile.compact cart.basic:write",
                "source": "env_migration"
            }
            
            token_cache[user_id] = hardcoded_token
            save_tokens_to_file(token_cache, client_credentials_token)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated. Please complete OAuth flow."
            )
    
    token_info = token_cache[user_id]
    
    # Check if token needs refresh
    if is_token_expired(token_info, 5):
        if "refresh_token" in token_info and token_info["refresh_token"]:
            try:
                token_info = await refresh_user_token(token_info["refresh_token"], user_id)
            except HTTPException as e:
                # If refresh fails and this is the hardcoded user, try env fallback
                if user_id == KROGER_HARDCODED_USER_ID and KROGER_USER_ACCESS_TOKEN:
                    env_expires_at = float(KROGER_USER_TOKEN_EXPIRES_AT or "0")
                    if env_expires_at > time.time() + 300:
                        logger.warning("Using environment token as fallback")
                        return KROGER_USER_ACCESS_TOKEN
                raise e
        else:
            # No refresh token available
            if user_id == KROGER_HARDCODED_USER_ID and KROGER_USER_ACCESS_TOKEN:
                # Fallback to env token for hardcoded user
                env_expires_at = float(KROGER_USER_TOKEN_EXPIRES_AT or "0")
                if env_expires_at > time.time() + 300:
                    logger.warning("No refresh token, using environment token as fallback")
                    return KROGER_USER_ACCESS_TOKEN
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired and no refresh token available"
            )
    
    return token_info["access_token"]


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Extract user ID from bearer token (for authenticated endpoints)"""
    # If we have hardcoded user tokens, always return the hardcoded user (LLM-friendly mode)
    if KROGER_USER_ACCESS_TOKEN and KROGER_USER_REFRESH_TOKEN:
        return KROGER_HARDCODED_USER_ID
    
    if not credentials:
        return None
    
    # In a real implementation, you'd decode/validate the JWT token
    # For now, we'll use a simple hash of the token as user ID
    user_id = hashlib.md5(credentials.credentials.encode()).hexdigest()
    return user_id


# ============================================================================
# Rate Limiting Helpers
# ============================================================================

def check_rate_limit(endpoint: str, user_id: str, limit: int) -> bool:
    """Check if user has exceeded rate limit for endpoint"""
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{user_id}:{endpoint}:{today}"
    
    if key not in rate_limit_counters:
        rate_limit_counters[key] = {"count": 0, "date": today}
    
    if rate_limit_counters[key]["count"] >= limit:
        return False
    
    rate_limit_counters[key]["count"] += 1
    return True


# ============================================================================
# HTTP Client Helper
# ============================================================================

async def make_kroger_request(
    method: str,
    endpoint: str,
    token: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make authenticated request to Kroger API"""
    # In development mode with dummy token, return mock responses
    if KROGER_DEV_MODE and token == "dev_mode_dummy_token":
        return get_mock_response(endpoint, params)
    
    url = f"{KROGER_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    if json_data:
        headers["Content-Type"] = "application/json"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token"
                )
            elif response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this operation"
                )
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resource not found"
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
            elif response.status_code >= 400:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error_description", error_detail)
                except:
                    pass
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Kroger API error: {error_detail}"
                )
            
            # Handle different response types
            if response.status_code == 204:  # No Content (cart operations)
                return None
            elif response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return response.text
            
        except httpx.RequestError as e:
            logger.error(f"Network error in Kroger request: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Network error connecting to Kroger API"
            )


def get_mock_response(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate mock responses for development mode"""
    logger.info(f"Returning mock response for endpoint: {endpoint}")
    
    if endpoint == "/products":
        # Mock product search response
        return {
            "data": [
                {
                    "productId": "0001111041195",
                    "description": "Kroger Vitamin D Whole Milk",
                    "brand": "Kroger",
                    "categories": [
                        {"categoryId": "01", "name": "Dairy"}
                    ],
                    "aisleLocations": [
                        {
                            "bayNumber": "12",
                            "description": "Dairy",
                            "number": "A12",
                            "numberOfFacings": "4",
                            "sequenceNumber": "1",
                            "side": "Right",
                            "shelfNumber": "3",
                            "shelfPositionInBay": "2"
                        }
                    ],
                    "items": [
                        {
                            "itemId": "0001111041195",
                            "favorite": False,
                            "fulfillment": {
                                "curbside": True,
                                "delivery": True,
                                "inStore": True,
                                "shipToHome": False
                            },
                            "price": {
                                "regular": 3.49,
                                "promo": 2.99,
                                "promoDescription": "Save $0.50"
                            },
                            "size": "1 gal",
                            "soldBy": "Each"
                        }
                    ],
                    "images": [
                        {
                            "id": "0001111041195-1",
                            "perspective": "front",
                            "featured": True,
                            "sizes": [
                                {"size": "small", "url": "https://kroger.com/product-images/small.jpg", "width": 100, "height": 100},
                                {"size": "medium", "url": "https://kroger.com/product-images/medium.jpg", "width": 300, "height": 300}
                            ]
                        }
                    ]
                }
            ],
            "meta": {
                "pagination": {
                    "start": 1,
                    "limit": 50,
                    "total": 1
                },
                "warnings": []
            }
        }
    
    elif endpoint.startswith("/products/"):
        # Mock product details response
        product_id = endpoint.split("/")[-1]
        return {
            "data": {
                "productId": product_id,
                "description": "Mock Product Details",
                "brand": "Mock Brand",
                "categories": [{"categoryId": "01", "name": "Mock Category"}],
                "aisleLocations": [],
                "items": [
                    {
                        "itemId": product_id,
                        "favorite": False,
                        "fulfillment": {"curbside": True, "delivery": True, "inStore": True},
                        "price": {"regular": 5.99},
                        "size": "1 unit",
                        "soldBy": "Each"
                    }
                ]
            }
        }
    
    elif endpoint == "/locations":
        # Mock locations search response
        return {
            "data": [
                {
                    "locationId": "01400943",
                    "chain": "KR",
                    "address": {
                        "addressLine1": "123 Main St",
                        "city": "Cincinnati",
                        "state": "OH",
                        "zipCode": "45202"
                    },
                    "geolocation": {
                        "latitude": 39.1031,
                        "longitude": -84.5120
                    },
                    "name": "Kroger Main Street",
                    "phone": "513-555-0123",
                    "hours": {
                        "monday": "6:00-24:00",
                        "tuesday": "6:00-24:00",
                        "wednesday": "6:00-24:00",
                        "thursday": "6:00-24:00",
                        "friday": "6:00-24:00",
                        "saturday": "6:00-24:00",
                        "sunday": "6:00-24:00"
                    },
                    "departments": [
                        {"departmentId": "01", "name": "Bakery"},
                        {"departmentId": "02", "name": "Deli"},
                        {"departmentId": "03", "name": "Pharmacy"}
                    ]
                }
            ],
            "meta": {
                "pagination": {
                    "start": 1,
                    "limit": 50,
                    "total": 1
                }
            }
        }
    
    elif endpoint.startswith("/locations/"):
        # Mock location details response
        location_id = endpoint.split("/")[-1]
        return {
            "data": {
                "locationId": location_id,
                "chain": "KR",
                "address": {
                    "addressLine1": "123 Mock Street",
                    "city": "Mock City",
                    "state": "OH",
                    "zipCode": "12345"
                },
                "geolocation": {
                    "latitude": 39.0,
                    "longitude": -84.0
                },
                "name": f"Mock Kroger Store {location_id}",
                "phone": "555-123-4567"
            }
        }
    
    elif endpoint == "/cart":
        # Mock cart response
        return {
            "data": {
                "cartId": "mock-cart-123",
                "customerId": "mock-customer-456",
                "locationId": "01400943",
                "items": []
            }
        }
    
    elif endpoint == "/identity/profile":
        # Mock user profile response
        return {
            "data": {
                "id": "mock-user-123",
                "firstName": "Mock",
                "lastName": "User"
            }
        }
    
    elif endpoint == "/identity/loyalty":
        # Mock loyalty response
        return {
            "data": {
                "loyaltyId": "mock-loyalty-789"
            }
        }
    
    else:
        # Default mock response
        return {
            "data": {},
            "meta": {
                "message": f"Mock response for {endpoint}"
            }
        }


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "kroger-mcp-server",
            "version": "1.0.1",  # Updated version
            "timestamp": datetime.now().isoformat(),
            "features": {
                "token_efficient_artifacts": True,
                "html_artifacts": True,
                "minimal_responses": True,
                "schema_version": "1.0.1"
            }
        },
        media_type="application/json"
    )

@app.get("/test/json")
async def test_json_response():
    """Test endpoint to verify clean JSON responses without SSE/streaming"""
    return JSONResponse(
        content={
            "status": "success",
            "message": "This is a clean JSON response without SSE prefix",
            "test_data": {
                "numbers": [1, 2, 3],
                "nested": {
                    "level": 2,
                    "clean": True
                }
            },
            "timestamp": datetime.now().isoformat(),
            "response_format": "json"
        },
        media_type="application/json",
        headers={
            "X-Response-Type": "json",
            "Cache-Control": "no-cache"
        }
    )

@app.get("/schema/refresh")
async def refresh_schema():
    """Force schema refresh for MCP clients - returns updated OpenAPI spec info"""
    return {
        "message": "Schema refresh endpoint called",
        "version": "1.0.1",
        "artifact_endpoints": {
            "/products/search/artifact": "Token-efficient product search with HTML artifacts",
            "/artifacts/{artifact_id}": "Retrieve cached HTML artifacts",
            "/products/search/minimal": "Ultra-minimal product data (90% token reduction)"
        },
        "instructions": "MCP clients should now use /products/search/artifact instead of /products/search/compact",
        "token_efficiency": "90-95% token reduction compared to full responses",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/config")
async def get_configuration():
    """Get current server configuration for LLM agents"""
    return {
        "default_location": {
            "zip_code": KROGER_DEFAULT_ZIP_CODE,
            "store_id": KROGER_DEFAULT_STORE_ID,
            "radius_miles": KROGER_DEFAULT_RADIUS_MILES
        },
        "default_fulfillment": {
            "type": KROGER_DEFAULT_FULFILLMENT,
            "delivery_type": KROGER_DEFAULT_DELIVERY_TYPE,
            "force_kroger_delivery": KROGER_FORCE_KROGER_DELIVERY
        },
        "dev_mode": KROGER_DEV_MODE,
        "available_endpoints": [
            "/products/search - Simple product search (only requires 'term' parameter)",
            "/locations/search - Simple store finder (no parameters needed)",
            "/cart - Manage shopping cart",
            "/identity/profile - User profile access",
            "/identity/loyalty - Loyalty program access"
        ],
        "llm_friendly_usage": {
            "product_search": "Use /products/search?term=milk - only requires search term, automatically filters for delivery-enabled items",
            "store_search": "Use /locations/search - no parameters needed at all",
            "cart_creation": "Use POST /cart - automatically uses Cemetery Road store with Kroger delivery, no parameters needed",
            "location_info": f"Default location is ZIP {KROGER_DEFAULT_ZIP_CODE}, default store is {KROGER_DEFAULT_STORE_ID}",
            "delivery_info": f"All operations default to {KROGER_DEFAULT_FULFILLMENT} via {KROGER_DEFAULT_DELIVERY_TYPE} delivery service"
        }
    }

# ============================================================================
# Simplified LLM-Friendly Endpoints (No Location Parameters Required)
# ============================================================================

@app.get("/products/search")
@limiter.limit("100/minute")
async def search_products(
    request: Request,
    term: str = Query(..., description="Product search term (e.g., 'milk', 'bread', 'apples')")
):
    """Simple product search - automatically uses Cemetery Road store, only requires search term"""
    # Use default store always
    store_id = KROGER_DEFAULT_STORE_ID
    
    # Get client credentials token
    token = await get_client_credentials_token()
    
    # Build query parameters with defaults (filter for delivery availability)
    params = {
        "filter.term": term,
        "filter.locationId": store_id,
        "filter.fulfillment": "del",  # Filter for delivery-enabled items only
        "filter.limit": 20,  # Smaller limit for simpler results
        "filter.start": 1
    }
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", "/products", token, params)
    return result

@app.get("/products/search/compact")
@limiter.limit("100/minute") 
async def search_products_compact(
    request: Request,
    term: str = Query(..., description="Search term for products"),
    limit: int = Query(8, description="Number of results (max 20 for UI display)")
):
    """
    🚀 LLM-optimized product search with visual HTML artifacts for Open WebUI
    
    Returns product data + ready-to-render HTML code block for Artifacts V3.
    The response includes display_instructions with HTML that Open WebUI can render visually.
    """
    if limit > 20:
        limit = 20  # Cap at 20 for UI display
        
    # Use same search logic but trim results
    store_id = KROGER_DEFAULT_STORE_ID
    token = await get_client_credentials_token()
    
    params = {
        "filter.term": term,
        "filter.locationId": store_id,
        "filter.fulfillment": "del",
        "filter.limit": limit,
        "filter.start": 1
    }
    
    result = await make_kroger_request("GET", "/products", token, params)
    
    # Transform to compact format for LLM efficiency
    if "data" in result:
        compact_products = []
        for product in result["data"]:
            # Extract only essential information
            compact_product = {
                "name": product.get("description", "Unknown"),
                "upc": product.get("upc", ""),
                "brand": product.get("brand", ""),
                "price": None,
                "size": None,
                "available": False,
                "delivery": False,
                "image_url": None
            }
            
            # Extract featured product image (front perspective, medium size)
            if "images" in product and product["images"]:
                for image in product["images"]:
                    if image.get("perspective") == "front" and image.get("featured"):
                        sizes = image.get("sizes", [])
                        # Look for medium size, fallback to any available size
                        for size_info in sizes:
                            if size_info.get("size") == "medium":
                                compact_product["image_url"] = size_info.get("url")
                                break
                        # If no medium, use first available size
                        if not compact_product["image_url"] and sizes:
                            compact_product["image_url"] = sizes[0].get("url")
                        break
                # If no featured front image, use first available image
                if not compact_product["image_url"] and product["images"]:
                    first_image = product["images"][0]
                    sizes = first_image.get("sizes", [])
                    if sizes:
                        compact_product["image_url"] = sizes[0].get("url")
            
            # Get pricing and availability from items
            if "items" in product and product["items"]:
                item = product["items"][0]  # Use first item
                if "price" in item:
                    compact_product["price"] = item["price"].get("regular", 0)
                if "size" in item:
                    compact_product["size"] = item["size"]
                if "fulfillment" in item:
                    fulfillment = item["fulfillment"]
                    compact_product["delivery"] = fulfillment.get("delivery", False)
                    compact_product["available"] = any([
                        fulfillment.get("delivery", False),
                        fulfillment.get("curbside", False),
                        fulfillment.get("inStore", False)
                    ])
            
            compact_products.append(compact_product)
        
        # Create MCP UI Protocol resources for Open WebUI artifact rendering
        ui_resource = mcp_ui_service.create_product_cards_resource(compact_products, "grid", term)
        
        # Cache the artifact for Open WebUI access
        if ui_resource:
            artifact_id = ui_resource.uri.split('/')[-1]  # Extract ID from uri://component/{id}
            artifact_cache[artifact_id] = {
                'content': ui_resource.content,
                'mimeType': ui_resource.mimeType,
                'metadata': ui_resource.metadata
            }
        
        # Create response with automatic HTML injection for Open WebUI
        response_data = {
            "products": compact_products,
            "count": len(compact_products),
            "search_term": term,
            "ui_resources": {ui_resource.uri: ui_resource},
            "expires_in": 3600,
            "display_instructions": f"To display the product cards visually in Open WebUI, include this HTML code block in your response:\n\n```html\n{ui_resource.content}\n```",
            "artifact_html": ui_resource.content
        }
        
        return response_data

@app.get("/products/search/openwebui")
@limiter.limit("30/minute") 
async def search_products_openwebui(
    request: Request,
    term: str = Query(..., description="Product search term"),
    limit: int = Query(6, ge=1, le=12, description="Number of products (1-12)")
):
    """
    Open WebUI compatible endpoint - returns plain text LLM response that Open WebUI expects.
    This bypasses the SSE wrapping issue by returning text directly instead of JSON.
    """
    try:
        # Get the LLM-ready data
        llm_data = await search_products_llm_ready(request, term=term, limit=limit)
        
        # Extract the response content 
        if hasattr(llm_data, 'body'):
            import json
            data = json.loads(llm_data.body.decode())
        else:
            data = llm_data
            
        # Return as JSON object for Open WebUI tool server integration
        return JSONResponse(content={
            "message": data.get("llm_response", f"No products found for '{term}'"),
            "type": "tool_response",
            "format": "html_artifact"
        })
        
    except Exception as e:
        return JSONResponse(content={
            "message": f"Error searching for '{term}': {str(e)}",
            "type": "error",
            "format": "text"
        }, status_code=500)

from fastapi.responses import StreamingResponse
import asyncio

@app.get("/products/search/sse")
@limiter.limit("30/minute")
async def search_products_sse(
    request: Request,
    term: str = Query(..., description="Product search term"),
    limit: int = Query(6, ge=1, le=12, description="Number of products (1-12)")
):
    """
    SSE-compatible endpoint for Open WebUI - returns proper Server-Sent Events format.
    This matches Open WebUI's expected streaming response format exactly.
    """
    async def generate_sse():
        try:
            # Get the LLM-ready data
            llm_data = await search_products_llm_ready(request, term=term, limit=limit)
            
            # Extract the response content
            if hasattr(llm_data, 'body'):
                import json
                data = json.loads(llm_data.body.decode())
            else:
                data = llm_data
            
            response_text = data.get("llm_response", f"No products found for '{term}'")
            
            # Split response into chunks for streaming (simulating LLM typing)
            # Open WebUI expects SSE format: "data: <content>\n\n"
            
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'model': 'kroger-mcp'})}\n\n"
            
            # Stream the response in chunks
            chunk_size = 50  # Characters per chunk
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                # Format as SSE with proper escaping
                sse_data = {
                    'type': 'content',
                    'content': chunk
                }
                yield f"data: {json.dumps(sse_data)}\n\n"
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"SSE error: {e}")
            error_msg = f"Error searching for '{term}': {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.get("/products/search/stream")
@limiter.limit("30/minute")
async def search_products_stream(
    request: Request,
    term: str = Query(..., description="Product search term"),
    limit: int = Query(6, ge=1, le=12, description="Number of products (1-12)")
):
    """
    Pure streaming endpoint that returns text/plain with embedded HTML.
    Designed to match Open WebUI's LLM response streaming format exactly.
    """
    async def generate_stream():
        try:
            # Get the LLM-ready data
            llm_data = await search_products_llm_ready(request, term=term, limit=limit)
            
            # Extract the response content
            if hasattr(llm_data, 'body'):
                import json
                data = json.loads(llm_data.body.decode())
            else:
                data = llm_data
            
            response_text = data.get("llm_response", f"No products found for '{term}'")
            
            # Stream the response character by character (simulating LLM typing)
            for char in response_text:
                yield char
                await asyncio.sleep(0.001)  # Very small delay for smooth streaming
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"\n\nError searching for '{term}': {str(e)}"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff"
        }
    )

@app.get("/products/search/llm-ready", response_model=Dict[str, Any])
@limiter.limit("30/minute")
async def search_products_llm_ready(
    request: Request,
    term: str = Query(..., description="Product search term"),
    limit: int = Query(6, ge=1, le=12, description="Number of products (1-12)")
) -> JSONResponse:
    """
    LLM-optimized endpoint that returns pre-formatted responses for guaranteed Open WebUI artifact rendering.
    
    This endpoint solves the core issue where Open WebUI only detects HTML code blocks in LLM responses,
    not in MCP JSON responses. Returns a ready-to-use response format that LLMs can include directly
    in their chat responses to trigger visual artifact rendering.
    """
    try:
        # Get compact products using existing logic
        compact_data = await search_products_compact(request, term=term, limit=limit)
        
        if not compact_data.get("products"):
            return JSONResponse(
                content={
                    "llm_response": f"No products found for '{term}'. Please try a different search term.",
                    "fallback_text": f"No {term} products available at this time.",
                    "artifact_available": False,
                    "search_term": term
                },
                media_type="application/json"
            )
        
        products = compact_data["products"]
        
        # Create lightweight, self-contained HTML for Open WebUI artifact rendering
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{term} - Kroger Products</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; padding: 16px; }}
        .header {{ text-align: center; margin-bottom: 24px; padding: 20px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border-radius: 12px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .stats {{ display: flex; justify-content: center; gap: 20px; margin-top: 12px; font-size: 14px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }}
        .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-2px); }}
        .img {{ height: 160px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; position: relative; }}
        .img img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        .status {{ position: absolute; top: 8px; right: 8px; background: #10b981; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
        .content {{ padding: 16px; }}
        .brand {{ color: #6b7280; font-size: 11px; text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }}
        .name {{ font-size: 14px; font-weight: 600; margin-bottom: 6px; line-height: 1.3; }}
        .size {{ color: #6b7280; font-size: 12px; margin-bottom: 8px; }}
        .price-row {{ display: flex; align-items: center; justify-content: space-between; }}
        .price {{ font-size: 18px; font-weight: 700; color: #111827; }}
        .btn {{ background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🥛 {term.title()}</h1>
        <div class="stats">
            <span>{len(products)} Products</span>
            <span>Kroger Delivery</span>
        </div>
    </div>
    <div class="grid">"""
        
        for product in products:
            price = product.get('price', 0)
            price_display = f"${price:.2f}" if price and price > 0 else "Price N/A"
            
            # Truncate name for display
            name = product.get('name', 'Unknown Product')
            display_name = name[:40] + '...' if len(name) > 40 else name
            
            html_content += f"""
        <div class="card">
            <div class="img">
                <div class="status">In Stock</div>
                <img src="{product.get('image_url', '')}" alt="{display_name}" onerror="this.style.display='none'">
            </div>
            <div class="content">
                <div class="brand">{product.get('brand', 'Kroger')}</div>
                <div class="name">{display_name}</div>
                <div class="size">{product.get('size', 'Standard Size')}</div>
                <div class="price-row">
                    <div class="price">{price_display}</div>
                    <button class="btn">Add</button>
                </div>
            </div>
        </div>"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        # Create LLM-ready response format
        response_data = {
            "llm_response": f"""Found {len(products)} {term} products available for delivery:

```html
{html_content}
```

**Product Summary:**
- {len(products)} items available
- All items available for delivery
- Prices range from ${min(p.get('price', 0) for p in products):.2f} to ${max(p.get('price', 0) for p in products):.2f}""",
            
            "artifact_available": True,
            "artifact_html": html_content,
            "fallback_text": f"Found {len(products)} {term} products: " + ", ".join([f"{p.get('name', 'Unknown')} (${p.get('price', 0):.2f})" for p in products[:3]]) + ("..." if len(products) > 3 else ""),
            "search_term": term,
            "product_count": len(products),
            "instructions": "Copy the 'llm_response' field directly into your chat response. The HTML code block will automatically render as a visual artifact in Open WebUI."
        }
        
        # Return explicit JSONResponse to ensure clean JSON format
        return JSONResponse(
            content=response_data,
            media_type="application/json",
            headers={
                "X-Response-Type": "json",
                "Cache-Control": "max-age=300"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in LLM-ready search: {e}")
        return JSONResponse(
            content={
                "llm_response": f"Sorry, I encountered an error searching for '{term}'. Please try again.",
                "fallback_text": f"Error searching for {term}",
                "artifact_available": False,
                "search_term": term,
                "error": str(e)
            },
            status_code=500,
            media_type="application/json"
        )

@app.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """
    Serve MCP UI Protocol artifacts for Open WebUI
    
    Returns artifact metadata + content for LLM consumption
    """
    if artifact_id not in artifact_cache:
        raise HTTPException(status_code=404, detail="Artifact not found or expired")
    
    artifact = artifact_cache[artifact_id]
    
    # Return JSON for LLM compatibility, with option for HTML rendering
    return {
        "artifact_id": artifact_id,
        "mimeType": artifact['mimeType'],
        "content": artifact['content'],
        "metadata": artifact['metadata'],
        "status": "available"
    }

@app.get("/artifacts/{artifact_id}/render")
async def render_artifact(artifact_id: str):
    """
    Render MCP UI Protocol artifacts as HTML for browser display
    """
    if artifact_id not in artifact_cache:
        raise HTTPException(status_code=404, detail="Artifact not found or expired")
    
    artifact = artifact_cache[artifact_id]
    
    # Return HTML content directly for browser rendering
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        content=artifact['content'], 
        media_type="text/html"
    )

# ============================================================================
# Token-Efficient Artifact Endpoints
# ============================================================================

@app.get("/products/search/artifact", response_model=ArtifactSearchResponse)
@limiter.limit("100/minute")
async def search_products_with_artifact(
    request: Request,
    term: str = Query(..., description="Search term for products"),
    limit: int = Query(5, ge=1, le=10, description="Max 10 for token efficiency"),
    template: str = Query("grid", description="Template type: grid, list, cards")
):
    """
    🚀 TOKEN-EFFICIENT PRODUCT SEARCH with Pre-rendered HTML Artifacts
    
    Returns minimal product data (90% token reduction) + artifact reference.
    LLMs get essential info only, Web UI displays beautiful pre-rendered HTML.
    """
    # Force limit to maximum efficiency
    if limit > 10:
        limit = 10
    
    # Get products from Kroger API
    store_id = KROGER_DEFAULT_STORE_ID
    token = await get_client_credentials_token()
    
    params = {
        "filter.term": term,
        "filter.locationId": store_id,
        "filter.fulfillment": "del",
        "filter.limit": limit,
        "filter.start": 1
    }
    
    result = await make_kroger_request("GET", "/products", token, params)
    
    if "data" not in result or not result["data"]:
        # Create empty UI resource
        empty_resource = mcp_ui_service.create_ui_resource(
            uri_id="empty-results",
            html_content="<div style='text-align: center; padding: 20px; color: #666;'>No products found</div>"
        )
        return ArtifactSearchResponse(
            query=term,
            count=0,
            products=[],
            ui_resources={empty_resource.uri: empty_resource},
            expires_in=0,
            artifact_html=empty_resource.content,
            display_instructions=f"No products found for '{term}'. The search returned empty results."
        )
    
    # Extract compact product data (same logic as compact endpoint)
    compact_products = []
    for product in result["data"]:
        # Extract only essential information
        compact_product = {
            "name": product.get("description", "Unknown"),
            "upc": product.get("upc", ""),
            "brand": product.get("brand", ""),
            "price": None,
            "size": None,
            "available": False,
            "delivery": False,
            "image_url": None
        }
        
        # Extract featured product image (front perspective, medium size)
        if "images" in product and product["images"]:
            for image in product["images"]:
                if image.get("perspective") == "front" and image.get("featured"):
                    sizes = image.get("sizes", [])
                    for size_info in sizes:
                        if size_info.get("size") == "medium":
                            compact_product["image_url"] = size_info.get("url")
                            break
                    # If no medium, use first available size
                    if not compact_product["image_url"] and sizes:
                        compact_product["image_url"] = sizes[0].get("url")
                    break
            # If no featured front image, use first available image
            if not compact_product["image_url"] and product["images"]:
                first_image = product["images"][0]
                sizes = first_image.get("sizes", [])
                if sizes:
                    compact_product["image_url"] = sizes[0].get("url")
        
        # Get pricing and availability from items
        if "items" in product and product["items"]:
            item = product["items"][0]  # Use first item
            if "price" in item:
                compact_product["price"] = item["price"].get("regular", 0)
            if "size" in item:
                compact_product["size"] = item["size"]
            if "fulfillment" in item:
                fulfillment = item["fulfillment"]
                compact_product["delivery"] = fulfillment.get("delivery", False)
                compact_product["available"] = any([
                    fulfillment.get("delivery", False),
                    fulfillment.get("curbside", False),
                    fulfillment.get("inStore", False)
                ])
        
        compact_products.append(compact_product)
    
    # Generate MCP UI Protocol resource with search term for proper theming
    ui_resource = mcp_ui_service.create_product_cards_resource(compact_products, template, term)
    
    # Cache the artifact for Open WebUI access
    if ui_resource:
        artifact_id = ui_resource.uri.split('/')[-1]  # Extract ID from uri://component/{id}
        artifact_cache[artifact_id] = {
            'content': ui_resource.content,
            'mimeType': ui_resource.mimeType,
            'metadata': ui_resource.metadata
        }
    
    # Create UI resources dictionary
    ui_resources = {
        ui_resource.uri: ui_resource
    }
    
    # Convert to minimal products (for token efficiency) - same format as compact endpoint
    minimal_products = []
    for compact_product in compact_products:
        # Truncate name to fit Pydantic validation (max 50 chars)
        full_name = compact_product.get("name", "Unknown")
        truncated_name = full_name[:47] + "..." if len(full_name) > 50 else full_name
        
        minimal = {
            "id": compact_product.get("upc", ""),
            "name": truncated_name,
            "price": compact_product.get("price", 0),
            "artifact_id": ui_resource.uri.split("/")[-1],
            "summary": f"{compact_product.get('brand', '')} - {compact_product.get('size', '')}".strip(" -")[:100] or "Product"
        }
        minimal_products.append(minimal)
    
    # Convert MCPUIResource objects to dictionaries for Pydantic
    ui_resources_dict = {
        uri: resource.model_dump() if hasattr(resource, 'model_dump') else resource
        for uri, resource in ui_resources.items()
    }
    
    # Return MCP UI Protocol response with Open WebUI artifact support
    return ArtifactSearchResponse(
        query=term,
        count=len(minimal_products),
        products=minimal_products,
        ui_resources=ui_resources_dict,
        expires_in=3600,  # 1 hour
        artifact_html=ui_resource.content,
        display_instructions=f"To display the product cards visually in Open WebUI, include this HTML code block in your response:\n\n```html\n{ui_resource.content}\n```"
    )


@app.get("/artifacts/{artifact_id}")
async def get_artifact(
    artifact_id: str = Path(..., description="Artifact ID"),
    format: str = Query("json", description="Response format: html or json")
):
    """
    📦 RETRIEVE PRE-RENDERED HTML ARTIFACT
    
    Returns compressed, ready-to-display HTML for Web UI.
    No token cost for display - just beautiful, interactive product cards.
    """
    html_content = await artifact_service.get_artifact(artifact_id)
    
    if not html_content:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found or expired"
        )
    
    if format == "html":
        # Return raw HTML for direct browser rendering
        return HTMLResponse(
            content=html_content,
            headers={"Cache-Control": "public, max-age=3600"}
        )
    else:
        # Return JSON-wrapped for MCP clients (default)
        return {
            "artifact_id": artifact_id,
            "content_type": "text/html",
            "content": html_content,
            "cached": True,
            "size_bytes": len(html_content),
            "instructions": "Render the 'content' field as HTML in your UI"
        }


@app.get("/ui/{resource_uri:path}")
async def get_mcp_ui_resource(
    resource_uri: str = Path(..., description="MCP UI Resource URI (without ui:// prefix)")
):
    """
    🎯 MCP UI Protocol Resource Endpoint
    
    Returns UI resources for MCP UI Protocol compliance.
    Format: GET /ui/component/product-cards-abc123
    """
    # This is a placeholder for direct UI resource access
    # In a full implementation, you might cache UI resources separately
    raise HTTPException(
        status_code=404,
        detail="UI resource not found. Resources are embedded in search responses."
    )


@app.get("/products/search/minimal")
@limiter.limit("100/minute")  
async def search_products_minimal(
    request: Request,
    term: str = Query(..., description="Search term"),
    limit: int = Query(3, ge=1, le=5, description="Max 5 for ultra-efficiency")
):
    """
    ⚡ ULTRA-MINIMAL PRODUCT SEARCH for Maximum Token Efficiency
    
    Returns only essential fields, no artifacts. For situations where
    you need the absolute minimum token usage (70% reduction).
    """
    if limit > 5:
        limit = 5
    
    store_id = KROGER_DEFAULT_STORE_ID
    token = await get_client_credentials_token()
    
    params = {
        "filter.term": term,
        "filter.locationId": store_id,
        "filter.fulfillment": "del",
        "filter.limit": limit,
        "filter.start": 1
    }
    
    result = await make_kroger_request("GET", "/products", token, params)
    
    if "data" not in result:
        return {"products": [], "query": term, "count": 0}
    
    # Ultra-minimal response
    minimal_products = []
    for product in result["data"]:
        items = product.get("items", [])
        item = items[0] if items else {}
        
        minimal_products.append({
            "id": product.get("productId", ""),
            "name": product.get("description", "")[:40],
            "price": item.get("price", {}).get("regular", 0),
            "brand": product.get("brand", "")[:15]
        })
    
    return {
        "query": term,
        "count": len(minimal_products),
        "products": minimal_products
    }


@app.delete("/artifacts/cleanup")
async def cleanup_expired_artifacts():
    """
    🧹 CLEANUP EXPIRED ARTIFACTS
    
    Manual cleanup of expired artifacts. Also runs automatically in background.
    Use this for manual maintenance or debugging.
    """
    cleaned = await artifact_service.cleanup_expired_artifacts()
    
    return {
        "message": f"Cleaned up {cleaned} expired artifacts",
        "remaining": len(artifact_service.cache),
        "cache_items": list(artifact_service.cache.keys())
    }


@app.get("/locations/search")
@limiter.limit("100/minute")
async def search_locations(request: Request):
    """Simple store finder - automatically searches near Hilliard, OH, no parameters needed"""
    # Use defaults always
    search_zip = KROGER_DEFAULT_ZIP_CODE
    search_radius = KROGER_DEFAULT_RADIUS_MILES
    
    # Get client credentials token
    token = await get_client_credentials_token()
    
    # Build query parameters with defaults
    params = {
        "filter.zipCode.near": search_zip,
        "filter.radiusInMiles": search_radius,
        "filter.limit": 10  # Smaller limit for simpler results
    }
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", "/locations", token, params)
    return result


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.get("/auth/authorize", include_in_schema=False)
async def get_authorization_url(
    scope: str = Query("profile.compact cart.basic:write", description="OAuth scope"),
    state: str = Query("", description="Optional state parameter")
):
    """Get Kroger OAuth authorization URL (Hidden from schema for GPT-5 compatibility)"""
    params = {
        "client_id": KROGER_CLIENT_ID,
        "redirect_uri": KROGER_REDIRECT_URI,
        "response_type": "code",
        "scope": scope
    }
    
    if state:
        params["state"] = state
    
    auth_url = f"{KROGER_AUTHORIZE_URL}?{urlencode(params)}"
    
    return {
        "authorization_url": auth_url,
        "redirect_uri": KROGER_REDIRECT_URI,
        "scope": scope
    }


@app.get("/auth/callback", include_in_schema=False)
async def auth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query("", description="State parameter")
):
    """Handle OAuth callback and exchange code for tokens"""
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required"
        )
    
    # Exchange code for tokens
    auth_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": KROGER_REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                KROGER_AUTH_URL,
                data=auth_data,
                auth=(KROGER_CLIENT_ID, KROGER_CLIENT_SECRET),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code for tokens"
                )
            
            token_data = response.json()
            
            # Generate user ID (in production, extract from JWT or use customer ID)
            user_id = hashlib.md5(f"{code}{time.time()}".encode()).hexdigest()
            
            # Store tokens
            token_cache[user_id] = {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"],
                "expires_at": time.time() + token_data["expires_in"],
                "refresh_token": token_data.get("refresh_token"),
                "scope": token_data.get("scope")
            }
            
            logger.info(f"Successfully authenticated user {user_id}")
            
            # Calculate expiration timestamp
            expires_at = time.time() + token_data["expires_in"]
            
            return {
                "message": "Authentication successful",
                "user_id": user_id,
                "access_token": token_data["access_token"],
                "expires_in": token_data["expires_in"],
                "scope": token_data.get("scope"),
                "hardcode_instructions": {
                    "message": "To hardcode these tokens in your .env file, copy these values:",
                    "env_variables": {
                        "KROGER_USER_ACCESS_TOKEN": token_data["access_token"],
                        "KROGER_USER_REFRESH_TOKEN": token_data.get("refresh_token", ""),
                        "KROGER_USER_TOKEN_EXPIRES_AT": str(expires_at),
                        "KROGER_HARDCODED_USER_ID": "user_default"
                    }
                }
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error during token exchange: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Network error connecting to Kroger API"
            )


@app.get("/auth/prompt-user")
async def prompt_user_for_authentication():
    """LLM-friendly endpoint to prompt user for authentication when cart operations fail"""
    import subprocess
    import platform
    
    # Get the authorization URL
    params = {
        "client_id": KROGER_CLIENT_ID,
        "redirect_uri": KROGER_REDIRECT_URI,
        "response_type": "code",
        "scope": "profile.compact cart.basic:write"
    }
    
    auth_url = f"{KROGER_AUTHORIZE_URL}?{urlencode(params)}"
    
    # Try to open the browser automatically
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", auth_url], check=False)
        elif platform.system() == "Windows":
            subprocess.run(["start", auth_url], shell=True, check=False)
        else:  # Linux
            subprocess.run(["xdg-open", auth_url], check=False)
        browser_opened = True
    except Exception:
        browser_opened = False
    
    return {
        "message": "🔐 Authentication Required",
        "details": "Your Kroger authentication tokens have expired. Please complete the OAuth flow to continue adding items to your cart.",
        "authorization_url": auth_url,
        "browser_opened": browser_opened,
        "instructions": [
            "1. Click the authorization URL above (or it should open automatically)",
            "2. Log in with your Kroger credentials (twocbusguys@gmail.com)",
            "3. Authorize the application",
            "4. You'll be redirected back and cart operations will work again"
        ],
        "tip": "This authentication lasts about 30 minutes. The system will prompt you again when needed."
    }


# ============================================================================
# Products API
# ============================================================================

@app.get("/products/search", include_in_schema=False)
@limiter.limit("100/minute")  # Public API rate limit
async def search_products_advanced(
    request: Request,
    term: str = Query(..., description="Search term for products"),
    locationId: str = Query("", description="Store location ID (OPTIONAL - defaults to Cemetery Road store 01600966)"),
    brand: str = Query("", description="Filter by brand"),
    fulfillment: str = Query("", description="Fulfillment type (ais, crs, dug, rog, shp)"),
    limit: int = Query(50, ge=1, le=50, description="Number of results to return"),
    start: int = Query(1, ge=1, description="Starting position for pagination")
):
    """Search for products. No parameters required except 'term' - automatically uses Cemetery Road store if no locationId provided."""
    # Use default store if not provided
    store_id = locationId if locationId else KROGER_DEFAULT_STORE_ID
    
    # Get client credentials token for product search
    token = await get_client_credentials_token()
    
    # Build query parameters (prioritize delivery-enabled items)
    params = {
        "filter.term": term,
        "filter.locationId": store_id,
        "filter.fulfillment": "del",  # Filter for delivery-enabled items
        "filter.limit": limit,
        "filter.start": start
    }
    
    if brand:
        params["filter.brand"] = brand
    # Always force delivery fulfillment (ignore user-provided fulfillment parameter)
    # This ensures all results are delivery-enabled for the hardcoded delivery preference
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", "/products", token, params)
    
    return ProductSearchResponse(**result)


@app.get("/products/{product_id}", response_model=Product)
@limiter.limit("100/minute")
async def get_product_details(
    request: Request,
    product_id: str = Path(..., description="Product ID or UPC"),
    locationId: str = Query(..., description="Store location ID")
):
    """Get detailed information about a specific product"""
    # Get client credentials token
    token = await get_client_credentials_token()
    
    params = {"filter.locationId": locationId}
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", f"/products/{product_id}", token, params)
    
    return Product(**result["data"])


# ============================================================================
# Locations API
# ============================================================================

@app.get("/locations/search", include_in_schema=False)
@limiter.limit("100/minute")
async def search_locations_advanced(
    request: Request,
    zipCode: str = Query("", description="ZIP code to search near (OPTIONAL - defaults to 43026)"),
    lat: float = Query(0.0, description="Latitude for location search (OPTIONAL)"),
    lon: float = Query(0.0, description="Longitude for location search (OPTIONAL)"),
    radiusInMiles: int = Query(0, description="Search radius in miles (OPTIONAL - defaults to 10)"),
    chain: str = Query("", description="Chain filter"),
    department: str = Query("", description="Department filter"),
    limit: int = Query(50, ge=1, le=50, description="Number of results to return")
):
    """Search for store locations. No parameters required - automatically searches near Hilliard, OH (43026) if no location provided."""
    # Use defaults if not provided
    search_zip = zipCode if zipCode else KROGER_DEFAULT_ZIP_CODE
    search_radius = radiusInMiles if radiusInMiles > 0 else KROGER_DEFAULT_RADIUS_MILES
    
    # Validate that we have location data
    if not search_zip and not (lat != 0.0 and lon != 0.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either zipCode or both lat and lon must be provided"
        )
    
    # Get client credentials token
    token = await get_client_credentials_token()
    
    # Build query parameters
    params = {
        "filter.radiusInMiles": search_radius,
        "filter.limit": limit
    }
    
    if search_zip:
        params["filter.zipCode.near"] = search_zip
    else:
        params["filter.lat.near"] = lat
        params["filter.lon.near"] = lon
    
    if chain:
        params["filter.chain"] = chain
    if department:
        params["filter.department"] = department
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", "/locations", token, params)
    
    return LocationSearchResponse(**result)


@app.get("/locations/{location_id}", response_model=Location)
@limiter.limit("100/minute")
async def get_location_details(
    request: Request,
    location_id: str = Path(..., description="Location ID")
):
    """Get detailed information about a specific location"""
    # Get client credentials token
    token = await get_client_credentials_token()
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", f"/locations/{location_id}", token)
    
    return Location(**result["data"])


# ============================================================================
# Cart API (Requires User Authentication)
# ============================================================================

@app.put("/cart/add")
@limiter.limit("50/minute")
async def add_to_cart(
    request: Request,
    items: CartItemRequest,
    user_id: str = Depends(get_current_user)
):
    """Add items to cart - automatically uses Cemetery Road store with Kroger delivery"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for cart operations"
        )
    
    # Check rate limit (5000 requests per day for cart operations)
    if not check_rate_limit("cart", user_id, 5000):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily cart operation limit exceeded"
        )
    
    # Get user access token
    token = await get_user_token(user_id)
    
    # Use correct cart/add endpoint format per Kroger API docs with delivery fulfillment
    cart_data = {
        "items": []
    }
    
    # Add fulfillment details for each item to ensure delivery
    for item in items.items:
        cart_item = {
            "upc": item.get("upc") if isinstance(item, dict) else item.upc,
            "quantity": item.get("quantity") if isinstance(item, dict) else item.quantity,
            "fulfillment": {
                "fulfillmentType": "delivery",
                "locationId": KROGER_DEFAULT_STORE_ID
            }
        }
        cart_data["items"].append(cart_item)
    
    # Make request to Kroger API using correct endpoint
    await make_kroger_request("PUT", "/cart/add", token, json_data=cart_data)
    
    # Cart API returns 204 (no content) on success
    return {"message": "Items added to cart successfully"}

@app.put("/cart/add/simple")
@limiter.limit("50/minute")
async def add_to_cart_simple(
    request: Request,
    upc: str = Query(..., description="Product UPC code"),
    quantity: int = Query(1, description="Quantity to add"),
    user_id: str = Depends(get_current_user)
):
    """LLM-optimized cart add - simple parameters, minimal response"""
    if not user_id:
        # Return LLM-friendly auth prompt instead of generic error
        return {
            "success": False,
            "error": "authentication_required",
            "message": "🔐 Authentication needed for cart operations",
            "action_required": "Please call the /auth/prompt-user endpoint to authenticate",
            "auth_url": f"http://localhost:9004/auth/prompt-user"
        }
    
    # Check rate limit
    if not check_rate_limit("cart", user_id, 5000):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily cart operation limit exceeded"
        )
    
    try:
        # Get user access token
        token = await get_user_token(user_id)
        
        # Simple cart data format
        cart_data = {
            "items": [{
                "upc": upc,
                "quantity": quantity,
                "fulfillment": {
                    "fulfillmentType": "delivery",
                    "locationId": KROGER_DEFAULT_STORE_ID
                }
            }]
        }
        
        # Make request to Kroger API using correct endpoint
        await make_kroger_request("PUT", "/cart/add", token, json_data=cart_data)
        
        # Simple success response for LLM
        return {
            "success": True,
            "upc": upc,
            "quantity": quantity,
            "message": f"Added {quantity}x item to cart"
        }
        
    except HTTPException as e:
        if e.status_code == 401:
            # Authentication error - return helpful prompt for LLM
            return {
                "success": False,
                "error": "authentication_expired",
                "message": "🔐 Your Kroger authentication has expired",
                "details": "Tokens expire after 30 minutes for security",
                "action_required": "Please call the /auth/prompt-user endpoint to re-authenticate",
                "auth_url": f"http://localhost:9004/auth/prompt-user",
                "upc": upc,
                "quantity": quantity,
                "note": "Item will be added to cart after you complete authentication"
            }
        else:
            # Re-raise other HTTP exceptions
            raise e


@app.get("/cart", response_model=CartResponse)
@limiter.limit("50/minute")
async def get_cart(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get current cart contents for authenticated user"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for cart operations"
        )
    
    # Check rate limit
    if not check_rate_limit("cart", user_id, 5000):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily cart operation limit exceeded"
        )
    
    # Get user access token
    token = await get_user_token(user_id)
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", "/cart", token)
    
    return CartResponse(**result)


@app.put("/cart/items", response_model=CartResponse)
@limiter.limit("50/minute")
async def add_cart_items(
    request: Request,
    items: CartItemRequest,
    user_id: str = Depends(get_current_user)
):
    """Add or update items in cart for authenticated user"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for cart operations"
        )
    
    # Check rate limit
    if not check_rate_limit("cart", user_id, 5000):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily cart operation limit exceeded"
        )
    
    # Get user access token
    token = await get_user_token(user_id)
    
    # Make request to Kroger API
    result = await make_kroger_request("PUT", "/cart/items", token, json_data=items.dict())
    
    return CartResponse(**result)


@app.delete("/cart/items/{item_id}")
@limiter.limit("50/minute")
async def remove_cart_item(
    request: Request,
    item_id: str = Path(..., description="Item ID to remove"),
    user_id: str = Depends(get_current_user)
):
    """Remove item from cart for authenticated user"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for cart operations"
        )
    
    # Check rate limit
    if not check_rate_limit("cart", user_id, 5000):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily cart operation limit exceeded"
        )
    
    # Get user access token
    token = await get_user_token(user_id)
    
    # Make request to Kroger API
    await make_kroger_request("DELETE", f"/cart/items/{item_id}", token)
    
    return {"message": "Item removed successfully"}


# ============================================================================
# Identity/Loyalty API (Requires User Authentication)
# ============================================================================

@app.get("/identity/profile", response_model=IdentityResponse)
@limiter.limit("100/minute")
async def get_user_profile(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get user profile information for authenticated user"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for profile access"
        )
    
    # Get user access token
    token = await get_user_token(user_id)
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", "/identity/profile", token)
    
    return IdentityResponse(**result)


@app.get("/identity/loyalty", response_model=LoyaltyResponse)
@limiter.limit("100/minute")
async def get_loyalty_info(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """Get loyalty account information for authenticated user"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for loyalty access"
        )
    
    # Get user access token
    token = await get_user_token(user_id)
    
    # Make request to Kroger API
    result = await make_kroger_request("GET", "/identity/loyalty", token)
    
    return LoyaltyResponse(**result)


# ============================================================================
# Admin/Debug Endpoints
# ============================================================================

@app.get("/admin/tokens")
async def list_cached_tokens():
    """List all cached tokens with status information"""
    current_time = time.time()
    
    client_info = None
    if client_credentials_token:
        expires_at = client_credentials_token.get("expires_at", 0)
        client_info = {
            "exists": True,
            "expires_at": expires_at,
            "expires_in_seconds": max(0, int(expires_at - current_time)),
            "is_expired": is_token_expired(client_credentials_token, 0),
            "needs_refresh_soon": is_token_expired(client_credentials_token, 5),
            "scope": client_credentials_token.get("scope")
        }
    else:
        client_info = {"exists": False}
    
    user_info = {}
    for user_id, token_info in token_cache.items():
        expires_at = token_info.get("expires_at", 0)
        user_info[user_id] = {
            "expires_at": expires_at,
            "expires_in_seconds": max(0, int(expires_at - current_time)),
            "is_expired": is_token_expired(token_info, 0),
            "needs_refresh_soon": is_token_expired(token_info, 5),
            "has_refresh_token": bool(token_info.get("refresh_token")),
            "scope": token_info.get("scope"),
            "source": token_info.get("source", "oauth")
        }
    
    return {
        "client_credentials": client_info,
        "user_tokens": user_info,
        "background_refresh_running": token_refresh_task is not None and not token_refresh_task.done(),
        "token_file_exists": token_file_path.exists(),
        "current_time": current_time
    }


@app.post("/admin/tokens/refresh")
async def manual_token_refresh():
    """Manually trigger token refresh for all tokens"""
    refresh_results = {}
    
    # Refresh client credentials token
    try:
        await get_client_credentials_token()
        refresh_results["client_credentials"] = "success"
    except Exception as e:
        refresh_results["client_credentials"] = f"failed: {str(e)}"
    
    # Refresh user tokens
    for user_id, token_info in list(token_cache.items()):
        if token_info.get("refresh_token"):
            try:
                await refresh_user_token(token_info["refresh_token"], user_id)
                refresh_results[f"user_{user_id}"] = "success"
            except Exception as e:
                refresh_results[f"user_{user_id}"] = f"failed: {str(e)}"
        else:
            refresh_results[f"user_{user_id}"] = "no_refresh_token"
    
    return {
        "message": "Manual token refresh completed",
        "results": refresh_results,
        "timestamp": time.time()
    }


@app.get("/admin/tokens/status")
async def get_token_status():
    """Get detailed token status for monitoring"""
    current_time = time.time()
    
    status = {
        "healthy": True,
        "issues": [],
        "tokens": {
            "client_credentials": None,
            "users": {}
        },
        "background_refresh": {
            "running": token_refresh_task is not None and not token_refresh_task.done(),
            "task_exists": token_refresh_task is not None
        },
        "persistence": {
            "file_exists": token_file_path.exists(),
            "file_path": str(token_file_path.absolute())
        }
    }
    
    # Check client credentials status
    if client_credentials_token:
        expires_at = client_credentials_token.get("expires_at", 0)
        expires_in = expires_at - current_time
        
        status["tokens"]["client_credentials"] = {
            "valid": expires_in > 300,  # Valid if >5 min remaining
            "expires_in_seconds": max(0, int(expires_in)),
            "status": "healthy" if expires_in > 600 else "expiring_soon" if expires_in > 0 else "expired"
        }
        
        if expires_in <= 300:
            status["issues"].append("Client credentials token expires soon or has expired")
            status["healthy"] = False
    else:
        status["tokens"]["client_credentials"] = {"valid": False, "status": "missing"}
        status["issues"].append("No client credentials token")
        status["healthy"] = False
    
    # Check user tokens status
    for user_id, token_info in token_cache.items():
        expires_at = token_info.get("expires_at", 0)
        expires_in = expires_at - current_time
        has_refresh = bool(token_info.get("refresh_token"))
        
        user_status = {
            "valid": expires_in > 300,
            "expires_in_seconds": max(0, int(expires_in)),
            "has_refresh_token": has_refresh,
            "status": "healthy" if expires_in > 600 else "expiring_soon" if expires_in > 0 else "expired",
            "source": token_info.get("source", "oauth")
        }
        
        status["tokens"]["users"][user_id] = user_status
        
        if expires_in <= 300 and not has_refresh:
            status["issues"].append(f"User {user_id} token expires soon with no refresh token")
            status["healthy"] = False
    
    return status


@app.get("/admin/rate-limits")
async def get_rate_limits():
    """Get current rate limit status"""
    return {"rate_limits": rate_limit_counters}


@app.delete("/admin/tokens/{user_id}")
async def revoke_user_token(user_id: str):
    """Revoke cached token for a user"""
    if user_id in token_cache:
        del token_cache[user_id]
        return {"message": f"Token revoked for user {user_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User token not found"
        )


# ============================================================================
# Token-Efficient Artifact System Services
# ============================================================================

class TemplateEngine:
    """HTML template generation for token-efficient artifacts"""
    
    def __init__(self):
        # Pre-loaded product card template with inline CSS for maximum efficiency
        self.product_card_template = '''
        <div class="product-card" data-upc="{upc}" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; background: linear-gradient(135deg, {gradient}); margin: 8px; min-width: 250px; transition: all 0.2s;">
            <div class="product-info">
                <h3 style="font-size: 14px; font-weight: 600; margin: 0 0 4px 0; color: #1a1a1a; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{name}">{name_short}</h3>
                <p style="font-size: 12px; color: #666; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px;">{brand}</p>
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 20px; font-weight: bold; color: #0066cc;">${price}</span>
                    <span style="font-size: 12px; color: #666; margin-left: 4px;">/ {size}</span>
                </div>
                <div style="margin-bottom: 8px;">
                    {availability_badges}
                </div>
                <button onclick="addToCart('{upc}', 1)" style="width: 100%; padding: 8px; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 12px; transition: background 0.2s;" onmouseover="this.style.background='#0052a3'" onmouseout="this.style.background='#0066cc'">
                    Add to Cart
                </button>
            </div>
        </div>
        '''
        
        # Gradient color variations for visual appeal
        self.gradients = [
            "#ffffff 0%, #f8f9ff 100%",  # Light blue
            "#ffffff 0%, #fff8f0 100%",  # Light orange
            "#ffffff 0%, #f0fff4 100%",  # Light green
            "#ffffff 0%, #fef7f0 100%",  # Light peach
            "#ffffff 0%, #f0f8ff 100%",  # Light cyan
            "#ffffff 0%, #fff5f7 100%",  # Light pink
            "#ffffff 0%, #f7f0ff 100%",  # Light purple
            "#ffffff 0%, #f0fff0 100%",  # Light mint
        ]
    
    def generate_product_grid(self, products: List[Product], template_type: str = "grid") -> str:
        """Generate complete HTML artifact with product cards"""
        cards_html = []
        
        for i, product in enumerate(products):
            if not product.items:
                continue
                
            item = product.items[0]
            price = item.price.get("regular", 0)
            
            # Availability badges
            badges = []
            if item.fulfillment.get("delivery"):
                badges.append('<span style="display: inline-block; padding: 2px 6px; font-size: 10px; background: #e6f4ea; color: #1e8e3e; border-radius: 3px; margin: 1px;">🚚 Delivery</span>')
            if item.fulfillment.get("curbside"):
                badges.append('<span style="display: inline-block; padding: 2px 6px; font-size: 10px; background: #fef7e0; color: #f9ab00; border-radius: 3px; margin: 1px;">🚗 Curbside</span>')
            
            if not badges:
                badges.append('<span style="display: inline-block; padding: 2px 6px; font-size: 10px; background: #fce8e6; color: #d93025; border-radius: 3px; margin: 1px;">❌ Unavailable</span>')
            
            # Generate card HTML
            card_html = self.product_card_template.format(
                upc=product.productId,
                name=product.description,
                name_short=product.description[:45] + ("..." if len(product.description) > 45 else ""),
                brand=product.brand or "Generic",
                price=f"{price:.2f}",
                size=item.size or "N/A",
                availability_badges="".join(badges),
                gradient=self.gradients[i % len(self.gradients)]
            )
            cards_html.append(card_html)
        
        # Complete HTML document with JavaScript
        full_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Kroger Products</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 16px; background: #f5f7fa; }}
                .product-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 12px; max-width: 1200px; margin: 0 auto; }}
                .product-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
                .toast {{ position: fixed; top: 20px; right: 20px; background: #2d7d32; color: white; padding: 12px 16px; border-radius: 4px; transform: translateX(400px); transition: transform 0.3s; z-index: 1000; }}
                .toast.show {{ transform: translateX(0); }}
                @media (max-width: 768px) {{ .product-grid {{ grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; }} }}
            </style>
        </head>
        <body>
            <div class="product-grid">
                {"".join(cards_html)}
            </div>
            <div id="toast" class="toast"></div>
            <script>
                function addToCart(upc, quantity) {{
                    // Dispatch custom event for MCP integration
                    const event = new CustomEvent('mcp:addToCart', {{
                        detail: {{ upc, quantity }}
                    }});
                    window.dispatchEvent(event);
                    
                    // Show feedback
                    showToast(`Added item ${{upc}} to cart!`);
                }}
                
                function showToast(message) {{
                    const toast = document.getElementById('toast');
                    toast.textContent = message;
                    toast.classList.add('show');
                    setTimeout(() => toast.classList.remove('show'), 3000);
                }}
                
                // Listen for MCP cart events
                window.addEventListener('mcp:addToCart', (e) => {{
                    console.log('MCP Cart Event:', e.detail);
                    // Here you would integrate with actual MCP cart endpoints
                }});
            </script>
        </body>
        </html>
        '''
        
        return full_html


class ArtifactService:
    """Service for generating and managing pre-rendered HTML artifacts"""
    
    def __init__(self):
        self.cache = {}  # In-memory artifact cache
        self.artifact_dir = FilePath("./artifacts")
        self.artifact_dir.mkdir(exist_ok=True)
        self.template_engine = TemplateEngine()
        logger.info(f"ArtifactService initialized with storage at {self.artifact_dir}")
    
    async def generate_product_artifact(self, products: List[Product], template_type: str = "grid") -> ArtifactMetadata:
        """Generate compressed HTML artifact from products"""
        artifact_id = str(uuid.uuid4())
        
        # Generate HTML content
        html_content = self.template_engine.generate_product_grid(products, template_type)
        
        # Compress for efficiency (typically 70% size reduction)
        compressed = gzip.compress(html_content.encode('utf-8'))
        
        # Store compressed artifact
        artifact_path = self.artifact_dir / f"{artifact_id}.html.gz"
        artifact_path.write_bytes(compressed)
        
        # Create metadata
        metadata = ArtifactMetadata(
            artifact_id=artifact_id,
            artifact_type=f"product_{template_type}",
            created_at=time.time(),
            expires_at=time.time() + 3600,  # 1 hour TTL
            content_hash=hashlib.sha256(html_content.encode()).hexdigest(),
            size_bytes=len(compressed),
            product_ids=[p.productId for p in products]
        )
        
        # Cache metadata for fast access
        self.cache[artifact_id] = metadata
        
        logger.info(f"Generated artifact {artifact_id} ({len(compressed)} bytes, {len(products)} products)")
        return metadata
    
    async def get_artifact(self, artifact_id: str) -> Optional[str]:
        """Retrieve and decompress artifact HTML by ID"""
        if artifact_id not in self.cache:
            return None
        
        metadata = self.cache[artifact_id]
        
        # Check if expired
        if metadata.expires_at < time.time():
            await self._cleanup_artifact(artifact_id)
            return None
        
        # Read and decompress
        artifact_path = self.artifact_dir / f"{artifact_id}.html.gz"
        if not artifact_path.exists():
            return None
        
        try:
            compressed = artifact_path.read_bytes()
            html_content = gzip.decompress(compressed).decode('utf-8')
            return html_content
        except Exception as e:
            logger.error(f"Failed to read artifact {artifact_id}: {e}")
            await self._cleanup_artifact(artifact_id)
            return None
    
    async def _cleanup_artifact(self, artifact_id: str):
        """Remove expired or corrupted artifact"""
        try:
            if artifact_id in self.cache:
                del self.cache[artifact_id]
            
            artifact_path = self.artifact_dir / f"{artifact_id}.html.gz"
            if artifact_path.exists():
                artifact_path.unlink()
            
            logger.info(f"Cleaned up artifact {artifact_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup artifact {artifact_id}: {e}")
    
    async def cleanup_expired_artifacts(self) -> int:
        """Clean up all expired artifacts - returns count cleaned"""
        current_time = time.time()
        cleaned = 0
        
        for artifact_id in list(self.cache.keys()):
            metadata = self.cache[artifact_id]
            if metadata.expires_at < current_time:
                await self._cleanup_artifact(artifact_id)
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired artifacts")
        
        return cleaned


class ResponseTransformer:
    """Transform full Kroger API responses to minimal, token-efficient formats"""
    
    @staticmethod
    def to_minimal_product(product: Product, artifact_id: str = "") -> MinimalProduct:
        """Convert full product to ultra-minimal representation"""
        item = product.items[0] if product.items else None
        price = item.price.get("regular", 0) if item else 0
        
        # Ultra-compact summary - brand + size
        brand_part = (product.brand or "")[:15]
        size_part = (item.size if item else "")[:15]
        summary = f"{brand_part} - {size_part}".strip(" -")[:100]
        
        return MinimalProduct(
            id=product.productId,
            name=product.description[:50],
            price=float(price),
            artifact_id=artifact_id,
            summary=summary
        )


# Initialize global services
# ============================================================================
# MCP UI Service (Reusable Infrastructure)
# ============================================================================

# Removed duplicate MCPUIService class - now using the one from mcp_ui_infrastructure.py


# ============================================================================
# Service Instances
# ============================================================================

artifact_service = ArtifactService()
mcp_ui_service = MCPUIService("kroger-server")
response_transformer = ResponseTransformer()


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup with token persistence"""
    global token_refresh_task
    
    logger.info("Starting Kroger MCP Server with robust token management...")
    
    # Load existing tokens from file
    try:
        saved_data = load_tokens_from_file()
        token_cache.update(saved_data.get("user_tokens", {}))
        
        global client_credentials_token
        saved_client_token = saved_data.get("client_credentials")
        if saved_client_token and not is_token_expired(saved_client_token, 5):
            client_credentials_token = saved_client_token
            logger.info("Loaded valid client credentials token from file")
        
        if token_cache:
            logger.info(f"Loaded {len(token_cache)} user tokens from persistent storage")
    except Exception as e:
        logger.error(f"Failed to load tokens from file: {e}")
    
    # Migrate tokens from environment variables if present
    migrate_env_tokens()
    
    # Validate configuration
    if not KROGER_DEV_MODE and (not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET):
        logger.error("KROGER_CLIENT_ID and KROGER_CLIENT_SECRET environment variables are required")
        logger.error("Set KROGER_DEV_MODE=true to run without credentials for testing")
        raise RuntimeError("Missing required Kroger API credentials")
    
    if KROGER_DEV_MODE:
        logger.warning("Running in DEVELOPMENT MODE - API calls will be simulated")
        if not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET:
            logger.warning("Missing Kroger API credentials - using mock responses")
    
    # Pre-fetch client credentials token (if credentials available)
    if KROGER_CLIENT_ID and KROGER_CLIENT_SECRET:
        try:
            await get_client_credentials_token()
            logger.info("Successfully obtained client credentials token")
        except Exception as e:
            logger.error(f"Failed to obtain initial client credentials token: {e}")
            if not KROGER_DEV_MODE:
                raise
    
    # Start background token refresh task
    try:
        token_refresh_task = asyncio.create_task(background_token_refresh())
        logger.info("Started background token refresh task")
    except Exception as e:
        logger.error(f"Failed to start background token refresh: {e}")
    
    # Start background artifact cleanup task
    try:
        asyncio.create_task(background_artifact_cleanup())
        logger.info("Started background artifact cleanup task")
    except Exception as e:
        logger.error(f"Failed to start artifact cleanup: {e}")
    
    logger.info("Kroger MCP Server started successfully on port 9004 with bulletproof token management")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown with token persistence"""
    logger.info("Shutting down Kroger MCP Server...")
    
    # Cancel background refresh task
    if token_refresh_task and not token_refresh_task.done():
        token_refresh_task.cancel()
        try:
            await token_refresh_task
        except asyncio.CancelledError:
            pass
        logger.info("Cancelled background token refresh task")
    
    # Save current tokens to file
    try:
        save_tokens_to_file(token_cache, client_credentials_token)
        logger.info("Saved tokens to persistent storage on shutdown")
    except Exception as e:
        logger.error(f"Failed to save tokens on shutdown: {e}")
    
    logger.info("Kroger MCP Server shutdown complete")


if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 9004))
    
    uvicorn.run(
        "kroger_mcp_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload to avoid conflicts
        log_level="info"
    )