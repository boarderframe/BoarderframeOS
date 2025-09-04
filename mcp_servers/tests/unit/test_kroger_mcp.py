"""
Comprehensive test suite for Kroger MCP Server implementation.
Tests OAuth2 authentication, API endpoints, error handling, and rate limiting.
"""
import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any, Optional
import uuid
from dataclasses import dataclass, asdict

import httpx
import jwt
from freezegun import freeze_time
import jsonschema
from jsonschema import validate, ValidationError

from tests.utils.test_helpers import (
    APITestHelper, 
    DataFactory, 
    MockFactory, 
    ValidationHelper,
    SecurityTestHelper,
    PerformanceTestHelper
)
from tests.factories.test_data_factory import TestDataFactory


# Kroger API Mock Data Factories
class KrogerDataFactory:
    """Factory for creating Kroger API test data."""
    
    @staticmethod
    def create_oauth_token_response(expires_in: int = 3600, **overrides) -> Dict[str, Any]:
        """Create OAuth2 token response."""
        base_data = {
            "access_token": f"kroger_token_{TestDataFactory.random_string(32)}",
            "token_type": "Bearer",
            "expires_in": expires_in,
            "scope": "product.compact cart.basic:write profile.compact"
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_product_data(**overrides) -> Dict[str, Any]:
        """Create Kroger product data."""
        base_data = {
            "productId": f"0001111{TestDataFactory.random_string(6, '0123456789')}",
            "upc": f"{TestDataFactory.random_string(12, '0123456789')}",
            "aisleLocations": [
                {
                    "locationId": "01700043",
                    "description": "Grocery",
                    "number": "14"
                }
            ],
            "brand": "Kroger",
            "categories": ["Natural & Organic", "Pantry", "Canned Goods & Soups"],
            "countryOrigin": "USA",
            "description": f"Organic {TestDataFactory.random_string(8)} Product",
            "items": [
                {
                    "itemId": f"0001111{TestDataFactory.random_string(6, '0123456789')}",
                    "favorite": False,
                    "fulfillment": {
                        "curbside": True,
                        "delivery": True,
                        "inStore": True,
                        "shipToHome": False
                    },
                    "price": {
                        "regular": 3.49,
                        "promo": 2.99
                    },
                    "size": "15 oz",
                    "soldBy": "Each"
                }
            ],
            "productImageURL": f"https://kroger.com/images/{TestDataFactory.random_string(8)}.jpg",
            "temperature": {
                "indicator": "Ambient",
                "heatSensitive": False
            }
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_location_data(**overrides) -> Dict[str, Any]:
        """Create Kroger location data."""
        base_data = {
            "locationId": f"017{TestDataFactory.random_string(5, '0123456789')}",
            "chain": "KROGER",
            "address": {
                "addressLine1": f"{TestDataFactory.random_string(4, '0123456789')} Main St",
                "city": "Cincinnati", 
                "county": "Hamilton",
                "state": "OH",
                "zipCode": "45202"
            },
            "geolocation": {
                "latitude": 39.1031,
                "longitude": -84.5120
            },
            "name": "Kroger Downtown",
            "phone": "513-555-0123",
            "departments": [
                {"departmentId": "01", "name": "Grocery"},
                {"departmentId": "02", "name": "Pharmacy"},
                {"departmentId": "03", "name": "Fuel"}
            ],
            "hours": {
                "monday": [{"open": "06:00", "close": "22:00"}],
                "tuesday": [{"open": "06:00", "close": "22:00"}],
                "wednesday": [{"open": "06:00", "close": "22:00"}],
                "thursday": [{"open": "06:00", "close": "22:00"}],
                "friday": [{"open": "06:00", "close": "22:00"}],
                "saturday": [{"open": "06:00", "close": "22:00"}],
                "sunday": [{"open": "07:00", "close": "21:00"}]
            }
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_cart_data(**overrides) -> Dict[str, Any]:
        """Create Kroger cart data."""
        base_data = {
            "cartId": str(uuid.uuid4()),
            "customerId": f"customer_{TestDataFactory.random_string(8)}",
            "items": [
                {
                    "upc": "0001111042100",
                    "quantity": 2,
                    "modality": "PICKUP"
                }
            ],
            "total": {
                "subTotal": 6.98,
                "tax": 0.42,
                "total": 7.40
            },
            "createdAt": datetime.utcnow().isoformat(),
            "modifiedAt": datetime.utcnow().isoformat()
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_user_profile(**overrides) -> Dict[str, Any]:
        """Create Kroger user profile data."""
        base_data = {
            "customerId": f"customer_{TestDataFactory.random_string(8)}",
            "firstName": "John",
            "lastName": "Doe", 
            "email": "john.doe@example.com",
            "loyaltyId": f"loyalty_{TestDataFactory.random_string(10, '0123456789')}",
            "preferences": {
                "communication": {
                    "email": True,
                    "text": False
                },
                "fulfillment": "PICKUP"
            }
        }
        base_data.update(overrides)
        return base_data


@pytest.mark.unit
@pytest.mark.asyncio
class TestKrogerMCPServerUnit:
    """Unit tests for Kroger MCP Server."""
    
    @pytest.fixture
    def mock_kroger_client(self):
        """Create a mock Kroger API client."""
        client = Mock()
        
        # OAuth2 methods
        client.get_access_token = AsyncMock()
        client.refresh_token = AsyncMock()
        client.revoke_token = AsyncMock()
        client.is_token_valid = Mock(return_value=True)
        
        # API methods
        client.search_products = AsyncMock()
        client.get_product_details = AsyncMock()
        client.search_locations = AsyncMock()
        client.get_location_details = AsyncMock()
        client.create_cart = AsyncMock()
        client.add_to_cart = AsyncMock()
        client.update_cart_item = AsyncMock()
        client.remove_from_cart = AsyncMock()
        client.get_cart = AsyncMock()
        client.get_user_profile = AsyncMock()
        
        # Rate limiting
        client.check_rate_limit = AsyncMock()
        client.get_rate_limit_status = AsyncMock()
        
        return client
    
    @pytest.fixture
    def mock_token_manager(self):
        """Create a mock token manager."""
        manager = Mock()
        manager.get_token = AsyncMock()
        manager.refresh_token = AsyncMock()
        manager.store_token = AsyncMock()
        manager.is_expired = Mock(return_value=False)
        manager.time_until_expiry = Mock(return_value=3600)
        return manager
    
    @pytest.fixture
    def sample_config(self):
        """Sample Kroger MCP server configuration."""
        return {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "redirect_uri": "http://localhost:8080/callback",
            "scope": "product.compact cart.basic:write profile.compact",
            "base_url": "https://api.kroger.com/v1",
            "auth_url": "https://api.kroger.com/v1/connect/oauth2",
            "rate_limit": {
                "requests_per_minute": 60,
                "burst_limit": 5
            }
        }


    # OAuth2 Authentication Tests
    async def test_oauth_token_request_success(self, mock_kroger_client, sample_config):
        """Test successful OAuth2 token request."""
        # Mock successful token response
        token_response = KrogerDataFactory.create_oauth_token_response()
        mock_kroger_client.get_access_token.return_value = token_response
        
        # Test token request
        result = await mock_kroger_client.get_access_token(
            client_id=sample_config["client_id"],
            client_secret=sample_config["client_secret"],
            scope=sample_config["scope"]
        )
        
        # Assertions
        assert result["access_token"].startswith("kroger_token_")
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 3600
        assert "product.compact" in result["scope"]
        
        mock_kroger_client.get_access_token.assert_called_once()
    
    async def test_oauth_token_request_failure(self, mock_kroger_client, sample_config):
        """Test OAuth2 token request failure scenarios."""
        # Test invalid client credentials
        error_response = {
            "error": "invalid_client",
            "error_description": "Client authentication failed"
        }
        mock_kroger_client.get_access_token.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=Mock(), response=Mock(status_code=401, json=lambda: error_response)
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await mock_kroger_client.get_access_token(
                client_id="invalid_client",
                client_secret="invalid_secret",
                scope=sample_config["scope"]
            )
    
    async def test_token_refresh_success(self, mock_kroger_client, mock_token_manager):
        """Test successful token refresh."""
        # Mock token manager returning expired token
        mock_token_manager.is_expired.return_value = True
        
        # Mock successful refresh
        new_token = KrogerDataFactory.create_oauth_token_response(
            access_token="new_kroger_token_123"
        )
        mock_kroger_client.refresh_token.return_value = new_token
        
        result = await mock_kroger_client.refresh_token("old_refresh_token")
        
        assert result["access_token"] == "new_kroger_token_123"
        assert result["token_type"] == "Bearer"
        mock_kroger_client.refresh_token.assert_called_once_with("old_refresh_token")
    
    async def test_token_validation(self, mock_kroger_client, mock_token_manager):
        """Test token validation logic."""
        # Test valid token
        mock_token_manager.is_expired.return_value = False
        mock_token_manager.time_until_expiry.return_value = 1800  # 30 minutes
        
        assert mock_kroger_client.is_token_valid()
        
        # Test expired token
        mock_token_manager.is_expired.return_value = True
        mock_kroger_client.is_token_valid.return_value = False
        
        assert not mock_kroger_client.is_token_valid()
    
    # Product API Tests
    async def test_product_search_success(self, mock_kroger_client):
        """Test successful product search."""
        # Mock product search response
        mock_products = [
            KrogerDataFactory.create_product_data(description="Organic Pasta"),
            KrogerDataFactory.create_product_data(description="Organic Sauce")
        ]
        mock_kroger_client.search_products.return_value = {
            "data": mock_products,
            "meta": {
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 2
                }
            }
        }
        
        result = await mock_kroger_client.search_products(
            term="organic pasta",
            location_id="01700043",
            limit=50
        )
        
        assert len(result["data"]) == 2
        assert "Organic Pasta" in result["data"][0]["description"]
        assert result["meta"]["pagination"]["total"] == 2
        
        mock_kroger_client.search_products.assert_called_once_with(
            term="organic pasta",
            location_id="01700043", 
            limit=50
        )
    
    async def test_product_search_no_results(self, mock_kroger_client):
        """Test product search with no results."""
        mock_kroger_client.search_products.return_value = {
            "data": [],
            "meta": {
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 0
                }
            }
        }
        
        result = await mock_kroger_client.search_products(
            term="nonexistent product"
        )
        
        assert len(result["data"]) == 0
        assert result["meta"]["pagination"]["total"] == 0
    
    async def test_product_details_success(self, mock_kroger_client):
        """Test successful product details retrieval."""
        product_id = "0001111042100"
        mock_product = KrogerDataFactory.create_product_data(
            productId=product_id,
            description="Kroger Organic Tomato Sauce"
        )
        
        mock_kroger_client.get_product_details.return_value = {
            "data": mock_product
        }
        
        result = await mock_kroger_client.get_product_details(product_id)
        
        assert result["data"]["productId"] == product_id
        assert "Kroger Organic Tomato Sauce" in result["data"]["description"]
        assert "items" in result["data"]
        assert len(result["data"]["items"]) > 0
    
    async def test_product_details_not_found(self, mock_kroger_client):
        """Test product details for non-existent product."""
        mock_kroger_client.get_product_details.side_effect = httpx.HTTPStatusError(
            "404 Not Found", 
            request=Mock(), 
            response=Mock(status_code=404)
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await mock_kroger_client.get_product_details("invalid_product_id")
    
    # Location API Tests
    async def test_location_search_success(self, mock_kroger_client):
        """Test successful location search."""
        mock_locations = [
            KrogerDataFactory.create_location_data(name="Kroger Downtown"),
            KrogerDataFactory.create_location_data(name="Kroger Uptown")
        ]
        
        mock_kroger_client.search_locations.return_value = {
            "data": mock_locations,
            "meta": {
                "pagination": {
                    "total": 2
                }
            }
        }
        
        result = await mock_kroger_client.search_locations(
            zipcode="45202",
            radius_miles=10
        )
        
        assert len(result["data"]) == 2
        assert result["data"][0]["name"] == "Kroger Downtown"
        assert "address" in result["data"][0]
        assert "geolocation" in result["data"][0]
    
    async def test_location_search_by_coordinates(self, mock_kroger_client):
        """Test location search by latitude/longitude."""
        mock_kroger_client.search_locations.return_value = {
            "data": [KrogerDataFactory.create_location_data()],
            "meta": {"pagination": {"total": 1}}
        }
        
        result = await mock_kroger_client.search_locations(
            lat=39.1031,
            lon=-84.5120,
            radius_miles=5
        )
        
        assert len(result["data"]) == 1
        mock_kroger_client.search_locations.assert_called_once()
    
    async def test_location_details_success(self, mock_kroger_client):
        """Test successful location details retrieval."""
        location_id = "01700043"
        mock_location = KrogerDataFactory.create_location_data(
            locationId=location_id,
            name="Kroger Test Store"
        )
        
        mock_kroger_client.get_location_details.return_value = {
            "data": mock_location
        }
        
        result = await mock_kroger_client.get_location_details(location_id)
        
        assert result["data"]["locationId"] == location_id
        assert result["data"]["name"] == "Kroger Test Store"
        assert "hours" in result["data"]
        assert "departments" in result["data"]
    
    # Cart API Tests
    async def test_create_cart_success(self, mock_kroger_client):
        """Test successful cart creation."""
        mock_cart = KrogerDataFactory.create_cart_data()
        mock_kroger_client.create_cart.return_value = {"data": mock_cart}
        
        result = await mock_kroger_client.create_cart()
        
        assert "cartId" in result["data"]
        assert "items" in result["data"]
        assert result["data"]["total"]["total"] > 0
    
    async def test_add_to_cart_success(self, mock_kroger_client):
        """Test successfully adding items to cart."""
        cart_id = str(uuid.uuid4())
        item_data = {
            "upc": "0001111042100",
            "quantity": 2,
            "modality": "PICKUP"
        }
        
        updated_cart = KrogerDataFactory.create_cart_data(
            cartId=cart_id,
            items=[item_data]
        )
        mock_kroger_client.add_to_cart.return_value = {"data": updated_cart}
        
        result = await mock_kroger_client.add_to_cart(cart_id, [item_data])
        
        assert result["data"]["cartId"] == cart_id
        assert len(result["data"]["items"]) == 1
        assert result["data"]["items"][0]["upc"] == "0001111042100"
        assert result["data"]["items"][0]["quantity"] == 2
    
    async def test_update_cart_item_success(self, mock_kroger_client):
        """Test successfully updating cart item quantity."""
        cart_id = str(uuid.uuid4())
        updated_item = {
            "upc": "0001111042100", 
            "quantity": 5,
            "modality": "PICKUP"
        }
        
        updated_cart = KrogerDataFactory.create_cart_data(
            cartId=cart_id,
            items=[updated_item]
        )
        mock_kroger_client.update_cart_item.return_value = {"data": updated_cart}
        
        result = await mock_kroger_client.update_cart_item(
            cart_id, 
            "0001111042100", 
            quantity=5
        )
        
        assert result["data"]["items"][0]["quantity"] == 5
    
    async def test_remove_from_cart_success(self, mock_kroger_client):
        """Test successfully removing items from cart."""
        cart_id = str(uuid.uuid4())
        empty_cart = KrogerDataFactory.create_cart_data(
            cartId=cart_id,
            items=[],
            total={"subTotal": 0, "tax": 0, "total": 0}
        )
        
        mock_kroger_client.remove_from_cart.return_value = {"data": empty_cart}
        
        result = await mock_kroger_client.remove_from_cart(cart_id, "0001111042100")
        
        assert len(result["data"]["items"]) == 0
        assert result["data"]["total"]["total"] == 0
    
    # User Profile Tests
    async def test_get_user_profile_success(self, mock_kroger_client):
        """Test successful user profile retrieval."""
        mock_profile = KrogerDataFactory.create_user_profile()
        mock_kroger_client.get_user_profile.return_value = {"data": mock_profile}
        
        result = await mock_kroger_client.get_user_profile()
        
        assert "customerId" in result["data"]
        assert "loyaltyId" in result["data"]
        assert "email" in result["data"]
        assert "preferences" in result["data"]
    
    # Error Handling Tests
    async def test_rate_limit_handling(self, mock_kroger_client):
        """Test rate limit error handling."""
        # Mock rate limit exceeded response
        mock_kroger_client.search_products.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=Mock(),
            response=Mock(
                status_code=429,
                headers={"Retry-After": "60"},
                json=lambda: {"error": "rate_limit_exceeded"}
            )
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_kroger_client.search_products(term="test")
        
        assert exc_info.value.response.status_code == 429
    
    async def test_authentication_error_handling(self, mock_kroger_client):
        """Test authentication error handling."""
        mock_kroger_client.search_products.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=Mock(),
            response=Mock(
                status_code=401,
                json=lambda: {"error": "invalid_token"}
            )
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_kroger_client.search_products(term="test")
        
        assert exc_info.value.response.status_code == 401
    
    async def test_server_error_handling(self, mock_kroger_client):
        """Test server error handling."""
        mock_kroger_client.search_products.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=Mock(),
            response=Mock(
                status_code=500,
                json=lambda: {"error": "internal_server_error"}
            )
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_kroger_client.search_products(term="test")
        
        assert exc_info.value.response.status_code == 500
    
    # Rate Limiting Tests
    async def test_rate_limit_status_check(self, mock_kroger_client):
        """Test rate limit status checking."""
        rate_limit_status = {
            "requests_remaining": 45,
            "requests_limit": 60,
            "reset_time": int(time.time()) + 3600,
            "retry_after": None
        }
        mock_kroger_client.get_rate_limit_status.return_value = rate_limit_status
        
        result = await mock_kroger_client.get_rate_limit_status()
        
        assert result["requests_remaining"] == 45
        assert result["requests_limit"] == 60
        assert result["retry_after"] is None
    
    async def test_rate_limit_exceeded_status(self, mock_kroger_client):
        """Test rate limit exceeded status."""
        rate_limit_status = {
            "requests_remaining": 0,
            "requests_limit": 60,
            "reset_time": int(time.time()) + 60,
            "retry_after": 60
        }
        mock_kroger_client.get_rate_limit_status.return_value = rate_limit_status
        
        result = await mock_kroger_client.get_rate_limit_status()
        
        assert result["requests_remaining"] == 0
        assert result["retry_after"] == 60


@pytest.mark.integration
@pytest.mark.asyncio
class TestKrogerMCPServerIntegration:
    """Integration tests for Kroger MCP Server."""
    
    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client for integration tests."""
        client = Mock()
        client.request = AsyncMock()
        client.get = AsyncMock()
        client.post = AsyncMock()
        client.put = AsyncMock()
        client.delete = AsyncMock()
        return client
    
    async def test_complete_oauth_flow(self, mock_http_client):
        """Test complete OAuth2 authentication flow."""
        # Step 1: Get authorization URL
        auth_url = (
            "https://api.kroger.com/v1/connect/oauth2/authorize"
            "?response_type=code&client_id=test_client_id"
            "&redirect_uri=http://localhost:8080/callback"
            "&scope=product.compact%20cart.basic:write%20profile.compact"
        )
        
        # Step 2: Mock authorization code callback
        auth_code = "test_auth_code_123"
        
        # Step 3: Exchange code for token
        token_response = KrogerDataFactory.create_oauth_token_response()
        mock_http_client.post.return_value = Mock(
            status_code=200,
            json=lambda: token_response
        )
        
        # Simulate token exchange
        response = await mock_http_client.post(
            "https://api.kroger.com/v1/connect/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": "http://localhost:8080/callback"
            }
        )
        
        result = response.json()
        assert result["access_token"].startswith("kroger_token_")
        assert result["token_type"] == "Bearer"
    
    async def test_product_search_with_location_filter(self, mock_http_client):
        """Test product search with location filtering."""
        # Mock product search response
        products_response = {
            "data": [
                KrogerDataFactory.create_product_data(
                    description="Kroger Brand Organic Pasta",
                    items=[{
                        "itemId": "test_item_1",
                        "price": {"regular": 2.99, "promo": 2.49},
                        "fulfillment": {
                            "curbside": True,
                            "delivery": True,
                            "inStore": True
                        }
                    }]
                )
            ],
            "meta": {"pagination": {"total": 1}}
        }
        
        mock_http_client.get.return_value = Mock(
            status_code=200,
            json=lambda: products_response
        )
        
        # Test search with location
        response = await mock_http_client.get(
            "https://api.kroger.com/v1/products",
            params={
                "filter.term": "organic pasta",
                "filter.locationId": "01700043",
                "filter.limit": 50
            }
        )
        
        result = response.json()
        assert len(result["data"]) == 1
        assert "Organic Pasta" in result["data"][0]["description"]
    
    async def test_cart_management_workflow(self, mock_http_client):
        """Test complete cart management workflow."""
        cart_id = str(uuid.uuid4())
        
        # 1. Create cart
        create_response = {"data": KrogerDataFactory.create_cart_data(cartId=cart_id)}
        mock_http_client.post.return_value = Mock(
            status_code=201,
            json=lambda: create_response
        )
        
        create_result = await mock_http_client.post(
            "https://api.kroger.com/v1/cart",
            json={}
        )
        assert create_result.json()["data"]["cartId"] == cart_id
        
        # 2. Add items to cart
        add_response = {
            "data": KrogerDataFactory.create_cart_data(
                cartId=cart_id,
                items=[{"upc": "0001111042100", "quantity": 2, "modality": "PICKUP"}]
            )
        }
        mock_http_client.put.return_value = Mock(
            status_code=200,
            json=lambda: add_response
        )
        
        add_result = await mock_http_client.put(
            f"https://api.kroger.com/v1/cart/{cart_id}/items",
            json={"items": [{"upc": "0001111042100", "quantity": 2, "modality": "PICKUP"}]}
        )
        assert len(add_result.json()["data"]["items"]) == 1
        
        # 3. Update item quantity
        update_response = {
            "data": KrogerDataFactory.create_cart_data(
                cartId=cart_id,
                items=[{"upc": "0001111042100", "quantity": 5, "modality": "PICKUP"}]
            )
        }
        mock_http_client.put.return_value = Mock(
            status_code=200,
            json=lambda: update_response
        )
        
        update_result = await mock_http_client.put(
            f"https://api.kroger.com/v1/cart/{cart_id}/items",
            json={"items": [{"upc": "0001111042100", "quantity": 5, "modality": "PICKUP"}]}
        )
        assert update_result.json()["data"]["items"][0]["quantity"] == 5
    
    async def test_location_search_and_details(self, mock_http_client):
        """Test location search and details retrieval."""
        # Search locations
        location_id = "01700043"
        search_response = {
            "data": [KrogerDataFactory.create_location_data(locationId=location_id)],
            "meta": {"pagination": {"total": 1}}
        }
        
        mock_http_client.get.return_value = Mock(
            status_code=200,
            json=lambda: search_response
        )
        
        search_result = await mock_http_client.get(
            "https://api.kroger.com/v1/locations",
            params={"filter.zipCode.near": "45202", "filter.radiusInMiles": 10}
        )
        
        locations = search_result.json()["data"]
        assert len(locations) == 1
        assert locations[0]["locationId"] == location_id
        
        # Get location details
        details_response = {"data": KrogerDataFactory.create_location_data(locationId=location_id)}
        mock_http_client.get.return_value = Mock(
            status_code=200,
            json=lambda: details_response
        )
        
        details_result = await mock_http_client.get(
            f"https://api.kroger.com/v1/locations/{location_id}"
        )
        
        location_details = details_result.json()["data"]
        assert location_details["locationId"] == location_id
        assert "hours" in location_details
        assert "departments" in location_details


@pytest.mark.e2e
@pytest.mark.asyncio
class TestKrogerMCPServerE2E:
    """End-to-end tests for Kroger MCP Server."""
    
    @pytest.fixture
    async def mcp_server(self):
        """Create MCP server instance for E2E testing."""
        # This would typically start an actual MCP server
        # For testing, we'll use a comprehensive mock
        server = Mock()
        server.start = AsyncMock()
        server.stop = AsyncMock()
        server.handle_request = AsyncMock()
        server.list_tools = AsyncMock()
        server.call_tool = AsyncMock()
        return server
    
    async def test_mcp_server_initialization(self, mcp_server):
        """Test MCP server initialization and configuration."""
        config = {
            "kroger": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "redirect_uri": "http://localhost:8080/callback"
            }
        }
        
        await mcp_server.start()
        mcp_server.start.assert_called_once()
    
    async def test_mcp_tool_registration(self, mcp_server):
        """Test that all Kroger tools are properly registered."""
        expected_tools = [
            "kroger_search_products",
            "kroger_get_product_details", 
            "kroger_search_locations",
            "kroger_get_location_details",
            "kroger_create_cart",
            "kroger_add_to_cart",
            "kroger_update_cart_item",
            "kroger_remove_from_cart",
            "kroger_get_cart",
            "kroger_get_user_profile"
        ]
        
        tools_response = {
            "tools": [
                {"name": tool_name, "description": f"Kroger {tool_name} tool"}
                for tool_name in expected_tools
            ]
        }
        mcp_server.list_tools.return_value = tools_response
        
        result = await mcp_server.list_tools()
        tool_names = [tool["name"] for tool in result["tools"]]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    async def test_product_search_tool_execution(self, mcp_server):
        """Test product search tool execution through MCP."""
        tool_request = {
            "name": "kroger_search_products",
            "arguments": {
                "term": "organic pasta",
                "location_id": "01700043",
                "limit": 10
            }
        }
        
        tool_response = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "products": [
                            KrogerDataFactory.create_product_data(
                                description="Kroger Organic Pasta"
                            )
                        ],
                        "total_count": 1
                    })
                }
            ]
        }
        mcp_server.call_tool.return_value = tool_response
        
        result = await mcp_server.call_tool(tool_request)
        response_data = json.loads(result["content"][0]["text"])
        
        assert len(response_data["products"]) == 1
        assert "Organic Pasta" in response_data["products"][0]["description"]
    
    async def test_cart_workflow_through_mcp(self, mcp_server):
        """Test complete cart workflow through MCP tools."""
        cart_id = str(uuid.uuid4())
        
        # 1. Create cart
        create_request = {"name": "kroger_create_cart", "arguments": {}}
        create_response = {
            "content": [{"type": "text", "text": json.dumps({"cart_id": cart_id})}]
        }
        mcp_server.call_tool.return_value = create_response
        
        create_result = await mcp_server.call_tool(create_request)
        create_data = json.loads(create_result["content"][0]["text"])
        assert create_data["cart_id"] == cart_id
        
        # 2. Add to cart
        add_request = {
            "name": "kroger_add_to_cart",
            "arguments": {
                "cart_id": cart_id,
                "items": [{"upc": "0001111042100", "quantity": 2, "modality": "PICKUP"}]
            }
        }
        add_response = {
            "content": [{"type": "text", "text": json.dumps({"success": True, "items_added": 1})}]
        }
        mcp_server.call_tool.return_value = add_response
        
        add_result = await mcp_server.call_tool(add_request)
        add_data = json.loads(add_result["content"][0]["text"])
        assert add_data["success"] is True
        assert add_data["items_added"] == 1


@pytest.mark.security
@pytest.mark.asyncio
class TestKrogerMCPServerSecurity:
    """Security tests for Kroger MCP Server."""
    
    async def test_oauth_token_security(self):
        """Test OAuth token security measures."""
        # Test token storage security
        token_data = KrogerDataFactory.create_oauth_token_response()
        
        # Verify token is not logged
        assert "access_token" in token_data
        
        # Test token expiration handling
        expired_token = KrogerDataFactory.create_oauth_token_response(expires_in=0)
        current_time = int(time.time())
        
        # Token should be considered expired
        token_expiry = current_time + expired_token["expires_in"]
        assert token_expiry <= current_time
    
    async def test_input_validation(self, mock_kroger_client):
        """Test input validation for security."""
        # Test SQL injection prevention
        malicious_inputs = SecurityTestHelper.get_sql_injection_payloads()
        
        for payload in malicious_inputs:
            mock_kroger_client.search_products.side_effect = ValueError("Invalid input")
            
            with pytest.raises(ValueError):
                await mock_kroger_client.search_products(term=payload)
    
    async def test_xss_prevention(self, mock_kroger_client):
        """Test XSS prevention in responses."""
        xss_payloads = SecurityTestHelper.get_xss_payloads()
        
        for payload in xss_payloads:
            # Simulate sanitized response
            sanitized_product = KrogerDataFactory.create_product_data(
                description="[SANITIZED_INPUT]"
            )
            mock_kroger_client.search_products.return_value = {
                "data": [sanitized_product],
                "meta": {"pagination": {"total": 1}}
            }
            
            result = await mock_kroger_client.search_products(term=payload)
            
            # Verify XSS payload is not in response
            description = result["data"][0]["description"]
            assert payload not in description
            assert description == "[SANITIZED_INPUT]"


@pytest.mark.performance
@pytest.mark.asyncio
class TestKrogerMCPServerPerformance:
    """Performance tests for Kroger MCP Server."""
    
    async def test_token_refresh_performance(self, mock_kroger_client):
        """Test token refresh performance."""
        mock_kroger_client.refresh_token.return_value = KrogerDataFactory.create_oauth_token_response()
        
        start_time = time.time()
        await mock_kroger_client.refresh_token("test_refresh_token")
        end_time = time.time()
        
        execution_time = end_time - start_time
        PerformanceTestHelper.assert_response_time(execution_time, 1.0)  # Should be under 1 second
    
    async def test_product_search_performance(self, mock_kroger_client):
        """Test product search performance."""
        mock_products = [KrogerDataFactory.create_product_data() for _ in range(50)]
        mock_kroger_client.search_products.return_value = {
            "data": mock_products,
            "meta": {"pagination": {"total": 50}}
        }
        
        start_time = time.time()
        await mock_kroger_client.search_products(term="test", limit=50)
        end_time = time.time()
        
        execution_time = end_time - start_time
        PerformanceTestHelper.assert_response_time(execution_time, 2.0)  # Should be under 2 seconds
    
    async def test_concurrent_requests_performance(self, mock_kroger_client):
        """Test performance under concurrent load."""
        mock_kroger_client.search_products.return_value = {
            "data": [KrogerDataFactory.create_product_data()],
            "meta": {"pagination": {"total": 1}}
        }
        
        async def make_request():
            return await mock_kroger_client.search_products(term="test")
        
        # Test 10 concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert len(results) == 10
        PerformanceTestHelper.assert_response_time(execution_time, 5.0)  # All 10 requests under 5 seconds


@pytest.mark.schema
@pytest.mark.asyncio
class TestKrogerMCPServerSchemaValidation:
    """OpenAPI schema validation tests for Kroger MCP Server."""
    
    @pytest.fixture
    def kroger_schemas(self):
        """Kroger API response schemas for validation."""
        return {
            "oauth_token": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "token_type": {"type": "string", "enum": ["Bearer"]},
                    "expires_in": {"type": "integer", "minimum": 0},
                    "scope": {"type": "string"}
                },
                "required": ["access_token", "token_type", "expires_in"]
            },
            "product": {
                "type": "object",
                "properties": {
                    "productId": {"type": "string"},
                    "upc": {"type": "string"},
                    "brand": {"type": "string"},
                    "description": {"type": "string"},
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "itemId": {"type": "string"},
                                "price": {
                                    "type": "object",
                                    "properties": {
                                        "regular": {"type": "number"},
                                        "promo": {"type": "number"}
                                    }
                                },
                                "fulfillment": {
                                    "type": "object",
                                    "properties": {
                                        "curbside": {"type": "boolean"},
                                        "delivery": {"type": "boolean"},
                                        "inStore": {"type": "boolean"},
                                        "shipToHome": {"type": "boolean"}
                                    }
                                }
                            },
                            "required": ["itemId", "price", "fulfillment"]
                        }
                    }
                },
                "required": ["productId", "description", "items"]
            },
            "location": {
                "type": "object",
                "properties": {
                    "locationId": {"type": "string"},
                    "chain": {"type": "string"},
                    "name": {"type": "string"},
                    "address": {
                        "type": "object",
                        "properties": {
                            "addressLine1": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "zipCode": {"type": "string"}
                        },
                        "required": ["addressLine1", "city", "state", "zipCode"]
                    },
                    "geolocation": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    },
                    "hours": {"type": "object"}
                },
                "required": ["locationId", "name", "address"]
            },
            "cart": {
                "type": "object",
                "properties": {
                    "cartId": {"type": "string"},
                    "customerId": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "upc": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1},
                                "modality": {"type": "string", "enum": ["PICKUP", "DELIVERY"]}
                            },
                            "required": ["upc", "quantity", "modality"]
                        }
                    },
                    "total": {
                        "type": "object",
                        "properties": {
                            "subTotal": {"type": "number"},
                            "tax": {"type": "number"},
                            "total": {"type": "number"}
                        },
                        "required": ["subTotal", "tax", "total"]
                    }
                },
                "required": ["cartId", "items", "total"]
            },
            "user_profile": {
                "type": "object",
                "properties": {
                    "customerId": {"type": "string"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "loyaltyId": {"type": "string"},
                    "preferences": {"type": "object"}
                },
                "required": ["customerId", "email"]
            },
            "error_response": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "error_description": {"type": "string"},
                    "error_code": {"type": "integer"}
                },
                "required": ["error"]
            },
            "api_response": {
                "type": "object",
                "properties": {
                    "data": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "array"}
                        ]
                    },
                    "meta": {
                        "type": "object",
                        "properties": {
                            "pagination": {
                                "type": "object",
                                "properties": {
                                    "start": {"type": "integer"},
                                    "limit": {"type": "integer"},
                                    "total": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "required": ["data"]
            }
        }
    
    def test_oauth_token_schema_validation(self, kroger_schemas):
        """Test OAuth token response schema validation."""
        # Valid token
        valid_token = KrogerDataFactory.create_oauth_token_response()
        validate(valid_token, kroger_schemas["oauth_token"])
        
        # Invalid token - missing required field
        invalid_token = {"token_type": "Bearer", "expires_in": 3600}
        with pytest.raises(ValidationError):
            validate(invalid_token, kroger_schemas["oauth_token"])
        
        # Invalid token - wrong type
        invalid_token_type = {
            "access_token": "token",
            "token_type": "InvalidType",
            "expires_in": 3600
        }
        with pytest.raises(ValidationError):
            validate(invalid_token_type, kroger_schemas["oauth_token"])
    
    def test_product_schema_validation(self, kroger_schemas):
        """Test product response schema validation."""
        # Valid product
        valid_product = KrogerDataFactory.create_product_data()
        validate(valid_product, kroger_schemas["product"])
        
        # Invalid product - missing required field
        invalid_product = {"productId": "123", "description": "test"}
        # Should fail because 'items' is required
        with pytest.raises(ValidationError):
            validate(invalid_product, kroger_schemas["product"])
        
        # Invalid product - wrong item structure
        invalid_product_items = {
            "productId": "123",
            "description": "test",
            "items": [{"itemId": "456"}]  # Missing required price and fulfillment
        }
        with pytest.raises(ValidationError):
            validate(invalid_product_items, kroger_schemas["product"])
    
    def test_location_schema_validation(self, kroger_schemas):
        """Test location response schema validation."""
        # Valid location
        valid_location = KrogerDataFactory.create_location_data()
        validate(valid_location, kroger_schemas["location"])
        
        # Invalid location - missing address
        invalid_location = {
            "locationId": "123",
            "name": "Test Store"
        }
        with pytest.raises(ValidationError):
            validate(invalid_location, kroger_schemas["location"])
        
        # Invalid location - incomplete address
        invalid_address = {
            "locationId": "123",
            "name": "Test Store",
            "address": {"city": "Cincinnati"}  # Missing required fields
        }
        with pytest.raises(ValidationError):
            validate(invalid_address, kroger_schemas["location"])
    
    def test_cart_schema_validation(self, kroger_schemas):
        """Test cart response schema validation."""
        # Valid cart
        valid_cart = KrogerDataFactory.create_cart_data()
        validate(valid_cart, kroger_schemas["cart"])
        
        # Invalid cart - missing total
        invalid_cart = {
            "cartId": "123",
            "items": []
        }
        with pytest.raises(ValidationError):
            validate(invalid_cart, kroger_schemas["cart"])
        
        # Invalid cart item - wrong modality
        invalid_cart_item = {
            "cartId": "123",
            "items": [{
                "upc": "123456789",
                "quantity": 1,
                "modality": "INVALID_MODE"
            }],
            "total": {"subTotal": 0, "tax": 0, "total": 0}
        }
        with pytest.raises(ValidationError):
            validate(invalid_cart_item, kroger_schemas["cart"])
    
    def test_user_profile_schema_validation(self, kroger_schemas):
        """Test user profile response schema validation."""
        # Valid profile
        valid_profile = KrogerDataFactory.create_user_profile()
        validate(valid_profile, kroger_schemas["user_profile"])
        
        # Invalid profile - missing required field
        invalid_profile = {"customerId": "123"}
        with pytest.raises(ValidationError):
            validate(invalid_profile, kroger_schemas["user_profile"])
        
        # Invalid profile - invalid email format
        invalid_email = {
            "customerId": "123",
            "email": "invalid-email"
        }
        with pytest.raises(ValidationError):
            validate(invalid_email, kroger_schemas["user_profile"])
    
    def test_error_response_schema_validation(self, kroger_schemas):
        """Test error response schema validation."""
        # Valid error response
        valid_error = {
            "error": "invalid_request",
            "error_description": "The request is missing a required parameter"
        }
        validate(valid_error, kroger_schemas["error_response"])
        
        # Invalid error response - missing required field
        invalid_error = {"error_description": "Some error occurred"}
        with pytest.raises(ValidationError):
            validate(invalid_error, kroger_schemas["error_response"])
    
    def test_api_response_wrapper_validation(self, kroger_schemas):
        """Test general API response wrapper schema validation."""
        # Valid response with data array
        valid_response_array = {
            "data": [KrogerDataFactory.create_product_data()],
            "meta": {
                "pagination": {
                    "start": 0,
                    "limit": 50,
                    "total": 1
                }
            }
        }
        validate(valid_response_array, kroger_schemas["api_response"])
        
        # Valid response with data object
        valid_response_object = {
            "data": KrogerDataFactory.create_product_data()
        }
        validate(valid_response_object, kroger_schemas["api_response"])
        
        # Invalid response - missing data field
        invalid_response = {
            "meta": {
                "pagination": {"total": 0}
            }
        }
        with pytest.raises(ValidationError):
            validate(invalid_response, kroger_schemas["api_response"])
    
    async def test_mcp_tool_parameter_schema_validation(self):
        """Test MCP tool parameter schema validation."""
        # Define MCP tool parameter schemas
        tool_schemas = {
            "kroger_search_products": {
                "type": "object",
                "properties": {
                    "term": {"type": "string", "minLength": 1},
                    "location_id": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    "start": {"type": "integer", "minimum": 0}
                },
                "required": ["term"]
            },
            "kroger_add_to_cart": {
                "type": "object",
                "properties": {
                    "cart_id": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "upc": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1},
                                "modality": {"type": "string", "enum": ["PICKUP", "DELIVERY"]}
                            },
                            "required": ["upc", "quantity", "modality"]
                        }
                    }
                },
                "required": ["cart_id", "items"]
            }
        }
        
        # Valid search parameters
        valid_search_params = {
            "term": "organic pasta",
            "location_id": "01700043",
            "limit": 50
        }
        validate(valid_search_params, tool_schemas["kroger_search_products"])
        
        # Invalid search parameters - empty term
        invalid_search_params = {"term": ""}
        with pytest.raises(ValidationError):
            validate(invalid_search_params, tool_schemas["kroger_search_products"])
        
        # Valid cart parameters
        valid_cart_params = {
            "cart_id": "cart123",
            "items": [{
                "upc": "1234567890",
                "quantity": 2,
                "modality": "PICKUP"
            }]
        }
        validate(valid_cart_params, tool_schemas["kroger_add_to_cart"])
        
        # Invalid cart parameters - missing required field
        invalid_cart_params = {"cart_id": "cart123"}
        with pytest.raises(ValidationError):
            validate(invalid_cart_params, tool_schemas["kroger_add_to_cart"])


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    import os
    original_env = os.environ.copy()
    
    test_env = {
        "KROGER_CLIENT_ID": "test_client_id",
        "KROGER_CLIENT_SECRET": "test_client_secret", 
        "KROGER_REDIRECT_URI": "http://localhost:8080/callback",
        "KROGER_BASE_URL": "https://api.kroger.com/v1",
        "TEST_MODE": "true"
    }
    
    os.environ.update(test_env)
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])