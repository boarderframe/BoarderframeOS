#!/usr/bin/env python3
"""
Enhance the metrics layer to use database colors and icons for all metric cards
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import psycopg2

from core.hq_metrics_layer import BFColors, BFIcons


class VisualMetadataCache:
    """Cache for visual metadata to avoid repeated database queries"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._cache = {
            "departments": {},
            "divisions": {},
            "agents": {},
            "leaders": {},
            "servers": {},
            "categories": {},  # For aggregate metrics
        }
        self._last_refresh = None
        self._cache_ttl = timedelta(minutes=10)

        # Default category colors for aggregate metrics
        self.category_colors = {
            "agents": "#3b82f6",  # Blue
            "leaders": "#ec4899",  # Pink
            "departments": "#10b981",  # Green
            "divisions": "#8b5cf6",  # Purple
            "database": "#14b8a6",  # Teal
            "servers": "#f59e0b",  # Amber
            "registry": "#6366f1",  # Indigo
        }

        # Default category icons
        self.category_icons = {
            "agents": "fa-robot",
            "leaders": "fa-crown",
            "departments": "fa-building",
            "divisions": "fa-sitemap",
            "database": "fa-database",
            "servers": "fa-server",
            "registry": "fa-network-wired",
        }

    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_config.get("host", "localhost"),
            port=self.db_config.get("port", 5434),
            database=self.db_config.get("database", "boarderframeos"),
            user=self.db_config.get("user", "boarderframe"),
            password=self.db_config.get("password", "boarderframe_secure_2025"),
        )

    def refresh_cache(self, force: bool = False):
        """Refresh the visual metadata cache"""
        now = datetime.now()

        # Check if cache is still valid
        if (
            not force
            and self._last_refresh
            and now - self._last_refresh < self._cache_ttl
        ):
            return

        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Fetch department visual metadata
            cur.execute(
                """
                SELECT id, name, configuration->'visual' as visual
                FROM departments
                WHERE configuration->'visual' IS NOT NULL
            """
            )

            for dept_id, name, visual in cur.fetchall():
                if visual:
                    self._cache["departments"][str(dept_id)] = visual
                    self._cache["departments"][name] = visual

            # Fetch division visual metadata
            cur.execute(
                """
                SELECT id, division_name, configuration->'visual' as visual
                FROM divisions
                WHERE configuration->'visual' IS NOT NULL
            """
            )

            for div_id, name, visual in cur.fetchall():
                if visual:
                    self._cache["divisions"][str(div_id)] = visual
                    self._cache["divisions"][name] = visual

            # Fetch agent visual metadata (from their departments)
            cur.execute(
                """
                SELECT
                    ar.agent_id, ar.name,
                    d.configuration->'visual' as dept_visual
                FROM agent_registry ar
                LEFT JOIN departments d ON ar.department_id = d.id
            """
            )

            for agent_id, name, dept_visual in cur.fetchall():
                # Agents inherit department colors but use agent icon
                if dept_visual:
                    agent_visual = (
                        dept_visual.copy() if isinstance(dept_visual, dict) else {}
                    )
                    agent_visual["icon"] = "fa-robot"
                    self._cache["agents"][str(agent_id)] = agent_visual
                    self._cache["agents"][name] = agent_visual

            # Fetch leader visual metadata (custom colors)
            cur.execute(
                """
                SELECT
                    dl.id, dl.name, dl.leadership_tier,
                    d.configuration->'visual' as dept_visual
                FROM department_leaders dl
                LEFT JOIN departments d ON dl.department_id = d.id
            """
            )

            for leader_id, name, tier, dept_visual in cur.fetchall():
                # Leaders get special colors based on tier
                leader_visual = {
                    "icon": "fa-crown" if tier == "executive" else "fa-user-tie",
                    "color": self._get_leader_color(tier),
                    "theme": tier,
                }
                self._cache["leaders"][str(leader_id)] = leader_visual
                self._cache["leaders"][name] = leader_visual

            # Set category visuals
            self._cache["categories"] = {
                "agents": {
                    "color": self.category_colors["agents"],
                    "icon": self.category_icons["agents"],
                },
                "leaders": {
                    "color": self.category_colors["leaders"],
                    "icon": self.category_icons["leaders"],
                },
                "departments": {
                    "color": self.category_colors["departments"],
                    "icon": self.category_icons["departments"],
                },
                "divisions": {
                    "color": self.category_colors["divisions"],
                    "icon": self.category_icons["divisions"],
                },
                "database": {
                    "color": self.category_colors["database"],
                    "icon": self.category_icons["database"],
                },
                "servers": {
                    "color": self.category_colors["servers"],
                    "icon": self.category_icons["servers"],
                },
            }

            cur.close()
            conn.close()

            self._last_refresh = now

        except Exception as e:
            print(f"Error refreshing visual metadata cache: {e}")

    def _get_leader_color(self, tier: str) -> str:
        """Get color for leader based on tier"""
        tier_colors = {
            "executive": "#dc2626",  # Red
            "division": "#7c3aed",  # Violet
            "department": "#ec4899",  # Pink
            "team": "#3b82f6",  # Blue
        }
        return tier_colors.get(tier, BFColors.LEADERSHIP)

    def get_visual(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
        entity_name: Optional[str] = None,
    ) -> Dict[str, str]:
        """Get visual metadata for an entity"""
        self.refresh_cache()

        # For categories
        if entity_type in self.category_icons and not entity_id and not entity_name:
            return self._cache["categories"].get(
                entity_type, {"color": BFColors.INFO, "icon": "fa-folder"}
            )

        # Get from cache
        cache_section = self._cache.get(entity_type, {})

        # Try ID first, then name
        visual = None
        if entity_id:
            visual = cache_section.get(str(entity_id))
        if not visual and entity_name:
            visual = cache_section.get(entity_name)

        # Return with defaults
        if visual:
            return {
                "color": visual.get("color", BFColors.INFO),
                "icon": visual.get(
                    "icon", self.category_icons.get(entity_type, "fa-folder")
                ),
                "theme": visual.get("theme", "default"),
            }

        # Default visuals by type
        return self._get_default_visual(entity_type)

    def _get_default_visual(self, entity_type: str) -> Dict[str, str]:
        """Get default visual for entity type"""
        defaults = {
            "agent": {"color": BFColors.INFO, "icon": BFIcons.AGENT},
            "leader": {"color": BFColors.LEADERSHIP, "icon": BFIcons.LEADER},
            "department": {"color": BFColors.OPERATIONS, "icon": BFIcons.DEPARTMENT},
            "division": {"color": BFColors.EXECUTIVE, "icon": BFIcons.DIVISION},
            "server": {"color": BFColors.NEUTRAL, "icon": BFIcons.SERVER},
            "database": {"color": BFColors.SUCCESS, "icon": BFIcons.DATABASE},
        }
        return defaults.get(entity_type, {"color": BFColors.INFO, "icon": "fa-folder"})


