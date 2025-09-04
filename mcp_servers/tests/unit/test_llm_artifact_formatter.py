"""
Unit tests for LLM Artifact Formatter
Validates artifact formatting for Open WebUI rendering
"""

import pytest
import json
import re
from typing import List, Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.app.services.llm_artifact_formatter import (
    LLMArtifactFormatter,
    ArtifactResponseBuilder,
    ArtifactType,
    ResponsePattern,
    format_product_search_response,
    validate_artifact_response
)


class TestLLMArtifactFormatter:
    """Test suite for LLM Artifact Formatter"""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter instance"""
        return LLMArtifactFormatter()
    
    @pytest.fixture
    def sample_products(self):
        """Sample product data"""
        return [
            {
                "name": "Organic Whole Milk",
                "price": 4.99,
                "description": "Fresh organic whole milk from local farms"
            },
            {
                "name": "Almond Milk Unsweetened",
                "price": 3.49,
                "description": "Plant-based almond milk, no added sugar"
            },
            {
                "name": "Oat Milk Barista Edition",
                "price": 5.99,
                "description": "Creamy oat milk perfect for coffee"
            }
        ]
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML artifact"""
        return """<div class="product-grid">
            <div class="product-card">
                <h3>Test Product</h3>
                <p class="price">$9.99</p>
            </div>
        </div>"""
    
    def test_format_response_direct_html(self, formatter, sample_html):
        """Test direct HTML response pattern"""
        response = formatter.format_response(
            message="Found products",
            artifact_html=sample_html,
            pattern=ResponsePattern.DIRECT_HTML
        )
        
        assert "Found products" in response
        assert "```html" in response
        assert sample_html in response
        assert response.count("```") >= 2
    
    def test_format_response_structured_json(self, formatter, sample_html):
        """Test structured JSON response pattern"""
        response = formatter.format_response(
            message="Found products",
            artifact_html=sample_html,
            pattern=ResponsePattern.STRUCTURED_JSON
        )
        
        # Should be valid JSON
        data = json.loads(response)
        assert data["message"] == "Found products"
        assert data["artifact"]["type"] == "html"
        assert data["artifact"]["content"] == sample_html
    
    def test_format_response_hybrid_natural(self, formatter, sample_html):
        """Test hybrid natural language response pattern"""
        response = formatter.format_response(
            message="Found products",
            artifact_html=sample_html,
            context="Available for pickup",
            pattern=ResponsePattern.HYBRID_NATURAL
        )
        
        assert "Found products" in response
        assert "**Visual Display:**" in response
        assert "```html" in response
        assert "Available for pickup" in response
    
    def test_format_response_minimal_token(self, formatter, sample_html):
        """Test minimal token response pattern"""
        response = formatter.format_response(
            message="Results",
            artifact_html=sample_html,
            pattern=ResponsePattern.MINIMAL_TOKEN
        )
        
        # Should be very concise
        assert len(response) < len(sample_html) + 50
        assert "```html" in response
        assert "Results" in response
    
    def test_optimize_html(self, formatter):
        """Test HTML optimization for token efficiency"""
        verbose_html = """
        <div style="background-color: #ffffff; padding: 16px; margin: 8px;">
            <h3 style="color: #333333; font-size: 18px;">Product Name</h3>
            <p style="color: #666666; font-size: 14px;">Description here</p>
            <!-- This is a comment -->
        </div>
        """
        
        optimized = formatter._optimize_html(verbose_html)
        
        # Should remove extra whitespace
        assert "\n" not in optimized
        assert "  " not in optimized
        
        # Should remove comments
        assert "<!--" not in optimized
        
        # Should be shorter
        assert len(optimized) < len(verbose_html)
    
    def test_convert_inline_styles(self, formatter):
        """Test inline style to class conversion"""
        html_with_styles = '''<div style="color: red;">Text</div><p style="color: red;">More</p>'''
        
        converted = formatter._convert_inline_styles(html_with_styles)
        
        # Should have style tag
        assert "<style>" in converted
        
        # Should have class instead of style
        assert 'class="s' in converted
        
        # Should not have inline styles
        assert 'style="color: red;"' not in converted
    
    def test_shorten_class_names(self, formatter):
        """Test CSS class name shortening"""
        html = '''<div class="product-card"><p class="description">Text</p></div>'''
        
        shortened = formatter._shorten_class_names(html)
        
        assert 'class="pc"' in shortened
        assert 'class="d"' in shortened
        assert "product-card" not in shortened
        assert "description" not in shortened
    
    def test_enforce_token_limit(self, formatter):
        """Test token limit enforcement"""
        # Create a very long response
        long_message = "x" * 5000
        artifact = "<div>Content</div>"
        
        response = formatter.format_response(
            message=long_message,
            artifact_html=artifact,
            optimize_tokens=True
        )
        
        # Estimate tokens
        estimated_tokens = len(response) / formatter.CHARS_PER_TOKEN
        
        # Should be within limits
        assert estimated_tokens <= formatter.MAX_TOKENS_RECOMMENDED + 100  # Some buffer
        
        # Should still contain artifact
        assert "```html" in response
        assert "Content" in response
    
    def test_create_display_instructions_minimal(self, formatter, sample_html):
        """Test minimal display instructions"""
        instructions = formatter.create_display_instructions(
            sample_html,
            instruction_level="minimal"
        )
        
        assert instructions == f"```html\n{sample_html}\n```"
    
    def test_create_display_instructions_concise(self, formatter, sample_html):
        """Test concise display instructions"""
        instructions = formatter.create_display_instructions(
            sample_html,
            instruction_level="concise"
        )
        
        assert "Include this in your response:" in instructions
        assert "```html" in instructions
        assert sample_html in instructions
    
    def test_create_display_instructions_detailed(self, formatter, sample_html):
        """Test detailed display instructions"""
        instructions = formatter.create_display_instructions(
            sample_html,
            instruction_level="detailed"
        )
        
        assert "ARTIFACT DISPLAY INSTRUCTIONS:" in instructions
        assert "Do NOT modify" in instructions
        assert "```html" in instructions
        assert sample_html in instructions
    
    def test_validate_response_valid(self, formatter, sample_html):
        """Test validation of valid response"""
        valid_response = f"Here are the results:\n\n```html\n{sample_html}\n```"
        
        is_valid, issues = formatter.validate_response(valid_response)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_response_missing_artifact(self, formatter):
        """Test validation of response without artifact"""
        invalid_response = "Here are the results but no HTML artifact"
        
        is_valid, issues = formatter.validate_response(invalid_response)
        
        assert is_valid is False
        assert "Missing ```html code block" in issues
    
    def test_validate_response_unclosed_block(self, formatter):
        """Test validation of response with unclosed code block"""
        invalid_response = "Results:\n```html\n<div>Content</div>"
        
        is_valid, issues = formatter.validate_response(invalid_response)
        
        assert is_valid is False
        assert "Improperly closed code block" in issues
    
    def test_validate_response_security_issues(self, formatter):
        """Test validation catches security issues"""
        dangerous_response = '''Results:
```html
<div onclick="alert('xss')">
    <script>alert('xss')</script>
    <a href="javascript:void(0)">Link</a>
</div>
```'''
        
        is_valid, issues = formatter.validate_response(dangerous_response)
        
        assert is_valid is False
        assert any("script" in issue.lower() for issue in issues)
        assert any("javascript:" in issue.lower() for issue in issues)
        assert any("event handler" in issue.lower() for issue in issues)
    
    def test_extract_artifact_from_html_block(self, formatter, sample_html):
        """Test artifact extraction from HTML code block"""
        response = f"Results:\n```html\n{sample_html}\n```\nEnd"
        
        extracted = formatter.extract_artifact(response)
        
        assert extracted == sample_html
    
    def test_extract_artifact_from_json(self, formatter, sample_html):
        """Test artifact extraction from JSON response"""
        response = json.dumps({
            "message": "Results",
            "artifact": {
                "type": "html",
                "content": sample_html
            }
        })
        
        extracted = formatter.extract_artifact(response)
        
        assert extracted == sample_html
    
    def test_extract_artifact_from_artifact_tag(self, formatter, sample_html):
        """Test artifact extraction from artifact tags"""
        response = f"Results:\n<artifact>{sample_html}</artifact>\nEnd"
        
        extracted = formatter.extract_artifact(response)
        
        assert extracted == sample_html
    
    def test_extract_artifact_not_found(self, formatter):
        """Test artifact extraction when not present"""
        response = "Just plain text without any artifacts"
        
        extracted = formatter.extract_artifact(response)
        
        assert extracted is None
    
    def test_generate_empty_state_artifact(self, formatter):
        """Test empty state artifact generation"""
        artifact = formatter.generate_empty_state_artifact(
            message="No products found",
            suggestion="Try searching for 'milk'"
        )
        
        assert "No products found" in artifact
        assert "Try searching for 'milk'" in artifact
        assert "empty-state" in artifact
        assert "<style>" in artifact
    
    def test_create_product_grid_artifact(self, formatter, sample_products):
        """Test product grid artifact creation"""
        artifact = formatter.create_product_grid_artifact(sample_products, max_items=2)
        
        # Should have grid structure
        assert 'class="g"' in artifact
        
        # Should have first two products
        assert "Organic Whole Milk" in artifact
        assert "Almond Milk" in artifact
        
        # Should not have third product (max_items=2)
        assert "Oat Milk" not in artifact
        
        # Should have styles
        assert "<style>" in artifact
    
    def test_create_product_grid_artifact_empty(self, formatter):
        """Test product grid with no products"""
        artifact = formatter.create_product_grid_artifact([])
        
        assert "No products found" in artifact
        assert "empty-state" in artifact


