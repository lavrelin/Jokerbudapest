import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import User, Card
from database.database import get_session
from utils.helpers import (
    get_or_create_user, get_cards_for_user, mark_card_as_viewed,
    format_card_text, get_card_rating, get_card_reviews_count
)
from keyboards.keyboards import (
    get_card_keyboard, get_pagination_keyboard, get_subscriptions_keyboard,
    get_text_form_keyboard
)
import config

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Добро пожаловать в BudapestJoker! 🃏\n\n"
        "Я помогу вам найти полезные сервисы и контакты в Будапеште.\n\n"
        "Используйте кнопки ниже для навигации или команды:\n"
        "/cards - Показать карточки\n"
        "/search - Поиск по каталогу\n"
        "/text - Отправить заявку или сообщение\n"
        "/myfollows - Мои подписки\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🃏 Показать карточки", callback_data="show_cards")],
        [InlineKeyboardButton("🔍 Поиск", callback_data="start_search")],
        [InlineKeyboardButton("📝 Отправить заявку", callback_data="text_form")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def cards_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cards command - show cards to user"""
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    # Get cards for user
    cards = get_cards_for_user(user.id, limit=config.CARDS_PER_PAGE)
    
    if not cards:
        await update.message.reply_text(
            "К сожалению, карточки не найдены. 😔\n"
            "Попробуйте позже или обновите страницу."
        )
        return
    
    # Store cards in context
    context.user_data['current_cards'] = [card.id for card in cards]
    context.user_data['current_card_index'] = 0
    
    # Show first card
    await show_card(update, context, 0, cards)


async def show_card(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int, cards: list):
    """Show a specific card to user"""
    if index < 0 or index >= len(cards):
        return
    
    card = cards[index]
    user = update.effective_user
    
    # Mark card as viewed
    mark_card_as_viewed(user.id, card.id)
    
    # Format card text
    card_text = format_card_text(card)
    
    # Get keyboard
    card_keyboard = get_card_keyboard(card, index)
    pagination_keyboard = get_pagination_keyboard(index, len(cards), card.id)
    
    # Combine keyboards
    combined_keyboard = card_keyboard.inline_keyboard + pagination_keyboard.inline_keyboard
    reply_markup = InlineKeyboardMarkup(combined_keyboard)
    
    # Send card
    if card.media_type and card.media_file_id:
        try:
            if card.media_type == 'photo':
                await update.effective_message.reply_photo(
                    photo=card.media_file_id,
                    caption=card_text,
                    reply_markup=reply_markup
                )
            elif card.media_type == 'video':
                await update.effective_message.reply_video(
                    video=card.media_file_id,
                    caption=card_text,
                    reply_markup=reply_markup
                )
            elif card.media_type == 'document':
                await update.effective_message.reply_document(
                    document=card.media_file_id,
                    caption=card_text,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Error sending media: {e}")
            await update.effective_message.reply_text(
                card_text,
                reply_markup=reply_markup
            )
    else:
        await update.effective_message.reply_text(
            card_text,
            reply_markup=reply_markup
        )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command"""
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    # Check if query provided
    if context.args:
        query = ' '.join(context.args)
        await perform_search(update, context, query)
    else:
        await update.message.reply_text(
            "🔍 Введите поисковый запрос:\n\n"
            "Используйте: /search <запрос>\n\n"
            "Например:\n"
            "/search барбер\n"
            "/search маникюр центр"
        )


async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Perform search and show results"""
    from utils.helpers import search_cards
    
    user = update.effective_user
    cards = search_cards(query, user.id)
    
    if not cards:
        await update.effective_message.reply_text(
            f"По запросу '{query}' ничего не найдено. 😔\n"
            "Попробуйте изменить запрос."
        )
        return
    
    # Limit to 5 cards (1-4 from search, 5th from groups D, E, F)
    search_results = cards[:4]
    
    # Add one card from groups D, E, F as 5th
    session = get_session()
    try:
        promo_cards = session.query(Card).filter(
            Card.groups.contains(['D']) | 
            Card.groups.contains(['E']) | 
            Card.groups.contains(['F'])
        ).all()
        
        if promo_cards:
            import random
            promo_card = random.choice(promo_cards)
            search_results.append(promo_card)
    finally:
        session.close()
    
    # Store in context
    context.user_data['current_cards'] = [card.id for card in search_results]
    context.user_data['current_card_index'] = 0
    
    await update.effective_message.reply_text(
        f"Найдено карточек: {len(cards)}\n"
        f"Показываю первые {len(search_results)} результатов:"
    )
    
    # Show first card
    await show_card(update, context, 0, search_results)


async def text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /text command - open text form"""
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    # Check cooldown
    from utils.helpers import check_cooldown
    from datetime import datetime
    
    cooldown_expires = check_cooldown(user.id, 'text_command')
    if cooldown_expires:
        time_left = cooldown_expires - datetime.utcnow()
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        
        await update.message.reply_text(
            f"⏳ Вы можете отправить следующую форму через {hours}ч {minutes}мин"
        )
        return
    
    keyboard = get_text_form_keyboard()
    
    await update.message.reply_text(
        "📝 Выберите тип формы:\n\n"
        "• Заявка в каталог - добавить свою карточку\n"
        "• Предложение публикации - предложить контент\n"
        "• Связь с администратором - задать вопрос\n"
        "• Жалоба на пользователя - сообщить о нарушении\n"
        "• Форма «Ищу» - найти что-то конкретное",
        reply_markup=keyboard
    )


async def myfollows_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myfollows command - show user subscriptions"""
    from database.models import CategorySubscription, CardSubscription
    
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    session = get_session()
    try:
        # Get category subscriptions
        cat_subs = session.query(CategorySubscription).filter(
            CategorySubscription.user_id == user.id
        ).all()
        
        # Get card subscriptions
        card_subs = session.query(CardSubscription).filter(
            CardSubscription.user_id == user.id
        ).all()
        
        text = "🔔 Ваши подписки:\n\n"
        
        if cat_subs:
            text += "📂 Категории:\n"
            for sub in cat_subs:
                text += f"• {sub.category}\n"
            text += "\n"
        
        if card_subs:
            text += "🃏 Карточки:\n"
            for sub in card_subs:
                card = session.query(Card).filter(Card.id == sub.card_id).first()
                if card:
                    text += f"• Карточка #{card.card_number}\n"
            text += "\n"
        
        if not cat_subs and not card_subs:
            text += "У вас пока нет подписок.\n\n"
        
        text += "Используйте команды:\n"
        text += "/follow - подписаться на категорию\n"
        text += "/unfollow - отписаться от категории\n"
        text += "/followid - подписаться на карточку"
        
        keyboard = get_subscriptions_keyboard()
        
        await update.message.reply_text(text, reply_markup=keyboard)
        
    finally:
        session.close()


async def follow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /follow command - subscribe to category"""
    await update.message.reply_text(
        "📂 Подписка на категории\n\n"
        "Используйте: /follow <категория>\n\n"
        "Доступные категории:\n"
        "• Барбер\n"
        "• Косметолог\n"
        "• Маникюр\n"
        "• Врач\n"
        "• Массажист\n"
        "• И другие..."
    )


async def unfollow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unfollow command - unsubscribe from category"""
    await update.message.reply_text(
        "📂 Отписка от категории\n\n"
        "Используйте: /unfollow <категория>\n\n"
        "Или используйте /myfollows чтобы увидеть ваши подписки"
    )


async def vote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /vote command - rate a card"""
    if not context.args:
        await update.message.reply_text(
            "⭐️ Оценка карточки\n\n"
            "Используйте: /vote <номер_карточки>\n\n"
            "Например: /vote 1234"
        )
        return
    
    try:
        card_number = int(context.args[0])
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.card_number == card_number).first()
            
            if not card:
                await update.message.reply_text("Карточка не найдена. 😔")
                return
            
            from keyboards.keyboards import get_rating_keyboard
            keyboard = get_rating_keyboard(card.id)
            
            await update.message.reply_text(
                f"⭐️ Оцените карточку #{card.card_number}\n\n"
                "Выберите количество звёзд:",
                reply_markup=keyboard
            )
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный номер карточки. Используйте число от 1 до 9999.")


