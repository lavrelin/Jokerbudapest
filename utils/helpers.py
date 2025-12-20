"""
Вспомогательные функции для бота
"""
import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import func, and_
from database.models import Card, User, ViewedCard, Rating, Cooldown
from database.database import get_session
import config


# ============== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==============

def generate_unique_card_number() -> int:
    """Generate unique random card number between 1-9999"""
    session = get_session()
    try:
        while True:
            number = random.randint(1, 9999)
            existing = session.query(Card).filter(Card.card_number == number).first()
            if not existing:
                return number
    finally:
        session.close()


def get_or_create_user(user_id: int, username: str = None, 
                       first_name: str = None, last_name: str = None) -> User:
    """Get existing user or create new one"""
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=user_id in config.ADMIN_IDS
            )
            session.add(user)
            session.commit()
        else:
            # Update user info
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_activity = datetime.utcnow()
            session.commit()
        return user
    finally:
        session.close()


# ============== РАБОТА С КАРТОЧКАМИ ==============

def get_cards_for_user(user_id: int, limit: int = 5) -> List[Card]:
    """
    Get random cards for user based on their card set
    Returns cards user hasn't viewed yet
    """
    session = get_session()
    try:
        # Get user
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get user's card set (which groups to show)
        card_set_index = user.current_card_set
        if card_set_index < 0 or card_set_index >= len(config.CARD_SETS):
            card_set_index = 0
        
        allowed_groups = config.CARD_SETS[card_set_index]
        
        # Get cards user has already viewed
        viewed_card_ids = session.query(ViewedCard.card_id).filter(
            ViewedCard.user_id == user_id
        ).all()
        viewed_ids = [v[0] for v in viewed_card_ids]
        
        # Get random cards from allowed groups that user hasn't viewed
        query = session.query(Card).filter(
            and_(
                Card.groups.op('@>')(allowed_groups),  # Card belongs to allowed groups
                Card.id.notin_(viewed_ids) if viewed_ids else True
            )
        )
        
        # If no unviewed cards, reset viewed cards for this user
        if query.count() == 0:
            session.query(ViewedCard).filter(ViewedCard.user_id == user_id).delete()
            session.commit()
            
            # Try again
            query = session.query(Card).filter(
                Card.groups.op('@>')(allowed_groups)
            )
        
        # Get random cards
        all_cards = query.all()
        if not all_cards:
            return []
        
        # Shuffle and limit
        random.shuffle(all_cards)
        return all_cards[:limit]
        
    finally:
        session.close()


def mark_card_as_viewed(user_id: int, card_id: int):
    """Mark card as viewed by user"""
    session = get_session()
    try:
        # Check if already viewed
        existing = session.query(ViewedCard).filter(
            and_(
                ViewedCard.user_id == user_id,
                ViewedCard.card_id == card_id
            )
        ).first()
        
        if not existing:
            viewed = ViewedCard(user_id=user_id, card_id=card_id)
            session.add(viewed)
            
            # Increment view counter
            card = session.query(Card).filter(Card.id == card_id).first()
            if card:
                card.views_count += 1
            
            session.commit()
    finally:
        session.close()


def increment_card_clicks(card_id: int):
    """Increment card click counter"""
    session = get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if card:
            card.clicks_count += 1
            session.commit()
    finally:
        session.close()


# ============== ФОРМАТИРОВАНИЕ КАРТОЧЕК ==============

def format_card_text(card: Card) -> str:
    """
    Format card text for display
    
    НОВЫЙ ФОРМАТ:
    🃏 Id: 1234
    🔥 Район: Будапешт 5
    🪽 Категория: Барбер
    #тату #будапешт #недорого
    ⭐️ Рейтинг: 8.5/10 (42 оценки)
    
    Описание...
    """
    # Получаем рейтинг
    avg_rating, rating_count = get_card_rating(card.id)
    
    # Формируем хештеги
    hashtags_text = ""
    if card.hashtags:
        hashtags_text = " ".join([f"#{tag}" for tag in card.hashtags])
    
    # Формируем текст
    text = f"🃏 Id: {card.card_number}\n"
    text += f"🔥 Район: {card.district or 'Не указан'}\n"
    text += f"🪽 {card.category or 'Без категории'}\n"
    
    if hashtags_text:
        text += f"{hashtags_text}\n"
    
    # Рейтинг
    if rating_count > 0:
        text += f"⭐️ Рейтинг: {avg_rating:.1f}/10 ({rating_count} оценок)\n"
    else:
        text += f"⭐️ Рейтинг: Нет оценок\n"
    
    # Описание
    if card.description:
        text += f"\n{card.description}"
    
    return text


