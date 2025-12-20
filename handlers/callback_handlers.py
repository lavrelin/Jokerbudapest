"""
Обработчики callback-кнопок
"""
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from database.models import Card
from database.database import get_session
from utils.helpers import (
    add_or_update_rating, increment_card_clicks,
    check_cooldown, set_cooldown, format_card_text
)
from keyboards.keyboards import (
    get_rating_keyboard, get_card_keyboard,
    get_start_keyboard, get_text_form_keyboard,
    get_form_preview_keyboard
)
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
    
    # Rating callbacks
    elif data.startswith('rate_'):
        await handle_rate_button(update, context, data)
    
    elif data.startswith('rating_'):
        await handle_rating_selection(update, context, data)
    
    elif data.startswith('back_to_card_'):
        await handle_back_to_card(update, context, data)
    
    # Start menu callbacks
    elif data == 'show_cards':
        from handlers.user_handlers import cards_command
        await cards_command(update, context)
    
    elif data == 'start_search':
        await query.message.reply_text(
            "🔍 Введите поисковый запрос:\n\n"
            "Используйте: /search <запрос>"
        )
    
    elif data == 'text_form':
        await query.message.reply_text(
            "📝 Выберите тип заявки:",
            reply_markup=get_text_form_keyboard()
        )
    
    # Form callbacks
    elif data.startswith('form_'):
        await handle_form_callbacks(update, context, data)
    
    # Admin callbacks
    elif data == 'admin_publish':
        from handlers.admin_handlers import publish_card
        await publish_card(update, context)
    
    elif data == 'admin_delete':
        from handlers.admin_handlers import delete_card_draft
        await delete_card_draft(update, context)


# ============== НАВИГАЦИЯ ==============

async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle navigation callbacks"""
    query = update.callback_query
    
    # Локальный импорт для избежания циклических зависимостей
    from handlers.user_handlers import show_card
    
    current_index = context.user_data.get('current_index', 0)
    card_ids = context.user_data.get('current_cards', [])
    
    if not card_ids:
        await query.answer("❌ Нет карточек для навигации")
        return
    
    if data == 'nav_prev':
        if current_index > 0:
            await show_card(update, context, current_index - 1)
        else:
            await query.answer("Это первая карточка")
    
    elif data == 'nav_next':
        if current_index < len(card_ids) - 1:
            await show_card(update, context, current_index + 1)
        else:
            await query.answer("Это последняя карточка")
    
    elif data == 'nav_refresh':
        await show_card(update, context, current_index)
    
    elif data == 'nav_info':
        await query.answer(f"Карточка {current_index + 1} из {len(card_ids)}")


# ============== РЕЙТИНГ ==============

async def handle_rate_button(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle rate button click - show rating keyboard"""
    query = update.callback_query
    
    # Extract card_id from callback data: rate_{card_id}
    try:
        card_id = int(data.split('_')[1])
    except (IndexError, ValueError):
        await query.answer("❌ Ошибка")
        return
    
    # Check cooldown
    cooldown_expires = check_cooldown(update.effective_user.id, 'rating')
    if cooldown_expires:
        time_left = (cooldown_expires - datetime.utcnow()).total_seconds()
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        await query.answer(
            f"⏳ Подождите {minutes}м {seconds}с перед следующей оценкой",
            show_alert=True
        )
        return
    
    # Show rating keyboard
    keyboard = get_rating_keyboard(card_id)
    
    await query.edit_message_reply_markup(reply_markup=keyboard)
    await query.answer("Выберите оценку от 1 до 10")


