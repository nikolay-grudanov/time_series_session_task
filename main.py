"""
Main entry point that runs the Telegram bot.
"""

import sys
import os

# Add the project root to Python path to enable imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import and run the bot
from src.main import main as run_bot


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_bot())
