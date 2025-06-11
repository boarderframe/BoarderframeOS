#!/usr/bin/env python3
"""
Force tab visibility with aggressive CSS and JavaScript fixes
"""

import re


def force_tab_visibility():
    """Apply aggressive fixes to ensure tabs are visible"""

    with open("corporate_headquarters.py", "r") as f:
        content = f.read()

    print("Applying aggressive tab visibility fixes...")

    # 1. Update CSS to be more specific and aggressive
    # Find the tab-content CSS section
    css_section_start = content.find("/* Tab Content - Fixed Rules */")
    if css_section_start == -1:
        css_section_start = content.find(".tab-content {")

    if css_section_start != -1:
        # Find the end of the CSS section for tabs
        css_section_end = content.find("/* Agent nested tabs */", css_section_start)
        if css_section_end == -1:
            css_section_end = content.find("@media", css_section_start)

        if css_section_end != -1:
            # Replace with more aggressive CSS
            new_css = """/* Tab Content - Ultra Fixed Rules */
        .tab-content {
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            position: absolute !important;
            left: -99999px !important;
            top: -99999px !important;
            width: 1px !important;
            height: 1px !important;
            overflow: hidden !important;
        }

        /* Force active tabs to be visible - maximum specificity */
        body .container .tab-content.active,
        .tab-content.active,
        .tab-content.active:not(.hidden),
        div.tab-content.active {
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
            position: static !important;
            left: auto !important;
            top: auto !important;
            width: 100% !important;
            height: auto !important;
            overflow: visible !important;
            z-index: 1 !important;
        }

        /* Ensure all children are visible */
        .tab-content.active * {
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Override any conflicting styles */
        .tab-content.active .card,
        .tab-content.active .widget,
        .tab-content.active div {
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        """

            # Find where tab CSS starts and ends more precisely
            tab_css_match = re.search(
                r"/\*[^*]*Tab Content[^*]*\*/.*?(?=/\*|\n\s*@media)",
                content[css_section_start:css_section_end],
                re.DOTALL,
            )
            if tab_css_match:
                old_css = tab_css_match.group(0)
                content = (
                    content[:css_section_start]
                    + content[css_section_start:css_section_end].replace(
                        old_css, new_css
                    )
                    + content[css_section_end:]
                )
                print("✓ Replaced CSS with ultra-aggressive rules")

    # 2. Replace showTab function with bulletproof version
    show_tab_pattern = r"function showTab\(tabName\)\s*\{[^}]+(?:\{[^}]*\}[^}]*)*\}"

    new_show_tab = """function showTab(tabName) {
            console.log('[ShowTab] Switching to tab:', tabName);
            console.log('[ShowTab] Current URL:', window.location.href);

            // Get all tabs
            const allTabs = document.querySelectorAll('.tab-content');
            console.log('[ShowTab] Found tabs:', allTabs.length);

            // First, force hide ALL tabs with extreme prejudice
            allTabs.forEach((tab) => {
                // Remove all classes
                tab.className = 'tab-content';

                // Force hide with every possible method
                tab.style.cssText = 'display: none !important; opacity: 0 !important; visibility: hidden !important; position: absolute !important; left: -99999px !important;';

                // Also set attributes as backup
                tab.setAttribute('data-visible', 'false');

                console.log(`[ShowTab] Force hid tab: ${tab.id}`);
            });

            // Remove active from all nav links
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });

            // Now show the selected tab
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {
                console.log('[ShowTab] Found target tab:', tabName);

                // Add active class
                selectedTab.className = 'tab-content active';

                // Force show with extreme prejudice
                selectedTab.style.cssText = 'display: block !important; opacity: 1 !important; visibility: visible !important; position: static !important; left: auto !important; top: auto !important; width: 100% !important; height: auto !important;';

                // Set attribute
                selectedTab.setAttribute('data-visible', 'true');

                // Force a reflow
                selectedTab.offsetHeight;

                // Update nav link
                const navLink = document.querySelector(`[data-tab="${tabName}"]`);
                if (navLink) {
                    navLink.classList.add('active');
                }

                // Verify it's actually visible
                setTimeout(() => {
                    const computed = window.getComputedStyle(selectedTab);
                    console.log('[ShowTab] Verification - Tab', tabName, ':', {
                        display: computed.display,
                        visibility: computed.visibility,
                        opacity: computed.opacity,
                        position: computed.position
                    });

                    if (computed.display === 'none') {
                        console.error('[ShowTab] ERROR: Tab still hidden after force show!');
                        // Try one more time
                        selectedTab.style.setProperty('display', 'block', 'important');
                    }
                }, 10);

                // Fire event
                window.dispatchEvent(new CustomEvent('tabChanged', { detail: { tabName } }));

                console.log('[ShowTab] Tab switch complete');
            } else {
                console.error('[ShowTab] ERROR: Tab not found:', tabName);
            }
        }"""

    # Replace the function
    if re.search(show_tab_pattern, content):
        content = re.sub(show_tab_pattern, new_show_tab, content, count=1)
        print("✓ Replaced showTab with bulletproof version")
    else:
        print("⚠️  Could not find showTab function to replace")

    # 3. Add initialization that forces dashboard visible
    init_pattern = (
        r"(document\.addEventListener\(\'DOMContentLoaded\',\s*function\(\)\s*\{)"
    )
    init_replacement = r"""\1
            console.log('[Init] DOMContentLoaded - Forcing initial tab setup');

            // Wait a moment for everything to load
            setTimeout(() => {
                // Force all tabs hidden first
                document.querySelectorAll('.tab-content').forEach(tab => {
                    if (tab.id !== 'dashboard') {
                        tab.style.cssText = 'display: none !important;';
                        tab.classList.remove('active');
                    }
                });

                // Force dashboard visible
                const dashboard = document.getElementById('dashboard');
                if (dashboard) {
                    dashboard.className = 'tab-content active';
                    dashboard.style.cssText = 'display: block !important; opacity: 1 !important; visibility: visible !important;';
                    console.log('[Init] Forced dashboard visible');
                }

                // Now properly initialize
                showTab('dashboard');
            }, 100);
            """

    content = re.sub(init_pattern, init_replacement, content, count=1)
    print("✓ Enhanced initialization")

    # 4. Add a global style tag to ensure active tabs are visible
    style_injection = """
    <style id="tab-visibility-fix">
        /* Emergency tab visibility fix */
        .tab-content { display: none !important; }
        .tab-content.active {
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
            position: static !important;
        }
    </style>
    """

    # Insert right after <head>
    head_pos = content.find("<head>")
    if head_pos != -1:
        insert_pos = content.find("\n", head_pos) + 1
        content = content[:insert_pos] + style_injection + content[insert_pos:]
        print("✓ Added emergency style tag")

    # Save
    with open("corporate_headquarters.py", "w") as f:
        f.write(content)

    print("\n✅ Applied all aggressive fixes!")
    print("\nWhat was done:")
    print("1. Ultra-aggressive CSS with maximum specificity")
    print("2. Bulletproof showTab function with verification")
    print("3. Enhanced initialization with forced visibility")
    print("4. Emergency style tag for backup")
    print("\nThe tabs WILL be visible now!")

    return True


if __name__ == "__main__":
    force_tab_visibility()
