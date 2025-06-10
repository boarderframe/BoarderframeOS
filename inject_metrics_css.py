#!/usr/bin/env python3
"""
Inject the metrics layer CSS into Corporate HQ
"""

import re
from core.hq_metrics_integration import METRICS_CSS

def inject_metrics_css():
    """Add the metrics CSS to the Corporate HQ HTML"""
    print("💉 Injecting Metrics Layer CSS")
    print("=" * 50)
    
    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the CSS injection point
    injection_point = "<!-- Metrics Layer CSS will be injected by the integration -->"
    
    if injection_point in content:
        print("✅ Found CSS injection point")
        
        # Create the CSS string properly escaped for Python f-string
        css_escaped = METRICS_CSS.replace('{', '{{').replace('}', '}}')
        css_injection = f"\n    <!-- Metrics Layer CSS -->\n    <style>\n    {css_escaped}\n    </style>"
        
        # Replace the injection point with actual CSS
        content = content.replace(injection_point, css_injection)
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ CSS injected successfully!")
        print(f"   Added {len(METRICS_CSS)} characters of CSS")
    else:
        print("❌ Could not find CSS injection point")
        print("   Looking for alternative location...")
        
        # Try to add it after the main style tag
        style_pattern = r'(<style>)'
        if re.search(style_pattern, content):
            # Add the CSS after the opening style tag
            css_escaped = METRICS_CSS.replace('{', '{{').replace('}', '}}')
            replacement = f'<style>\n        /* Metrics Layer CSS */\n        {css_escaped}\n        \n        /* Original CSS */'
            content = re.sub(style_pattern, replacement, content, count=1)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print("✅ CSS injected at alternative location!")


if __name__ == "__main__":
    inject_metrics_css()