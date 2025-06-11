#!/usr/bin/env python3
"""
Test calling showTab directly via browser console
"""

print("""
🔍 Direct Tab Testing Instructions
==================================

1. Open Corporate HQ at http://localhost:8888
2. Open browser console (F12 > Console)
3. Try these commands one by one:

   showTab('agents')
   showTab('departments')
   showTab('database')

4. Check for any JavaScript errors in the console

5. Also try:
   document.getElementById('departments')
   document.getElementById('departments').classList
   document.getElementById('departments').style.display

This will help identify if:
- The showTab function exists
- The tab elements exist
- There are any JavaScript errors
- The CSS is being applied correctly
""")
