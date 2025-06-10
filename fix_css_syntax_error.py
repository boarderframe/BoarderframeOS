#!/usr/bin/env python3
"""
Fix CSS syntax error in f-string
"""

def fix_css_syntax():
    """Fix the CSS braces in f-string that are causing syntax error"""
    
    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()
    
    print("Fixing CSS syntax error in f-string...")
    
    # The issue is CSS braces {} inside f-strings need to be doubled {{}}
    # Find the generate_dashboard_html method and its f-string
    
    # Find where the f-string starts
    f_string_start = content.find('return f"""<!DOCTYPE html>')
    if f_string_start == -1:
        print("Could not find f-string start")
        return False
    
    # Find where the f-string ends (three quotes)
    f_string_end = content.find('"""', f_string_start + 20)
    if f_string_end == -1:
        print("Could not find f-string end")
        return False
    
    # Extract the f-string content
    f_string_content = content[f_string_start:f_string_end + 3]
    
    # Count braces to identify the problem
    single_open = f_string_content.count('{')
    single_close = f_string_content.count('}')
    double_open = f_string_content.count('{{')
    double_close = f_string_content.count('}}')
    
    print(f"Found {single_open} '{' and {single_close} '}' in f-string")
    print(f"Found {double_open} '{{' and {double_close} '}}' already escaped")
    
    # Replace CSS braces with escaped versions
    # We need to be careful to only replace CSS braces, not Python expressions
    
    # Common CSS patterns that need escaping
    css_patterns = [
        # CSS rule blocks
        (r'(\s+\.[a-zA-Z0-9-_]+\s*)\{', r'\1{{'),  # .class {
        (r'(\s+#[a-zA-Z0-9-_]+\s*)\{', r'\1{{'),   # #id {
        (r'(\s+[a-zA-Z]+\s*)\{', r'\1{{'),         # element {
        (r'(\s+@media[^{]+)\{', r'\1{{'),          # @media ... {
        (r'(\s+@keyframes[^{]+)\{', r'\1{{'),      # @keyframes ... {
        (r'\}(\s*\n)', r'}}\1'),                   # } at end of CSS blocks
        
        # Specific problematic patterns
        (r'\.nav-link\s*\{', r'.nav-link {{'),
        (r'(\s+)(\w+:\s*[^;{]+;)\s*\}', r'\1\2 }}'),  # property: value; }
    ]
    
    import re
    
    fixed_content = f_string_content
    
    # Apply fixes
    for pattern, replacement in css_patterns:
        fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # Also need to escape any remaining single braces that aren't Python expressions
    # Look for patterns like "{ " or " }" that are clearly CSS
    fixed_content = re.sub(r'\{\s+([a-zA-Z-]+:)', r'{{\1', fixed_content)  # { property:
    fixed_content = re.sub(r';\s*\}', r'; }}', fixed_content)  # ; }
    
    # Replace in the original content
    new_content = content[:f_string_start] + fixed_content + content[f_string_end + 3:]
    
    # Save the fixed file
    with open('corporate_headquarters.py', 'w') as f:
        f.write(new_content)
    
    print("✓ Fixed CSS syntax errors in f-string")
    print("✓ Escaped CSS braces to prevent Python interpretation")
    
    return True

if __name__ == "__main__":
    if fix_css_syntax():
        print("\nCSS syntax fixed! You can now restart the server.")
    else:
        print("\nFailed to fix CSS syntax")