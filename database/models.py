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
    reviews = relationship('Review', back_populates='user', cascade='all, delete-orphan')
    category_subscriptions = relationship('CategorySubscription', back_populates='user', cascade='all, delete-orphan')
    card_subscriptions = relationship('CardSubscription', back_populates='user', cascade='all, delete-orphan')
    owned_cards = relationship('CardOwner', back_populates='user', cascade='all, delete-orphan')
    cooldowns = relationship('Cooldown', back_populates='user', cascade='all, delete-orphan')


class Card(Base):
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_number = Column(Integer, unique=True, nullable=False)  # Random 1-9999
    groups = Column(JSON, nullable=False)  # List of groups ['A', 'B', 'D']
    categories = Column(JSON, nullable=False)  # 1-3 categories
    hashtags = Column(JSON, nullable=True)  # 1-3 hashtags
    address = Column(String(500), nullable=True)
    name = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    original_link = Column(String(1000), nullable=True)
    
    # Media
    media_type = Column(String(50), nullable=True)  # photo, video, document
    media_file_id = Column(String(500), nullable=True)
    
    # Stats
    unique_views = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    link_clicks = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    delete_at = Column(DateTime, nullable=True)  # For group F cards (24 hours)
    
    # Relationships
    viewed_by = relationship('ViewedCard', back_populates='card', cascade='all, delete-orphan')
    ratings = relationship('Rating', back_populates='card', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='card', cascade='all, delete-orphan')
    subscriptions = relationship('CardSubscription', back_populates='card', cascade='all, delete-orphan')
    owners = relationship('CardOwner', back_populates='card', cascade='all, delete-orphan')


class ViewedCard(Base):
    __tablename__ = 'viewed_cards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='viewed_cards')
    card = relationship('Card', back_populates='viewed_by')


class Rating(Base):
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='ratings')
    card = relationship('Card', back_populates='ratings')


class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='reviews')
    card = relationship('Card', back_populates='reviews')


class CategorySubscription(Base):
    __tablename__ = 'category_subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='category_subscriptions')


class CardSubscription(Base):
    __tablename__ = 'card_subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='card_subscriptions')
    card = relationship('Card', back_populates='subscriptions')


class CardOwner(Base):
    __tablename__ = 'card_owners'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    verified_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='owned_cards')
    card = relationship('Card', back_populates='owners')


class Cooldown(Base):
    __tablename__ = 'cooldowns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    cooldown_type = Column(String(50), nullable=False)  # text_command, review, mycard_request
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='cooldowns')
