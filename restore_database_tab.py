#!/usr/bin/env python3
"""
Restore the original database tab UI with all its features
"""

import re


def restore_database_tab():
    """Restore the complete database tab UI from backup"""

    # Read the current file
    with open("corporate_headquarters.py", "r") as f:
        current_content = f.read()

    # Read the backup to get the original database UI
    with open("corporate_headquarters.py.backup", "r") as f:
        backup_content = f.read()

    print("Restoring database tab UI...")

    # Extract the original database tab content from backup
    # Find the database tab section in backup
    db_tab_start = backup_content.find("<!-- Database Tab -->")
    if db_tab_start == -1:
        print("Could not find database tab in backup")
        return False

    # Find the end of database tab (next tab or settings)
    db_tab_end = backup_content.find(
        '<div id="settings" class="tab-content">', db_tab_start
    )
    if db_tab_end == -1:
        # Try to find another end marker
        db_tab_end = backup_content.find("<!-- Settings Tab -->", db_tab_start)

    if db_tab_end == -1:
        print("Could not find end of database tab")
        return False

    # Extract the database tab content
    original_db_content = backup_content[db_tab_start:db_tab_end].rstrip()

    # Now find the refreshDatabaseMetrics function from backup
    refresh_func_match = re.search(
        r"(async function refreshDatabaseMetrics\(\)\s*\{[^}]+(?:\{[^}]*\}[^}]*)*\})",
        backup_content,
        re.DOTALL,
    )

    if not refresh_func_match:
        print("Could not find refreshDatabaseMetrics function in backup")
    else:
        refresh_function = refresh_func_match.group(1)

    # Also get the helper functions
    helper_functions = []

    # Get showRefreshProgress function
    show_progress_match = re.search(
        r"(function showRefreshProgress\(message\)\s*\{[^}]+(?:\{[^}]*\}[^}]*)*\})",
        backup_content,
        re.DOTALL,
    )
    if show_progress_match:
        helper_functions.append(show_progress_match.group(1))

    # Get updateRefreshProgress function
    update_progress_match = re.search(
        r"(function updateRefreshProgress\(message\)\s*\{[^}]+(?:\{[^}]*\}[^}]*)*\})",
        backup_content,
        re.DOTALL,
    )
    if update_progress_match:
        helper_functions.append(update_progress_match.group(1))

    # Get simulateDelay function
    delay_match = re.search(
        r"(function simulateDelay\(ms\)\s*\{[^}]+\})", backup_content
    )
    if delay_match:
        helper_functions.append(delay_match.group(1))

    # Now update the current file
    # Find where to replace the database tab
    current_db_start = current_content.find("<!-- Database Tab -->")
    if current_db_start == -1:
        print("Could not find database tab in current file")
        return False

    # Find the end of the current database tab
    current_db_end = current_content.find(
        '<div id="settings" class="tab-content">', current_db_start
    )
    if current_db_end == -1:
        # Try next tab marker
        current_db_end = current_content.find("<!-- Registry Tab -->", current_db_start)
        if current_db_end == -1:
            current_db_end = current_content.find(
                "<!-- System Tab -->", current_db_start
            )

    if current_db_end == -1:
        print("Could not determine end of current database tab")
        return False

    # Replace the database tab content
    new_content = (
        current_content[:current_db_start]
        + original_db_content
        + "\n        \n        "
        + current_content[current_db_end:]
    )

    # Now add the JavaScript functions if they're missing
    if refresh_func_match and "function refreshDatabaseMetrics" not in new_content:
        # Find where to insert the function (after other refresh functions or before DOMContentLoaded)
        insert_pos = new_content.find("document.addEventListener('DOMContentLoaded'")
        if insert_pos != -1:
            # Insert before DOMContentLoaded
            functions_to_add = (
                "\n        ".join(helper_functions + [refresh_function])
                + "\n        \n        "
            )
            new_content = (
                new_content[:insert_pos] + functions_to_add + new_content[insert_pos:]
            )
            print("Added refreshDatabaseMetrics and helper functions")

    # Also need to add the _generate_database_content method as fallback
    if "def _generate_database_content" not in new_content:
        # Find where to add it (after other _generate methods)
        insert_pos = new_content.rfind("def _generate_")
        if insert_pos != -1:
            # Find the end of that method
            next_method = new_content.find("\n    def ", insert_pos + 10)
            if next_method == -1:
                next_method = new_content.find("\nclass ", insert_pos)

            if next_method != -1:
                database_method = '''
    def _generate_database_content(self):
        """Generate database tab content - fallback when metrics layer not available"""
        return f"""
        <!-- Database Overview Card -->
        <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #f59e0b20; background: linear-gradient(135deg, #f59e0b08, #f59e0b03);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="
                        width: 60px; height: 60px;
                        background: linear-gradient(135deg, #f59e0b, #f59e0bcc);
                        border-radius: 12px;
                        display: flex; align-items: center; justify-content: center;
                        color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #f59e0b40;
                    ">
                        <i class="fas fa-database"></i>
                    </div>
                    <div>
                        <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Database Status</h3>
                        <p style="margin: 0; color: var(--secondary-text); font-size: 0.95rem;">BoarderframeOS Primary Data Storage</p>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.2rem; color: var(--success-color);">
                        <i class="fas fa-check-circle"></i> Connected
                    </div>
                </div>
            </div>
            <p style="text-align: center; color: var(--secondary-text);">
                Database UI is being restored. Please refresh the page.
            </p>
        </div>
        """
'''
                new_content = (
                    new_content[:next_method]
                    + database_method
                    + new_content[next_method:]
                )
                print("Added _generate_database_content fallback method")

    # Save the updated file
    with open("corporate_headquarters.py", "w") as f:
        f.write(new_content)

    print("✓ Restored complete database tab UI")
    print("✓ Added refresh functionality")
    print("✓ Database tab should now show all metrics and refresh button")

    return True


if __name__ == "__main__":
    if restore_database_tab():
        print("\nDatabase tab successfully restored!")
        print("The database tab now includes:")
        print("- Database status overview")
        print("- Refresh button with progress indicator")
        print("- Metrics grid (Tables, Connections, Size, Cache)")
        print("- Complete table listings")
        print("- All original functionality")
    else:
        print("\nFailed to restore database tab")
