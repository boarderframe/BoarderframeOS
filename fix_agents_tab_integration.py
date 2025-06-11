#!/usr/bin/env python3
"""
Fix agents tab to use metrics layer integration
"""

def fix_agents_tab_integration():
    """Update agents tab to use metrics layer get_agents_page_html method"""

    # Read the file
    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    # Find the agents tab content
    agents_start = content.find('<div id="agents" class="tab-content">')
    if agents_start == -1:
        print("Could not find agents tab")
        return False

    # Find the end of agents tab (start of Leaders tab)
    leaders_start = content.find('<!-- Leaders Tab -->', agents_start)
    if leaders_start == -1:
        print("Could not find Leaders tab marker")
        return False

    # Replace the agents tab content to use metrics layer
    new_agents_content = '''<div id="agents" class="tab-content">
            {self.metrics_layer.get_agents_page_html() if self.metrics_layer and hasattr(self.metrics_layer, 'get_agents_page_html') else self._generate_enhanced_agents_html()}
        </div>
        '''

    # Replace the content
    content = content[:agents_start] + new_agents_content + content[leaders_start:]

    # Save the file
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)

    print("Successfully updated agents tab to use metrics layer")
    return True

if __name__ == "__main__":
    if fix_agents_tab_integration():
        print("✓ Agents tab now uses metrics layer integration")
    else:
        print("✗ Failed to update agents tab")
