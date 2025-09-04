#!/bin/bash
# Open WebUI Frontend Startup Script
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 22
cd /Users/cosburn/open_webui/open-webui
npm run dev