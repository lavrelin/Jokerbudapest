import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database.models import Card, User, Review, Cooldown
from database.database import get_session
from utils.helpers import (
    generate_unique_card_number, get_card_rating, 
    get_card_reviews_count, remove_cooldown
)
from keyboards.keyboards import (
    get_add_card_type_keyboard, get_admin_card_preview_keyboard,
    get_category_selection_keyboard, get_group_selection_keyboard
)
import config

logger = logging.getLogger(__name__)

# Conversation states
(WAITING_LINK, WAITING_CATEGORIES, WAITING_HASHTAGS, 
 WAITING_ADDRESS, WAITING_DESCRIPTION, WAITING_MEDIA, WAITING_GROUP_SELECTION) = range(7)


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS


async def addcatalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addcatalog command - add card to group A"""
    user_id = update.effective_user.id
    logger.info(f"addcatalog command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа к этой команде\n\nВаш ID: {user_id}\nАдмин IDs: {config.ADMIN_IDS}")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['A']}
    
    await update.message.reply_text(
        "📚 Добавление карточки в Каталог (группа A)\n\n"
        "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
    )
    return WAITING_LINK


async def addpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addpost command - add card to group B"""
    user_id = update.effective_user.id
    logger.info(f"addpost command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа к этой команде")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['B']}
    
    await update.message.reply_text(
        "📰 Добавление карточки в Посты (группа B)\n\n"
        "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
    )
    return WAITING_LINK


async def addpeople_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addpeople command - add card to group C"""
    user_id = update.effective_user.id
    logger.info(f"addpeople command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа к этой команде")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['C']}
    
    await update.message.reply_text(
        "👤 Добавление карточки в Люди (группа C)\n\n"
        "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
    )
    return WAITING_LINK


async def addpriority_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addpriority command - add card to group D"""
    user_id = update.effective_user.id
    logger.info(f"addpriority command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа к этой команде")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['D']}
    
    await update.message.reply_text(
        "⭐️ Добавление приоритетной карточки (группа D)\n\n"
        "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
    )
    return WAITING_LINK


async def addreklama_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addreklama command - add card to group E"""
    user_id = update.effective_user.id
    logger.info(f"addreklama command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа к этой команде")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['E']}
    
    await update.message.reply_text(
        "📢 Добавление рекламной карточки (группа E)\n\n"
        "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
    )
    return WAITING_LINK


async def add24_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add24 command - add card to group F (24 hours)"""
    user_id = update.effective_user.id
    logger.info(f"add24 command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа к этой команде")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['F']}
    
    await update.message.reply_text(
        "⏰ Добавление карточки на 24 часа (группа F)\n\n"
        "Карточка будет автоматически удалена через 24 часа.\n\n"
        "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
    )
    return WAITING_LINK


async def addwork_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addwork command - add card to group G"""
    user_id = update.effective_user.id
    logger.info(f"addwork command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа к этой команде")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['G']}
    
    await update.message.reply_text(
        "💼 Добавление карточки в Работа (группа G)\n\n"
        "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
    )
    return WAITING_LINK


async def addhome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addhome command - add card to group H"""
    user_id = update.effective_user.id
    logger.info(f"addhome command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа к этой команде")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['H']}
    
    await update.message.reply_text(
        "🏠 Добавление карточки в Дом (группа H)\n\n"
        "Шаг 1/6: Отправьте ссылку на оригинальный пост:"
    )
    return WAITING_LINK


async def addcard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addcard command - select groups for card"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': []}
    
    keyboard = get_group_selection_keyboard()
    
    await update.message.reply_text(
        "🎯 Выберите 1-3 группы для карточки:",
        reply_markup=keyboard
    )
    return WAITING_GROUP_SELECTION


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive original link"""
    link = update.message.text
    context.user_data['new_card']['original_link'] = link
    
    keyboard = get_category_selection_keyboard()
    
    await update.message.reply_text(
        "Шаг 2/6: Выберите 1-3 категории:",
        reply_markup=keyboard
    )
    return WAITING_CATEGORIES


async def receive_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive categories (handled by callback)"""
    # This will be handled by callback handler
    pass


