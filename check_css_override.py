#!/usr/bin/env python3
"""
Check for CSS that might be overriding tab display
"""

import requests
from bs4 import BeautifulSoup
import re

def check_css_override():
    """Find any CSS that might be hiding tabs"""
    print("🔍 Checking for CSS Override Issues")
    print("=" * 60)
    
    response = requests.get('http://localhost:8888')
    
    # Extract all CSS
    css_blocks = re.findall(r'<style[^>]*>(.*?)</style>', response.text, re.DOTALL)
    
    print(f"\n📊 Found {len(css_blocks)} style blocks")
    
    # Look for any display:none that might affect tabs
    problematic_rules = []
    
    for i, css in enumerate(css_blocks):
        lines = css.split('\n')
        for j, line in enumerate(lines):
            if 'display:' in line.replace(' ', ''):
                # Get context (previous few lines to see selector)
                start = max(0, j-3)
                context = lines[start:j+2]
                context_str = '\n'.join(context)
                
                # Check if it might affect tabs
                if any(keyword in context_str for keyword in ['tab-content', '.card', 'div', '*']):
                    if 'none' in line:
                        problematic_rules.append({
                            'block': i,
                            'line': j,
                            'context': context_str,
                            'type': 'display:none'
                        })
    
    if problematic_rules:
        print(f"\n⚠️ Found {len(problematic_rules)} potentially problematic CSS rules:")
        for rule in problematic_rules[:5]:  # Show first 5
            print(f"\nStyle block {rule['block']}, line {rule['line']}:")
            print(rule['context'])
    
    # Check for !important rules
    important_count = response.text.count('!important')
    print(f"\n📊 Found {important_count} !important rules")
    
    # Check specifically for .tab-content rules
    print("\n🎯 Specific .tab-content CSS rules:")
    for css in css_blocks:
        if '.tab-content' in css:
            # Extract just the tab-content rules
            tab_rules = re.findall(r'\.tab-content[^{]*\{[^}]+\}', css, re.DOTALL)
            for rule in tab_rules:
                print(f"\n{rule.strip()}")
    
    # Check for any inline styles on tab divs
    soup = BeautifulSoup(response.text, 'html.parser')
    tabs = soup.find_all('div', class_='tab-content')
    
    print(f"\n📊 Checking {len(tabs)} tab elements for inline styles:")
    for tab in tabs:
        if tab.get('style'):
            print(f"  {tab.get('id')}: style='{tab.get('style')}'")
    
    # Check if there's a global CSS reset
    if '* {' in response.text or '*{' in response.text:
        print("\n⚠️ Found global CSS reset (*) - might affect display")
    
    # Look for visibility:hidden
    if 'visibility:' in response.text.replace(' ', ''):
        print("\n⚠️ Found visibility rules that might hide content")


if __name__ == "__main__":
    check_css_override()