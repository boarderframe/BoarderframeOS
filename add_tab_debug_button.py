#!/usr/bin/env python3
"""
Add a debug button to test tab switching directly
"""

def add_debug_button():
    """Add a debug button to the UI for testing"""

    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    # Find where to add the debug button (after the nav)
    nav_end = content.find('</nav>')
    if nav_end == -1:
        print("Could not find navigation end")
        return False

    # Add debug button
    debug_button = '''
            <!-- Debug Button -->
            <div style="position: fixed; bottom: 20px; right: 20px; z-index: 9999;">
                <button onclick="debugTabSwitch()" style="
                    background: #ff0000;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                ">
                    Debug Tab Switch
                </button>
            </div>'''

    # Add debug function
    debug_function = '''

        // Debug function for testing tab switching
        function debugTabSwitch() {
            console.log('=== DEBUG TAB SWITCH ===');

            // Get all tabs
            const tabs = document.querySelectorAll('.tab-content');
            console.log('Found tabs:', tabs.length);

            tabs.forEach(tab => {
                const computed = window.getComputedStyle(tab);
                console.log(`Tab ${tab.id}:`, {
                    classList: tab.classList.toString(),
                    inlineDisplay: tab.style.display,
                    computedDisplay: computed.display,
                    computedVisibility: computed.visibility,
                    computedOpacity: computed.opacity
                });
            });

            // Try to force show database tab
            console.log('\\nForcing database tab visible...');
            const dbTab = document.getElementById('database');
            if (dbTab) {
                // Remove all classes and add back
                dbTab.className = 'tab-content active';

                // Force all styles
                dbTab.style.display = 'block';
                dbTab.style.visibility = 'visible';
                dbTab.style.opacity = '1';
                dbTab.style.position = 'static';
                dbTab.style.left = 'auto';

                // Check again
                const afterComputed = window.getComputedStyle(dbTab);
                console.log('After forcing:', {
                    classList: dbTab.classList.toString(),
                    inlineDisplay: dbTab.style.display,
                    computedDisplay: afterComputed.display,
                    computedVisibility: afterComputed.visibility,
                    computedOpacity: afterComputed.opacity
                });

                // Also hide other tabs
                tabs.forEach(tab => {
                    if (tab.id !== 'database') {
                        tab.classList.remove('active');
                        tab.style.display = 'none';
                    }
                });

                console.log('Database tab should now be visible!');
            } else {
                console.error('Database tab not found!');
            }
        }'''

    # Insert debug button
    insert_pos = nav_end + len('</nav>')
    content = content[:insert_pos] + debug_button + content[insert_pos:]

    # Insert debug function (before DOMContentLoaded)
    dom_pos = content.find('document.addEventListener(\'DOMContentLoaded\'')
    if dom_pos != -1:
        content = content[:dom_pos] + debug_function + '\n        \n        ' + content[dom_pos:]

    # Save
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)

    print("Added debug button and function")
    print("Look for red 'Debug Tab Switch' button in bottom right corner")
    print("Click it and check browser console for output")

    return True

if __name__ == "__main__":
    add_debug_button()
