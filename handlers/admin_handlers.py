import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database.models import Card, User, Cooldown
from database.database import get_session
from utils.helpers import generate_unique_card_number
from utils.telegram_parser import parse_telegram_link
from keyboards.keyboards import get_admin_card_preview_keyboard
import config

logger = logging.getLogger(__name__)

# Conversation states
(WAITING_LINK, WAITING_DISTRICT, WAITING_CATEGORY, 
 WAITING_HASHTAGS, WAITING_DESCRIPTION) = range(5)


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS


# ============== КОМАНДЫ ДОБАВЛЕНИЯ КАРТОЧЕК ==============

async def addcatalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add card to group A (Catalog)"""
    user_id = update.effective_user.id
    logger.info(f"addcatalog command from user {user_id}, is_admin: {is_admin(user_id)}")
    
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа\n\nВаш ID: {user_id}\nАдмин IDs: {config.ADMIN_IDS}")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['A']}
    
    await update.message.reply_text(
        "📚 Добавление карточки в КАТАЛОГ (группа A)\n\n"
        "Шаг 1/5: Отправьте ссылку на Telegram пост\n"
        "Медиа будет импортировано автоматически!"
    )
    return WAITING_LINK


async def addpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add card to group B (Posts)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['B']}
    await update.message.reply_text(
        "📰 Добавление карточки в ПОСТЫ (группа B)\n\n"
        "Шаг 1/5: Отправьте ссылку на Telegram пост"
    )
    return WAITING_LINK


async def addpeople_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add card to group C (People)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['C']}
    await update.message.reply_text(
        "👤 Добавление карточки в ЛЮДИ (группа C)\n\n"
        "Шаг 1/5: Отправьте ссылку на Telegram пост"
    )
    return WAITING_LINK


async def addpriority_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add card to group D (Priority)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['D']}
    await update.message.reply_text(
        "⭐️ Добавление ПРИОРИТЕТНОЙ карточки (группа D)\n\n"
        "Шаг 1/5: Отправьте ссылку на Telegram пост"
    )
    return WAITING_LINK


async def addreklama_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add card to group E (Advertising)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['E']}
    await update.message.reply_text(
        "📢 Добавление РЕКЛАМНОЙ карточки (группа E)\n\n"
        "Шаг 1/5: Отправьте ссылку на Telegram пост"
    )
    return WAITING_LINK


async def add24_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add card to group F (24 hours auto-delete)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['F']}
    await update.message.reply_text(
        "⏰ Добавление карточки на 24 ЧАСА (группа F)\n"
        "⚠️ Автоудаление через 24 часа!\n\n"
        "Шаг 1/5: Отправьте ссылку на Telegram пост"
    )
    return WAITING_LINK


async def addwork_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add card to group G (Work)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['G']}
    await update.message.reply_text(
        "💼 Добавление карточки в РАБОТА (группа G)\n\n"
        "Шаг 1/5: Отправьте ссылку на Telegram пост"
    )
    return WAITING_LINK


async def addhome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add card to group H (Home/Real Estate)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(f"❌ У вас нет доступа")
        return ConversationHandler.END
    
    context.user_data['new_card'] = {'groups': ['H']}
    await update.message.reply_text(
        "🏠 Добавление карточки в ДОМ (группа H)\n\n"
        "Шаг 1/5: Отправьте ссылку на Telegram пост"
    )
    return WAITING_LINK


# ============== ОБРАБОТЧИКИ ЭТАПОВ ==============

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and parse Telegram link"""
    link = update.message.text.strip()
    
    await update.message.reply_text("⏳ Получаю медиа из поста...")
    
    # Парсим ссылку и извлекаем медиа
    result = await parse_telegram_link(context.bot, link)
    
    if result['error']:
        await update.message.reply_text(
            f"❌ Ошибка: {result['error']}\n\n"
            "Отправьте правильную ссылку на пост или /cancel для отмены"
        )
        return WAITING_LINK
    
    if not result['media_type']:
        await update.message.reply_text(
            "❌ Пост не содержит медиа (фото/видео/документ)\n\n"
            "Отправьте ссылку на пост с медиа или /cancel для отмены"
        )
        return WAITING_LINK
    
    # Сохраняем данные
    context.user_data['new_card']['link'] = link
    context.user_data['new_card']['media_type'] = result['media_type']
    context.user_data['new_card']['media_file_id'] = result['media_file_id']
    
    # Если есть caption, предлагаем использовать как описание
    if result['caption']:
        context.user_data['new_card']['suggested_description'] = result['caption']
    
    await update.message.reply_text(
        f"✅ Медиа получено: {result['media_type']}\n\n"
        "Шаг 2/5: Введите РАЙОН\n"
        "Например: Будапешт 5, Центр, Pest, и т.д."
    )
    
    return WAITING_DISTRICT