# ============== РАБОТА С РЕЙТИНГОМ ==============

def get_card_rating(card_id: int) -> Tuple[float, int]:
    """
    Get average rating and count for card
    Returns: (average_rating, count)
    """
    session = get_session()
    try:
        result = session.query(
            func.avg(Rating.rating),
            func.count(Rating.id)
        ).filter(Rating.card_id == card_id).first()
        
        avg = result[0] if result[0] else 0.0
        count = result[1] if result[1] else 0
        
        return (float(avg), int(count))
    finally:
        session.close()


def add_or_update_rating(user_id: int, card_id: int, rating: int):
    """Add or update user's rating for card"""
    if rating < 1 or rating > 10:
        raise ValueError("Rating must be between 1 and 10")
    
    session = get_session()
    try:
        # Check if user already rated this card
        existing = session.query(Rating).filter(
            and_(
                Rating.user_id == user_id,
                Rating.card_id == card_id
            )
        ).first()
        
        if existing:
            existing.rating = rating
            existing.created_at = datetime.utcnow()
        else:
            new_rating = Rating(
                user_id=user_id,
                card_id=card_id,
                rating=rating
            )
            session.add(new_rating)
        
        session.commit()
    finally:
        session.close()


# ============== КУЛДАУНЫ ==============

def set_cooldown(user_id: int, cooldown_type: str, duration_seconds: int):
    """Set cooldown for user"""
    session = get_session()
    try:
        expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        cooldown = Cooldown(
            user_id=user_id,
            cooldown_type=cooldown_type,
            expires_at=expires_at
        )
        session.add(cooldown)
        session.commit()
    finally:
        session.close()


def check_cooldown(user_id: int, cooldown_type: str) -> Optional[datetime]:
    """
    Check if user has active cooldown
    Returns: expires_at datetime if cooldown active, None otherwise
    """
    session = get_session()
    try:
        cooldown = session.query(Cooldown).filter(
            and_(
                Cooldown.user_id == user_id,
                Cooldown.cooldown_type == cooldown_type,
                Cooldown.expires_at > datetime.utcnow()
            )
        ).first()
        
        if cooldown:
            return cooldown.expires_at
        return None
    finally:
        session.close()


def remove_cooldown(user_id: int, cooldown_type: str = None):
    """Remove cooldown(s) for user"""
    session = get_session()
    try:
        query = session.query(Cooldown).filter(Cooldown.user_id == user_id)
        
        if cooldown_type:
            query = query.filter(Cooldown.cooldown_type == cooldown_type)
        
        query.delete()
        session.commit()
    finally:
        session.close()


# ============== УДАЛЕНИЕ УСТАРЕВШИХ КАРТОЧЕК ==============

def delete_expired_f_cards() -> int:
    """
    Delete cards from group F that have expired
    Returns: number of deleted cards
    """
    session = get_session()
    try:
        now = datetime.utcnow()
        
        expired_cards = session.query(Card).filter(
            and_(
                Card.expires_at.isnot(None),
                Card.expires_at <= now
            )
        ).all()
        
        count = len(expired_cards)
        
        for card in expired_cards:
            session.delete(card)
        
        session.commit()
        return count
    finally:
        session.close()


# ============== ПОИСК ==============

def search_cards(query: str, limit: int = 10) -> List[Card]:
    """
    Search cards by district, category, or hashtags
    """
    session = get_session()
    try:
        query = query.lower().strip()
        
        # Search in district, category, and hashtags
        cards = session.query(Card).filter(
            or_(
                Card.district.ilike(f"%{query}%"),
                Card.category.ilike(f"%{query}%"),
                Card.hashtags.op('@>')(f'["{query}"]')  # JSON search
            )
        ).limit(limit).all()
        
        return cards
    finally:
        session.close()
