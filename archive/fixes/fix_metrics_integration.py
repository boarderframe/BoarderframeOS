#!/usr/bin/env python3
"""
Fix the metrics integration file structure
"""


def fix_metrics_integration():
    """Remove duplicate methods and fix file structure"""

    with open("core/hq_metrics_integration.py", "r") as f:
        content = f.read()

    # Find where METRICS_CSS is defined
    css_start = content.find('# CSS for the metric cards\nMETRICS_CSS = """')
    if css_start == -1:
        print("Could not find METRICS_CSS definition")
        return False

    # Find the end of METRICS_CSS
    css_end = content.find('"""', css_start + 50)
    if css_end == -1:
        print("Could not find end of METRICS_CSS")
        return False

    # Find duplicate methods after METRICS_CSS
    duplicate_start = content.find(
        "    def get_agents_page_html(self) -> str:", css_end
    )

    if duplicate_start != -1:
        # Remove everything after METRICS_CSS except the closing quotes
        new_content = content[: css_end + 3]  # +3 for the closing """

        # Save the fixed file
        with open("core/hq_metrics_integration.py", "w") as f:
            f.write(new_content)

        print("✓ Removed duplicate methods after METRICS_CSS")
        print("✓ File structure fixed")
        return True
    else:
        print("No duplicates found to remove")
        return True


if __name__ == "__main__":
    fix_metrics_integration()
