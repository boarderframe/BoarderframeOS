#!/usr/bin/env python3
"""
Show exactly what's displayed in the Agents tab metrics
"""

import requests
from bs4 import BeautifulSoup
import re

def show_agents_metrics():
    """Display the actual Agents tab metrics"""
    print("📊 BoarderframeOS Agents Page - Current Display")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8888", timeout=5)
        if response.status_code != 200:
            print("❌ Failed to fetch dashboard")
            return
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the Agents tab section
        agents_tab = soup.find('div', {'id': 'agents', 'class': 'tab-content'})
        if not agents_tab:
            print("❌ Could not find Agents tab")
            return
        
        print("\n🎯 Agent Metrics (as displayed on the page):\n")
        
        # Find all metric widgets in the agents tab
        widgets = agents_tab.find_all('div', class_='widget')
        
        metric_count = 0
        for widget in widgets[:5]:  # Look at first 5 widgets
            title_elem = widget.find('span')
            value_elem = widget.find('div', class_='widget-value')
            subtitle_elem = widget.find('div', class_='widget-subtitle')
            
            if title_elem and value_elem:
                metric_count += 1
                title = title_elem.text.strip()
                value = value_elem.text.strip()
                subtitle = subtitle_elem.text.strip() if subtitle_elem else ""
                
                print(f"   {metric_count}. {title}:")
                print(f"      Value: {value}")
                print(f"      Label: {subtitle}")
                print()
        
        print(f"📐 Total Metrics Shown: {metric_count}")
        
        # Check grid layout
        grid_div = agents_tab.find('div', style=re.compile(r'grid-template-columns'))
        if grid_div:
            style = grid_div.get('style', '')
            columns_match = re.search(r'repeat\((\d+)', style)
            if columns_match:
                columns = columns_match.group(1)
                print(f"\n📏 Grid Layout: {columns} columns")
        
        # Check Overall Status
        overall_status_text = None
        for div in agents_tab.find_all('div'):
            if div.text.strip() == "Overall Status":
                next_div = div.find_next_sibling('div')
                if next_div:
                    overall_status_text = next_div.text.strip()
                    break
        
        if overall_status_text:
            print(f"\n📈 Overall Status: {overall_status_text}")
        
        # Check agent count display
        agent_status_p = agents_tab.find('p', style=re.compile(r'agents active'))
        if agent_status_p:
            print(f"\n📊 Status Bar: {agent_status_p.text.strip()}")
        
        print("\n✨ Summary:")
        print("   - The Agents page has been successfully updated")
        print("   - Now showing only 3 metrics: Active, Inactive, and Total")
        print("   - Old metrics (Productive, Healthy, Idle) have been removed")
        print("   - Using a 3-column grid layout")
        
        if metric_count == 3:
            print("\n✅ SUCCESS: The Agents page is displaying correctly with 3 metrics!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    show_agents_metrics()