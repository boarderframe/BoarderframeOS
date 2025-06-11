#!/usr/bin/env python3
"""
Force fix tabs by adding more explicit JavaScript
"""


def force_fix_tabs():
    """Add more explicit tab handling"""
    print("🔧 Force Fixing Tab Display")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, "r") as f:
        content = f.read()

    # Find the showTab function
    import re

    # Replace the entire showTab function with a more explicit version
    old_function = r"function showTab\(tabName\) \{[^}]+\}"

    new_function = """function showTab(tabName) {
            console.log('Switching to tab:', tabName);

            // Hide all tab contents with explicit style
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => {
                tab.classList.remove('active');
                tab.style.display = 'none';  // Force hide
            });

            // Remove active class from all nav links
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => link.classList.remove('active'));

            // Show selected tab content with explicit style
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {
                selectedTab.classList.add('active');
                selectedTab.style.display = 'block';  // Force show
                console.log('Tab found and activated:', tabName);
            } else {
                console.error('Tab not found:', tabName);
            }

            // Add active class to clicked nav link
            const clickedLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
            if (clickedLink) {
                clickedLink.classList.add('active');
            }
        }"""

    # Replace the function
    content = re.sub(old_function, new_function, content, flags=re.DOTALL)

    # Also add a debug function and auto-init
    debug_code = """

        // Debug function to check tab states
        function debugTabs() {
            const tabs = document.querySelectorAll('.tab-content');
            console.log('Tab states:');
            tabs.forEach(tab => {
                console.log(`- ${tab.id}: display=${window.getComputedStyle(tab).display}, classes=${tab.className}`);
            });
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Page loaded, initializing tabs...');

            // Ensure dashboard is shown by default
            showTab('dashboard');

            // Add keyboard shortcuts for testing
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey && e.key >= '1' && e.key <= '9') {
                    const tabNames = ['dashboard', 'agents', 'leaders', 'departments', 'divisions', 'database', 'services', 'system', 'reporting'];
                    const index = parseInt(e.key) - 1;
                    if (index < tabNames.length) {
                        showTab(tabNames[index]);
                    }
                }
            });

            console.log('Tabs initialized. Use Ctrl+1 through Ctrl+9 to switch tabs.');
        });"""

    # Find where to insert (after showTab function)
    insert_point = content.find("        }", content.find("function showTab"))
    if insert_point > 0:
        insert_point = content.find("\n", insert_point) + 1
        content = content[:insert_point] + debug_code + content[insert_point:]
        print("✅ Added debug code and initialization")

    # Write back
    with open(file_path, "w") as f:
        f.write(content)

    print("\n✅ Force fix applied!")
    print("\n🚀 Refresh Corporate HQ and:")
    print("   1. Check browser console for debug messages")
    print("   2. Try clicking tabs - you should see console logs")
    print("   3. Use Ctrl+1 through Ctrl+9 to switch tabs")
    print("   4. Type debugTabs() in console to see tab states")


if __name__ == "__main__":
    force_fix_tabs()
