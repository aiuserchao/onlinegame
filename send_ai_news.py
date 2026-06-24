#!/usr/bin/env python3
"""
AI News Sender Script
Fetches AI news and sends it via OpenClaw's messaging system.
Designed to be run by cron.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from get_ai_news import get_all_ai_news, format_news
import json
from datetime import datetime

def main():
    try:
        # Get AI news
        news_items = get_all_ai_news()
        formatted_news = format_news(news_items)
        
        # Prepare message to send via OpenClaw
        # We'll output to stdout and let the cron system handle delivery
        # Or we could try to send via sessions_send if we can get the session key
        
        # For now, let's output the news and also try to send it
        print(formatted_news)
        
        # Also save to a file for debugging
        with open("/home/node/.openclaw/workspace/ai_news_latest.txt", "w", encoding="utf-8") as f:
            f.write(formatted_news)
            
        # Try to send via OpenClaw's internal messaging if possible
        # This would require knowing the session key or using a system event
        
    except Exception as e:
        error_msg = f"❌ Error in AI news job: {str(e)}\nTimestamp: {datetime.now().isoformat()}"
        print(error_msg, file=sys.stderr)
        # Also save error to file
        with open("/home/node/.openclaw/workspace/ai_news_error.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()