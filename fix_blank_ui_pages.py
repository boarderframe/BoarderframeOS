#!/usr/bin/env python3
"""
Fix blank UI pages in BoarderframeOS Corporate Headquarters
"""

import re

def fix_corporate_headquarters():
    """Fix the blank pages issue in corporate_headquarters.py"""
    
    # Read the current file
    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()
    
    # Find the agents tab section
    agents_tab_start = content.find('<!-- Agents Tab -->')
    agents_tab_end = content.find('<!-- Leaders Tab -->')
    
    if agents_tab_start == -1 or agents_tab_end == -1:
        print("Could not find agents tab markers")
        return False
    
    # Extract the current agents tab content
    current_agents_content = content[agents_tab_start:agents_tab_end]
    
    # Check if the agent list is missing
    if '_generate_enhanced_agents_html()' not in current_agents_content:
        print("Agents tab is missing agent list content")
        
        # Find where to insert the agent list (after the metrics card closing div)
        metrics_card_end = current_agents_content.rfind('</div>', 0, current_agents_content.find('<!-- Organizational Chart -->'))
        
        if metrics_card_end == -1:
            # Try to find the end of agent metrics
            metrics_pattern = r'get_agent_metrics_cards\(\)[^<]*</div>'
            match = re.search(metrics_pattern, current_agents_content)
            if match:
                insert_pos = match.end()
            else:
                print("Could not find proper insertion point for agent list")
                return False
        else:
            # Insert after the metrics card
            insert_pos = current_agents_content.find('</div>', current_agents_content.find('get_agent_metrics_cards()')) + 6
        
        # Create the new agents tab content with proper structure
        new_agents_content = current_agents_content[:insert_pos] + '''
            </div>
            
            <!-- Agent List -->
            <div class="card full-width">
                <h3 style="margin-bottom: 1.5rem;">
                    <i class="fas fa-robot"></i> Active Agents
                </h3>
                {self._generate_enhanced_agents_html()}
            </div>
        </div>
        '''
        
        # Replace the content
        content = content[:agents_tab_start] + new_agents_content + content[agents_tab_end:]
        
        print("Fixed agents tab content")
    
    # Check database tab structure
    database_tab_start = content.find('<!-- Database Tab -->')
    if database_tab_start == -1:
        database_tab_start = content.find('<div id="database" class="tab-content">')
    
    if database_tab_start != -1:
        # Find the next tab after database
        next_tab_pattern = r'<div id="[^"]*" class="tab-content">'
        match = re.search(next_tab_pattern, content[database_tab_start + 100:])
        
        if match:
            database_tab_end = database_tab_start + 100 + match.start()
            database_content = content[database_tab_start:database_tab_end]
            
            # Check if database tab is properly closed
            open_divs = database_content.count('<div')
            close_divs = database_content.count('</div>')
            
            if open_divs > close_divs:
                # Add missing closing divs
                missing_divs = open_divs - close_divs
                print(f"Database tab is missing {missing_divs} closing div(s)")
                
                # Insert before the next tab
                closing_divs = '</div>\n' * missing_divs
                content = content[:database_tab_end] + closing_divs + content[database_tab_end:]
                print("Fixed database tab closing divs")
    
    # Save the fixed content
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)
    
    print("Successfully fixed blank UI pages")
    return True

def add_missing_page_methods():
    """Add missing page HTML generation methods to HQ metrics integration"""
    
    # Read the metrics integration file
    with open('core/hq_metrics_integration.py', 'r') as f:
        content = f.read()
    
    # Check if get_agents_page_html method exists
    if 'def get_agents_page_html' not in content:
        print("Adding get_agents_page_html method to metrics integration")
        
        # Find where to insert (after get_divisions_page_html)
        insert_pos = content.find('def get_divisions_page_html')
        if insert_pos != -1:
            # Find the end of that method
            next_method = content.find('\n    def ', insert_pos + 10)
            if next_method == -1:
                next_method = len(content)
            
            # Insert the new method
            new_method = '''
    def get_agents_page_html(self) -> str:
        """Generate comprehensive agents page with metrics"""
        try:
            # Get agent metrics
            agents_metrics = self.get_agents_page_metrics()
            
            return f"""
            <div class="metrics-container" style="padding: 1rem;">
                <!-- Agent Overview -->
                <div class="metric-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                    <div class="metric-card" style="background: linear-gradient(135deg, #3b82f6, #1e40af); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {agents_metrics.get('total_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Total Agents
                        </div>
                    </div>
                    
                    <div class="metric-card" style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {agents_metrics.get('active_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Active Agents
                        </div>
                    </div>
                    
                    <div class="metric-card" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-sync-alt"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {agents_metrics.get('processing_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Processing
                        </div>
                    </div>
                    
                    <div class="metric-card" style="background: linear-gradient(135deg, #6b7280, #4b5563); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-pause-circle"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {agents_metrics.get('inactive_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Inactive
                        </div>
                    </div>
                </div>
                
                <!-- Agents by Department -->
                <div class="card" style="padding: 1.5rem; margin-bottom: 2rem;">
                    <h3 style="margin-bottom: 1rem;">Agents by Department</h3>
                    {self._generate_agent_department_chart(agents_metrics.get('by_department', {}))}
                </div>
                
                <!-- Agent List -->
                <div class="card" style="padding: 1.5rem;">
                    <h3 style="margin-bottom: 1rem;">All Agents</h3>
                    {self.get_agent_cards_html()}
                </div>
            </div>
            """
        except Exception as e:
            logger.error(f"Error generating agents page HTML: {e}")
            return self._generate_error_html("agents", str(e))
    
    def _generate_agent_department_chart(self, dept_data: Dict[str, int]) -> str:
        """Generate department distribution chart for agents"""
        if not dept_data:
            return "<p>No department data available</p>"
        
        # Sort departments by agent count
        sorted_depts = sorted(dept_data.items(), key=lambda x: x[1], reverse=True)[:10]
        
        chart_html = '<div style="display: grid; gap: 0.5rem;">'
        max_count = max(dept_data.values()) if dept_data else 1
        
        for dept, count in sorted_depts:
            percentage = (count / max_count) * 100
            chart_html += f"""
            <div style="display: grid; grid-template-columns: 150px 1fr 50px; align-items: center; gap: 1rem;">
                <div style="font-size: 0.9rem; color: var(--secondary-text);">{dept}</div>
                <div style="background: var(--border-color); height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #3b82f6, #1e40af); height: 100%; width: {percentage}%; transition: width 0.3s ease;"></div>
                </div>
                <div style="font-size: 0.9rem; font-weight: bold; text-align: right;">{count}</div>
            </div>
            """
        
        chart_html += '</div>'
        return chart_html
'''
            
            content = content[:next_method] + new_method + content[next_method:]
            
            # Save the updated file
            with open('core/hq_metrics_integration.py', 'w') as f:
                f.write(content)
            
            print("Added get_agents_page_html method")

if __name__ == "__main__":
    print("Fixing blank UI pages in BoarderframeOS Corporate Headquarters...")
    
    # Fix the main corporate headquarters file
    if fix_corporate_headquarters():
        print("✓ Fixed corporate_headquarters.py")
    
    # Add missing methods to metrics integration
    add_missing_page_methods()
    
    print("\nFixes complete! Restart the Corporate Headquarters to see the changes.")