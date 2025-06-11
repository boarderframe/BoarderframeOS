#!/usr/bin/env python3
"""
Populate visual metadata (colors and icons) for departments and divisions
"""

import json

import psycopg2

from core.hq_metrics_layer import BFColors, BFIcons

# Department visual mappings
DEPARTMENT_VISUALS = {
    # Executive & Leadership
    'Executive Leadership': {'color': BFColors.EXECUTIVE, 'icon': 'fa-crown', 'theme': 'executive'},
    'Strategic Planning': {'color': BFColors.EXECUTIVE, 'icon': 'fa-chess', 'theme': 'executive'},
    'Board Relations': {'color': BFColors.EXECUTIVE, 'icon': 'fa-handshake', 'theme': 'executive'},

    # Engineering & Technology
    'Software Engineering': {'color': BFColors.ENGINEERING, 'icon': 'fa-code', 'theme': 'engineering'},
    'Infrastructure': {'color': BFColors.INFRASTRUCTURE, 'icon': 'fa-server', 'theme': 'infrastructure'},
    'DevOps': {'color': BFColors.INFRASTRUCTURE, 'icon': 'fa-infinity', 'theme': 'infrastructure'},
    'Quality Assurance': {'color': BFColors.ENGINEERING, 'icon': 'fa-check-double', 'theme': 'engineering'},
    'Architecture': {'color': BFColors.ENGINEERING, 'icon': 'fa-drafting-compass', 'theme': 'engineering'},

    # Operations
    'Operations': {'color': BFColors.OPERATIONS, 'icon': 'fa-cogs', 'theme': 'operations'},
    'Business Operations': {'color': BFColors.OPERATIONS, 'icon': 'fa-briefcase', 'theme': 'operations'},
    'Supply Chain': {'color': BFColors.OPERATIONS, 'icon': 'fa-truck', 'theme': 'operations'},
    'Customer Service': {'color': BFColors.OPERATIONS, 'icon': 'fa-headset', 'theme': 'operations'},

    # Intelligence & Analytics
    'Business Intelligence': {'color': BFColors.INTELLIGENCE, 'icon': 'fa-brain', 'theme': 'intelligence'},
    'Data Analytics': {'color': BFColors.INTELLIGENCE, 'icon': 'fa-chart-line', 'theme': 'intelligence'},
    'Market Research': {'color': BFColors.INTELLIGENCE, 'icon': 'fa-microscope', 'theme': 'intelligence'},

    # Innovation & Research
    'Innovation Lab': {'color': BFColors.INNOVATION, 'icon': 'fa-lightbulb', 'theme': 'innovation'},
    'Research & Development': {'color': BFColors.RESEARCH, 'icon': 'fa-flask', 'theme': 'research'},
    'Product Development': {'color': BFColors.INNOVATION, 'icon': 'fa-cube', 'theme': 'innovation'},

    # Support Functions
    'Human Resources': {'color': BFColors.WARNING, 'icon': 'fa-users', 'theme': 'support'},
    'Finance': {'color': BFColors.SUCCESS, 'icon': 'fa-dollar-sign', 'theme': 'support'},
    'Legal': {'color': BFColors.NEUTRAL, 'icon': 'fa-gavel', 'theme': 'support'},
    'Security': {'color': BFColors.DANGER, 'icon': 'fa-shield-alt', 'theme': 'security'},
    'Compliance': {'color': BFColors.WARNING, 'icon': 'fa-clipboard-check', 'theme': 'compliance'},

    # Sales & Marketing
    'Sales': {'color': BFColors.SUCCESS, 'icon': 'fa-chart-line', 'theme': 'sales'},
    'Marketing': {'color': BFColors.INNOVATION, 'icon': 'fa-bullhorn', 'theme': 'marketing'},
    'Business Development': {'color': BFColors.INFO, 'icon': 'fa-handshake', 'theme': 'business'},
}

# Division visual mappings (by number for now)
DIVISION_VISUALS = {
    1: {'color': BFColors.DIVISION_1, 'icon': 'fa-layer-group', 'theme': 'division'},
    2: {'color': BFColors.DIVISION_2, 'icon': 'fa-layer-group', 'theme': 'division'},
    3: {'color': BFColors.DIVISION_3, 'icon': 'fa-layer-group', 'theme': 'division'},
    4: {'color': BFColors.DIVISION_4, 'icon': 'fa-layer-group', 'theme': 'division'},
    5: {'color': BFColors.DIVISION_5, 'icon': 'fa-layer-group', 'theme': 'division'},
    6: {'color': BFColors.DIVISION_6, 'icon': 'fa-layer-group', 'theme': 'division'},
    7: {'color': BFColors.DIVISION_7, 'icon': 'fa-layer-group', 'theme': 'division'},
    8: {'color': BFColors.DIVISION_8, 'icon': 'fa-layer-group', 'theme': 'division'},
    9: {'color': BFColors.DIVISION_9, 'icon': 'fa-layer-group', 'theme': 'division'},
}

