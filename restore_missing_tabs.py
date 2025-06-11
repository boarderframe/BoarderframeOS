#!/usr/bin/env python3
"""
Restore the missing tabs (Leaders, Departments, Divisions)
"""

def restore_tabs():
    """Add back the missing tab content divs"""
    print("🔧 Restoring Missing Tabs")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Find where to insert the tabs (after agents tab closes)
    agents_tab_end = content.find('        </div>\n\n        <!-- System Tab -->')

    if agents_tab_end > 0:
        print("✅ Found insertion point after agents tab")

        # The missing tabs content
        missing_tabs = '''
        <!-- Leaders Tab -->
        <div id="leaders" class="tab-content">
            {self.metrics_layer.get_leaders_page_html() if self.metrics_layer and hasattr(self.metrics_layer, 'get_leaders_page_html') else self._generate_leaders_html()}
        </div>

        <!-- Departments Tab -->
        <div id="departments" class="tab-content">
            <!-- Department Overview Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #ec489920; background: linear-gradient(135deg, #ec489908, #ec489903);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #ec4899, #ec4899cc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #ec489940;
                        ">
                            <i class="fas fa-building"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Departments Status</h3>
                            <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                {total_departments} departments across {total_divisions} divisions • Organizational structure
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Department Status</div>
                        <div style="font-size: 1rem; font-weight: 600; color: var(--success-color);">
                            Operational
                        </div>
                    </div>
                </div>

                <!-- Department Metrics from Metrics Layer -->
                {self.metrics_layer.get_department_metrics_cards() if self.metrics_layer and hasattr(self.metrics_layer, 'get_department_metrics_cards') else ""}

                <!-- Department Cards -->
                <div style="grid-column: span 12;">
                    {self.metrics_layer.get_department_cards_html() if self.metrics_layer else self._generate_divisions_html()}
                </div>
            </div>
        </div>

        <!-- Divisions Tab -->
        <div id="divisions" class="tab-content">
            {self.metrics_layer.get_divisions_page_html() if self.metrics_layer and hasattr(self.metrics_layer, 'get_divisions_page_html') else self._generate_divisions_html()}
        </div>'''

        # Insert the missing tabs
        content = content[:agents_tab_end + 8] + missing_tabs + content[agents_tab_end + 8:]

        # Write back
        with open(file_path, 'w') as f:
            f.write(content)

        print("✅ Restored all missing tabs:")
        print("   - Leaders tab")
        print("   - Departments tab")
        print("   - Divisions tab")
        print("\n🚀 Tabs should now be visible in Corporate HQ!")
    else:
        print("❌ Could not find insertion point")


if __name__ == "__main__":
    restore_tabs()
