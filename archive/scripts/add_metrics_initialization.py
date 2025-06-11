#!/usr/bin/env python3
"""
Add metrics layer initialization to HealthDataManager
"""

import re


def add_metrics_initialization():
    """Add metrics initialization to the proper location"""
    print("🔧 Adding Metrics Layer Initialization")
    print("=" * 50)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, "r") as f:
        content = f.read()

    # Find the HealthDataManager __init__ method
    init_pattern = r"(self\.departments_data = \{\})"

    if re.search(init_pattern, content):
        print("✅ Found HealthDataManager init section")

        # Add metrics initialization after departments_data
        replacement = r"""\1

        # === METRICS LAYER INTEGRATION ===
        # Initialize the comprehensive metrics layer
        try:
            self.metrics_layer = HQMetricsIntegration()
            print("✅ Metrics layer initialized successfully")
        except Exception as e:
            print(f"⚠️ Failed to initialize metrics layer: {e}")
            self.metrics_layer = None"""

        content = re.sub(init_pattern, replacement, content)

        # Write back
        with open(file_path, "w") as f:
            f.write(content)

        print("✅ Added metrics layer initialization to HealthDataManager")
    else:
        print("❌ Could not find init pattern")


if __name__ == "__main__":
    add_metrics_initialization()