class TestArtifactResponseBuilder:
    """Test suite for Artifact Response Builder"""
    
    @pytest.fixture
    def builder(self):
        """Create builder instance"""
        return ArtifactResponseBuilder()
    
    def test_builder_basic_flow(self, builder):
        """Test basic builder flow"""
        response = (
            builder
            .with_message("Found 3 products")
            .with_artifact("<div>Products</div>")
            .build()
        )
        
        assert "Found 3 products" in response
        assert "```html" in response
        assert "<div>Products</div>" in response
    
    def test_builder_with_all_options(self, builder):
        """Test builder with all options"""
        response = (
            builder
            .with_message("Search results")
            .with_artifact("<div>Content</div>")
            .with_context("Available now")
            .with_type(ArtifactType.PRODUCT_LIST)
            .with_pattern(ResponsePattern.HYBRID_NATURAL)
            .optimize_tokens(True)
            .build()
        )
        
        assert "Search results" in response
        assert "Visual Display" in response
        assert "Available now" in response
        assert "```html" in response
    
    def test_builder_reset(self, builder):
        """Test builder reset functionality"""
        # Build first response
        response1 = (
            builder
            .with_message("First")
            .with_artifact("<div>1</div>")
            .build()
        )
        
        # Reset and build second response
        response2 = (
            builder
            .reset()
            .with_message("Second")
            .with_artifact("<div>2</div>")
            .build()
        )
        
        assert "First" in response1
        assert "First" not in response2
        assert "Second" in response2


