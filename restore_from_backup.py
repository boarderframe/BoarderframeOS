#!/usr/bin/env python3
"""
Restore the corporate headquarters from backup since the CSS is too corrupted
"""

import shutil

def restore_from_backup():
    """Restore from the backup file"""
    
    print("The current file has too many CSS syntax errors.")
    print("Restoring from backup...")
    
    try:
        # Make a copy of the corrupted file just in case
        shutil.copy('corporate_headquarters.py', 'corporate_headquarters.py.corrupted')
        print("✓ Saved corrupted file as corporate_headquarters.py.corrupted")
        
        # Restore from backup
        shutil.copy('corporate_headquarters.py.backup', 'corporate_headquarters.py')
        print("✓ Restored from corporate_headquarters.py.backup")
        
        print("\nThe file has been restored to its backup state.")
        print("All the UI fixes we applied have been lost.")
        print("The server should now start, but tabs may not display properly.")
        print("\nYou may want to:")
        print("1. Start the server to verify it works")
        print("2. Re-apply specific fixes carefully")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    restore_from_backup()