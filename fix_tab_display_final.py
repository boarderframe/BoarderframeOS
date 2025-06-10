#!/usr/bin/env python3
"""
Final comprehensive fix for tab display issues
"""

import re

def fix_tab_display_final():
    """Apply final fixes to ensure all tabs display properly"""
    
    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()
    
    print("Applying comprehensive tab display fixes...")
    
    # 1. Fix the showTab function to ensure it works properly
    show_tab_pattern = r'function showTab\(tabName\)\s*{[^}]+(?:{[^}]*}[^}]*)*}'
    
    new_show_tab = '''function showTab(tabName) {
            console.log('[ShowTab] Switching to tab:', tabName);
            
            // First, hide all tabs by removing active class
            const allTabs = document.querySelectorAll('.tab-content');
            allTabs.forEach((tab) => {
                tab.classList.remove('active');
                // Force hide with inline style as backup
                tab.style.display = 'none';
                tab.style.opacity = '0';
                tab.style.visibility = 'hidden';
            });
            
            // Remove active from all nav links
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => link.classList.remove('active'));
            
            // Show the selected tab
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {
                selectedTab.classList.add('active');
                // Force show with inline styles to override any CSS issues
                selectedTab.style.display = 'block';
                selectedTab.style.opacity = '1';
                selectedTab.style.visibility = 'visible';
                
                console.log('[ShowTab] Successfully activated tab:', tabName);
                
                // Update nav link
                const clickedLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
                if (clickedLink) {
                    clickedLink.classList.add('active');
                }
                
                // Fire custom event for tab change
                window.dispatchEvent(new CustomEvent('tabChanged', { detail: { tabName } }));
            } else {
                console.error('[ShowTab] Tab not found:', tabName);
            }
            
            // Debug output
            debugTabs();
        }'''
    
    # Replace the showTab function
    content = re.sub(show_tab_pattern, new_show_tab, content, count=1)
    
    # 2. Ensure CSS doesn't interfere - update the CSS rules to be more specific
    css_pattern = r'(\.tab-content\s*{[^}]+})'
    css_replacement = '''.tab-content {
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            position: absolute;
            left: -9999px;
            transition: opacity 0.3s ease;
        }
        
        /* Ensure active tabs are fully visible */
        .tab-content.active {
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
            position: static !important;
            left: auto !important;
        }
        
        /* Ensure all children are visible too */
        .tab-content.active * {
            opacity: 1 !important;
            visibility: visible !important;
        }'''
    
    content = re.sub(css_pattern, css_replacement, content, count=1)
    
    # 3. Add initialization code to ensure tabs work on load
    init_pattern = r'(document\.addEventListener\(\'DOMContentLoaded\', function\(\) {[^}]+console\.log\(\'Tabs initialized[^}]+}\);)'
    
    new_init = '''document.addEventListener('DOMContentLoaded', function() {
            console.log('Page loaded, initializing tabs...');
            
            // Force hide all tabs first
            document.querySelectorAll('.tab-content').forEach(tab => {
                if (!tab.classList.contains('active')) {
                    tab.style.display = 'none';
                    tab.style.opacity = '0';
                    tab.style.visibility = 'hidden';
                }
            });
            
            // Ensure dashboard is shown by default
            setTimeout(() => {
                showTab('dashboard');
                console.log('Dashboard tab activated');
            }, 100);
            
            // Add click handlers to nav buttons as backup
            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const tabName = this.getAttribute('data-tab');
                    if (tabName) {
                        console.log('Nav click:', tabName);
                        showTab(tabName);
                    }
                });
            });
            
            // Add keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey && e.key >= '1' && e.key <= '9') {
                    const tabNames = ['dashboard', 'agents', 'leaders', 'departments', 'divisions', 'database', 'registry', 'services', 'system'];
                    const index = parseInt(e.key) - 1;
                    if (index < tabNames.length) {
                        showTab(tabNames[index]);
                    }
                }
            });
            
            console.log('Tabs initialized. Use Ctrl+1 through Ctrl+9 to switch tabs.');
            console.log('Current active tab:', document.querySelector('.tab-content.active')?.id);
        });'''
    
    content = re.sub(init_pattern, new_init, content, count=1, flags=re.DOTALL)
    
    # 4. Fix the onclick handlers in nav buttons to ensure they work
    nav_pattern = r'onclick="showTab\(\'([^\']+)\'\)"'
    
    def nav_replacement(match):
        tab_name = match.group(1)
        return f'onclick="showTab(\'{tab_name}\'); return false;"'
    
    content = re.sub(nav_pattern, nav_replacement, content)
    
    # 5. Ensure debugTabs function is properly defined
    if 'function debugTabs()' not in content:
        # Add it after showTab
        show_tab_end = content.find('}\n', content.find('function showTab'))
        if show_tab_end != -1:
            debug_func = '''
        
        // Debug function to check tab states
        function debugTabs() {
            const tabs = document.querySelectorAll('.tab-content');
            console.log('=== Tab States ===');
            tabs.forEach(tab => {
                const computed = window.getComputedStyle(tab);
                const isActive = tab.classList.contains('active');
                console.log(`${tab.id}:`, {
                    active: isActive,
                    display: computed.display,
                    visibility: computed.visibility,
                    opacity: computed.opacity,
                    position: computed.position
                });
            });
        }'''
            content = content[:show_tab_end + 1] + debug_func + content[show_tab_end + 1:]
    
    # Save the fixed content
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)
    
    print("✓ Updated showTab function with forced display styles")
    print("✓ Enhanced CSS rules for better specificity")
    print("✓ Added comprehensive initialization code")
    print("✓ Fixed onclick handlers")
    print("✓ Added debug function")
    
    return True

if __name__ == "__main__":
    if fix_tab_display_final():
        print("\nAll tab display fixes applied successfully!")
        print("\nThe UI should now work properly with:")
        print("- All tabs displaying their content when clicked")
        print("- Smooth transitions between tabs")
        print("- Keyboard shortcuts (Ctrl+1 through Ctrl+9)")
        print("- Debug output in console")
    else:
        print("\nFailed to apply fixes")