def update_metrics_layer():
    """Update the metrics layer files to use visual metadata cache"""
    print("🎨 Updating Metrics Layer for Visual Integration")
    print("=" * 60)

    # Read the current hq_metrics_layer.py
    with open("core/hq_metrics_layer.py", "r") as f:
        content = f.read()

    # Add visual metadata cache initialization
    cache_init = """
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._cache = {}
        self._cache_ttl = 30  # seconds
        # Initialize visual metadata cache
        from enhance_metrics_visual_integration import VisualMetadataCache
        self._visual_cache = VisualMetadataCache(db_config)
"""

    # Replace the __init__ method in MetricsCalculator
    import re

    content = re.sub(
        r"def __init__\(self, db_config: Dict\[str, Any\]\):\s*self\.db_config = db_config\s*self\._cache = \{\}\s*self\._cache_ttl = 30  # seconds",
        cache_init.strip(),
        content,
    )

    # Update department metrics to use visual cache
    dept_visual_code = """
                # Get visual configuration from cache
                visual = self._visual_cache.get_visual('departments', str(row[0]), row[1])

                dept_color = visual.get('color', self._get_department_color(row[1]))
                dept_icon = visual.get('icon', self._get_department_icon(row[1]))
"""

    # Replace the visual configuration code
    content = re.sub(
        r"# Get visual configuration from database.*?dept_icon = visual_config\.get\(\'icon\', self\._get_department_icon\(row\[1\]\)\)",
        dept_visual_code.strip(),
        content,
        flags=re.DOTALL,
    )

    # Save the updated file
    with open("core/hq_metrics_layer.py", "w") as f:
        f.write(content)

    print("✅ Updated hq_metrics_layer.py")

    # Now update hq_metrics_integration.py
    with open("core/hq_metrics_integration.py", "r") as f:
        integration_content = f.read()

    # Add import for visual cache
    if (
        "from enhance_metrics_visual_integration import VisualMetadataCache"
        not in integration_content
    ):
        integration_content = integration_content.replace(
            "logger = logging.getLogger(__name__)",
            """logger = logging.getLogger(__name__)

try:
    from enhance_metrics_visual_integration import VisualMetadataCache
except ImportError:
    VisualMetadataCache = None""",
        )

    # Update the _generate_metric_summary_cards method to use database colors
    new_summary_cards = '''
    def _generate_metric_summary_cards(self, metrics: Dict[str, Any]) -> str:
        """Generate summary cards for key metrics with database colors"""
        cards = []

        # Initialize visual cache if available
        visual_cache = None
        if VisualMetadataCache:
            try:
                visual_cache = VisualMetadataCache(self.metrics_calc.db_config)
                visual_cache.refresh_cache()
            except:
                pass

        # Helper function to extract value
        def get_value(data):
            if hasattr(data, 'value'):
                return data.value
            return data if data is not None else 0

        # Get visual metadata for categories
        def get_category_visual(category):
            if visual_cache:
                return visual_cache.get_visual(category)
            # Fallback to defaults
            defaults = {
                'agents': {'color': '#3b82f6', 'icon': 'fa-robot'},
                'leaders': {'color': '#ec4899', 'icon': 'fa-crown'},
                'departments': {'color': '#10b981', 'icon': 'fa-building'},
                'divisions': {'color': '#8b5cf6', 'icon': 'fa-sitemap'},
                'database': {'color': '#14b8a6', 'icon': 'fa-database'},
                'servers': {'color': '#f59e0b', 'icon': 'fa-server'}
            }
            return defaults.get(category, {'color': '#6b7280', 'icon': 'fa-folder'})

        # 1. Agents summary (first)
        agent_data = metrics.get('agents', {}).get('summary', {})
        if agent_data:
            total = get_value(agent_data.get('total', 0))
            online = get_value(agent_data.get('online', 0))
            visual = get_category_visual('agents')
            cards.append(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">Agents</div>
                            <div style="font-size: 2rem; font-weight: bold;">{total}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">{online} online</div>
                        </div>
                        <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    </div>
                </div>
            """)

        # 2. Leaders summary (second)
        leaders_data = metrics.get('leaders', {})
        if leaders_data:
            visual = get_category_visual('leaders')
            # Check if it's from metrics layer (has summary) or raw data
            if 'summary' in leaders_data:
                # From metrics layer
                summary = leaders_data.get('summary', {})
                total = get_value(summary.get('total', 0))
                active = get_value(summary.get('active', 0))
                cards.append(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.9;">Leaders</div>
                                <div style="font-size: 2rem; font-weight: bold;">{total}</div>
                                <div style="font-size: 0.85rem; opacity: 0.8;">{active} active leaders</div>
                            </div>
                            <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        </div>
                    </div>
                """)
            else:
                # From raw data (legacy format)
                leaders_count = len(leaders_data) if isinstance(leaders_data, (list, dict)) else 0
                cards.append(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.9;">Leaders</div>
                                <div style="font-size: 2rem; font-weight: bold;">{leaders_count}</div>
                                <div style="font-size: 0.85rem; opacity: 0.8;">Organizational leaders</div>
                            </div>
                            <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        </div>
                    </div>
                """)

        # 3. Departments summary (third)
        dept_data = metrics.get('departments', {}).get('summary', {})
        if dept_data:
            total = get_value(dept_data.get('total', 0))
            active = get_value(dept_data.get('active', 0))
            visual = get_category_visual('departments')
            cards.append(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">Departments</div>
                            <div style="font-size: 2rem; font-weight: bold;">{total}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">{active} active</div>
                        </div>
                        <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    </div>
                </div>
            """)

        # 4. Divisions summary (fourth)
        div_data = metrics.get('divisions', {}).get('summary', {})
        divisions_count = 0

        if div_data:
            divisions_count = get_value(div_data.get('total', 0))

        # If no divisions data, check departments summary for divisions count
        if divisions_count == 0 and dept_data:
            divisions_value = dept_data.get('divisions')
            if divisions_value:
                divisions_count = get_value(divisions_value)

        # If still no data, count unique divisions from departments
        if divisions_count == 0:
            dept_details = metrics.get('departments', {}).get('individual', [])
            if dept_details:
                unique_divisions = set()
                for dept in dept_details:
                    if hasattr(dept, 'metadata') and dept.metadata.get('division'):
                        unique_divisions.add(dept.metadata['division'])
                divisions_count = len(unique_divisions)

        if divisions_count > 0:
            visual = get_category_visual('divisions')
            cards.append(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">Divisions</div>
                            <div style="font-size: 2rem; font-weight: bold;">{divisions_count}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">Organizational units</div>
                        </div>
                        <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    </div>
                </div>
            """)

        # 5. Database summary (fifth)
        database_metrics = metrics.get('database', {})
        if database_metrics:
            visual = get_category_visual('database')
            # Check if it's from metrics layer (has summary) or raw data
            if 'summary' in database_metrics:
                # From metrics layer
                summary = database_metrics.get('summary', {})
                size = get_value(summary.get('size', 'Unknown'))
                tables = get_value(summary.get('tables', 0))
                connections_data = database_metrics.get('connections', {})
                active_conn = get_value(connections_data.get('active', 0))
                total_conn = get_value(connections_data.get('total', 0))

                cards.append(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.9;">Database</div>
                                <div style="font-size: 2rem; font-weight: bold;">{size}</div>
                                <div style="font-size: 0.85rem; opacity: 0.8;">{tables} tables • {active_conn}/{total_conn} connections</div>
                            </div>
                            <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        </div>
                    </div>
                """)
            else:
                # From raw data (legacy format)
                db_size = database_metrics.get('database_size', 'Unknown')
                tables_count = len(database_metrics.get('tables', []))
                connections = database_metrics.get('active_connections', 0)
                cards.append(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.9;">Database</div>
                                <div style="font-size: 2rem; font-weight: bold;">{db_size}</div>
                                <div style="font-size: 0.85rem; opacity: 0.8;">{tables_count} tables • {connections} connections</div>
                            </div>
                            <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        </div>
                    </div>
                """)

        # 6. Servers summary (last)
        server_data = metrics.get('servers', {}).get('summary', {})
        if server_data:
            total = get_value(server_data.get('total', 0))
            online = get_value(server_data.get('online', 0))
            visual = get_category_visual('servers')
            cards.append(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">Servers</div>
                            <div style="font-size: 2rem; font-weight: bold;">{total}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">{online} online</div>
                        </div>
                        <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    </div>
                </div>
            """)

        return '\\n'.join(cards)
'''

    # Replace the _generate_metric_summary_cards method
    integration_content = re.sub(
        r"def _generate_metric_summary_cards\(self, metrics: Dict\[str, Any\]\) -> str:.*?return \'\\\n\'\.join\(cards\)",
        new_summary_cards.strip(),
        integration_content,
        flags=re.DOTALL,
    )

    # Save the updated integration file
    with open("core/hq_metrics_integration.py", "w") as f:
        f.write(integration_content)

    print("✅ Updated hq_metrics_integration.py")

    # Run the visual metadata population if needed
    print("\n🎨 Ensuring visual metadata is populated...")
    from populate_visual_metadata import populate_visual_metadata

    populate_visual_metadata()

    print("\n✅ Visual integration complete!")
    print("\nThe metrics layer will now:")
    print("  • Fetch colors and icons from the database")
    print("  • Cache visual metadata for performance")
    print("  • Use category-specific colors for aggregate metrics")
    print("  • Apply consistent visual styling throughout")


if __name__ == "__main__":
    update_metrics_layer()