async def handle_rating_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle rating selection"""
    query = update.callback_query
    
    # Parse callback data: rating_{card_id}_{rating}
    try:
        parts = data.split('_')
        card_id = int(parts[1])
        rating = int(parts[2])
    except (IndexError, ValueError):
        await query.answer("❌ Ошибка")
        return
    
    # Validate rating
    if rating < 1 or rating > 10:
        await query.answer("❌ Неверная оценка")
        return
    
    # Add rating
    try:
        add_or_update_rating(update.effective_user.id, card_id, rating)
        
        # Set cooldown
        set_cooldown(update.effective_user.id, 'rating', config.COOLDOWN_RATING)
        
        # Get updated card
        session = get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if card:
                # Get current index and cards list
                current_index = context.user_data.get('current_index', 0)
                card_ids = context.user_data.get('current_cards', [])
                
                # Update keyboard
                keyboard = get_card_keyboard(card, current_index, len(card_ids))
                
                # Update caption with new rating
                text = format_card_text(card)
                
                await query.edit_message_caption(
                    caption=text,
                    reply_markup=keyboard
                )
                
                await query.answer(f"✅ Вы оценили на {rating}/10!", show_alert=True)
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error saving rating: {e}")
        await query.answer("❌ Ошибка при сохранении оценки", show_alert=True)


async def handle_back_to_card(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle back to card button"""
    query = update.callback_query
    
    # Parse callback data: back_to_card_{card_id}
    try:
        card_id = int(data.split('_')[-1])
    except (IndexError, ValueError):
        await query.answer("❌ Ошибка")
        return
    
    # Get card
    session = get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            await query.answer("❌ Карточка не найдена")
            return
        
        # Get current index and cards list
        current_index = context.user_data.get('current_index', 0)
        card_ids = context.user_data.get('current_cards', [])
        
        # Restore keyboard
        keyboard = get_card_keyboard(card, current_index, len(card_ids))
        
        await query.edit_message_reply_markup(reply_markup=keyboard)
        await query.answer()
        
    finally:
        session.close()


# ============== ФОРМА ЗАЯВКИ ==============

async def handle_form_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle form callbacks"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check cooldown
    cooldown_expires = check_cooldown(user_id, 'text_form')
    if cooldown_expires:
        time_left = (cooldown_expires - datetime.utcnow()).total_seconds()
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        await query.answer(
            f"⏳ Подождите {hours}ч {minutes}м перед следующей заявкой",
            show_alert=True
        )
        return
    
    if data == 'form_catalog':
        context.user_data['form_type'] = 'catalog'
        await query.message.reply_text(
            "📋 ЗАЯВКА В КАТАЛОГ\n\n"
            "Отправьте информацию в формате:\n"
            "Название\nКатегория\nРайон\nОписание\nСсылка на пост\n\n"
            "Или /cancel для отмены"
        )
    
    elif data == 'form_post':
        context.user_data['form_type'] = 'post'
        await query.message.reply_text(
            "📝 ПРЕДЛОЖЕНИЕ ПУБЛИКАЦИИ\n\n"
            "Опишите что вы хотите опубликовать\n\n"
            "Или /cancel для отмены"
        )
    
    elif data == 'form_admin':
        context.user_data['form_type'] = 'admin'
        await query.message.reply_text(
            "👤 СВЯЗЬ С АДМИНИСТРАТОРОМ\n\n"
            "Напишите ваше сообщение\n\n"
            "Или /cancel для отмены"
        )
    
    elif data == 'form_submit':
        await submit_form(update, context)
    
    elif data == 'form_cancel':
        context.user_data.pop('form_type', None)
        context.user_data.pop('form_text', None)
        await query.message.edit_text("❌ Заявка отменена")
    
    elif data == 'back_to_start':
        keyboard = get_start_keyboard()
        await query.message.edit_text(
            "Главное меню:",
            reply_markup=keyboard
        )


async def submit_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Submit form to moderation group"""
    query = update.callback_query
    user_id = update.effective_user.id
    user = update.effective_user
    
    form_type = context.user_data.get('form_type', 'unknown')
    form_text = context.user_data.get('form_text', '')
    
    # Send to moderation group
    try:
        message_text = (
            f"📝 НОВАЯ ЗАЯВКА\n\n"
            f"Тип: {form_type}\n"
            f"От: {user.first_name} (@{user.username or 'без username'})\n"
            f"ID: {user_id}\n\n"
            f"{form_text}"
        )
        
        await context.bot.send_message(
            chat_id=config.MODERATION_GROUP_ID,
            text=message_text
        )
        
        # Set cooldown
        set_cooldown(user_id, 'text_form', config.COOLDOWN_TEXT_FORM)
        
        # Notify user
        await query.edit_message_text(
            "✅ Заявка отправлена!\n\n"
            "Вы получите уведомление когда администратор её рассмотрит.\n"
            f"Следующую заявку можно отправить через {config.COOLDOWN_TEXT_FORM // 3600} часов."
        )
        
        # Clear form data
        context.user_data.pop('form_type', None)
        context.user_data.pop('form_text', None)
        
    except Exception as e:
        logger.error(f"Error submitting form: {e}")
        await query.answer("❌ Ошибка при отправке заявки", show_alert=True)