async def receive_hashtags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive hashtags"""
    hashtags = update.message.text
    hashtag_list = [tag.strip('#').strip() for tag in hashtags.split() if tag.strip()]
    
    if len(hashtag_list) > 3:
        await update.message.reply_text(
            "⚠️ Максимум 3 хештега. Пожалуйста, введите снова:"
        )
        return WAITING_HASHTAGS
    
    context.user_data['new_card']['hashtags'] = hashtag_list
    
    await update.message.reply_text(
        "Шаг 4/6: Введите адрес или локацию (или отправьте '-' чтобы пропустить):"
    )
    return WAITING_ADDRESS


async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive address"""
    address = update.message.text
    
    if address != '-':
        context.user_data['new_card']['address'] = address
    
    await update.message.reply_text(
        "Шаг 5/6: Введите краткое описание для карточки:"
    )
    return WAITING_DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive description"""
    description = update.message.text
    context.user_data['new_card']['description'] = description
    
    await update.message.reply_text(
        "Шаг 6/6: Отправьте медиа (фото, видео или документ):"
    )
    return WAITING_MEDIA


async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive media and create card preview"""
    new_card = context.user_data.get('new_card', {})
    
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
        await update.message.reply_text(
            "⚠️ Неподдерживаемый тип медиа. Отправьте фото, видео или документ."
        )
        return WAITING_MEDIA
    
    new_card['media_type'] = media_type
    new_card['media_file_id'] = media_file_id
    
    # Generate temporary ID for preview
    import uuid
    temp_id = str(uuid.uuid4())
    context.user_data['temp_card_id'] = temp_id
    context.user_data['new_card'] = new_card
    
    # Show preview
    await show_card_preview(update, context, new_card, temp_id)
    
    return ConversationHandler.END


async def show_card_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, card_data: dict, temp_id: str):
    """Show card preview to admin"""
    text = "📋 Предпросмотр карточки:\n\n"
    text += f"Группы: {', '.join(card_data.get('groups', []))}\n"
    text += f"Категории: {', '.join(card_data.get('categories', []))}\n"
    
    if card_data.get('hashtags'):
        text += f"Хештеги: {' '.join(['#' + tag for tag in card_data['hashtags']])}\n"
    
    if card_data.get('address'):
        text += f"Адрес: {card_data['address']}\n"
    
    text += f"\n{card_data.get('description', '')}\n"
    text += f"\nСсылка: {card_data.get('original_link', 'Не указана')}"
    
    keyboard = get_admin_card_preview_keyboard(temp_id)
    
    # Send with media
    if card_data.get('media_type') == 'photo':
        await update.message.reply_photo(
            photo=card_data['media_file_id'],
            caption=text,
            reply_markup=keyboard
        )
    elif card_data.get('media_type') == 'video':
        await update.message.reply_video(
            video=card_data['media_file_id'],
            caption=text,
            reply_markup=keyboard
        )
    elif card_data.get('media_type') == 'document':
        await update.message.reply_document(
            document=card_data['media_file_id'],
            caption=text,
            reply_markup=keyboard
        )


async def publish_card(update: Update, context: ContextTypes.DEFAULT_TYPE, temp_id: str):
    """Publish card to database"""
    new_card = context.user_data.get('new_card', {})
    
    session = get_session()
    try:
        # Generate card number
        card_number = generate_unique_card_number()
        
        # Create card
        card = Card(
            card_number=card_number,
            groups=new_card.get('groups', []),
            categories=new_card.get('categories', []),
            hashtags=new_card.get('hashtags', []),
            address=new_card.get('address'),
            description=new_card.get('description'),
            original_link=new_card.get('original_link'),
            media_type=new_card.get('media_type'),
            media_file_id=new_card.get('media_file_id')
        )
        
        # Set delete time for group F cards
        if 'F' in new_card.get('groups', []):
            card.delete_at = datetime.utcnow() + timedelta(seconds=config.GROUP_F_DELETE_TIME)
        
        session.add(card)
        session.commit()
        
        await update.callback_query.answer("✅ Карточка успешно опубликована!")
        await update.callback_query.edit_message_caption(
            caption=f"✅ Карточка #{card_number} успешно опубликована!"
        )
        
        # Clear temp data
        context.user_data.pop('new_card', None)
        context.user_data.pop('temp_card_id', None)
        
    except Exception as e:
        logger.error(f"Error publishing card: {e}")
        await update.callback_query.answer("❌ Ошибка при публикации карточки")
    finally:
        session.close()


