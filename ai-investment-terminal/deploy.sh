#!/bin/bash
# Daily deployment script — fetches fresh data and pushes to GitHub Pages
set -e

echo "🚀 Starting daily AI Terminal update..."
cd "$(dirname "$0")"

# Load env vars
source .env 2>/dev/null || true

# Fetch fresh data
python3 fetch_data.py
if [ $? -ne 0 ]; then
  echo "❌ fetch_data.py failed — not pushing to GitHub"
  exit 1
fi

# Commit and push
git add data/data.json
if git diff --cached --quiet; then
  echo "ℹ️  No changes to commit"
else
  git commit -m "data: auto-update $(date '+%Y-%m-%d %H:%M')"
  git push origin main
  echo "✅ Deployed to GitHub Pages"
fi
