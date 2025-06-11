#!/usr/bin/env python3
"""
Fix JavaScript syntax errors in corporate headquarters
"""

import re


def fix_javascript_errors():
    """Fix the duplicate showTab code and other JavaScript issues"""

    with open("corporate_headquarters.py", "r") as f:
        content = f.read()

    print("Fixing JavaScript syntax errors...")

    # Find the script section
    script_start = content.find("<script>\n        // Tab switching functionality")
    if script_start == -1:
        print("Could not find script section")
        return False

    # Find the end of the script section
    script_end = content.find("</script>", script_start)
    if script_end == -1:
        print("Could not find end of script section")
        return False

    # Extract the script content
    script_content = content[script_start : script_end + 9]  # +9 for </script>

    # Check for the duplicate code pattern
    if (
        "});            \n            // Remove active class from all nav links"
        in script_content
    ):
        print("Found duplicate showTab code!")

        # Find where the proper showTab function ends
        proper_end = script_content.find("});", script_content.find("function showTab"))

        # Find where DOMContentLoaded starts
        dom_loaded_start = script_content.find("// Initialize on page load")

        # Extract the clean parts
        before_duplicate = script_content[: proper_end + 3]  # +3 for });\n

        # Find the DOMContentLoaded section
        dom_section_match = re.search(
            r"(// Initialize on page load.*?console\.log\(\'Tabs initialized.*?\'\);.*?\}\);)",
            script_content,
            re.DOTALL,
        )

        if dom_section_match:
            dom_section = dom_section_match.group(1)

            # Build the fixed script
            fixed_script = """<script>
        // Tab switching functionality
        function showTab(tabName) {
            console.log('[ShowTab] Switching to:', tabName);

            // Hide all tabs
            const allTabs = document.querySelectorAll('.tab-content');
            allTabs.forEach((tab) => {
                tab.classList.remove('active');
                tab.style.display = 'none';  // Ensure hidden
                console.log(`[ShowTab] Hiding tab: ${tab.id}`);
            });

            // Remove active from all nav links
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => link.classList.remove('active'));

            // Show the selected tab
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {
                selectedTab.classList.add('active');
                selectedTab.style.display = 'block';  // Force display
                console.log('[ShowTab] Showing tab:', tabName);

                // Update nav link
                const clickedLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
                if (clickedLink) {
                    clickedLink.classList.add('active');
                }

                // Trigger any tab-specific initialization
                if (tabName === 'registry') {
                    console.log('[ShowTab] Registry tab activated');
                }
            } else {
                console.error('[ShowTab] Tab not found:', tabName);
            }

            // Debug info
            console.log('[ShowTab] Active tabs:', document.querySelectorAll('.tab-content.active').length);
        }

        // Debug function to check tab states
        function debugTabs() {
            const tabs = document.querySelectorAll('.tab-content');
            console.log('Tab states:');
            tabs.forEach(tab => {
                const computed = window.getComputedStyle(tab);
                console.log(`- ${tab.id}: display=${computed.display}, visibility=${computed.visibility}, opacity=${computed.opacity}, classes=${tab.className}`);
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
                    const tabNames = ['dashboard', 'agents', 'leaders', 'departments', 'divisions', 'database', 'registry', 'services', 'system', 'reporting'];
                    const index = parseInt(e.key) - 1;
                    if (index < tabNames.length) {
                        showTab(tabNames[index]);
                    }
                }
            });

            console.log('Tabs initialized. Use Ctrl+1 through Ctrl+9 to switch tabs.');
            console.log('Run debugTabs() in console to check tab states.');
        });"""

            # Find where to continue after the script
            remaining_content_start = content.find("</script>", script_start) + 9

            # Build the final content
            new_content = content[:script_start] + fixed_script

            # Find the next non-duplicate content after the script
            # Look for the next legitimate content (not duplicate showTab code)
            next_content_patterns = [
                "\n\n        function refreshAgentsMetrics",
                "\n                console.log('Response status:",
                "\n        async function refreshSystemsMetrics",
                "\n    </script>",
                "\n\n        // Global refresh function",
            ]

            next_content_pos = None
            for pattern in next_content_patterns:
                pos = content.find(pattern, remaining_content_start)
                if pos != -1 and (next_content_pos is None or pos < next_content_pos):
                    next_content_pos = pos

            if next_content_pos:
                new_content += content[next_content_pos:]
            else:
                new_content += content[remaining_content_start:]

            # Save the fixed content
            with open("corporate_headquarters.py", "w") as f:
                f.write(new_content)

            print("✓ Fixed duplicate showTab code")
            print("✓ Added explicit display style manipulation for better visibility")
            print("✓ Enhanced debug output")
            return True

    print("No duplicate code found to fix")
    return False


if __name__ == "__main__":
    if fix_javascript_errors():
        print("\nJavaScript syntax errors fixed successfully!")
        print("The tabs should now switch properly.")
    else:
        print("\nNo fixes needed or could not fix.")
