"""
Парсинг медиа из Telegram ссылки
ВНИМАНИЕ: Для работы парсинга бот должен быть добавлен в канал!
"""
import re
import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def parse_telegram_link(bot: Bot, link: str):
    """
    Парсит Telegram ссылку и извлекает медиа
    
    ВАЖНО: Бот должен иметь доступ к каналу!
    Добавьте бота в канал как администратора.
    
    Returns:
        dict: {
            'media_type': 'photo' | 'video' | 'document' | None,
            'media_file_id': str | None,
            'caption': str | None,
            'error': str | None
        }
    """
    result = {
        'media_type': None,
        'media_file_id': None,
        'caption': None,
        'error': None
    }
    
    try:
        # Парсим ссылку
        chat_id, message_id = extract_chat_and_message_id(link)
        
        if not chat_id or not message_id:
            result['error'] = (
                "❌ Неверный формат ссылки.\n\n"
                "Правильный формат:\n"
                "https://t.me/название_канала/номер\n\n"
                "Пример: https://t.me/mychannel/123"
            )
            return result
        
        logger.info(f"Parsing link: chat_id={chat_id}, message_id={message_id}")
        
        # Пытаемся получить сообщение
        try:
            # Пробуем получить сообщение через getChatMember
            message = await bot.get_chat(chat_id)
            
            # Если канал найден, пробуем forwardMessage
            forwarded = await bot.forward_message(
                chat_id=chat_id,  
                from_chat_id=chat_id,
                message_id=message_id
            )
            
            # Извлекаем медиа
            if forwarded.photo:
                result['media_type'] = 'photo'
                result['media_file_id'] = forwarded.photo[-1].file_id
            elif forwarded.video:
                result['media_type'] = 'video'
                result['media_file_id'] = forwarded.video.file_id
            elif forwarded.document:
                result['media_type'] = 'document'
                result['media_file_id'] = forwarded.document.file_id
            else:
                result['error'] = "Сообщение не содержит медиа"
            
            # Извлекаем caption
            if forwarded.caption:
                result['caption'] = forwarded.caption
            elif forwarded.text:
                result['caption'] = forwarded.text
                
        except TelegramError as e:
            error_msg = str(e).lower()
            logger.error(f"Telegram error: {e}")
            
            # Понятное сообщение об ошибке
            result['error'] = (
                "❌ Не могу получить медиа из этой ссылки.\n\n"
                "Возможные причины:\n"
                "• Бот не добавлен в канал\n"
                "• Канал приватный\n"
                "• Сообщение удалено\n\n"
                "✅ РЕШЕНИЕ:\n"
                "Вместо ссылки отправьте медиа напрямую боту!\n"
                "(Просто перешлите сообщение с фото/видео)"
            )
            
    except Exception as e:
        logger.error(f"Error parsing link: {e}")
        result['error'] = f"Ошибка: {str(e)}"
    
    return result


def extract_chat_and_message_id(link: str):
    """
    Извлекает chat_id и message_id из Telegram ссылки
    
    Форматы:
    - https://t.me/channelname/123
    - https://t.me/c/1234567890/123
    - t.me/channelname/123
    
    Returns:
        tuple: (chat_id, message_id) или (None, None)
    """
    link = link.strip()
    
    # Формат: https://t.me/c/1234567890/123 (приватный канал)
    match = re.match(r'https?://t\.me/c/(\d+)/(\d+)', link)
    if match:
        chat_id = f"-100{match.group(1)}"
        message_id = int(match.group(2))
        return chat_id, message_id
    
    # Формат: https://t.me/channelname/123
    match = re.match(r'(?:https?://)?t\.me/([a-zA-Z0-9_]+)/(\d+)', link)
    if match:
        chat_id = f"@{match.group(1)}"
        message_id = int(match.group(2))
        return chat_id, message_id
    
    return None, None


async def get_media_from_link(bot: Bot, link: str):
    """
    Упрощенная функция для получения медиа из ссылки
    
    Returns:
        tuple: (media_type, media_file_id) или (None, None)
    """
    result = await parse_telegram_link(bot, link)
    
    if result['error']:
        logger.error(f"Error: {result['error']}")
        return None, None
    
    return result['media_type'], result['media_file_id']
