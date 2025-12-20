"""
Парсинг медиа из Telegram ссылки
"""
import re
import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def parse_telegram_link(bot: Bot, link: str):
    """
    Парсит Telegram ссылку и извлекает медиа
    
    Поддерживаемые форматы:
    - https://t.me/channel/123
    - https://t.me/c/123456789/123
    - @channel/123
    
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
            result['error'] = "Неверный формат ссылки"
            return result
        
        logger.info(f"Parsing link: chat_id={chat_id}, message_id={message_id}")
        
        # Пытаемся получить сообщение
        try:
            # Для публичных каналов используем username
            message = await bot.forward_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            
            # Извлекаем медиа
            if message.photo:
                result['media_type'] = 'photo'
                result['media_file_id'] = message.photo[-1].file_id  # Берем самое большое фото
            elif message.video:
                result['media_type'] = 'video'
                result['media_file_id'] = message.video.file_id
            elif message.document:
                result['media_type'] = 'document'
                result['media_file_id'] = message.document.file_id
            else:
                result['error'] = "Сообщение не содержит медиа (фото/видео/документ)"
            
            # Извлекаем caption
            if message.caption:
                result['caption'] = message.caption
            elif message.text:
                result['caption'] = message.text
                
        except TelegramError as e:
            logger.error(f"Telegram error while fetching message: {e}")
            result['error'] = f"Не удалось получить сообщение: {str(e)}"
            
    except Exception as e:
        logger.error(f"Error parsing telegram link: {e}")
        result['error'] = f"Ошибка парсинга: {str(e)}"
    
    return result


def extract_chat_and_message_id(link: str):
    """
    Извлекает chat_id и message_id из Telegram ссылки
    
    Форматы:
    - https://t.me/channelname/123
    - https://t.me/c/1234567890/123
    - t.me/channelname/123
    - @channelname/123
    
    Returns:
        tuple: (chat_id, message_id) или (None, None)
    """
    link = link.strip()
    
    # Формат: https://t.me/c/1234567890/123 (приватный канал)
    match = re.match(r'https?://t\.me/c/(\d+)/(\d+)', link)
    if match:
        chat_id = f"-100{match.group(1)}"  # Приватные каналы начинаются с -100
        message_id = int(match.group(2))
        return chat_id, message_id
    
    # Формат: https://t.me/channelname/123 или t.me/channelname/123
    match = re.match(r'(?:https?://)?t\.me/([a-zA-Z0-9_]+)/(\d+)', link)
    if match:
        chat_id = f"@{match.group(1)}"
        message_id = int(match.group(2))
        return chat_id, message_id
    
    # Формат: @channelname/123
    match = re.match(r'@([a-zA-Z0-9_]+)/(\d+)', link)
    if match:
        chat_id = f"@{match.group(1)}"
        message_id = int(match.group(2))
        return chat_id, message_id
    
    return None, None


async def get_media_from_link(bot: Bot, link: str):
    """
    Упрощенная функция для получения медиа из ссылки
    
    Args:
        bot: Telegram Bot instance
        link: Ссылка на пост
        
    Returns:
        tuple: (media_type, media_file_id) или (None, None) если ошибка
    """
    result = await parse_telegram_link(bot, link)
    
    if result['error']:
        logger.error(f"Error getting media: {result['error']}")
        return None, None
    
    return result['media_type'], result['media_file_id']
