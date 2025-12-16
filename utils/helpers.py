import random
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import func, and_, or_
from database.models import Card, User, ViewedCard, Rating, Review, Cooldown, CardOwner
from database.database import get_session
import config


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


def get_or_create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
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


def get_cards_for_user(user_id: int, limit: int = 5) -> List[Card]:
    """Get random cards for user based on their card set"""
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get groups for current user's set
        card_set_groups = config.CARD_SETS[user.current_card_set]
        
        # Get viewed card IDs
        viewed_card_ids = session.query(ViewedCard.card_id).filter(
            ViewedCard.user_id == user_id
        ).all()
        viewed_ids = [v[0] for v in viewed_card_ids]
        
        # Query cards from user's groups that haven't been viewed
        cards = session.query(Card).filter(
            Card.id.notin_(viewed_ids) if viewed_ids else True
        ).all()
        
        # Filter cards by groups (card must have at least one group from card_set_groups)
        filtered_cards = []
        for card in cards:
            card_groups = card.groups if isinstance(card.groups, list) else []
            if any(group in card_set_groups for group in card_groups):
                filtered_cards.append(card)
        
        # If no unviewed cards, reset viewed cards for this user
        if not filtered_cards:
            session.query(ViewedCard).filter(ViewedCard.user_id == user_id).delete()
            session.commit()
            
            # Get all cards again
            cards = session.query(Card).all()
            filtered_cards = []
            for card in cards:
                card_groups = card.groups if isinstance(card.groups, list) else []
                if any(group in card_set_groups for group in card_groups):
                    filtered_cards.append(card)
        
        # Randomly select cards
        if len(filtered_cards) > limit:
            selected_cards = random.sample(filtered_cards, limit)
        else:
            selected_cards = filtered_cards
        
        return selected_cards
    finally:
        session.close()


def mark_card_as_viewed(user_id: int, card_id: int):
    """Mark card as viewed by user"""
    session = get_session()
    try:
        # Check if already viewed
        viewed = session.query(ViewedCard).filter(
            and_(ViewedCard.user_id == user_id, ViewedCard.card_id == card_id)
        ).first()
        
        if not viewed:
            viewed = ViewedCard(user_id=user_id, card_id=card_id)
            session.add(viewed)
            
            # Increment card views
            card = session.query(Card).filter(Card.id == card_id).first()
            if card:
                card.total_views += 1
                
                # Check if this is unique view
                total_views_by_user = session.query(ViewedCard).filter(
                    and_(ViewedCard.user_id == user_id, ViewedCard.card_id == card_id)
                ).count()
                if total_views_by_user == 1:
                    card.unique_views += 1
            
            session.commit()
    finally:
        session.close()


def get_card_rating(card_id: int) -> tuple:
    """Get average rating and count for card"""
    session = get_session()
    try:
        ratings = session.query(func.avg(Rating.rating), func.count(Rating.id)).filter(
            Rating.card_id == card_id
        ).first()
        
        avg_rating = round(ratings[0], 1) if ratings[0] else 0.0
        count = ratings[1] if ratings[1] else 0
        
        return avg_rating, count
    finally:
        session.close()


def get_card_reviews_count(card_id: int) -> int:
    """Get review count for card"""
    session = get_session()
    try:
        count = session.query(Review).filter(Review.card_id == card_id).count()
        return count
    finally:
        session.close()


def check_cooldown(user_id: int, cooldown_type: str) -> Optional[datetime]:
    """Check if user has active cooldown. Returns expiry time if active, None otherwise"""
    session = get_session()
    try:
        cooldown = session.query(Cooldown).filter(
            and_(
                Cooldown.user_id == user_id,
                Cooldown.cooldown_type == cooldown_type,
                Cooldown.expires_at > datetime.utcnow()
            )
        ).first()
        
        return cooldown.expires_at if cooldown else None
    finally:
        session.close()


def set_cooldown(user_id: int, cooldown_type: str, duration_seconds: int):
    """Set cooldown for user"""
    session = get_session()
    try:
        # Remove existing cooldown
        session.query(Cooldown).filter(
            and_(Cooldown.user_id == user_id, Cooldown.cooldown_type == cooldown_type)
        ).delete()
        
        # Create new cooldown
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


def remove_cooldown(user_id: int, cooldown_type: str = None):
    """Remove cooldown for user"""
    session = get_session()
    try:
        query = session.query(Cooldown).filter(Cooldown.user_id == user_id)
        if cooldown_type:
            query = query.filter(Cooldown.cooldown_type == cooldown_type)
        query.delete()
        session.commit()
    finally:
        session.close()


def is_card_owner(user_id: int, card_id: int) -> bool:
    """Check if user owns the card"""
    session = get_session()
    try:
        owner = session.query(CardOwner).filter(
            and_(CardOwner.user_id == user_id, CardOwner.card_id == card_id)
        ).first()
        return owner is not None
    finally:
        session.close()


def format_card_text(card: Card) -> str:
    """Format card information as text"""
    avg_rating, rating_count = get_card_rating(card.id)
    review_count = get_card_reviews_count(card.id)
    
    text = f"🃏 Номер карточки: {card.card_number}\n\n"
    
    if card.categories:
        categories = ', '.join(card.categories) if isinstance(card.categories, list) else card.categories
        text += f"📂 Категория: {categories}\n"
    
    if card.name:
        text += f"👤 {card.name}\n"
    
    if card.address:
        text += f"📍 {card.address}\n"
    
    if card.hashtags:
        hashtags = ' '.join([f"#{tag}" for tag in card.hashtags]) if isinstance(card.hashtags, list) else card.hashtags
        text += f"\n{hashtags}\n"
    
    text += f"\n⭐️ Рейтинг: {avg_rating} ({rating_count})\n"
    text += f"💬 Отзывы: {review_count}\n"
    
    if card.description:
        text += f"\n{card.description}\n"
    
    return text


def search_cards(query: str, user_id: int = None) -> List[Card]:
    """Search cards by keywords"""
    session = get_session()
    try:
        query_lower = query.lower()
        
        # Search in description, categories, hashtags
        cards = session.query(Card).all()
        
        matching_cards = []
        for card in cards:
            # Search in description
            if card.description and query_lower in card.description.lower():
                matching_cards.append(card)
                continue
            
            # Search in categories
            if card.categories:
                categories = card.categories if isinstance(card.categories, list) else []
                if any(query_lower in cat.lower() for cat in categories):
                    matching_cards.append(card)
                    continue
            
            # Search in hashtags
            if card.hashtags:
                hashtags = card.hashtags if isinstance(card.hashtags, list) else []
                if any(query_lower in tag.lower() for tag in hashtags):
                    matching_cards.append(card)
                    continue
            
            # Search in name
            if card.name and query_lower in card.name.lower():
                matching_cards.append(card)
                continue
            
            # Search in address
            if card.address and query_lower in card.address.lower():
                matching_cards.append(card)
                continue
        
        return matching_cards
    finally:
        session.close()


def delete_expired_f_cards():
    """Delete cards from group F that have expired (24 hours)"""
    session = get_session()
    try:
        expired_cards = session.query(Card).filter(
            and_(
                Card.delete_at.isnot(None),
                Card.delete_at <= datetime.utcnow()
            )
        ).all()
        
        for card in expired_cards:
            session.delete(card)
        
        session.commit()
        return len(expired_cards)
    finally:
        session.close()