async def receive_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive district"""
    district = update.message.text.strip()
    
    if len(district) > 100:
        await update.message.reply_text("❌ Район слишком длинный (макс 100 символов)")
        return WAITING_DISTRICT
    
    context.user_data['new_card']['district'] = district
    
    await update.message.reply_text(
        f"✅ Район: {district}\n\n"
        "Шаг 3/5: Введите КАТЕГОРИЮ (одно слово)\n"
        "Например: Барбер, Массаж, Ресторан, Ремонт и т.д.\n\n"
        "Это слово будет использоваться для поиска и подписок!"
    )
    
    return WAITING_CATEGORY


async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive category (free word)"""
    category = update.message.text.strip()
    
    if len(category) > 50:
        await update.message.reply_text("❌ Категория слишком длинная (макс 50 символов)")
        return WAITING_CATEGORY
    
    # Проверяем что это одно слово или фраза из 2-3 слов
    word_count = len(category.split())
    if word_count > 3:
        await update.message.reply_text("❌ Категория должна быть 1-3 слова")
        return WAITING_CATEGORY
    
    context.user_data['new_card']['category'] = category
    
    await update.message.reply_text(
        f"✅ Категория: {category}\n\n"
        "Шаг 4/5: Введите ХЕШТЕГИ (через пробел)\n"
        "Например: #барбер #будапешт #недорого"
    )
    
    return WAITING_HASHTAGS


async def receive_hashtags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive hashtags"""
    text = update.message.text.strip()
    
    # Парсим хештеги
    hashtags = []
    for word in text.split():
        # Убираем # если есть
        tag = word.lstrip('#').strip()
        if tag:
            hashtags.append(tag)
    
    if not hashtags:
        await update.message.reply_text("❌ Введите хотя бы один хештег")
        return WAITING_HASHTAGS
    
    context.user_data['new_card']['hashtags'] = hashtags
    
    # Если было suggested_description из caption
    suggested = context.user_data['new_card'].get('suggested_description', '')
    if suggested:
        await update.message.reply_text(
            f"✅ Хештеги: {' '.join(['#' + h for h in hashtags])}\n\n"
            "Шаг 5/5: Введите ОПИСАНИЕ\n\n"
            f"💡 Предложенное описание из поста:\n{suggested[:200]}...\n\n"
            "Введите свое описание или отправьте \".\" чтобы использовать предложенное"
        )
    else:
        await update.message.reply_text(
            f"✅ Хештеги: {' '.join(['#' + h for h in hashtags])}\n\n"
            "Шаг 5/5: Введите ОПИСАНИЕ карточки"
        )
    
    return WAITING_DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive description and show preview"""
    description = update.message.text.strip()
    
    # Если пользователь отправил "." - используем suggested
    if description == "." and context.user_data['new_card'].get('suggested_description'):
        description = context.user_data['new_card']['suggested_description']
    
    if len(description) > 1000:
        await update.message.reply_text("❌ Описание слишком длинное (макс 1000 символов)")
        return WAITING_DESCRIPTION
    
    context.user_data['new_card']['description'] = description
    
    # Показываем предпросмотр
    await show_card_preview(update, context)
    
    return ConversationHandler.END


