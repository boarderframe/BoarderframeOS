#!/usr/bin/env python3
"""
Fix the JavaScript template syntax issue that's breaking tab display
"""

def fix_javascript_template_syntax():
    """Fix double curly braces in JavaScript"""
    print("🔧 Fixing JavaScript Template Syntax")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Count issues before
    double_braces = content.count('{{')
    print(f"Found {double_braces} instances of '{{' in the file")

    # In the showTab function, the template syntax is breaking it
    # Look for the specific line with the template variable
    import re

    # Fix the showTab function's template string
    # Original: const clickedLink = document.querySelector(`.nav-link[data-tab="${{tabName}}"]`);
    # Should be: const clickedLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);

    pattern = r'const clickedLink = document\.querySelector\(`\.nav-link\[data-tab="\$\{\{tabName\}\}"\]`\);'
    replacement = 'const clickedLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);'

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        print("✅ Fixed template syntax in showTab function")
    else:
        # Try simpler pattern
        content = content.replace('data-tab="${{tabName}}"', 'data-tab="${tabName}"')
        print("✅ Fixed template syntax using simple replacement")

    # Also fix any CSS keyframes that use {{
    # These need to be single braces for CSS
    css_pattern = r'@keyframes\s+\w+\s*\{\{(.*?)\}\}'
    matches = re.findall(css_pattern, content, re.DOTALL)
    if matches:
        print(f"\n📊 Found {len(matches)} CSS keyframes with double braces")
        # Replace {{ with { and }} with } in keyframes
        content = re.sub(r'(@keyframes\s+\w+\s*)\{\{', r'\1{', content)
        content = re.sub(r'(\d+%\s*)\{\{', r'\1{', content)
        content = re.sub(r'\}\}(\s*\d+%)', r'}\1', content)
        content = re.sub(r'\}\}(\s*\})', r'}\1', content)
        print("✅ Fixed CSS keyframes syntax")

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    # Verify
    with open(file_path, 'r') as f:
        new_content = f.read()

    new_double_braces = new_content.count('{{')
    print(f"\n📊 After fix: {new_double_braces} instances of '{{' remaining")
    print("✅ JavaScript template syntax fixed!")
    print("\n🚀 Please refresh Corporate HQ - tabs should now work properly!")


if __name__ == "__main__":
    fix_javascript_template_syntax()
