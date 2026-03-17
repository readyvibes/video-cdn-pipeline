"""
API routes for user watch history, watchlist, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from database.models import WatchHistory, Watchlist, Episode, Series, VideoAnalytics, User
from api.schemas import (
    WatchHistoryUpdate, WatchHistoryResponse, WatchHistoryWithEpisode,
    WatchlistAdd, WatchlistResponse, WatchlistWithSeries,
    VideoAnalyticsCreate
)
from api.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


# Watch History Routes
@router.get("/{user_id}/history", response_model=List[WatchHistoryWithEpisode])
def get_watch_history(
    user_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's watch history (requires authentication)."""
    # Ensure user can only access their own history
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's history"
        )

    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id
    ).order_by(
        WatchHistory.last_watched_at.desc()
    ).limit(limit).all()

    return history


@router.get("/{user_id}/history/{episode_id}", response_model=WatchHistoryResponse)
def get_episode_progress(
    user_id: int,
    episode_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's progress for a specific episode (requires authentication)."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's history"
        )

    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.episode_id == episode_id
    ).first()

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No watch history found for this episode"
        )

    return history


@router.post("/{user_id}/history/{episode_id}", response_model=WatchHistoryResponse)
def update_watch_progress(
    user_id: int,
    episode_id: int,
    progress_data: WatchHistoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update or create watch progress for an episode (requires authentication)."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's history"
        )

    # Verify episode exists
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found"
        )

    # Find or create watch history entry
    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.episode_id == episode_id
    ).first()

    if history:
        # Update existing
        history.progress_seconds = progress_data.progress_seconds
        history.completed = progress_data.completed
        history.last_watched_at = datetime.utcnow()
    else:
        # Create new
        history = WatchHistory(
            user_id=user_id,
            episode_id=episode_id,
            progress_seconds=progress_data.progress_seconds,
            completed=progress_data.completed
        )
        db.add(history)

    db.commit()
    db.refresh(history)

    return history


@router.delete("/{user_id}/history/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watch_history(
    user_id: int,
    episode_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove an episode from watch history (requires authentication)."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's history"
        )

    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.episode_id == episode_id
    ).first()

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch history entry not found"
        )

    db.delete(history)
    db.commit()

    return None


# Watchlist Routes
@router.get("/{user_id}/watchlist", response_model=List[WatchlistWithSeries])
def get_watchlist(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's watchlist (requires authentication)."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's watchlist"
        )

    watchlist = db.query(Watchlist).filter(
        Watchlist.user_id == user_id
    ).order_by(
        Watchlist.added_at.desc()
    ).all()

    return watchlist


@router.post("/{user_id}/watchlist", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    user_id: int,
    watchlist_data: WatchlistAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a series to user's watchlist (requires authentication)."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this user's watchlist"
        )

    # Verify series exists
    series = db.query(Series).filter(Series.id == watchlist_data.series_id).first()
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id {watchlist_data.series_id} not found"
        )

    # Check if already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.series_id == watchlist_data.series_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Series already in watchlist"
        )

    watchlist_entry = Watchlist(
        user_id=user_id,
        series_id=watchlist_data.series_id
    )
    db.add(watchlist_entry)
    db.commit()
    db.refresh(watchlist_entry)

    return watchlist_entry


@router.delete("/{user_id}/watchlist/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    user_id: int,
    series_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a series from user's watchlist (requires authentication)."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this user's watchlist"
        )

    watchlist_entry = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.series_id == series_id
    ).first()

    if not watchlist_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Series not found in watchlist"
        )

    db.delete(watchlist_entry)
    db.commit()

    return None


# Analytics Route
@router.post("/analytics", status_code=status.HTTP_201_CREATED)
def record_video_analytics(
    analytics_data: VideoAnalyticsCreate,
    db: Session = Depends(get_db)
):
    """Record video viewing analytics."""
    analytics = VideoAnalytics(
        episode_id=analytics_data.episode_id,
        user_id=analytics_data.user_id,
        view_date=datetime.utcnow(),
        watch_duration_seconds=analytics_data.watch_duration_seconds,
        quality_level=analytics_data.quality_level,
        device_type=analytics_data.device_type
    )

    db.add(analytics)
    db.commit()

    return {"status": "recorded"}
