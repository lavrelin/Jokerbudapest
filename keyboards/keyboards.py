"""
Клавиатуры для Telegram бота
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ============== КЛАВИАТУРЫ КАРТОЧЕК ==============

def get_card_keyboard(card, current_index, total_cards):
    """
    Клавиатура для карточки
    
    [👍 Перейти]  [⭐️ Оценить]
    [◀️ Назад] [1/5] [Вперед ▶️]
    [🪞 Обновить]
    """
    buttons = []
    
    # Первый ряд: Перейти и Оценить
    row1 = [
        InlineKeyboardButton("👍 Перейти", url=card.original_link),
        InlineKeyboardButton("⭐️ Оценить", callback_data=f"rate_{card.id}")
    ]
    buttons.append(row1)
    
    # Второй ряд: Навигация
    row2 = []
    if current_index > 0:
        row2.append(InlineKeyboardButton("◀️ Назад", callback_data="nav_prev"))
    row2.append(InlineKeyboardButton(f"{current_index + 1}/{total_cards}", callback_data="nav_info"))
    if current_index < total_cards - 1:
        row2.append(InlineKeyboardButton("Вперед ▶️", callback_data="nav_next"))
    buttons.append(row2)
    
    # Третий ряд: Обновить
    row3 = [InlineKeyboardButton("🪞 Обновить", callback_data="nav_refresh")]
    buttons.append(row3)
    
    return InlineKeyboardMarkup(buttons)


def get_rating_keyboard(card_id):
    """
    Клавиатура выбора рейтинга 1-10
    
    [1] [2] [3] [4] [5]
    [6] [7] [8] [9] [10]
    [⬅️ Назад]
    """
    buttons = []
    
    # Первый ряд: 1-5
    row1 = [
        InlineKeyboardButton(str(i), callback_data=f"rating_{card_id}_{i}")
        for i in range(1, 6)
    ]
    buttons.append(row1)
    
    # Второй ряд: 6-10
    row2 = [
        InlineKeyboardButton(str(i), callback_data=f"rating_{card_id}_{i}")
        for i in range(6, 11)
    ]
    buttons.append(row2)
    
    # Третий ряд: Назад
    row3 = [InlineKeyboardButton("⬅️ Назад", callback_data=f"back_to_card_{card_id}")]
    buttons.append(row3)
    
    return InlineKeyboardMarkup(buttons)


# ============== АДМИНСКИЕ КЛАВИАТУРЫ ==============

def get_admin_card_preview_keyboard():
    """
    Клавиатура предпросмотра карточки для админа
    
    [✅ Опубликовать]
    [🗑️ Удалить]
    """
    buttons = [
        [InlineKeyboardButton("✅ Опубликовать", callback_data="admin_publish")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data="admin_delete")]
    ]
    return InlineKeyboardMarkup(buttons)


# ============== КЛАВИАТУРА СТАРТА ==============

def get_start_keyboard():
    """
    Клавиатура для команды /start
    
    [🃏 Показать карточки]
    [🔍 Поиск]
    [📝 Отправить заявку]
    """
    buttons = [
        [InlineKeyboardButton("🃏 Показать карточки", callback_data="show_cards")],
        [InlineKeyboardButton("🔍 Поиск", callback_data="start_search")],
        [InlineKeyboardButton("📝 Отправить заявку", callback_data="text_form")]
    ]
    return InlineKeyboardMarkup(buttons)


# ============== ФОРМА ЗАЯВКИ ==============

def get_text_form_keyboard():
    """
    Клавиатура выбора типа заявки
    
    [📋 Заявка в каталог]
    [📝 Предложение публикации]
    [👤 Связь с администратором]
    [⬅️ Назад]
    """
    buttons = [
        [InlineKeyboardButton("📋 Заявка в каталог", callback_data="form_catalog")],
        [InlineKeyboardButton("📝 Предложение публикации", callback_data="form_post")],
        [InlineKeyboardButton("👤 Связь с администратором", callback_data="form_admin")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_form_preview_keyboard():
    """
    Клавиатура предпросмотра заявки
    
    [✅ Отправить]
    [🗑️ Отменить]
    """
    buttons = [
        [InlineKeyboardButton("✅ Отправить", callback_data="form_submit")],
        [InlineKeyboardButton("🗑️ Отменить", callback_data="form_cancel")]
    ]
    return InlineKeyboardMarkup(buttons)
