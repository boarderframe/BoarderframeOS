#!/usr/bin/env python3
"""
Fix all over-escaped braces in the f-string
"""

import re


def fix_all_braces():
    """Fix all instances of over-escaped braces"""

    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    print("Fixing all over-escaped braces...")

    # Find patterns of over-escaped braces and fix them
    # Replace patterns like }}}} with }}
    # Replace patterns like {{{ with {{

    # Count initial braces
    initial_triple_open = content.count('{{{')
    initial_triple_close = content.count('}}}')
    initial_quad_close = content.count('}}}}')

    print(f"Found {initial_triple_open} instances of triple open braces")
    print(f"Found {initial_triple_close} instances of triple close braces")
    print(f"Found {initial_quad_close} instances of quadruple close braces")

    # Fix them
    # Replace }}}} with }}
    content = re.sub(r'\}\}\}\}', '}}', content)

    # Replace {{{ with {{
    content = re.sub(r'\{\{\{', '{{', content)

    # Replace remaining }}} with }}
    content = re.sub(r'\}\}\}', '}}', content)

    # Save
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)

    # Verify
    final_triple_open = content.count('{{{')
    final_triple_close = content.count('}}}')
    final_quad_close = content.count('}}}}')

    print(f"\nAfter fix:")
    print(f"  {final_triple_open} instances of triple open braces")
    print(f"  {final_triple_close} instances of triple close braces")
    print(f"  {final_quad_close} instances of quadruple close braces")

    print("\n✓ Fixed all over-escaped braces")

    return True

if __name__ == "__main__":
    fix_all_braces()
