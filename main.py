import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
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
    WAITING_ADDRESS, WAITING_DESCRIPTION, WAITING_MEDIA, WAITING_GROUP_SELECTION
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


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for reviews and forms"""
    user = update.effective_user
    text = update.message.text
    
    # Check if user is writing a review
    if 'review_card_id' in context.user_data:
        from database.models import Review
        from utils.helpers import set_cooldown, is_card_owner
        from database.database import get_session
        
        card_id = context.user_data['review_card_id']
        card_number = context.user_data.get('review_card_number', 'неизвестно')
        
        # Check if card owner (no cooldown for owners)
        is_owner = is_card_owner(user.id, card_id)
        
        session = get_session()
        try:
            # Save review
            review = Review(
                user_id=user.id,
                card_id=card_id,
                text=text
            )
            session.add(review)
            session.commit()
            
            # Set cooldown if not owner
            if not is_owner:
                set_cooldown(user.id, 'review', config.COOLDOWN_REVIEW)
            
            await update.message.reply_text(
                f"✅ Спасибо за ваш отзыв о карточке #{card_number}!\n"
                "Отзыв успешно добавлен."
            )
            
            # Clear context
            context.user_data.pop('review_card_id', None)
            context.user_data.pop('review_card_number', None)
            
        except Exception as e:
            logger.error(f"Error saving review: {e}")
            await update.message.reply_text("❌ Ошибка при сохранении отзыва")
        finally:
            session.close()
    
    # Check if user is filling a text form
    elif 'text_form_type' in context.user_data:
        from utils.helpers import set_cooldown
        
        form_type = context.user_data['text_form_type']
        
        form_names = {
            'catalog': 'Заявка в каталог',
            'post': 'Предложение публикации',
            'admin': 'Связь с администратором',
            'report': 'Жалоба на пользователя',
            'search': 'Форма «Ищу»'
        }
        
        # Store message
        context.user_data['text_form_message'] = text
        
        # Check if media was sent
        from keyboards.keyboards import get_text_preview_keyboard
        keyboard = get_text_preview_keyboard(form_type)
        
        await update.message.reply_text(
            f"📋 Предпросмотр: {form_names[form_type]}\n\n"
            f"{text}\n\n"
            "Выберите действие:",
            reply_markup=keyboard
        )


async def handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle media messages for forms"""
    user = update.effective_user
    
    # Check if user is filling a text form
    if 'text_form_type' in context.user_data:
        form_type = context.user_data['text_form_type']
        
        # Get media
        if update.message.photo:
            media_type = 'photo'
            media_file_id = update.message.photo[-1].file_id
        elif update.message.video:
            media_type = 'video'
            media_file_id = update.message.video.file_id
        elif update.message.document:
            media_type = 'document'
            media_file_id = update.message.document.file_id
        else:
            return
        
        # Store media
        context.user_data['text_form_media_type'] = media_type
        context.user_data['text_form_media_id'] = media_file_id
        
        # Get caption or previous text
        caption = update.message.caption or context.user_data.get('text_form_message', '')
        context.user_data['text_form_message'] = caption
        
        from keyboards.keyboards import get_text_preview_keyboard
        keyboard = get_text_preview_keyboard(form_type)
        
        form_names = {
            'catalog': 'Заявка в каталог',
            'post': 'Предложение публикации',
            'admin': 'Связь с администратором',
            'report': 'Жалоба на пользователя',
            'search': 'Форма «Ищу»'
        }
        
        # Send preview with media
        if media_type == 'photo':
            await update.message.reply_photo(
                photo=media_file_id,
                caption=f"📋 Предпросмотр: {form_names[form_type]}\n\n{caption}\n\nВыберите действие:",
                reply_markup=keyboard
            )
        elif media_type == 'video':
            await update.message.reply_video(
                video=media_file_id,
                caption=f"📋 Предпросмотр: {form_names[form_type]}\n\n{caption}\n\nВыберите действие:",
                reply_markup=keyboard
            )
        elif media_type == 'document':
            await update.message.reply_document(
                document=media_file_id,
                caption=f"📋 Предпросмотр: {form_names[form_type]}\n\n{caption}\n\nВыберите действие:",
                reply_markup=keyboard
            )


async def error_handler(update: Update, context):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    logger.error(f"Error traceback:", exc_info=context.error)
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")


async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug handler to log all incoming messages"""
    if update.message:
        user = update.effective_user
        text = update.message.text or "[media]"
        logger.info(f"Received message from {user.id} (@{user.username}): {text}")
    elif update.callback_query:
        user = update.effective_user
        data = update.callback_query.data
        logger.info(f"Received callback from {user.id} (@{user.username}): {data}")


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
            WAITING_GROUP_SELECTION: [CallbackQueryHandler(handle_callback, pattern='^grp_')],
            WAITING_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            WAITING_CATEGORIES: [CallbackQueryHandler(handle_callback, pattern='^cat_')],
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
    logger.info("Registering command handlers...")
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
    logger.info("Registering admin command handlers...")
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
    logger.info("Registering conversation handlers...")
    application.add_handler(card_conv_handler)
    
    # Add callback handler
    logger.info("Registering callback handlers...")
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add text and media handlers
    logger.info("Registering message handlers...")
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(
        (filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND,
        handle_media_message
    ))
    
    # Add error handler
    logger.info("Registering error handler...")
    application.add_error_handler(error_handler)
    
    # Register post init
    application.post_init = post_init
    
    # Start bot
    logger.info("All handlers registered successfully!")
    logger.info(f"Admin IDs: {config.ADMIN_IDS}")
    logger.info("Bot started successfully! Waiting for updates...")
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
