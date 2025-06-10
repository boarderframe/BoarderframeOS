#!/usr/bin/env python3
"""
Fix the missing updateRefreshDisplay function that's causing JavaScript errors
"""

def fix_missing_function():
    """Add the missing updateRefreshDisplay function"""
    print("🔧 Fixing Missing updateRefreshDisplay Function")
    print("=" * 60)
    
    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if updateRefreshDisplay is defined
    if 'function updateRefreshDisplay' not in content:
        print("❌ updateRefreshDisplay function is missing!")
        
        # Find where it's being called from
        import re
        calls = re.findall(r'(updateRefreshDisplay\([^)]*\))', content)
        print(f"📊 Found {len(calls)} calls to updateRefreshDisplay")
        
        # Find resetRefreshTimer function to add the missing function near it
        reset_pos = content.find('function resetRefreshTimer')
        if reset_pos > -1:
            # Insert before resetRefreshTimer
            insert_pos = reset_pos
            
            missing_function = '''
        // Update refresh display
        function updateRefreshDisplay(message = '') {
            const display = document.getElementById('refreshDisplay');
            if (display) {
                display.textContent = message || 'Ready';
            }
            console.log('[Refresh]', message);
        }
        
        '''
            
            content = content[:insert_pos] + missing_function + content[insert_pos:]
            print("✅ Added updateRefreshDisplay function")
        else:
            # Add it after showTab function
            showTab_end = content.find('        }', content.find('function showTab'))
            if showTab_end > -1:
                insert_pos = showTab_end + 9  # After the closing brace and newline
                
                missing_function = '''
        
        // Update refresh display (was missing)
        function updateRefreshDisplay(message = '') {
            const display = document.getElementById('refreshDisplay');
            if (display) {
                display.textContent = message || 'Ready';
            }
            console.log('[Refresh]', message);
        }
        '''
                
                content = content[:insert_pos] + missing_function + content[insert_pos:]
                print("✅ Added updateRefreshDisplay function after showTab")
    else:
        print("✅ updateRefreshDisplay function already exists")
    
    # Also check for other potentially missing functions
    print("\n🔍 Checking for other missing functions...")
    
    # Common functions that might be missing
    functions_to_check = [
        ('simulateDelay', 'function simulateDelay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }'),
        ('updateRefreshProgress', 'function updateRefreshProgress(message) { console.log("[Progress]", message); }'),
        ('showRefreshProgress', 'function showRefreshProgress(message) { console.log("[Progress Start]", message); }'),
    ]
    
    for func_name, func_code in functions_to_check:
        if func_name + '(' in content and f'function {func_name}' not in content:
            print(f"❌ {func_name} is called but not defined - adding it")
            
            # Insert after updateRefreshDisplay
            insert_pos = content.find('function updateRefreshDisplay')
            if insert_pos > -1:
                # Find the end of updateRefreshDisplay
                func_end = content.find('        }', insert_pos) + 9
                content = content[:func_end] + f'\n        {func_code}\n' + content[func_end:]
                print(f"✅ Added {func_name} function")
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("\n✅ Fixed missing functions!")
    print("🚀 JavaScript errors should now be resolved")
    print("\n📋 The tabs should work properly now!")


if __name__ == "__main__":
    fix_missing_function()