import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.models import Card, Rating, Review, CategorySubscription, CardSubscription
from database.database import get_session
from utils.helpers import (
    get_cards_for_user, format_card_text, set_cooldown,
    check_cooldown, get_card_rating
)
from keyboards.keyboards import (
    get_review_keyboard, get_rating_keyboard, get_subscriptions_keyboard,
    get_text_form_keyboard, get_category_selection_keyboard, 
    get_group_selection_keyboard
)
from handlers.admin_handlers import (
    publish_card, WAITING_CATEGORIES, WAITING_HASHTAGS, WAITING_LINK, WAITING_GROUP_SELECTION
)
from datetime import datetime
import config

logger = logging.getLogger(__name__)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback handler"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Navigation callbacks
    if data.startswith('nav_'):
        await handle_navigation(update, context, data)
        return
    
    # Review callbacks
    elif data.startswith('rvw_'):
        await handle_reviews(update, context, data)
        return
    
    # Rating callbacks
    elif data.startswith('rt_'):
        await handle_rating(update, context, data)
        return
    
    # Subscription callbacks
    elif data.startswith('subs_') or data == 'my_subs':
        await handle_subscriptions(update, context, data)
        return
    
    # Text form callbacks
    elif data.startswith('txtf_') or data == 'text_form':
        await handle_text_form(update, context, data)
        return
    
    # Category selection callbacks - ВАЖНО для ConversationHandler
    elif data.startswith('cat_'):
        result = await handle_category_selection(update, context, data)
        return result  # Возвращаем состояние для ConversationHandler
    
    # Group selection callbacks
    elif data.startswith('grp_'):
        result = await handle_group_selection(update, context, data)
        return result  # Возвращаем состояние для ConversationHandler
    
    # Admin callbacks
    elif data.startswith('adm_'):
        await handle_admin_callbacks(update, context, data)
        return
    
    # Catalog application
    elif data == 'ctlg_app':
        await query.edit_message_caption(
            caption="📝 Для подачи заявки в каталог используйте команду /text"
        )
        return
    
    # Show cards
    elif data == 'show_cards':
        from handlers.user_handlers import cards_command
        await cards_command(update, context)
        return
    
    # Start search
    elif data == 'start_search':
        await query.message.reply_text(
            "🔍 Введите поисковый запрос:\n\n"
            "Используйте: /search <запрос>"
        )
        return