class TestConvenienceFunctions:
    """Test suite for convenience functions"""
    
    def test_format_product_search_response_with_products(self):
        """Test product search response formatting with results"""
        products = [
            {"name": "Milk", "price": 4.99},
            {"name": "Bread", "price": 2.99}
        ]
        
        response = format_product_search_response(products, "grocery")
        
        assert "Found 2 products for 'grocery'" in response
        assert "```html" in response
        assert "Milk" in response
        assert "4.99" in response
    
    def test_format_product_search_response_empty(self):
        """Test product search response with no results"""
        response = format_product_search_response([], "unicorn milk")
        
        assert "No products found for 'unicorn milk'" in response
        assert "```html" in response
        assert "empty-state" in response
        assert "Try different search terms" in response
    
    def test_validate_artifact_response_detailed(self):
        """Test detailed validation report"""
        valid_response = "Results:\n```html\n<div>Content</div>\n```"
        
        report = validate_artifact_response(valid_response)
        
        assert report["is_valid"] is True
        assert report["has_artifact"] is True
        assert report["artifact_length"] > 0
        assert report["estimated_tokens"] > 0
        assert len(report["issues"]) == 0
    
    def test_validate_artifact_response_with_issues(self):
        """Test validation report with issues"""
        invalid_response = "Results without any HTML artifact"
        
        report = validate_artifact_response(invalid_response)
        
        assert report["is_valid"] is False
        assert report["has_artifact"] is False
        assert report["artifact_length"] == 0
        assert len(report["issues"]) > 0
        assert any("Use ```html blocks" in rec for rec in report["recommendations"] if rec)