async def checkid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checkid command - check card information"""
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Информация о карточке\n\n"
            "Используйте: /checkid <номер_карточки>\n\n"
            "Например: /checkid 1234"
        )
        return
    
    try:
        card_number = int(context.args[0])
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.card_number == card_number).first()
            
            if not card:
                await update.message.reply_text("Карточка не найдена. 😔")
                return
            
            avg_rating, rating_count = get_card_rating(card.id)
            review_count = get_card_reviews_count(card.id)
            
            text = f"ℹ️ Информация о карточке #{card.card_number}\n\n"
            text += f"⭐️ Рейтинг: {avg_rating} ({rating_count} оценок)\n"
            text += f"💬 Отзывы: {review_count}\n"
            text += f"👁 Просмотры: {card.total_views} (уникальных: {card.unique_views})\n"
            text += f"🔗 Переходы: {card.link_clicks}\n"
            
            await update.message.reply_text(text)
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный номер карточки. Используйте число от 1 до 9999.")


async def mycard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mycard command - verify card ownership"""
    from database.models import CardOwner
    
    if not context.args:
        await update.message.reply_text(
            "👤 Подтверждение владения карточкой\n\n"
            "Используйте: /mycard <номер_карточки>\n\n"
            "Например: /mycard 1234\n\n"
            "После подтверждения вы сможете:\n"
            "• Отвечать на комментарии без кулдауна\n"
            "• Подавать заявку на изменения карточки раз в 12 часов"
        )
        return
    
    try:
        card_number = int(context.args[0])
        user = update.effective_user
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.card_number == card_number).first()
            
            if not card:
                await update.message.reply_text("Карточка не найдена. 😔")
                return
            
            # Check if already owner
            existing = session.query(CardOwner).filter(
                CardOwner.user_id == user.id,
                CardOwner.card_id == card.id
            ).first()
            
            if existing:
                await update.message.reply_text(
                    f"✅ Вы уже подтверждены как владелец карточки #{card_number}"
                )
                return
            
            # Add owner
            owner = CardOwner(
                user_id=user.id,
                card_id=card.id
            )
            session.add(owner)
            session.commit()
            
            await update.message.reply_text(
                f"✅ Вы подтверждены как владелец карточки #{card_number}!\n\n"
                "Теперь вы можете:\n"
                "• Отвечать на комментарии без кулдауна\n"
                "• Подавать заявку на изменения раз в 12 часов"
            )
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный номер карточки. Используйте число от 1 до 9999.")


