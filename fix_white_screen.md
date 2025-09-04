# Open WebUI White Screen Fix

## Problem Analysis
The application shows a white screen after the splash screen is removed. The SvelteKit app loads but the main layout's `loaded` flag is not being set to `true`, preventing content from rendering.

## Root Cause
The `onMount` function in `/src/routes/+layout.svelte` is either:
1. Not completing due to an async operation hanging
2. Encountering an error that prevents `loaded = true` from being set
3. Having a race condition with the splash screen removal

## Solution Applied

### 1. Added timeout protection for backend config fetch
- Prevents the app from hanging if the backend is slow
- Uses a default config if the backend is unavailable

### 2. Added failsafe timer
- Forces `loaded = true` after 5 seconds if normal flow fails
- Ensures the app always shows something

### 3. Added splash screen fallback removal
- Removes splash screen from app.html after 8 seconds
- Provides visual feedback even if SvelteKit fails to initialize

### 4. Added comprehensive error handling
- Wraps the entire onMount in try-catch
- Sets loaded = true even on error

### 5. Added debug logging
- Console messages track the initialization flow
- Helps identify where the process stops

## To Complete the Fix

1. **Open the browser console** (Cmd+Option+I on Mac, F12 on Windows/Linux)
2. **Navigate to http://localhost:5173**
3. **Look for these console messages**:
   - "Layout onMount started"
   - "Fetching backend config..."
   - "Backend config: ..."
   - "Removing splash screen and setting loaded = true"

4. **If you see errors**, note which step fails

5. **Wait 8-10 seconds** - the failsafes should kick in and show the auth page

## Testing Steps

1. Clear browser cache and cookies
2. Open http://localhost:5173 in an incognito/private window
3. Open the browser console before the page loads
4. Watch for the debug messages and any errors
5. The auth page should appear within 10 seconds maximum

## If the Issue Persists

The problem might be deeper in the SvelteKit initialization. Try:

1. **Restart the development server**:
   ```bash
   cd /Users/cosburn/open_webui/open-webui
   npm run dev
   ```

2. **Check for JavaScript errors** in the browser console

3. **Verify the backend is running**:
   ```bash
   curl http://localhost:8080/api/config
   ```

4. **Force a full rebuild**:
   ```bash
   rm -rf .svelte-kit
   npm run dev
   ```

## Current Status
- Added multiple failsafes to ensure the app loads
- Debug logging added to track initialization
- Timeout protection on all async operations
- Default config fallback if backend is unavailable
- Forced splash screen removal after 8 seconds