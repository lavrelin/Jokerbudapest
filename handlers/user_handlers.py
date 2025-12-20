"""
Обработчики пользовательских команд
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.models import Card
from database.database import get_session
from utils.helpers import (
    get_or_create_user, get_cards_for_user, 
    format_card_text, mark_card_as_viewed,
    search_cards
)
from keyboards.keyboards import get_start_keyboard, get_card_keyboard

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"Start command from user {user.id} (@{user.username})")
    
    # Create or update user in database
    get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = (
        f"Привет, 🃏 {user.first_name}! 👋\n\n"
        f"Добро пожаловать в BudapestJoker! 🎭\n\n"
        f"Я помогу вам найти полезные сервисы и контакты в Будапеште.\n\n"
        f"Используйте кнопки ниже для навигации или команды:\n"
        f"/cards - Показать карточки\n"
        f"/search <запрос> - Поиск по каталогу\n"
        f"/text - Отправить заявку"
    )
    
    keyboard = get_start_keyboard()
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard
    )


async def cards_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cards command - show cards"""
    user_id = update.effective_user.id
    
    # Get cards for user
    cards = get_cards_for_user(user_id, limit=5)
    
    if not cards:
        await update.message.reply_text(
            "😔 К сожалению, нет доступных карточек.\n"
            "Попробуйте позже или используйте /search для поиска."
        )
        return
    
    # Store cards in context
    context.user_data['current_cards'] = [card.id for card in cards]
    context.user_data['current_index'] = 0
    
    # Show first card
    await show_card(update, context, 0)


async def show_card(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    """Show card at specified index"""
    card_ids = context.user_data.get('current_cards', [])
    
    if not card_ids or index < 0 or index >= len(card_ids):
        if update.message:
            await update.message.reply_text("❌ Карточка не найдена")
        return
    
    card_id = card_ids[index]
    
    session = get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            if update.message:
                await update.message.reply_text("❌ Карточка не найдена")
            return
        
        # Mark as viewed
        mark_card_as_viewed(update.effective_user.id, card_id)
        
        # Format card text
        text = format_card_text(card)
        
        # Get keyboard
        keyboard = get_card_keyboard(card, index, len(card_ids))
        
        # Send with media
        try:
            if card.media_type == 'photo':
                if update.message:
                    await update.message.reply_photo(
                        photo=card.media_file_id,
                        caption=text,
                        reply_markup=keyboard
                    )
                elif update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=card.media_file_id,
                        caption=text,
                        reply_markup=keyboard
                    )
            elif card.media_type == 'video':
                if update.message:
                    await update.message.reply_video(
                        video=card.media_file_id,
                        caption=text,
                        reply_markup=keyboard
                    )
                elif update.callback_query:
                    await update.callback_query.message.reply_video(
                        video=card.media_file_id,
                        caption=text,
                        reply_markup=keyboard
                    )
            elif card.media_type == 'document':
                if update.message:
                    await update.message.reply_document(
                        document=card.media_file_id,
                        caption=text,
                        reply_markup=keyboard
                    )
                elif update.callback_query:
                    await update.callback_query.message.reply_document(
                        document=card.media_file_id,
                        caption=text,
                        reply_markup=keyboard
                    )
            else:
                # No media - just text
                if update.message:
                    await update.message.reply_text(text, reply_markup=keyboard)
                elif update.callback_query:
                    await update.callback_query.message.reply_text(text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error sending card media: {e}")
            # Fallback to text only
            if update.message:
                await update.message.reply_text(text, reply_markup=keyboard)
            elif update.callback_query:
                await update.callback_query.message.reply_text(text, reply_markup=keyboard)
        
        # Update current index
        context.user_data['current_index'] = index
        
    finally:
        session.close()


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command"""
    # Check if query provided
    if not context.args:
        await update.message.reply_text(
            "🔍 Поиск по каталогу\n\n"
            "Использование: /search <запрос>\n\n"
            "Примеры:\n"
            "• /search барбер\n"
            "• /search будапешт\n"
            "• /search массаж"
        )
        return
    
    query = ' '.join(context.args)
    
    # Search
    cards = search_cards(query, limit=10)
    
    if not cards:
        await update.message.reply_text(
            f"😔 По запросу «{query}» ничего не найдено.\n\n"
            "Попробуйте другой запрос или используйте /cards"
        )
        return
    
    # Show results
    await update.message.reply_text(
        f"🔍 Найдено карточек: {len(cards)}\n"
        f"Запрос: «{query}»"
    )
    
    # Store in context and show first
    context.user_data['current_cards'] = [card.id for card in cards]
    context.user_data['current_index'] = 0
    
    await show_card(update, context, 0)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📚 СПРАВКА\n\n"
        "🃏 Основные команды:\n"
        "/start - Главное меню\n"
        "/cards - Показать карточки\n"
        "/search <запрос> - Поиск\n"
        "/text - Отправить заявку\n"
        "/help - Эта справка\n\n"
        "⭐️ Оценивайте карточки от 1 до 10!\n"
        "🔍 Используйте поиск по району, категории или хештегам\n"
        "📝 Отправляйте заявки для добавления в каталог"
    )
    
    await update.message.reply_text(help_text)


async def text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /text command - submit application form"""
    from keyboards.keyboards import get_text_form_keyboard
    
    await update.message.reply_text(
        "📝 Выберите тип заявки:",
        reply_markup=get_text_form_keyboard()
    )
