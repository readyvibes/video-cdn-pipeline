"""
SQLAlchemy ORM models for the Anime CDN database.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Series(Base):
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    poster_url = Column(String(512))
    banner_url = Column(String(512))
    release_year = Column(Integer)
    status = Column(String(50))  # 'ongoing', 'completed', 'upcoming'
    total_episodes = Column(Integer, default=0)
    genres = Column(String(255))
    studio = Column(String(255))
    rating = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    episodes = relationship("Episode", back_populates="series", cascade="all, delete-orphan")
    watchlist_entries = relationship("Watchlist", back_populates="series", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = 'episodes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(Integer, ForeignKey('series.id', ondelete='CASCADE'), nullable=False)
    episode_number = Column(Integer, nullable=False)
    season_number = Column(Integer, default=1)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    thumbnail_url = Column(String(512))
    duration_seconds = Column(Integer)
    master_playlist_path = Column(String(512))
    video_file_id = Column(String(255))
    status = Column(String(50), default='processing')  # 'processing', 'ready', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    series = relationship("Series", back_populates="episodes")
    subtitles = relationship("Subtitle", back_populates="episode", cascade="all, delete-orphan")
    watch_history = relationship("WatchHistory", back_populates="episode", cascade="all, delete-orphan")
    analytics = relationship("VideoAnalytics", back_populates="episode", cascade="all, delete-orphan")


class Subtitle(Base):
    __tablename__ = 'subtitles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    episode_id = Column(Integer, ForeignKey('episodes.id', ondelete='CASCADE'), nullable=False)
    language_code = Column(String(10), nullable=False)
    language_name = Column(String(50), nullable=False)
    subtitle_type = Column(String(20), default='subtitle')
    file_path = Column(String(512), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    episode = relationship("Episode", back_populates="subtitles")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    subscription_tier = Column(String(50), default='free')
    subscription_expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)

    # Relationships
    watch_history = relationship("WatchHistory", back_populates="user", cascade="all, delete-orphan")
    watchlist = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("VideoAnalytics", back_populates="user")


class WatchHistory(Base):
    __tablename__ = 'watch_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    episode_id = Column(Integer, ForeignKey('episodes.id', ondelete='CASCADE'), nullable=False)
    progress_seconds = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    last_watched_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watch_history")
    episode = relationship("Episode", back_populates="watch_history")


class Watchlist(Base):
    __tablename__ = 'watchlist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    series_id = Column(Integer, ForeignKey('series.id', ondelete='CASCADE'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watchlist")
    series = relationship("Series", back_populates="watchlist_entries")


class VideoAnalytics(Base):
    __tablename__ = 'video_analytics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    episode_id = Column(Integer, ForeignKey('episodes.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    view_date = Column(DateTime, nullable=False)
    watch_duration_seconds = Column(Integer, default=0)
    quality_level = Column(String(20))
    device_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    episode = relationship("Episode", back_populates="analytics")
    user = relationship("User", back_populates="analytics")