class TestTokenEfficiency:
    """Test suite for token efficiency optimizations"""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter instance"""
        return LLMArtifactFormatter()
    
    def test_token_reduction_inline_styles(self, formatter):
        """Test token reduction from inline style conversion"""
        html_with_styles = '''
        <div style="background: #fff; padding: 16px; border: 1px solid #ddd;">
            <h3 style="color: #333; font-size: 18px;">Product 1</h3>
        </div>
        <div style="background: #fff; padding: 16px; border: 1px solid #ddd;">
            <h3 style="color: #333; font-size: 18px;">Product 2</h3>
        </div>
        '''
        
        optimized = formatter._optimize_html(html_with_styles)
        
        # Should be significantly shorter
        assert len(optimized) < len(html_with_styles) * 0.7
    
    def test_token_estimation_accuracy(self, formatter):
        """Test token estimation accuracy"""
        test_text = "This is a test message " * 100  # ~400 chars
        
        estimated_tokens = len(test_text) / formatter.CHARS_PER_TOKEN
        
        # Should be roughly 100 tokens (4 chars per token)
        assert 90 < estimated_tokens < 110
    
    def test_response_under_token_limit(self, formatter):
        """Test that responses stay under token limits"""
        # Generate a large product list
        products = [
            {"name": f"Product {i}", "price": i * 1.99, "description": f"Description {i}"}
            for i in range(50)
        ]
        
        artifact = formatter.create_product_grid_artifact(products, max_items=5)
        response = formatter.format_response(
            message="Found many products",
            artifact_html=artifact,
            optimize_tokens=True
        )
        
        estimated_tokens = len(response) / formatter.CHARS_PER_TOKEN
        
        assert estimated_tokens <= formatter.MAX_TOKENS_RECOMMENDED


class TestSecurityValidation:
    """Test suite for security validation"""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter instance"""
        return LLMArtifactFormatter()
    
    def test_xss_prevention(self, formatter):
        """Test XSS attack prevention"""
        dangerous_html = '''
        <div onclick="alert('XSS')">Click me</div>
        <img src="x" onerror="alert('XSS')">
        <script>alert('XSS')</script>
        '''
        
        response = formatter.format_response(
            message="Results",
            artifact_html=dangerous_html
        )
        
        is_valid, issues = formatter.validate_response(response)
        
        assert is_valid is False
        assert len(issues) >= 2  # Should catch multiple security issues
    
    def test_javascript_protocol_prevention(self, formatter):
        """Test javascript: protocol prevention"""
        dangerous_html = '''
        <a href="javascript:alert('XSS')">Click</a>
        <form action="javascript:alert('XSS')">
        '''
        
        response = formatter.format_response(
            message="Results",
            artifact_html=dangerous_html
        )
        
        is_valid, issues = formatter.validate_response(response)
        
        assert is_valid is False
        assert any("javascript:" in issue.lower() for issue in issues)
    
    def test_safe_html_passes_validation(self, formatter):
        """Test that safe HTML passes validation"""
        safe_html = '''
        <div class="product">
            <h3>Product Name</h3>
            <p>Description</p>
            <button type="button">Add to Cart</button>
        </div>
        '''
        
        response = formatter.format_response(
            message="Product details",
            artifact_html=safe_html
        )
        
        is_valid, issues = formatter.validate_response(response)
        
        assert is_valid is True
        assert len(issues) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--color=yes"])