#!/bin/bash
# One-time setup: installs dependencies and registers daily cron job

echo "⚙️  Setting up AI Investment Intelligence Terminal..."
echo ""

# Install Python deps
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
  echo "❌ pip install failed. Make sure Python 3 and pip are installed."
  exit 1
fi

# Copy env template
if [ ! -f .env ]; then
  cp .env.example .env
  echo "📝 Created .env — open it and add your YouTube API key:"
  echo "   Get one free at: https://console.cloud.google.com → APIs → YouTube Data API v3"
  echo ""
fi

# Create logs directory
mkdir -p logs

# Register cron job (runs daily at 7:00 AM local time)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRON_LINE="0 7 * * * cd $SCRIPT_DIR && bash deploy.sh >> $SCRIPT_DIR/logs/cron.log 2>&1"

# Check if already registered
if crontab -l 2>/dev/null | grep -q "$SCRIPT_DIR/deploy.sh"; then
  echo "ℹ️  Cron job already registered"
else
  (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
  echo "✅ Cron job added — will run daily at 7:00 AM"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your YouTube API key"
echo "  2. Test the fetcher: python3 fetch_data.py --skip-youtube"
echo "  3. Open index.html in your browser"
echo "  4. Enable GitHub Pages: Settings → Pages → Deploy from main branch → / (root)"
echo ""
