#!/usr/bin/env python3
"""
Test script to verify the refresh modal fixes
"""

import re


def verify_fixes():
    """Verify all fixes were applied correctly"""

    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    print("🔍 Verifying refresh modal fixes...\n")

    fixes_verified = []
    fixes_failed = []

    # Test 1: Check for fixed close button ID
    if 'id="closeRefreshBtnHeader"' in content and 'onclick="closeGlobalRefreshModal()"' in content:
        fixes_verified.append("✅ Close button header ID fixed")
    else:
        fixes_failed.append("❌ Close button header ID not fixed")

    # Test 2: Check for closeModal function
    if 'function closeModal(modalId)' in content:
        fixes_verified.append("✅ closeModal function added")
    else:
        fixes_failed.append("❌ closeModal function missing")

    # Test 3: Check for async organizational data refresh
    if 'await loop.run_in_executor(None, self.dashboard._fetch_organizational_data)' in content:
        fixes_verified.append("✅ Organizational data refresh is async")
    else:
        fixes_failed.append("❌ Organizational data refresh not async")

    # Test 4: Check for debug logging
    if 'Refreshed organizational data:' in content:
        fixes_verified.append("✅ Debug logging added")
    else:
        fixes_failed.append("❌ Debug logging missing")

    # Test 5: Check for failed component handling
    if 'failed_components' in content and 'updateComponentStatus(component, \'error\')' in content:
        fixes_verified.append("✅ Failed component handling added")
    else:
        fixes_failed.append("❌ Failed component handling missing")

    # Print results
    print("Fixes Verified:")
    for fix in fixes_verified:
        print(f"  {fix}")

    if fixes_failed:
        print("\nFixes Failed:")
        for fix in fixes_failed:
            print(f"  {fix}")

    # Check for duplicate IDs that might cause issues
    print("\n🔍 Checking for potential ID conflicts...")

    # Count occurrences of closeRefreshBtn
    close_btn_count = len(re.findall(r'id="closeRefreshBtn"', content))
    if close_btn_count > 1:
        print(f"⚠️  Found {close_btn_count} elements with id='closeRefreshBtn' - potential conflict!")
    else:
        print("✅ No ID conflicts for closeRefreshBtn")

    # Summary
    total_fixes = len(fixes_verified) + len(fixes_failed)
    success_rate = (len(fixes_verified) / total_fixes * 100) if total_fixes > 0 else 0

    print(f"\n📊 Summary: {len(fixes_verified)}/{total_fixes} fixes verified ({success_rate:.0f}% success)")

    if success_rate == 100:
        print("\n🎉 All fixes successfully applied!")
        print("\n🚀 Ready to test:")
        print("1. Start Corporate HQ: python corporate_headquarters.py")
        print("2. Click 'Refresh OS' button")
        print("3. Watch all components refresh")
        print("4. Test both close buttons (X in header and Close in footer)")
    else:
        print("\n⚠️  Some fixes may not have been applied correctly.")
        print("Please review the failed fixes above.")

if __name__ == "__main__":
    verify_fixes()
