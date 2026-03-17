"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Series Schemas
class SeriesBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    release_year: Optional[int] = None
    status: Optional[str] = "ongoing"
    genres: Optional[str] = None
    studio: Optional[str] = None
    rating: Optional[str] = None


class SeriesCreate(SeriesBase):
    pass


class SeriesUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    status: Optional[str] = None
    genres: Optional[str] = None
    total_episodes: Optional[int] = None


class SeriesResponse(SeriesBase):
    id: int
    total_episodes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SeriesWithEpisodes(SeriesResponse):
    episodes: List['EpisodeResponse'] = []


# Episode Schemas
class EpisodeBase(BaseModel):
    series_id: int
    episode_number: int
    season_number: int = 1
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None


class EpisodeCreate(EpisodeBase):
    video_file_id: str
    master_playlist_path: Optional[str] = None


class EpisodeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: Optional[str] = None


class EpisodeResponse(EpisodeBase):
    id: int
    master_playlist_path: Optional[str] = None
    video_file_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EpisodeWithSubtitles(EpisodeResponse):
    subtitles: List['SubtitleResponse'] = []


# Subtitle Schemas
class SubtitleCreate(BaseModel):
    episode_id: int
    language_code: str
    language_name: str
    subtitle_type: str = "subtitle"
    file_path: str
    is_default: bool = False


class SubtitleResponse(BaseModel):
    id: int
    episode_id: int
    language_code: str
    language_name: str
    subtitle_type: str
    file_path: str
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    subscription_tier: str
    subscription_expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Watch History Schemas
class WatchHistoryUpdate(BaseModel):
    progress_seconds: int
    completed: bool = False


class WatchHistoryResponse(BaseModel):
    id: int
    user_id: int
    episode_id: int
    progress_seconds: int
    completed: bool
    last_watched_at: datetime

    class Config:
        from_attributes = True


class WatchHistoryWithEpisode(WatchHistoryResponse):
    episode: EpisodeResponse


# Watchlist Schemas
class WatchlistAdd(BaseModel):
    series_id: int


class WatchlistResponse(BaseModel):
    id: int
    user_id: int
    series_id: int
    added_at: datetime

    class Config:
        from_attributes = True


class WatchlistWithSeries(WatchlistResponse):
    series: SeriesResponse


# Analytics Schemas
class VideoAnalyticsCreate(BaseModel):
    episode_id: int
    user_id: Optional[int] = None
    watch_duration_seconds: int
    quality_level: Optional[str] = None
    device_type: Optional[str] = None


class VideoAnalyticsResponse(BaseModel):
    id: int
    episode_id: int
    view_date: datetime
    watch_duration_seconds: int
    quality_level: Optional[str] = None
    device_type: Optional[str] = None

    class Config:
        from_attributes = True


# Streaming URL Response
class StreamingURLResponse(BaseModel):
    master_playlist_url: str
    episode: EpisodeWithSubtitles