async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle navigation callbacks"""
    query = update.callback_query
    
    if data == 'nav_refresh':
        # Refresh cards
        user = update.effective_user
        cards = get_cards_for_user(user.id, limit=config.CARDS_PER_PAGE)
        
        if cards:
            context.user_data['current_cards'] = [card.id for card in cards]
            context.user_data['current_card_index'] = 0
            
            from handlers.user_handlers import show_card
            await show_card(update, context, 0, cards)
        else:
            await query.edit_message_caption(
                caption="Нет доступных карточек. Попробуйте позже."
            )
    
    elif data.startswith('nav_prev_') or data.startswith('nav_next_'):
        # Navigate between cards
        current_index = int(data.split('_')[-1])
        
        if data.startswith('nav_prev_'):
            new_index = current_index - 1
        else:
            new_index = current_index + 1
        
        card_ids = context.user_data.get('current_cards', [])
        
        if 0 <= new_index < len(card_ids):
            session = get_session()
            try:
                cards = session.query(Card).filter(Card.id.in_(card_ids)).all()
                cards_dict = {card.id: card for card in cards}
                ordered_cards = [cards_dict[cid] for cid in card_ids if cid in cards_dict]
                
                context.user_data['current_card_index'] = new_index
                
                from handlers.user_handlers import show_card
                await show_card(update, context, new_index, ordered_cards)
            finally:
                session.close()


async def handle_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle review callbacks"""
    query = update.callback_query
    
    if data.startswith('rvw_add_'):
        # Add review
        card_id = int(data.split('_')[-1])
        
        # Check cooldown
        user = update.effective_user
        cooldown_expires = check_cooldown(user.id, 'review')
        
        if cooldown_expires:
            time_left = cooldown_expires - datetime.utcnow()
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            await query.answer(
                f"⏳ Вы можете оставить следующий отзыв через {hours}ч {minutes}мин",
                show_alert=True
            )
            return
        
        context.user_data['review_card_id'] = card_id
        await query.message.reply_text(
            "📝 Напишите свой отзыв о карточке:\n\n"
            "(Используйте команду /cancel для отмены)"
        )
    
    elif data.startswith('rvw_stats_'):
        # Show review statistics
        card_id = int(data.split('_')[-1])
        
        session = get_session()
        try:
            reviews = session.query(Review).filter(Review.card_id == card_id).all()
            avg_rating, rating_count = get_card_rating(card_id)
            
            text = f"📊 Статистика отзывов\n\n"
            text += f"⭐️ Средний рейтинг: {avg_rating} ({rating_count} оценок)\n"
            text += f"💬 Всего отзывов: {len(reviews)}\n\n"
            
            if reviews:
                text += "Последние отзывы:\n"
                for review in reviews[-5:]:  # Last 5 reviews
                    text += f"• {review.text[:100]}...\n"
            
            await query.edit_message_caption(
                caption=text,
                reply_markup=get_review_keyboard(card_id)
            )
        finally:
            session.close()
    
    elif data.startswith('rvw_back_'):
        # Back to card
        card_id = int(data.split('_')[-1])
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if card:
                card_text = format_card_text(card)
                from keyboards.keyboards import get_card_keyboard
                keyboard = get_card_keyboard(card)
                
                await query.edit_message_caption(
                    caption=card_text,
                    reply_markup=keyboard
                )
        finally:
            session.close()
    
    elif data.startswith('rvw_'):
        # Show reviews
        card_id = int(data.split('_')[1])
        keyboard = get_review_keyboard(card_id)
        
        await query.edit_message_caption(
            caption="⭐️ Отзывы и оценки\n\nВыберите действие:",
            reply_markup=keyboard
        )


async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle rating callbacks"""
    query = update.callback_query
    
    if data.startswith('rt_show_'):
        # Show rating keyboard
        card_id = int(data.split('_')[-1])
        keyboard = get_rating_keyboard(card_id)
        
        await query.edit_message_caption(
            caption="⭐️ Оцените карточку от 1 до 5 звёзд:",
            reply_markup=keyboard
        )
    
    elif data.startswith('rt_vote_'):
        # Vote
        parts = data.split('_')
        card_id = int(parts[2])
        rating_value = int(parts[3])
        
        user = update.effective_user
        
        session = get_session()
        try:
            # Check if already rated
            existing = session.query(Rating).filter(
                Rating.user_id == user.id,
                Rating.card_id == card_id
            ).first()
            
            if existing:
                existing.rating = rating_value
            else:
                rating = Rating(
                    user_id=user.id,
                    card_id=card_id,
                    rating=rating_value
                )
                session.add(rating)
            
            session.commit()
            
            await query.answer(f"✅ Вы поставили оценку: {'⭐️' * rating_value}")
            
            # Show updated reviews menu
            keyboard = get_review_keyboard(card_id)
            await query.edit_message_caption(
                caption="✅ Спасибо за вашу оценку!\n\n⭐️ Отзывы и оценки",
                reply_markup=keyboard
            )
        finally:
            session.close()


async def handle_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle subscription callbacks"""
    query = update.callback_query
    
    if data == 'my_subs' or data == 'subs_back':
        # Show subscriptions menu
        keyboard = get_subscriptions_keyboard()
        await query.edit_message_caption(
            caption="🔔 Подписки\n\nВыберите тип подписок:",
            reply_markup=keyboard
        )
    
    elif data == 'subs_cats':
        # Show category subscriptions
        user = update.effective_user
        
        session = get_session()
        try:
            subs = session.query(CategorySubscription).filter(
                CategorySubscription.user_id == user.id
            ).all()
            
            text = "📂 Подписки на категории:\n\n"
            
            if subs:
                for sub in subs:
                    text += f"• {sub.category}\n"
            else:
                text += "У вас нет подписок на категории.\n"
            
            text += "\nИспользуйте команды:\n"
            text += "/follow <категория> - подписаться\n"
            text += "/unfollow <категория> - отписаться"
            
            await query.edit_message_caption(
                caption=text,
                reply_markup=get_subscriptions_keyboard()
            )
        finally:
            session.close()
    
    elif data == 'subs_cards':
        # Show card subscriptions
        user = update.effective_user
        
        session = get_session()
        try:
            subs = session.query(CardSubscription).filter(
                CardSubscription.user_id == user.id
            ).all()
            
            text = "🃏 Подписки на карточки:\n\n"
            
            if subs:
                for sub in subs:
                    card = session.query(Card).filter(Card.id == sub.card_id).first()
                    if card:
                        text += f"• Карточка #{card.card_number}\n"
            else:
                text += "У вас нет подписок на карточки.\n"
            
            text += "\nИспользуйте команду:\n"
            text += "/followid <номер> - подписаться на карточку"
            
            await query.edit_message_caption(
                caption=text,
                reply_markup=get_subscriptions_keyboard()
            )
        finally:
            session.close()


