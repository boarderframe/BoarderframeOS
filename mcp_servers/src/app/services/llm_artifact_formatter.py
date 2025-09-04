"""
LLM Artifact Response Formatter Service
Ensures consistent artifact formatting for Open WebUI rendering
"""

import re
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime


class ArtifactType(Enum):
    """Supported artifact types for Open WebUI"""
    PRODUCT_GRID = "product_grid"
    PRODUCT_LIST = "product_list"
    CHART = "chart"
    TABLE = "table"
    CARD = "card"
    INTERACTIVE = "interactive"
    EMPTY_STATE = "empty_state"


class ResponsePattern(Enum):
    """LLM response patterns for artifact inclusion"""
    DIRECT_HTML = "direct_html"  # ```html block only
    STRUCTURED_JSON = "structured_json"  # JSON with artifact field
    HYBRID_NATURAL = "hybrid_natural"  # Natural language + artifact
    MINIMAL_TOKEN = "minimal_token"  # Ultra-compressed format


class LLMArtifactFormatter:
    """
    Formats LLM responses to guarantee Open WebUI artifact rendering
    Optimized for token efficiency and rendering reliability
    """
    
    # Artifact detection regex patterns
    HTML_BLOCK_PATTERN = re.compile(r'```html\s*\n([\s\S]*?)\n```', re.MULTILINE)
    ARTIFACT_TAG_PATTERN = re.compile(r'<artifact[^>]*>([\s\S]*?)</artifact>', re.MULTILINE)
    
    # Token estimation constants
    CHARS_PER_TOKEN = 4  # Approximate for GPT models
    MAX_TOKENS_RECOMMENDED = 1000
    MAX_TOKENS_HARD_LIMIT = 2000
    
    def __init__(self, default_pattern: ResponsePattern = ResponsePattern.DIRECT_HTML):
        """
        Initialize formatter with default response pattern
        
        Args:
            default_pattern: Default pattern for formatting responses
        """
        self.default_pattern = default_pattern
        self.template_cache = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load response templates for different patterns"""
        self.templates = {
            ResponsePattern.DIRECT_HTML: """{message}

```html
{artifact_html}
```

{context}""",
            
            ResponsePattern.STRUCTURED_JSON: {
                "message": "{message}",
                "artifact": {
                    "type": "html",
                    "content": "{artifact_html}"
                },
                "context": "{context}"
            },
            
            ResponsePattern.HYBRID_NATURAL: """{message}

**Visual Display:**
```html
{artifact_html}
```