async def otzivid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /otzivid command - leave review for card"""
    if not context.args:
        await update.message.reply_text(
            "💬 Оставить отзыв о карточке\n\n"
            "Используйте: /otzivid <номер_карточки>\n\n"
            "Например: /otzivid 1234"
        )
        return
    
    try:
        card_number = int(context.args[0])
        user = update.effective_user
        
        # Check cooldown (unless card owner)
        from utils.helpers import is_card_owner
        from datetime import datetime
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.card_number == card_number).first()
            
            if not card:
                await update.message.reply_text("Карточка не найдена. 😔")
                return
            
            # Check if card owner
            is_owner = is_card_owner(user.id, card.id)
            
            if not is_owner:
                cooldown_expires = check_cooldown(user.id, 'review')
                
                if cooldown_expires:
                    time_left = cooldown_expires - datetime.utcnow()
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    
                    await update.message.reply_text(
                        f"⏳ Вы можете оставить следующий отзыв через {hours}ч {minutes}мин"
                    )
                    return
            
            # Store card ID for review
            context.user_data['review_card_id'] = card.id
            context.user_data['review_card_number'] = card_number
            
            await update.message.reply_text(
                f"💬 Оставить отзыв о карточке #{card_number}\n\n"
                "Напишите ваш отзыв:"
            )
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный номер карточки. Используйте число от 1 до 9999.")


async def followid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /followid command - subscribe to card notifications"""
    from database.models import CardSubscription
    
    if not context.args:
        await update.message.reply_text(
            "🔔 Подписка на уведомления по карточке\n\n"
            "Используйте: /followid <номер_карточки>\n\n"
            "Например: /followid 1234\n\n"
            "Вы будете получать уведомления о:\n"
            "• Новых оценках\n"
            "• Новых отзывах"
        )
        return
    
    try:
        card_number = int(context.args[0])
        user = update.effective_user
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.card_number == card_number).first()
            
            if not card:
                await update.message.reply_text("Карточка не найдена. 😔")
                return
            
            # Check if already subscribed
            existing = session.query(CardSubscription).filter(
                CardSubscription.user_id == user.id,
                CardSubscription.card_id == card.id
            ).first()
            
            if existing:
                await update.message.reply_text(
                    f"✅ Вы уже подписаны на карточку #{card_number}"
                )
                return
            
            # Add subscription
            subscription = CardSubscription(
                user_id=user.id,
                card_id=card.id
            )
            session.add(subscription)
            session.commit()
            
            await update.message.reply_text(
                f"✅ Вы подписались на уведомления о карточке #{card_number}!"
            )
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный номер карточки. Используйте число от 1 до 9999.")
