#!/usr/bin/env python3
"""
Fix the registry navigation issue - either add the tab or remove the nav
"""

def fix_registry_nav():
    """Remove registry nav since it's part of the Database tab"""
    print("🔧 Fixing Registry Navigation")
    print("=" * 60)
    
    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if registry tab exists
    if '<div id="registry" class="tab-content"' not in content:
        print("❌ Registry tab doesn't exist")
        print("   Registry functionality is part of Database tab")
        
        # Remove the registry navigation item
        import re
        registry_nav_pattern = r'<li class="nav-item">\s*<button class="nav-link" onclick="showTab\(\'registry\'\)"[^>]*>.*?</button>\s*</li>'
        
        if re.search(registry_nav_pattern, content, re.DOTALL):
            print("✅ Removing registry navigation link")
            content = re.sub(registry_nav_pattern, '', content, flags=re.DOTALL)
            
            # Write back
            with open(file_path, 'w') as f:
                f.write(content)
            
            print("✅ Registry navigation removed")
            print("   Users can access registry info in the Database tab")
        else:
            print("⚠️ Registry navigation not found in expected format")
    else:
        print("✅ Registry tab exists, navigation is valid")


if __name__ == "__main__":
    fix_registry_nav()