def get_default_visual(name, entity_type='department'):
    """Get default visual configuration based on name"""
    name_lower = name.lower()

    if entity_type == 'department':
        # Check exact matches first
        if name in DEPARTMENT_VISUALS:
            return DEPARTMENT_VISUALS[name]

        # Check partial matches
        for key, visual in DEPARTMENT_VISUALS.items():
            if key.lower() in name_lower or name_lower in key.lower():
                return visual

        # Default based on keywords
        if any(x in name_lower for x in ['executive', 'leadership', 'chief']):
            return {'color': BFColors.EXECUTIVE, 'icon': 'fa-crown', 'theme': 'executive'}
        elif any(x in name_lower for x in ['engineering', 'software', 'tech']):
            return {'color': BFColors.ENGINEERING, 'icon': 'fa-code', 'theme': 'engineering'}
        elif any(x in name_lower for x in ['operation', 'ops']):
            return {'color': BFColors.OPERATIONS, 'icon': 'fa-cogs', 'theme': 'operations'}
        elif any(x in name_lower for x in ['infrastructure', 'system', 'network']):
            return {'color': BFColors.INFRASTRUCTURE, 'icon': 'fa-server', 'theme': 'infrastructure'}
        elif any(x in name_lower for x in ['intelligence', 'analytics', 'data']):
            return {'color': BFColors.INTELLIGENCE, 'icon': 'fa-brain', 'theme': 'intelligence'}
        elif any(x in name_lower for x in ['innovation', 'lab', 'experimental']):
            return {'color': BFColors.INNOVATION, 'icon': 'fa-lightbulb', 'theme': 'innovation'}
        elif any(x in name_lower for x in ['research', 'science']):
            return {'color': BFColors.RESEARCH, 'icon': 'fa-flask', 'theme': 'research'}
        elif any(x in name_lower for x in ['security', 'defense']):
            return {'color': BFColors.DANGER, 'icon': 'fa-shield-alt', 'theme': 'security'}
        elif any(x in name_lower for x in ['finance', 'accounting']):
            return {'color': BFColors.SUCCESS, 'icon': 'fa-dollar-sign', 'theme': 'finance'}
        else:
            return {'color': BFColors.INFO, 'icon': 'fa-building', 'theme': 'default'}

    return {'color': BFColors.INFO, 'icon': 'fa-folder', 'theme': 'default'}

def populate_visual_metadata():
    """Populate visual metadata in database"""
    print("🎨 Populating Visual Metadata")
    print("=" * 60)

    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='boarderframeos',
            user='boarderframe',
            password='boarderframe_secure_2025'
        )
        cur = conn.cursor()

        # Run migration first
        print("\n📝 Running migration...")
        with open('migrations/007_add_visual_metadata.sql', 'r') as f:
            cur.execute(f.read())
        conn.commit()
        print("   ✅ Migration completed")

        # Update departments
        print("\n🏢 Updating department visual metadata...")
        cur.execute("SELECT id, name, configuration FROM departments")
        departments = cur.fetchall()

        updated = 0
        for dept_id, name, config in departments:
            visual = get_default_visual(name, 'department')

            # Update configuration
            config = config or {}
            config['visual'] = visual

            cur.execute("""
                UPDATE departments
                SET configuration = %s
                WHERE id = %s
            """, (json.dumps(config), dept_id))

            updated += 1
            print(f"   ✅ {name}: {visual['icon']} ({visual['color']})")

        print(f"\n   Updated {updated} departments")

        # Update divisions
        print("\n🏛️ Updating division visual metadata...")
        # Check what columns divisions table has
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'divisions'
            ORDER BY ordinal_position
        """)
        div_columns = [col[0] for col in cur.fetchall()]
        print(f"   Division columns: {div_columns}")

        # Try to get divisions with appropriate column
        name_col = 'division_name' if 'division_name' in div_columns else 'id'
        cur.execute(f"SELECT id, {name_col} FROM divisions")
        divisions = cur.fetchall()

        div_updated = 0
        for div_id, name in divisions:
            # Extract division number from name if possible
            div_num = None
            try:
                # Try to extract number from name like "Division 1" or "Div 1"
                import re
                match = re.search(r'\d+', name)
                if match:
                    div_num = int(match.group())
            except:
                pass

            visual = DIVISION_VISUALS.get(div_num, {
                'color': BFColors.INFO,
                'icon': 'fa-layer-group',
                'theme': 'division'
            })

            config = {'visual': visual}

            cur.execute("""
                UPDATE divisions
                SET configuration = %s
                WHERE id = %s
            """, (json.dumps(config), div_id))

            div_updated += 1
            print(f"   ✅ {name}: {visual['icon']} ({visual['color']})")

        print(f"\n   Updated {div_updated} divisions")

        # Also update department_registry
        print("\n📋 Updating department registry visual metadata...")
        cur.execute("""
            UPDATE department_registry dr
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{visual}',
                (SELECT configuration->'visual' FROM departments d WHERE d.name = dr.name),
                true
            )
            WHERE EXISTS (SELECT 1 FROM departments d WHERE d.name = dr.name)
        """)

        registry_updated = cur.rowcount
        print(f"   ✅ Updated {registry_updated} registry entries")

        conn.commit()
        cur.close()
        conn.close()

        print("\n✅ Visual metadata population complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    populate_visual_metadata()
