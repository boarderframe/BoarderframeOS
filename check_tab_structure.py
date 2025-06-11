#!/usr/bin/env python3
"""
Check the structure of tabs in corporate headquarters
"""

import re


def check_tab_structure():
    with open("corporate_headquarters.py", "r") as f:
        content = f.read()

    # Find all tab divs
    tabs = re.findall(r'<div id="([^"]+)" class="tab-content[^"]*">', content)
    print("Found tabs:", tabs)

    # For each tab, count opening and closing divs
    for tab in tabs:
        # Find the start and potential end of each tab
        tab_start = content.find(f'<div id="{tab}" class="tab-content')

        # Find the next tab or end marker
        next_positions = []
        for other_tab in tabs:
            if other_tab != tab:
                pos = content.find(
                    f'<div id="{other_tab}" class="tab-content', tab_start + 1
                )
                if pos > tab_start:
                    next_positions.append(pos)

        # Also check for script tags or end of content area
        script_pos = content.find("<script", tab_start)
        if script_pos > tab_start:
            next_positions.append(script_pos)

        if next_positions:
            tab_end = min(next_positions)
            tab_content = content[tab_start:tab_end]

            # Count divs
            open_divs = tab_content.count("<div")
            close_divs = tab_content.count("</div>")

            print(f"\n{tab} tab:")
            print(f"  Position: {tab_start}")
            print(f"  Open divs: {open_divs}")
            print(f"  Close divs: {close_divs}")
            print(f"  Difference: {open_divs - close_divs}")

            # Check if properly closed
            if open_divs - close_divs > 0:
                print(f"  ⚠️  Missing {open_divs - close_divs} closing </div> tags!")
            elif open_divs - close_divs < 0:
                print(f"  ⚠️  Extra {close_divs - open_divs} closing </div> tags!")
            else:
                print("  ✓ Properly balanced")


if __name__ == "__main__":
    check_tab_structure()