async def say_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /say command - send message to user"""
    if not is_admin(update.effective_user.id):
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "Использование:\n"
            "/say <user_id> <text> - отправить сообщение по ID\n"
            "/say @username <text> - отправить сообщение по username"
        )
        return
    
    target = context.args[0]
    message_text = ' '.join(context.args[1:])
    
    try:
        if target.startswith('@'):
            # Send by username
            username = target[1:]
            session = get_session()
            try:
                user = session.query(User).filter(User.username == username).first()
                if not user:
                    await update.message.reply_text(f"Пользователь {target} не найден")
                    return
                user_id = user.id
            finally:
                session.close()
        else:
            # Send by ID
            user_id = int(target)
        
        await context.bot.send_message(chat_id=user_id, text=message_text)
        await update.message.reply_text(f"✅ Сообщение отправлено пользователю {target}")
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await update.message.reply_text(f"❌ Ошибка при отправке сообщения: {e}")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command - send message to all users"""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text(
            "Использование: /broadcast <текст сообщения>"
        )
        return
    
    message_text = ' '.join(context.args)
    
    session = get_session()
    try:
        users = session.query(User).all()
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                await context.bot.send_message(chat_id=user.id, text=message_text)
                success_count += 1
            except Exception as e:
                logger.error(f"Error sending to user {user.id}: {e}")
                fail_count += 1
        
        await update.message.reply_text(
            f"✅ Рассылка завершена\n"
            f"Успешно: {success_count}\n"
            f"Ошибок: {fail_count}"
        )
    finally:
        session.close()


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove command - delete card by ID"""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /remove <card_id>")
        return
    
    try:
        card_id = int(context.args[0])
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                await update.message.reply_text(f"Карточка с ID {card_id} не найдена")
                return
            
            card_number = card.card_number
            session.delete(card)
            session.commit()
            
            await update.message.reply_text(f"✅ Карточка #{card_number} (ID: {card_id}) удалена")
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный ID карточки")


async def removecd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removecd command - remove user cooldown"""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /removecd <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        remove_cooldown(user_id)
        await update.message.reply_text(f"✅ Кулдауны пользователя {user_id} сняты")
    except ValueError:
        await update.message.reply_text("Неверный ID пользователя")


async def cardstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cardstats command - show card statistics"""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /cardstats <card_id>")
        return
    
    try:
        card_id = int(context.args[0])
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                await update.message.reply_text(f"Карточка с ID {card_id} не найдена")
                return
            
            avg_rating, rating_count = get_card_rating(card_id)
            review_count = get_card_reviews_count(card_id)
            
            text = f"📊 Статистика карточки #{card.card_number} (ID: {card_id})\n\n"
            text += f"Группы: {', '.join(card.groups)}\n"
            text += f"⭐️ Рейтинг: {avg_rating} ({rating_count} оценок)\n"
            text += f"💬 Отзывы: {review_count}\n"
            text += f"👁 Просмотры: {card.total_views} (уникальных: {card.unique_views})\n"
            text += f"🔗 Переходы по ссылке: {card.link_clicks}\n"
            
            # Send to admin group
            await context.bot.send_message(
                chat_id=config.ADMIN_GROUP_ID,
                text=text
            )
            
            await update.message.reply_text("✅ Статистика отправлена в админ-группу")
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный ID карточки")


async def statsf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /statsf command - show group F cards statistics"""
    if not is_admin(update.effective_user.id):
        return
    
    session = get_session()
    try:
        # Get all cards in group F
        cards = session.query(Card).all()
        f_cards = [card for card in cards if 'F' in card.groups]
        
        text = f"📊 Статистика группы F\n"
        text += f"Всего карточек: {len(f_cards)}\n\n"
        
        for card in f_cards:
            if card.delete_at:
                time_left = card.delete_at - datetime.utcnow()
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                countdown = f"{hours}ч {minutes}мин"
            else:
                countdown = "Не установлено"
            
            text += f"ID: {card.id}, Номер: {card.card_number}\n"
            text += f"До удаления: {countdown}\n\n"
        
        # Send to admin group
        await context.bot.send_message(
            chat_id=config.ADMIN_GROUP_ID,
            text=text if text else "Нет карточек в группе F"
        )
        
        await update.message.reply_text("✅ Статистика отправлена в админ-группу")
    finally:
        session.close()


