from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Float, BigInteger, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    current_card_set = Column(Integer, default=0)  # Which set of cards to show (0-4)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    viewed_cards = relationship('ViewedCard', back_populates='user', cascade='all, delete-orphan')
    ratings = relationship('Rating', back_populates='user', cascade='all, delete-orphan')
    saved_cards = relationship('SavedCard', back_populates='user', cascade='all, delete-orphan')
    district_subscriptions = relationship('DistrictSubscription', back_populates='user', cascade='all, delete-orphan')
    category_subscriptions = relationship('CategorySubscription', back_populates='user', cascade='all, delete-orphan')
    cooldowns = relationship('Cooldown', back_populates='user', cascade='all, delete-orphan')


class Card(Base):
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_number = Column(Integer, unique=True, nullable=False)  # Random 1-9999
    groups = Column(JSON, nullable=False)  # List of groups ['A', 'B', 'D']
    
    # NEW: Район вместо адреса
    district = Column(String(255), nullable=True)  # 🔥 Район
    
    # NEW: Свободное слово-категория (одна)
    category = Column(String(255), nullable=True)  # 🪽 Категория
    
    hashtags = Column(JSON, nullable=True)  # Хештеги
    name = Column(String(500), nullable=True)  # Имя/название
    description = Column(Text, nullable=True)
    original_link = Column(String(1000), nullable=False)  # Ссылка на пост
    
    # Media
    media_type = Column(String(50), nullable=True)  # photo, video, document
    media_file_id = Column(String(500), nullable=True)
    
    # Statistics
    views_count = Column(Integer, default=0)
    clicks_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)  # NEW: Сколько раз сохранили
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For group F (24h)
    
    # Relationships
    viewed_by = relationship('ViewedCard', back_populates='card', cascade='all, delete-orphan')
    ratings = relationship('Rating', back_populates='card', cascade='all, delete-orphan')
    saved_by = relationship('SavedCard', back_populates='card', cascade='all, delete-orphan')


class ViewedCard(Base):
    __tablename__ = 'viewed_cards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='viewed_cards')
    card = relationship('Card', back_populates='viewed_by')


class Rating(Base):
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, nullable=False)  # NEW: 1-10 (было 1-5)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='ratings')
    card = relationship('Card', back_populates='ratings')


class SavedCard(Base):
    """NEW: Сохраненные карточки пользователя"""
    __tablename__ = 'saved_cards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='saved_cards')
    card = relationship('Card', back_populates='saved_by')


class DistrictSubscription(Base):
    """NEW: Подписки на районы"""
    __tablename__ = 'district_subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    district = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='district_subscriptions')


class CategorySubscription(Base):
    """Подписки на категории (свободные слова)"""
    __tablename__ = 'category_subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    category = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='category_subscriptions')


class Cooldown(Base):
    __tablename__ = 'cooldowns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    cooldown_type = Column(String(50), nullable=False)  # 'text_form', 'rating'
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='cooldowns')
