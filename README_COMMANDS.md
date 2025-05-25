# 🎯 BoarderframeOS Commands

## Quick Commands

| Command | Action |
|---------|--------|
| `./start` | Start the dashboard |
| `./ui` | Start the dashboard (alias) |
| `./dashboard` | Start the dashboard (alias) |
| `./status` | Check system status |

## Usage

### Start the Dashboard
```bash
cd /Users/cosburn/BoarderframeOS
./start
```
- Opens http://localhost:8888
- Shows system status
- Displays setup instructions
- Provides Solomon chat interface

### Check System Status
```bash
./status
```
- Shows UI server status
- Checks backend services
- Displays process information

### Stop the Server
Press **Ctrl+C** in the terminal running the server

## What Each Script Does

### `./start`
- Main launcher script
- Starts Python UI server
- Auto-opens browser
- Runs on port 8888

### `./ui` & `./dashboard`
- Simple aliases to `./start`
- Same functionality

### `./status`
- Checks if UI server is running
- Tests backend connectivity
- Shows process information
- Provides next step guidance

## Dashboard Features

✅ **System Overview** - Agent status, metrics
✅ **Solomon Interface** - Chat with chief of staff  
✅ **Setup Guide** - Built-in instructions
✅ **Status Monitoring** - Real-time updates
✅ **Quick Actions** - System controls

## Next Steps

1. Run `./start` to open dashboard
2. Follow setup instructions in UI
3. Use `./status` to monitor progress

Simple as that!