async def reviewdelete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reviewdelete command - delete review"""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /reviewdelete <review_id>")
        return
    
    try:
        review_id = int(context.args[0])
        
        session = get_session()
        try:
            review = session.query(Review).filter(Review.id == review_id).first()
            if not review:
                await update.message.reply_text(f"Отзыв с ID {review_id} не найден")
                return
            
            session.delete(review)
            session.commit()
            
            await update.message.reply_text(f"✅ Отзыв ID {review_id} удалён")
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный ID отзыва")


async def statscoldown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /statscoldown command - show users with active cooldown"""
    if not is_admin(update.effective_user.id):
        return
    
    session = get_session()
    try:
        cooldowns = session.query(Cooldown).filter(
            Cooldown.expires_at > datetime.utcnow()
        ).all()
        
        text = "📊 Пользователи с активным кулдауном:\n\n"
        
        if not cooldowns:
            text = "Нет пользователей с активным кулдауном"
        else:
            for cd in cooldowns:
                user = session.query(User).filter(User.id == cd.user_id).first()
                username = f"@{user.username}" if user and user.username else f"ID: {cd.user_id}"
                
                time_left = cd.expires_at - datetime.utcnow()
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                text += f"{username}\n"
                text += f"Тип: {cd.cooldown_type}\n"
                text += f"Осталось: {hours}ч {minutes}мин\n\n"
        
        # Send to admin group
        await context.bot.send_message(
            chat_id=config.ADMIN_GROUP_ID,
            text=text
        )
        
        await update.message.reply_text("✅ Статистика отправлена в админ-группу")
    finally:
        session.close()


async def statsgroups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /statsgroups command - show cards count in each group"""
    if not is_admin(update.effective_user.id):
        return
    
    session = get_session()
    try:
        all_cards = session.query(Card).all()
        
        group_counts = {group: 0 for group in config.CARD_GROUPS}
        
        for card in all_cards:
            for group in card.groups:
                if group in group_counts:
                    group_counts[group] += 1
        
        text = "📊 Количество карточек в каждой группе:\n\n"
        
        for group in config.CARD_GROUPS:
            text += f"Группа {group}: {group_counts[group]} карточек\n"
        
        text += f"\nВсего карточек: {len(all_cards)}"
        
        # Send to admin group
        await context.bot.send_message(
            chat_id=config.ADMIN_GROUP_ID,
            text=text
        )
        
        await update.message.reply_text("✅ Статистика отправлена в админ-группу")
    finally:
        session.close()


async def cardgroupedit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cardgroupedit command - edit card groups"""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /cardgroupedit <card_id>")
        return
    
    try:
        card_id = int(context.args[0])
        
        session = get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                await update.message.reply_text(f"Карточка с ID {card_id} не найдена")
                return
            
            # Store card ID in context for callback
            context.user_data['edit_card_id'] = card_id
            context.user_data['edit_card_groups'] = card.groups.copy()
            
            from keyboards.keyboards import get_group_selection_keyboard
            keyboard = get_group_selection_keyboard(card.groups)
            
            await update.message.reply_text(
                f"Редактирование групп карточки #{card.card_number}\n"
                f"Текущие группы: {', '.join(card.groups)}\n\n"
                "Выберите новые группы:",
                reply_markup=keyboard
            )
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный ID карточки")


async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /edit command - edit card"""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /edit <card_id>")
        return
    
    await update.message.reply_text("⚠️ Функция редактирования в разработке")


async def changenumber_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /changenumber command - change card number"""
    if not is_admin(update.effective_user.id):
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /changenumber <old_number> <new_number>")
        return
    
    try:
        old_number = int(context.args[0])
        new_number = int(context.args[1])
        
        if new_number < 1 or new_number > 9999:
            await update.message.reply_text("Новый номер должен быть от 1 до 9999")
            return
        
        session = get_session()
        try:
            # Find card with old number
            old_card = session.query(Card).filter(Card.card_number == old_number).first()
            if not old_card:
                await update.message.reply_text(f"Карточка с номером {old_number} не найдена")
                return
            
            # Check if new number exists
            new_card = session.query(Card).filter(Card.card_number == new_number).first()
            if new_card:
                await update.message.reply_text(f"Номер {new_number} уже используется")
                return
            
            # Update number
            old_card.card_number = new_number
            session.commit()
            
            await update.message.reply_text(
                f"✅ Номер карточки изменён: {old_number} → {new_number}"
            )
        finally:
            session.close()
            
    except ValueError:
        await update.message.reply_text("Неверный формат номеров")
