import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters
)

# Import config and database
import config
from database.database import init_db, close_session
from database.models import User

# Import handlers
from handlers.user_handlers import (
    start_command, cards_command, search_command, text_command,
    myfollows_command, follow_command, unfollow_command,
    vote_command, checkid_command, mycard_command, otzivid_command,
    followid_command
)
from handlers.admin_handlers import (
    addcatalog_command, addpost_command, addpeople_command,
    addpriority_command, addreklama_command, add24_command,
    addwork_command, addhome_command, addcard_command,
    receive_link, receive_hashtags, receive_address,
    receive_description, receive_media,
    say_command, broadcast_command, remove_command, edit_command,
    removecd_command, cardstats_command, statsf_command,
    reviewdelete_command, statscoldown_command, statsgroups_command,
    cardgroupedit_command, changenumber_command,
    WAITING_LINK, WAITING_CATEGORIES, WAITING_HASHTAGS,
    WAITING_ADDRESS, WAITING_DESCRIPTION, WAITING_MEDIA
)
from handlers.callback_handlers import handle_callback

# Import utilities
from utils.helpers import delete_expired_f_cards

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")


async def periodic_cleanup(application: Application):
    """Periodically clean up expired F cards"""
    while True:
        try:
            deleted_count = delete_expired_f_cards()
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} expired F cards")
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
        
        # Sleep for 1 hour
        await asyncio.sleep(3600)


async def post_init(application: Application):
    """Post initialization tasks"""
    logger.info("Starting periodic cleanup task...")
    asyncio.create_task(periodic_cleanup(application))


def main():
    """Main function to run the bot"""
    logger.info("Initializing database...")
    init_db()
    
    logger.info("Starting bot...")
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add conversation handler for card creation
    card_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('addcatalog', addcatalog_command),
            CommandHandler('addpost', addpost_command),
            CommandHandler('addpeople', addpeople_command),
            CommandHandler('addpriority', addpriority_command),
            CommandHandler('addreklama', addreklama_command),
            CommandHandler('add24', add24_command),
            CommandHandler('addwork', addwork_command),
            CommandHandler('addhome', addhome_command),
            CommandHandler('addcard', addcard_command),
        ],
        states={
            WAITING_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            WAITING_HASHTAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_hashtags)],
            WAITING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
            WAITING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            WAITING_MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, receive_media)
            ],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('cards', cards_command))
    application.add_handler(CommandHandler('search', search_command))
    application.add_handler(CommandHandler('text', text_command))
    application.add_handler(CommandHandler('myfollows', myfollows_command))
    application.add_handler(CommandHandler('follow', follow_command))
    application.add_handler(CommandHandler('unfollow', unfollow_command))
    application.add_handler(CommandHandler('vote', vote_command))
    application.add_handler(CommandHandler('checkid', checkid_command))
    application.add_handler(CommandHandler('mycard', mycard_command))
    application.add_handler(CommandHandler('otzivid', otzivid_command))
    application.add_handler(CommandHandler('followid', followid_command))
    
    # Admin commands
    application.add_handler(CommandHandler('say', say_command))
    application.add_handler(CommandHandler('broadcast', broadcast_command))
    application.add_handler(CommandHandler('remove', remove_command))
    application.add_handler(CommandHandler('edit', edit_command))
    application.add_handler(CommandHandler('removecd', removecd_command))
    application.add_handler(CommandHandler('cardstats', cardstats_command))
    application.add_handler(CommandHandler('statsf', statsf_command))
    application.add_handler(CommandHandler('reviewdelete', reviewdelete_command))
    application.add_handler(CommandHandler('statscoldown', statscoldown_command))
    application.add_handler(CommandHandler('statsgroups', statsgroups_command))
    application.add_handler(CommandHandler('cardgroupedit', cardgroupedit_command))
    application.add_handler(CommandHandler('changenumber', changenumber_command))
    
    # Add conversation handler
    application.add_handler(card_conv_handler)
    
    # Add callback handler
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Register post init
    application.post_init = post_init
    
    # Start bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        close_session()
        logger.info("Bot shutdown complete")
