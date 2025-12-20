import os
import logging
from dotenv import load_dotenv

# Configure basic logging for config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip()]
ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', '-4843909295'))
MODERATION_GROUP_ID = int(os.getenv('MODERATION_GROUP_ID', '-1002734837434'))

# Log configuration on load
logger.info(f"🔧 Config loaded:")
logger.info(f"   BOT_TOKEN: {'Set' if BOT_TOKEN else 'NOT SET'}")
logger.info(f"   ADMIN_IDS (raw): '{ADMIN_IDS_STR}'")
logger.info(f"   ADMIN_IDS (parsed): {ADMIN_IDS}")
logger.info(f"   Number of admins: {len(ADMIN_IDS)}")
logger.info(f"   ADMIN_GROUP_ID: {ADMIN_GROUP_ID}")
logger.info(f"   MODERATION_GROUP_ID: {MODERATION_GROUP_ID}")

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# Card groups
CARD_GROUPS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

# Card sets for users (which groups to show)
CARD_SETS = [
    ['A'],                      # Set 1: Only A
    ['A', 'B'],                 # Set 2: A and B
    ['A', 'C'],                 # Set 3: A and C
    ['A', 'B', 'D', 'E'],       # Set 4: A, B, D, E
    ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']  # Set 5: All groups
]

# Cooldowns (in seconds)
COOLDOWN_TEXT_FORM = 8 * 3600  # 8 hours for submitting forms
COOLDOWN_RATING = 60  # 1 minute between ratings

# Card deletion time for group F
GROUP_F_DELETE_TIME = 24 * 3600  # 24 hours

# Cards per page
CARDS_PER_PAGE = 5

# Rating (UPDATED: 1-10 вместо 1-5)
MIN_RATING = 1
MAX_RATING = 10
