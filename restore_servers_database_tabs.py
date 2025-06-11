#!/usr/bin/env python3
"""
Restore the missing Servers and Database tabs
"""

def restore_servers_database_tabs():
    """Add back the missing Servers tab"""
    print("🔧 Restoring Servers Tab")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Find where to insert (after divisions tab, before system tab)
    insertion_point = content.find('        </div></div>\n\n        <!-- System Tab -->')

    if insertion_point > 0:
        print("✅ Found insertion point after divisions tab")

        # The servers tab content from backup
        servers_tab = '''
        <!-- Servers Tab -->
        <div id="services" class="tab-content">
            <!-- System Status Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #10b98120; background: linear-gradient(135deg, #10b98108, #10b98103);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #10b981, #10b981cc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #10b98140;
                        ">
                            <i class="fas fa-server"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Servers Status</h3>
                            <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                {healthy_services} healthy systems • Infrastructure monitoring
                            </p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="text-align: right;">
                            <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">System Health</div>
                            <div style="font-size: 1rem; font-weight: 600; color: {'var(--success-color)' if healthy_services == total_services else 'var(--warning-color)' if healthy_services > 0 else 'var(--danger-color)'};">
                                {(healthy_services/total_services*100):.0f}% Operational
                            </div>
                            <div style="font-size: 0.75rem; color: var(--secondary-text); margin-top: 0.25rem;">
                                Last updated: <span id="systems-last-update">{self._get_formatted_timestamp()}</span>
                            </div>
                        </div>
                        <button
                            onclick="refreshSystemsMetrics()"
                            id="systemsRefreshBtn"
                            style="
                                background: linear-gradient(135deg, #10b981, #059669);
                                color: white;
                                border: none;
                                padding: 0.5rem 1rem;
                                border-radius: 8px;
                                font-size: 0.85rem;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                gap: 0.5rem;
                                transition: all 0.2s ease;
                            "
                            onmouseover="this.style.background='linear-gradient(135deg, #059669, #047857)'"
                            onmouseout="this.style.background='linear-gradient(135deg, #10b981, #059669)'"
                        >
                            <i class="fas fa-sync-alt"></i>
                            <span>Refresh</span>
                        </button>
                    </div>
                </div>

                <!-- Systems Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; align-items: stretch;">
                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-server" style="color: var(--success-color);"></i>
                                <span>Total</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--success-color);">
                            {total_services}
                        </div>
                        <div class="widget-subtitle">Services</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-check-circle" style="color: var(--success-color);"></i>
                                <span>Healthy</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--success-color);">
                            {healthy_services}
                        </div>
                        <div class="widget-subtitle">Operational</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-exclamation-triangle" style="color: var(--warning-color);"></i>
                                <span>Degraded</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--warning-color);">
                            {degraded_services}
                        </div>
                        <div class="widget-subtitle">Warning</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-times-circle" style="color: var(--danger-color);"></i>
                                <span>Offline</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--danger-color);">
                            {offline_services}
                        </div>
                        <div class="widget-subtitle">Down</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-clock" style="color: var(--info-color);"></i>
                                <span>Uptime</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--info-color);">
                            99.9%
                        </div>
                        <div class="widget-subtitle">Average</div>
                    </div>
                </div>
            </div>

            <!-- Service Details -->
            <div class="card full-width">
                <h3 style="margin-bottom: 1.5rem;">
                    <i class="fas fa-list"></i> Service Details
                </h3>
                {self._generate_services_html()}
            </div>
        </div>'''

        # Insert the servers tab
        content = content[:insertion_point + 17] + servers_tab + content[insertion_point + 17:]

        # Write back
        with open(file_path, 'w') as f:
            f.write(content)

        print("✅ Restored Servers tab")
        print("\n🚀 Servers tab should now be visible in Corporate HQ!")
    else:
        print("❌ Could not find insertion point")


if __name__ == "__main__":
    restore_servers_database_tabs()
