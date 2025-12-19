import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', '-4843909295'))
MODERATION_GROUP_ID = int(os.getenv('MODERATION_GROUP_ID', '-1002734837434'))

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# Card groups
CARD_GROUPS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

# Card sets for users (which groups to show)
CARD_SETS = [
    ['A'],                      # Set 1: Only A
    ['A', 'B'],                 # Set 2: A and B
    ['A', 'C'],                 # Set 3: A and C
    ['A', 'B', 'D', 'E'],       # Set 4: A, B, D, E
    ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']  # Set 5: All groups
]

# Categories
CATEGORIES = {
    '💇‍♀️ Красота и уход': [
        'Барбер', 'БьютиПроцедуры', 'Волосы', 'Косметолог', 
        'Депиляция', 'Эпиляция', 'Маникюр', 'Ресницы и брови', 'Тату'
    ],
    '🩺 Здоровье и тело': [
        'Ветеринар', 'Врач', 'Массажист', 'Психолог', 'Стоматолог', 'Спорт'
    ],
    '🛠️ Услуги и помощь': [
        'Автомеханик', 'Грузчик', 'Клининг', 'Мастер по дому', 
        'Перевозчик', 'Ремонт техники', 'Няня', 'Юрист', 'Риелтор'
    ],
    '📚 Обучение и развитие': [
        'Каналы по изучению венгерского', 'Каналы по изучению английского', 
        'Курсы', 'Переводчик', 'Репетитор', 'Музыка'
    ],
    '🎭 Досуг и впечатления': [
        'Еда', 'Фотограф', 'Экскурсии', 'Для детей', 'Ремонт', 'Швея', 'Цветы'
    ]
}

# Cooldowns (in seconds)
COOLDOWN_TEXT_COMMAND = 8 * 3600  # 8 hours
COOLDOWN_REVIEW = 6 * 3600  # 6 hours
COOLDOWN_MY_CARD_REQUEST = 12 * 3600  # 12 hours

# Card deletion time for group F
GROUP_F_DELETE_TIME = 24 * 3600  # 24 hours

# Cards per page
CARDS_PER_PAGE = 5

# Rating
MIN_RATING = 1
MAX_RATING = 5