async def handle_text_form(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle text form callbacks"""
    query = update.callback_query
    
    if data == 'text_form':
        keyboard = get_text_form_keyboard()
        await query.message.reply_text(
            "📝 Выберите тип формы:",
            reply_markup=keyboard
        )
    
    elif data.startswith('txtf_'):
        parts = data.split('_')
        action = parts[1]
        
        if action in ['catalog', 'post', 'admin', 'report', 'search']:
            # Start form
            context.user_data['text_form_type'] = action
            
            form_names = {
                'catalog': 'Заявка в каталог',
                'post': 'Предложение публикации',
                'admin': 'Связь с администратором',
                'report': 'Жалоба на пользователя',
                'search': 'Форма «Ищу»'
            }
            
            await query.message.reply_text(
                f"📝 {form_names[action]}\n\n"
                "Напишите ваше сообщение и при необходимости прикрепите медиа:"
            )
        
        elif action == 'send':
            # Send form to moderation
            form_type = parts[2] if len(parts) > 2 else context.user_data.get('text_form_type')
            
            message_text = context.user_data.get('text_form_message', '')
            media_type = context.user_data.get('text_form_media_type')
            media_id = context.user_data.get('text_form_media_id')
            
            user = query.from_user
            
            form_names = {
                'catalog': 'Заявка в каталог',
                'post': 'Предложение публикации',
                'admin': 'Связь с администратором',
                'report': 'Жалоба на пользователя',
                'search': 'Форма «Ищу»'
            }
            
            # Create message for admin group
            admin_text = f"📬 {form_names.get(form_type, 'Новая форма')}\n\n"
            admin_text += f"От: {user.first_name}"
            if user.username:
                admin_text += f" (@{user.username})"
            admin_text += f"\nID: {user.id}\n\n"
            admin_text += message_text
            
            # Send to moderation group
            try:
                if media_type and media_id:
                    if media_type == 'photo':
                        await context.bot.send_photo(
                            chat_id=config.MODERATION_GROUP_ID,
                            photo=media_id,
                            caption=admin_text
                        )
                    elif media_type == 'video':
                        await context.bot.send_video(
                            chat_id=config.MODERATION_GROUP_ID,
                            video=media_id,
                            caption=admin_text
                        )
                    elif media_type == 'document':
                        await context.bot.send_document(
                            chat_id=config.MODERATION_GROUP_ID,
                            document=media_id,
                            caption=admin_text
                        )
                else:
                    await context.bot.send_message(
                        chat_id=config.MODERATION_GROUP_ID,
                        text=admin_text
                    )
                
                # Set cooldown
                from utils.helpers import set_cooldown
                set_cooldown(user.id, 'text_command', config.COOLDOWN_TEXT_COMMAND)
                
                await query.edit_message_text(
                    "✅ Ваша заявка отправлена администратору!\n"
                    "Кулдаун: 8 часов до следующей заявки."
                )
                
                # Clear context
                context.user_data.pop('text_form_type', None)
                context.user_data.pop('text_form_message', None)
                context.user_data.pop('text_form_media_type', None)
                context.user_data.pop('text_form_media_id', None)
                
            except Exception as e:
                logger.error(f"Error sending form to moderation: {e}")
                await query.answer("❌ Ошибка при отправке формы", show_alert=True)
        
        elif action == 'edit':
            # Edit form
            await query.message.reply_text(
                "✏️ Отправьте новое сообщение для редактирования:"
            )
        
        elif action == 'del':
            # Delete form
            context.user_data.pop('text_form_type', None)
            context.user_data.pop('text_form_message', None)
            context.user_data.pop('text_form_media_type', None)
            context.user_data.pop('text_form_media_id', None)
            
            await query.edit_message_text("🗑 Форма удалена")


async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle category selection callbacks"""
    query = update.callback_query
    
    if data.startswith('cat_sel_'):
        # Toggle category
        category = data.replace('cat_sel_', '')
        
        new_card = context.user_data.get('new_card', {})
        categories = new_card.get('categories', [])
        
        if category in categories:
            categories.remove(category)
        else:
            if len(categories) < 3:
                categories.append(category)
            else:
                await query.answer("Максимум 3 категории", show_alert=True)
                return
        
        new_card['categories'] = categories
        context.user_data['new_card'] = new_card
        
        keyboard = get_category_selection_keyboard(categories)
        await query.edit_message_reply_markup(reply_markup=keyboard)
    
    elif data == 'cat_done':
        # Finish category selection
        new_card = context.user_data.get('new_card', {})
        categories = new_card.get('categories', [])
        
        if not categories:
            await query.answer("Выберите хотя бы одну категорию", show_alert=True)
            return WAITING_CATEGORIES
        
        await query.message.reply_text(
            f"✅ Выбрано категорий: {len(categories)}\n\n"
            "Шаг 3/6: Введите 1-3 хештега (через пробел):"
        )
        
        return WAITING_HASHTAGS


async def handle_group_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle group selection callbacks"""
    query = update.callback_query
    
    if data.startswith('grp_sel_'):
        # Toggle group
        group = data.replace('grp_sel_', '')
        
        new_card = context.user_data.get('new_card', {})
        groups = new_card.get('groups', [])
        
        if group in groups:
            groups.remove(group)
        else:
            if len(groups) < 3:
                groups.append(group)
            else:
                await query.answer("Максимум 3 группы", show_alert=True)
                return
        
        new_card['groups'] = groups
        context.user_data['new_card'] = new_card
        
        keyboard = get_group_selection_keyboard(groups)
        await query.edit_message_reply_markup(reply_markup=keyboard)
    
    elif data == 'grp_done':
        # Finish group selection
        new_card = context.user_data.get('new_card', {})
        groups = new_card.get('groups', [])
        
        if not groups:
            await query.answer("Выберите хотя бы одну группу", show_alert=True)
            return
        
        await query.message.reply_text(
            f"✅ Выбрано групп: {len(groups)}\n\n"
            "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
        )
        
        return WAITING_LINK


async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle admin callbacks"""
    query = update.callback_query
    
    if not query.from_user.id in config.ADMIN_IDS:
        await query.answer("У вас нет доступа", show_alert=True)
        return
    
    if data.startswith('adm_pub_'):
        # Publish card
        temp_id = data.replace('adm_pub_', '')
        await publish_card(update, context, temp_id)
    
    elif data.startswith('adm_del_'):
        # Delete card preview
        await query.edit_message_caption(
            caption="🗑 Карточка удалена"
        )
        context.user_data.pop('new_card', None)
        context.user_data.pop('temp_card_id', None)
    
    elif data.startswith('adm_edit_'):
        # Edit card
        await query.answer("Редактирование пока недоступно", show_alert=True)
