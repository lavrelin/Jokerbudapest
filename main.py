#!/usr/bin/env python3
"""
BudapestJoker Telegram Bot - MVP Version
"""
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

# Configuration
import config

# Database
from database.database import init_db

# Handlers
from handlers.user_handlers import (
    start_command, cards_command, search_command,
    help_command, text_command
)

from handlers.admin_handlers import (
    addcatalog_command, addpost_command, addpeople_command,
    addpriority_command, addreklama_command, add24_command,
    addwork_command, addhome_command,
    receive_link, receive_district, receive_category,
    receive_hashtags, receive_description,
    remove_command, cardstats_command,
    WAITING_LINK, WAITING_DISTRICT, WAITING_CATEGORY,
    WAITING_HASHTAGS, WAITING_DESCRIPTION
)

from handlers.callback_handlers import handle_callback

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    # Notify user
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка. Попробуйте еще раз или обратитесь к администратору."
        )


def main():
    """Start the bot"""
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized!")
    
    # Create application
    logger.info("Creating application...")
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # ============== USER COMMANDS ==============
    logger.info("Registering user handlers...")
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("cards", cards_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("text", text_command))
    
    # ============== ADMIN COMMANDS ==============
    logger.info("Registering admin handlers...")
    
    # Conversation handler for card creation
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
        ],
        states={
            WAITING_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            WAITING_DISTRICT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_district)],
            WAITING_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_category)],
            WAITING_HASHTAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_hashtags)],
            WAITING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)],
    )
    application.add_handler(card_conv_handler)
    
    # Simple admin commands
    application.add_handler(CommandHandler("remove", remove_command))
    application.add_handler(CommandHandler("cardstats", cardstats_command))
    
    # ============== CALLBACK HANDLERS ==============
    logger.info("Registering callback handlers...")
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # ============== ERROR HANDLER ==============
    application.add_error_handler(error_handler)
    
    # ============== START BOT ==============
    logger.info("=" * 60)
    logger.info("🤖 BudapestJoker Bot MVP Started!")
    logger.info(f"📊 Admin IDs: {config.ADMIN_IDS}")
    logger.info("=" * 60)
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
