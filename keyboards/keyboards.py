from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List
from database.models import Card


def get_card_keyboard(card: Card, card_index: int = 0) -> InlineKeyboardMarkup:
    """Get inline keyboard for card"""
    keyboard = []
    
    # First row: Link button if available
    if card.original_link:
        keyboard.append([
            InlineKeyboardButton("⚡️ Перейти", url=card.original_link)
        ])
    
    # Second row: Reviews and Application
    keyboard.append([
        InlineKeyboardButton("⭐️ Отзывы", callback_data=f"rvw_{card.id}"),
        InlineKeyboardButton("🪽 Заявка в каталог", callback_data="ctlg_app")
    ])
    
    # Third row: Subscriptions
    keyboard.append([
        InlineKeyboardButton("🔔 Подписки", callback_data="my_subs")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(current_index: int, total_cards: int, card_id: int = None) -> InlineKeyboardMarkup:
    """Get pagination keyboard for cards"""
    keyboard = []
    
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"nav_prev_{current_index}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{current_index + 1}/{total_cards}", callback_data="nav_info"))
    
    if current_index < total_cards - 1:
        nav_buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"nav_next_{current_index}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Refresh button
    keyboard.append([
        InlineKeyboardButton("🔄 Обновить", callback_data="nav_refresh")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_review_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for reviews"""
    keyboard = [
        [
            InlineKeyboardButton("📝 Оставить отзыв", callback_data=f"rvw_add_{card_id}"),
            InlineKeyboardButton("⭐️ Оценить", callback_data=f"rt_show_{card_id}")
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data=f"rvw_stats_{card_id}"),
            InlineKeyboardButton("🔙 К карточке", callback_data=f"rvw_back_{card_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_rating_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for rating"""
    keyboard = [
        [
            InlineKeyboardButton("⭐️", callback_data=f"rt_vote_{card_id}_1"),
            InlineKeyboardButton("⭐️⭐️", callback_data=f"rt_vote_{card_id}_2"),
            InlineKeyboardButton("⭐️⭐️⭐️", callback_data=f"rt_vote_{card_id}_3"),
        ],
        [
            InlineKeyboardButton("⭐️⭐️⭐️⭐️", callback_data=f"rt_vote_{card_id}_4"),
            InlineKeyboardButton("⭐️⭐️⭐️⭐️⭐️", callback_data=f"rt_vote_{card_id}_5"),
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data=f"rvw_{card_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_card_preview_keyboard(temp_id: str) -> InlineKeyboardMarkup:
    """Get keyboard for admin card preview"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"adm_edit_{temp_id}"),
            InlineKeyboardButton("✅ Опубликовать", callback_data=f"adm_pub_{temp_id}"),
        ],
        [
            InlineKeyboardButton("🗑 Удалить", callback_data=f"adm_del_{temp_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_category_selection_keyboard(selected: List[str] = None) -> InlineKeyboardMarkup:
    """Get keyboard for category selection (up to 3)"""
    if selected is None:
        selected = []
    
    keyboard = []
    
    # Main category groups
    categories = {
        '💇‍♀️ Красота': ['Барбер', 'Косметолог', 'Маникюр', 'Тату'],
        '🩺 Здоровье': ['Врач', 'Массажист', 'Психолог', 'Спорт'],
        '🛠️ Услуги': ['Автомеханик', 'Клининг', 'Ремонт', 'Юрист'],
        '📚 Обучение': ['Курсы', 'Репетитор', 'Музыка'],
        '🎭 Досуг': ['Еда', 'Фотограф', 'Экскурсии']
    }
    
    for main_cat, subcats in categories.items():
        row = []
        for subcat in subcats[:2]:  # Show 2 per row
            marker = "✅" if subcat in selected else ""
            row.append(InlineKeyboardButton(
                f"{marker} {subcat}",
                callback_data=f"cat_sel_{subcat}"
            ))
        if row:
            keyboard.append(row)
    
    # Done button
    if selected:
        keyboard.append([
            InlineKeyboardButton("✅ Готово", callback_data="cat_done")
        ])
    
    return InlineKeyboardMarkup(keyboard)


def get_group_selection_keyboard(selected: List[str] = None) -> InlineKeyboardMarkup:
    """Get keyboard for group selection (1-3 groups)"""
    if selected is None:
        selected = []
    
    keyboard = []
    
    groups = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    
    # Create rows of 4 buttons each
    for i in range(0, len(groups), 4):
        row = []
        for group in groups[i:i+4]:
            marker = "✅" if group in selected else ""
            row.append(InlineKeyboardButton(
                f"{marker} {group}",
                callback_data=f"grp_sel_{group}"
            ))
        keyboard.append(row)
    
    # Done button
    if selected:
        keyboard.append([
            InlineKeyboardButton("✅ Готово", callback_data="grp_done")
        ])
    
    return InlineKeyboardMarkup(keyboard)


def get_subscriptions_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for subscriptions menu"""
    keyboard = [
        [
            InlineKeyboardButton("📂 Категории", callback_data="subs_cats"),
            InlineKeyboardButton("🃏 Карточки", callback_data="subs_cards")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="subs_back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_text_form_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for text form selection"""
    keyboard = [
        [InlineKeyboardButton("📋 Заявка в каталог", callback_data="txtf_catalog")],
        [InlineKeyboardButton("💡 Предложение публикации", callback_data="txtf_post")],
        [InlineKeyboardButton("📞 Связь с администратором", callback_data="txtf_admin")],
        [InlineKeyboardButton("⚠️ Жалоба на пользователя", callback_data="txtf_report")],
        [InlineKeyboardButton("🔍 Форма «Ищу»", callback_data="txtf_search")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_text_preview_keyboard(form_type: str) -> InlineKeyboardMarkup:
    """Get keyboard for text form preview"""
    keyboard = [
        [
            InlineKeyboardButton("📤 Отправить", callback_data=f"txtf_send_{form_type}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"txtf_edit_{form_type}")
        ],
        [
            InlineKeyboardButton("🗑 Удалить", callback_data=f"txtf_del_{form_type}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Get admin menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить карточку", callback_data="adm_menu_add"),
            InlineKeyboardButton("📊 Статистика", callback_data="adm_menu_stats")
        ],
        [
            InlineKeyboardButton("📝 Команды", callback_data="adm_menu_cmds"),
            InlineKeyboardButton("🔄 Обновить", callback_data="adm_menu_refresh")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_add_card_type_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting card type to add"""
    keyboard = [
        [
            InlineKeyboardButton("📚 Каталог (A)", callback_data="adm_add_catalog"),
            InlineKeyboardButton("📰 Пост (B)", callback_data="adm_add_post")
        ],
        [
            InlineKeyboardButton("👤 Люди (C)", callback_data="adm_add_people"),
            InlineKeyboardButton("⭐️ Приоритет (D)", callback_data="adm_add_priority")
        ],
        [
            InlineKeyboardButton("📢 Реклама (E)", callback_data="adm_add_reklama"),
            InlineKeyboardButton("⏰ 24 часа (F)", callback_data="adm_add_24")
        ],
        [
            InlineKeyboardButton("💼 Работа (G)", callback_data="adm_add_work"),
            InlineKeyboardButton("🏠 Дом (H)", callback_data="adm_add_home")
        ],
        [
            InlineKeyboardButton("🎯 Выбрать группы (Custom)", callback_data="adm_add_custom")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="adm_menu_back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