{context}""",
            
            ResponsePattern.MINIMAL_TOKEN: "{message}\n```html\n{artifact_html}\n```"
        }
    
    def format_response(
        self,
        message: str,
        artifact_html: str,
        context: Optional[str] = None,
        artifact_type: ArtifactType = ArtifactType.PRODUCT_GRID,
        pattern: Optional[ResponsePattern] = None,
        optimize_tokens: bool = True
    ) -> str:
        """
        Format LLM response with guaranteed artifact inclusion
        
        Args:
            message: Main response message
            artifact_html: HTML content to display
            context: Optional additional context
            artifact_type: Type of artifact for styling
            pattern: Response pattern to use (defaults to instance default)
            optimize_tokens: Whether to optimize for token efficiency
        
        Returns:
            Formatted response string that will trigger artifact rendering
        """
        pattern = pattern or self.default_pattern
        
        # Optimize HTML if requested
        if optimize_tokens:
            artifact_html = self._optimize_html(artifact_html)
        
        # Ensure HTML has root element
        if not artifact_html.strip().startswith("<"):
            artifact_html = f'<div class="{artifact_type.value}">{artifact_html}</div>'
        
        # Format based on pattern
        if pattern == ResponsePattern.STRUCTURED_JSON:
            template = self.templates[pattern]
            response = json.dumps({
                "message": message,
                "artifact": {
                    "type": "html",
                    "content": artifact_html
                },
                "context": context or ""
            }, indent=2)
        else:
            template = self.templates[pattern]
            response = template.format(
                message=message,
                artifact_html=artifact_html,
                context=context or ""
            ).strip()
        
        # Validate token count
        if optimize_tokens:
            response = self._enforce_token_limit(response)
        
        return response
    
    def _optimize_html(self, html: str) -> str:
        """
        Optimize HTML for token efficiency
        
        Args:
            html: Original HTML content
        
        Returns:
            Optimized HTML with reduced token usage
        """
        # Remove unnecessary whitespace
        html = re.sub(r'\s+', ' ', html)
        html = re.sub(r'>\s+<', '><', html)
        
        # Convert inline styles to classes
        html = self._convert_inline_styles(html)
        
        # Shorten class names
        html = self._shorten_class_names(html)
        
        # Remove HTML comments
        html = re.sub(r'<!--[\s\S]*?-->', '', html)
        
        return html.strip()
    
    def _convert_inline_styles(self, html: str) -> str:
        """Convert inline styles to CSS classes for token efficiency"""
        # Extract unique inline styles
        style_pattern = re.compile(r'style="([^"]*)"')
        styles = style_pattern.findall(html)
        
        if not styles:
            return html
        
        # Create class mappings
        style_map = {}
        style_css = ["<style>"]
        
        for i, style in enumerate(set(styles)):
            class_name = f"s{i}"
            style_map[style] = class_name
            style_css.append(f".{class_name}{{{style}}}")
        
        style_css.append("</style>")
        
        # Replace inline styles with classes
        for style, class_name in style_map.items():
            html = html.replace(f'style="{style}"', f'class="{class_name}"')
        
        # Prepend styles
        return "".join(style_css) + html
    
    def _shorten_class_names(self, html: str) -> str:
        """Shorten CSS class names for token efficiency"""
        replacements = {
            "product-card": "pc",
            "product-grid": "pg",
            "product-list": "pl",
            "price": "pr",
            "description": "d",
            "button": "b",
            "container": "c",
            "wrapper": "w",
            "header": "h",
            "footer": "f"
        }
        
        for long_name, short_name in replacements.items():
            html = html.replace(f'class="{long_name}"', f'class="{short_name}"')
            html = html.replace(f"class='{long_name}'", f"class='{short_name}'")
        
        return html
    
    def _enforce_token_limit(self, response: str, hard_limit: bool = False) -> str:
        """
        Enforce token limits on response
        
        Args:
            response: Original response
            hard_limit: Use hard limit instead of recommended
        
        Returns:
            Response within token limits
        """
        limit = self.MAX_TOKENS_HARD_LIMIT if hard_limit else self.MAX_TOKENS_RECOMMENDED
        estimated_tokens = len(response) / self.CHARS_PER_TOKEN
        
        if estimated_tokens <= limit:
            return response
        
        # Extract and preserve artifact
        artifact_match = self.HTML_BLOCK_PATTERN.search(response)
        if not artifact_match:
            return response[:limit * self.CHARS_PER_TOKEN]
        
        # Truncate message/context but preserve artifact
        artifact_block = artifact_match.group(0)
        prefix = response[:artifact_match.start()].strip()
        suffix = response[artifact_match.end():].strip()
        
        # Calculate available space
        artifact_tokens = len(artifact_block) / self.CHARS_PER_TOKEN
        available_tokens = limit - artifact_tokens - 10  # Reserve tokens
        
        if available_tokens < 20:
            # Artifact too large, truncate it
            return f"Results available:\n\n{artifact_block[:limit * self.CHARS_PER_TOKEN]}"
        
        # Truncate prefix and suffix
        prefix_chars = int(available_tokens * 0.7 * self.CHARS_PER_TOKEN)
        suffix_chars = int(available_tokens * 0.3 * self.CHARS_PER_TOKEN)
        
        truncated_prefix = prefix[:prefix_chars]
        truncated_suffix = suffix[:suffix_chars] if suffix else ""
        
        return f"{truncated_prefix}\n\n{artifact_block}\n\n{truncated_suffix}".strip()
    
    def create_display_instructions(
        self,
        artifact_html: str,
        instruction_level: str = "concise"
    ) -> str:
        """
        Create display instructions for LLM to include artifact
        
        Args:
            artifact_html: HTML content to display
            instruction_level: Level of detail (minimal, concise, detailed)
        
        Returns:
            Display instructions string
        """
        if instruction_level == "minimal":
            return f"```html\n{artifact_html}\n```"
        
        elif instruction_level == "concise":
            return f"""Include this in your response:
```html
{artifact_html}
```"""
        
        else:  # detailed
            return f"""ARTIFACT DISPLAY INSTRUCTIONS:
1. Include the HTML code block below in your response
2. Use ```html syntax for Open WebUI artifact detection
3. Place the artifact after your text explanation
4. Do NOT modify or summarize the HTML content

HTML ARTIFACT:
```html
{artifact_html}
```

USAGE: Copy the entire HTML block above (including backticks) into your response."""
    
    def validate_response(self, response: str) -> Tuple[bool, List[str]]:
        """
        Validate that response will trigger artifact rendering
        
        Args:
            response: LLM response to validate
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for HTML code block
        if "```html" not in response:
            issues.append("Missing ```html code block")
        
        # Check for proper closing
        if response.count("```") < 2:
            issues.append("Improperly closed code block")
        
        # Extract and validate HTML content
        artifact_match = self.HTML_BLOCK_PATTERN.search(response)
        if not artifact_match:
            issues.append("Could not extract HTML artifact")
        else:
            html_content = artifact_match.group(1).strip()
            
            if len(html_content) == 0:
                issues.append("Empty HTML artifact")
            
            if "<" not in html_content or ">" not in html_content:
                issues.append("Invalid HTML structure")
            
            # Check for balanced tags
            open_tags = html_content.count("<")
            close_tags = html_content.count(">")
            if open_tags != close_tags:
                issues.append(f"Unbalanced HTML tags: {open_tags} open, {close_tags} close")
            
            # Check for security issues
            if "<script" in html_content.lower():
                issues.append("Contains script tags (security risk)")
            
            if "javascript:" in html_content.lower():
                issues.append("Contains javascript: protocol (security risk)")
            
            if re.search(r'on\w+\s*=', html_content, re.IGNORECASE):
                issues.append("Contains inline event handlers (security risk)")
        
        # Check token efficiency
        estimated_tokens = len(response) / self.CHARS_PER_TOKEN
        if estimated_tokens > self.MAX_TOKENS_RECOMMENDED:
            issues.append(f"Response exceeds recommended token limit ({estimated_tokens:.0f} > {self.MAX_TOKENS_RECOMMENDED})")
        
        return len(issues) == 0, issues
    
    def extract_artifact(self, response: str) -> Optional[str]:
        """
        Extract HTML artifact from LLM response
        
        Args:
            response: LLM response containing artifact
        
        Returns:
            Extracted HTML content or None if not found
        """
        # Try HTML code block first
        match = self.HTML_BLOCK_PATTERN.search(response)
        if match:
            return match.group(1).strip()
        
        # Try artifact tags
        match = self.ARTIFACT_TAG_PATTERN.search(response)
        if match:
            return match.group(1).strip()
        
        # Try JSON structure
        try:
            data = json.loads(response)
            if isinstance(data, dict):
                if "artifact" in data and isinstance(data["artifact"], dict):
                    return data["artifact"].get("content", "")
                if "display_instructions" in data:
                    return self.extract_artifact(data["display_instructions"])
                if "artifact_html" in data:
                    return data["artifact_html"]
        except (json.JSONDecodeError, TypeError):
            pass
        
        return None
    
    def generate_empty_state_artifact(
        self,
        message: str = "No results found",
        suggestion: Optional[str] = None
    ) -> str:
        """
        Generate empty state artifact for no results
        
        Args:
            message: Empty state message
            suggestion: Optional suggestion text
        
        Returns:
            HTML artifact for empty state
        """
        suggestion_html = f'<p class="suggestion">{suggestion}</p>' if suggestion else ""
        
        return f"""<div class="empty-state">
    <style>
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            color: white;
        }}
        .empty-state h3 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .empty-state .suggestion {{
            margin-top: 20px;
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
    <h3>{message}</h3>
    {suggestion_html}
</div>"""
    
    def create_product_grid_artifact(
        self,
        products: List[Dict[str, Any]],
        max_items: int = 5
    ) -> str:
        """
        Create optimized product grid artifact
        
        Args:
            products: List of product dictionaries
            max_items: Maximum number of items to include
        
        Returns:
            HTML artifact for product grid
        """
        products = products[:max_items]
        
        if not products:
            return self.generate_empty_state_artifact(
                "No products found",
                "Try adjusting your search terms"
            )
        
        cards_html = ""
        for i, product in enumerate(products):
            name = product.get("name", "Unknown")[:30]
            price = product.get("price", 0)
            description = product.get("description", "")[:50]
            
            cards_html += f'<div class="c" data-id="{i}"><h4>{name}</h4><p class="pr">${price:.2f}</p><p class="d">{description}</p></div>'
        
        return f"""<style>.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}}.c{{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;transition:transform .2s}}.c:hover{{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.1)}}.pr{{font-size:20px;font-weight:bold;color:#059669;margin:8px 0}}.d{{color:#6b7280;font-size:14px}}</style><div class="g">{cards_html}</div>"""


