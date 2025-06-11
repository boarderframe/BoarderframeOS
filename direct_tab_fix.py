#!/usr/bin/env python3
"""
Direct fix for tab display by updating the CSS to be more specific
"""

def direct_tab_fix():
    """Apply a more aggressive CSS fix"""
    print("🔧 Applying Direct Tab Display Fix")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Find the existing tab CSS
    import re

    # Replace the tab-content CSS with more specific rules
    old_css = r'\.tab-content \{\s*display: none;\s*\}\s*\.tab-content\.active \{\s*display: block;\s*\}'

    new_css = '''/* Tab Content - More Specific Rules */
        .tab-content {
            display: none !important;
            opacity: 0;
            visibility: hidden;
        }

        .tab-content.active {
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Ensure child elements are visible when tab is active */
        .tab-content.active * {
            opacity: 1 !important;
            visibility: visible !important;
        }'''

    # Try to replace
    if re.search(old_css, content, re.DOTALL):
        content = re.sub(old_css, new_css, content, flags=re.DOTALL)
        print("✅ Replaced existing CSS with more specific rules")
    else:
        # Find a place to insert
        css_insert = content.find('/* Tab Content */')
        if css_insert > -1:
            # Replace the section up to the next comment or closing style tag
            end_point = content.find('/*', css_insert + 20)
            if end_point == -1:
                end_point = content.find('</style>', css_insert)

            content = content[:css_insert] + new_css + content[end_point:]
            print("✅ Inserted new CSS rules")

    # Also update the showTab function to be more aggressive
    print("\n🔍 Updating showTab function...")

    # Find and replace the showTab function
    showTab_pattern = r'function showTab\(tabName\) \{[^}]+\}'

    new_showTab = '''function showTab(tabName) {
            console.log('[ShowTab] Switching to:', tabName);

            // First, force hide ALL tabs
            const allTabs = document.querySelectorAll('.tab-content');
            allTabs.forEach((tab, index) => {
                tab.classList.remove('active');
                tab.style.display = 'none';
                tab.style.opacity = '0';
                tab.style.visibility = 'hidden';
                console.log(`[ShowTab] Hiding tab ${index}:`, tab.id);
            });

            // Remove active from all nav links
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => link.classList.remove('active'));

            // Now show the selected tab
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {
                selectedTab.classList.add('active');
                selectedTab.style.display = 'block';
                selectedTab.style.opacity = '1';
                selectedTab.style.visibility = 'visible';
                console.log('[ShowTab] Showing tab:', tabName);

                // Force a reflow to ensure styles are applied
                selectedTab.offsetHeight;

                // Also ensure all child elements are visible
                const children = selectedTab.querySelectorAll('*');
                children.forEach(child => {
                    if (child.style.display === 'none') {
                        console.log('[ShowTab] Found hidden child:', child);
                    }
                });
            } else {
                console.error('[ShowTab] Tab not found:', tabName);
            }

            // Update nav link
            const clickedLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
            if (clickedLink) {
                clickedLink.classList.add('active');
            }

            // Debug info
            console.log('[ShowTab] Active tabs:', document.querySelectorAll('.tab-content.active').length);
        }'''

    content = re.sub(showTab_pattern, new_showTab, content, flags=re.DOTALL)
    print("✅ Updated showTab function with aggressive display control")

    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

    print("\n✅ Direct fix applied!")
    print("\n📋 To test:")
    print("1. Refresh Corporate HQ")
    print("2. Open browser console (F12)")
    print("3. Click any tab - you'll see detailed logs")
    print("4. If tabs still don't show, the console will show what's blocking them")


if __name__ == "__main__":
    direct_tab_fix()
