#!/usr/bin/env python3
"""
Fix all JavaScript issues preventing tabs from working
"""

def fix_all_js_issues():
    """Fix template syntax and function ordering issues"""
    print("🔧 Fixing All JavaScript Issues")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Fix 1: Replace all {{ and }} in JavaScript sections
    print("🔍 Fixing template syntax in JavaScript...")

    # Find script sections and fix template syntax
    import re

    # Pattern to find script blocks
    script_blocks = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)

    for i, script in enumerate(script_blocks):
        if '{{' in script:
            # Fix template syntax in this script block
            fixed_script = script
            # Replace {{ with { and }} with } but be careful with template literals
            fixed_script = re.sub(r'\$\{\{(\w+)\}\}', r'${$1}', fixed_script)  # Fix template literals
            fixed_script = re.sub(r'`([^`]*)\{\{(\w+)\}\}([^`]*)`', r'`$1${$2}$3`', fixed_script)  # Fix in template strings
            fixed_script = re.sub(r'function (\w+)\(\) \{\{', r'function $1() {', fixed_script)  # Fix function declarations
            fixed_script = re.sub(r'\}\}(\s*\n)', r'}$1', fixed_script)  # Fix closing braces

            # Replace in content
            content = content.replace(f'<script>{script}</script>', f'<script>{fixed_script}</script>')
            print(f"✅ Fixed template syntax in script block {i+1}")

    # Fix 2: Ensure updateRefreshDisplay is defined before it's used
    print("\n🔍 Checking function order...")

    # Find where startRefreshCountdown is defined
    countdown_match = re.search(r'function startRefreshCountdown\(\) \{([^}]+)\}', content)
    if countdown_match:
        # Check if updateRefreshDisplay is defined before this
        countdown_pos = countdown_match.start()
        update_display_pos = content.find('function updateRefreshDisplay')

        if update_display_pos > countdown_pos or update_display_pos == -1:
            print("❌ updateRefreshDisplay is defined after startRefreshCountdown or missing")

            # Define it at the beginning of the script section
            first_script_pos = content.find('<script>') + 8
            if first_script_pos > 8:
                # Add at the beginning of first script tag
                early_definition = '''
        // Core refresh display function (defined early to prevent errors)
        let refreshCounter = 30;
        let refreshInterval = null;
        let isRefreshing = false;

        function updateRefreshDisplay(message = '') {
            const display = document.getElementById('refreshDisplay');
            if (display) {
                display.textContent = message || `Refreshing in ${refreshCounter}s`;
            }
        }

        '''
                content = content[:first_script_pos] + early_definition + content[first_script_pos:]
                print("✅ Added updateRefreshDisplay at the beginning of scripts")

    # Fix 3: Remove any duplicate definitions
    print("\n🔍 Removing duplicate function definitions...")

    # Count occurrences
    update_display_count = content.count('function updateRefreshDisplay')
    if update_display_count > 1:
        print(f"⚠️ Found {update_display_count} definitions of updateRefreshDisplay")
        # Keep only the first one
        first_pos = content.find('function updateRefreshDisplay')
        if first_pos > -1:
            # Find the end of the first definition
            func_end = content.find('\n        }', first_pos) + 10
            first_def = content[first_pos:func_end]

            # Remove all other definitions
            remaining = content[func_end:]
            remaining = re.sub(r'function updateRefreshDisplay\([^)]*\) \{[^}]+\}\s*', '', remaining)
            content = content[:func_end] + remaining
            print("✅ Removed duplicate definitions")

    # Fix 4: Ensure all required variables are defined
    print("\n🔍 Ensuring all required variables are defined...")

    # Add variable declarations if missing
    if 'let refreshCounter' not in content and 'var refreshCounter' not in content:
        # Add after the first script tag
        first_script = content.find('<script>') + 8
        if first_script > 8 and 'refreshCounter = 30' not in content[:first_script + 1000]:
            content = content[:first_script] + '\n        let refreshCounter = 30;\n' + content[first_script:]
            print("✅ Added refreshCounter variable declaration")

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    print("\n✅ All JavaScript issues fixed!")
    print("🚀 The page should now work without errors")
    print("\n📋 Refresh Corporate HQ and check if tabs are working")


if __name__ == "__main__":
    fix_all_js_issues()