async def show_card_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show card preview with publish/delete buttons"""
    card_data = context.user_data.get('new_card', {})
    
    # Формируем текст превью
    preview_text = (
        f"📋 ПРЕДПРОСМОТР КАРТОЧКИ\n\n"
        f"🔥 Район: {card_data.get('district', 'Не указан')}\n"
        f"🪽 Категория: {card_data.get('category', 'Не указана')}\n"
        f"{' '.join(['#' + h for h in card_data.get('hashtags', [])])}\n\n"
        f"{card_data.get('description', '')}\n\n"
        f"🔗 Ссылка: {card_data.get('link', '')}\n"
        f"📊 Группы: {', '.join(card_data.get('groups', []))}"
    )
    
    keyboard = get_admin_card_preview_keyboard()
    
    # Отправляем с медиа
    media_type = card_data.get('media_type')
    media_file_id = card_data.get('media_file_id')
    
    try:
        if media_type == 'photo':
            await update.message.reply_photo(
                photo=media_file_id,
                caption=preview_text,
                reply_markup=keyboard
            )
        elif media_type == 'video':
            await update.message.reply_video(
                video=media_file_id,
                caption=preview_text,
                reply_markup=keyboard
            )
        elif media_type == 'document':
            await update.message.reply_document(
                document=media_file_id,
                caption=preview_text,
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error sending preview: {e}")
        await update.message.reply_text(
            preview_text,
            reply_markup=keyboard
        )


async def publish_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Publish the card to database"""
    query = update.callback_query
    await query.answer()
    
    card_data = context.user_data.get('new_card', {})
    
    session = get_session()
    try:
        # Генерируем уникальный номер
        card_number = generate_unique_card_number()
        
        # Создаем карточку
        card = Card(
            card_number=card_number,
            groups=card_data.get('groups', ['A']),
            district=card_data.get('district'),
            category=card_data.get('category'),
            hashtags=card_data.get('hashtags', []),
            description=card_data.get('description'),
            original_link=card_data.get('link'),
            media_type=card_data.get('media_type'),
            media_file_id=card_data.get('media_file_id')
        )
        
        # Для группы F устанавливаем expires_at
        if 'F' in card_data.get('groups', []):
            card.expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session.add(card)
        session.commit()
        
        await query.edit_message_caption(
            caption=f"✅ Карточка #{card_number} опубликована!\n\n"
                   f"Группы: {', '.join(card.groups)}\n"
                   f"Район: {card.district}\n"
                   f"Категория: {card.category}"
        )
        
        # Очищаем контекст
        context.user_data.pop('new_card', None)
        
    except Exception as e:
        logger.error(f"Error publishing card: {e}")
        await query.edit_message_caption(
            caption=f"❌ Ошибка при публикации: {str(e)}"
        )
        session.rollback()
    finally:
        session.close()


async def delete_card_draft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete card draft"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.pop('new_card', None)
    
    await query.edit_message_caption(
        caption="🗑️ Черновик удален"
    )


# ============== ПРОСТЫЕ АДМИН КОМАНДЫ ==============

async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove card by number"""
    if not is_admin(update.effective_user.id):
        return
    
    try:
        card_number = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Использование: /remove <номер карточки>")
        return
    
    session = get_session()
    try:
        card = session.query(Card).filter_by(card_number=card_number).first()
        if card:
            session.delete(card)
            session.commit()
            await update.message.reply_text(f"✅ Карточка #{card_number} удалена")
        else:
            await update.message.reply_text(f"❌ Карточка #{card_number} не найдена")
    finally:
        session.close()


async def cardstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show card statistics"""
    if not is_admin(update.effective_user.id):
        return
    
    try:
        card_number = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Использование: /cardstats <номер>")
        return
    
    session = get_session()
    try:
        card = session.query(Card).filter_by(card_number=card_number).first()
        if not card:
            await update.message.reply_text(f"❌ Карточка #{card_number} не найдена")
            return
        
        # Считаем средний рейтинг
        from sqlalchemy import func
        from database.models import Rating
        
        avg_rating = session.query(func.avg(Rating.rating)).filter_by(card_id=card.id).scalar()
        rating_count = session.query(func.count(Rating.id)).filter_by(card_id=card.id).scalar()
        
        stats_text = (
            f"📊 Статистика карточки #{card_number}\n\n"
            f"🔥 Район: {card.district or 'Не указан'}\n"
            f"🪽 Категория: {card.category or 'Не указана'}\n"
            f"📊 Группы: {', '.join(card.groups)}\n"
            f"👁 Просмотры: {card.views_count}\n"
            f"🖱 Переходы: {card.clicks_count}\n"
            f"♥️ Сохранения: {card.saves_count}\n"
            f"⭐️ Рейтинг: {avg_rating:.1f}/10 ({rating_count} оценок)\n"
            f"📅 Создана: {card.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        if card.expires_at:
            stats_text += f"\n⏰ Удалится: {card.expires_at.strftime('%d.%m.%Y %H:%M')}"
        
        await update.message.reply_text(stats_text)
        
    finally:
        session.close()