class ArtifactResponseBuilder:
    """
    Builder pattern for constructing artifact responses
    Provides fluent interface for response construction
    """
    
    def __init__(self, formatter: Optional[LLMArtifactFormatter] = None):
        """
        Initialize response builder
        
        Args:
            formatter: Optional formatter instance (creates default if not provided)
        """
        self.formatter = formatter or LLMArtifactFormatter()
        self.reset()
    
    def reset(self) -> 'ArtifactResponseBuilder':
        """Reset builder to initial state"""
        self._message = ""
        self._artifact_html = ""
        self._context = None
        self._artifact_type = ArtifactType.PRODUCT_GRID
        self._pattern = None
        self._optimize = True
        return self
    
    def with_message(self, message: str) -> 'ArtifactResponseBuilder':
        """Set response message"""
        self._message = message
        return self
    
    def with_artifact(self, html: str) -> 'ArtifactResponseBuilder':
        """Set artifact HTML"""
        self._artifact_html = html
        return self
    
    def with_context(self, context: str) -> 'ArtifactResponseBuilder':
        """Set additional context"""
        self._context = context
        return self
    
    def with_type(self, artifact_type: ArtifactType) -> 'ArtifactResponseBuilder':
        """Set artifact type"""
        self._artifact_type = artifact_type
        return self
    
    def with_pattern(self, pattern: ResponsePattern) -> 'ArtifactResponseBuilder':
        """Set response pattern"""
        self._pattern = pattern
        return self
    
    def optimize_tokens(self, optimize: bool = True) -> 'ArtifactResponseBuilder':
        """Set token optimization"""
        self._optimize = optimize
        return self
    
    def build(self) -> str:
        """Build final response"""
        return self.formatter.format_response(
            message=self._message,
            artifact_html=self._artifact_html,
            context=self._context,
            artifact_type=self._artifact_type,
            pattern=self._pattern,
            optimize_tokens=self._optimize
        )


# Convenience functions for common patterns
def format_product_search_response(
    products: List[Dict[str, Any]],
    search_term: str,
    formatter: Optional[LLMArtifactFormatter] = None
) -> str:
    """
    Format product search response with artifact
    
    Args:
        products: List of product dictionaries
        search_term: Search term used
        formatter: Optional formatter instance
    
    Returns:
        Formatted response with product grid artifact
    """
    formatter = formatter or LLMArtifactFormatter()
    
    if not products:
        message = f"No products found for '{search_term}'"
        artifact = formatter.generate_empty_state_artifact(
            message,
            "Try different search terms or browse categories"
        )
    else:
        message = f"Found {len(products)} products for '{search_term}'"
        artifact = formatter.create_product_grid_artifact(products)
    
    return formatter.format_response(
        message=message,
        artifact_html=artifact,
        artifact_type=ArtifactType.PRODUCT_GRID if products else ArtifactType.EMPTY_STATE
    )


def validate_artifact_response(response: str) -> Dict[str, Any]:
    """
    Validate artifact response and return detailed report
    
    Args:
        response: Response to validate
    
    Returns:
        Validation report dictionary
    """
    formatter = LLMArtifactFormatter()
    is_valid, issues = formatter.validate_response(response)
    artifact = formatter.extract_artifact(response)
    
    return {
        "is_valid": is_valid,
        "issues": issues,
        "has_artifact": artifact is not None,
        "artifact_length": len(artifact) if artifact else 0,
        "estimated_tokens": len(response) / 4,
        "recommendations": [
            "Use ```html blocks for artifacts" if "```html" not in response else None,
            "Reduce response size" if len(response) / 4 > 1000 else None,
            "Add artifact content" if not artifact else None
        ]
    }