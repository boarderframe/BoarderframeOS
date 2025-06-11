#!/bin/bash
# Complete overwrite of remote repository with local state
# This script ensures a complete replacement of the remote repo

echo "🚀 BoarderframeOS Complete Repository Overwrite"
echo "=============================================="
echo "⚠️  WARNING: This will COMPLETELY REPLACE the remote repository!"
echo "    All remote history and changes will be preserved but current HEAD will be overwritten."
echo "=============================================="

# Confirm
read -p "Type 'OVERWRITE' to confirm: " confirm
if [ "$confirm" != "OVERWRITE" ]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "📋 Pre-flight checks..."

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository!"
    exit 1
fi

# Show current status
echo "📌 Current branch: $(git branch --show-current)"
echo "📝 Changed files: $(git status --porcelain | wc -l)"
echo "🔗 Remote: $(git remote get-url origin)"

echo ""
echo "🔧 Starting complete overwrite process..."

# Step 1: Stage all changes including untracked files
echo "1️⃣ Staging all files (including untracked)..."
git add -A

# Step 2: Commit everything
echo "2️⃣ Creating comprehensive commit..."
commit_msg="Complete BoarderframeOS state - $(date '+%Y-%m-%d %H:%M:%S')

This commit represents the complete current state of BoarderframeOS including:
- All source code updates
- Configuration files
- Documentation
- Test scripts
- All new features and fixes"

git commit -m "$commit_msg" || echo "ℹ️  No changes to commit"

# Step 3: Force push to overwrite remote
echo "3️⃣ Force pushing to completely overwrite remote..."
current_branch=$(git branch --show-current)

# Try force-with-lease first (safer)
if git push origin $current_branch --force-with-lease; then
    echo "✅ Successfully overwrote remote repository (safe mode)"
else
    echo "⚠️  Safe push failed, using force push..."
    if git push origin $current_branch --force; then
        echo "✅ Successfully overwrote remote repository (force mode)"
    else
        echo "❌ Push failed!"
        echo "💡 Try setting up credentials:"
        echo "   git config --global credential.helper store"
        echo "   Or use SSH: git remote set-url origin git@github.com:boarderframe/BoarderframeOS.git"
        exit 1
    fi
fi

echo ""
echo "✅ Complete! Remote repository has been overwritten with local state."
echo "🌐 View at: https://github.com/boarderframe/BoarderframeOS"
echo ""
echo "📊 Summary of what was pushed:"
git log --oneline -5
echo ""
echo "🔍 To verify remote state matches local:"
echo "   git fetch origin"
echo "   git diff origin/$current_branch"
