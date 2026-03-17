"""
API routes for episode management and streaming.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
import config

from database import get_db
from database.models import Episode, Series, Subtitle
from api.schemas import (
    EpisodeCreate, EpisodeUpdate, EpisodeResponse,
    EpisodeWithSubtitles, StreamingURLResponse, SubtitleCreate, SubtitleResponse
)

router = APIRouter(prefix="/episodes", tags=["Episodes"])


@router.get("/{episode_id}", response_model=EpisodeWithSubtitles)
def get_episode(episode_id: int, db: Session = Depends(get_db)):
    """Get episode details with subtitles."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found"
        )

    return episode


@router.post("/", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
def create_episode(episode_data: EpisodeCreate, db: Session = Depends(get_db)):
    """Create a new episode."""
    # Verify series exists
    series = db.query(Series).filter(Series.id == episode_data.series_id).first()
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id {episode_data.series_id} not found"
        )

    # Check for duplicate episode
    existing = db.query(Episode).filter(
        Episode.series_id == episode_data.series_id,
        Episode.season_number == episode_data.season_number,
        Episode.episode_number == episode_data.episode_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Episode S{episode_data.season_number}E{episode_data.episode_number} already exists"
        )

    episode = Episode(**episode_data.model_dump())
    db.add(episode)

    # Update series total episodes
    series.total_episodes = db.query(Episode).filter(Episode.series_id == series.id).count() + 1

    db.commit()
    db.refresh(episode)

    return episode


@router.put("/{episode_id}", response_model=EpisodeResponse)
def update_episode(
    episode_id: int,
    episode_data: EpisodeUpdate,
    db: Session = Depends(get_db)
):
    """Update episode metadata."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found"
        )

    for field, value in episode_data.model_dump(exclude_unset=True).items():
        setattr(episode, field, value)

    db.commit()
    db.refresh(episode)

    return episode


@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_episode(episode_id: int, db: Session = Depends(get_db)):
    """Delete an episode."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found"
        )

    series_id = episode.series_id
    db.delete(episode)

    # Update series total episodes
    series = db.query(Series).filter(Series.id == series_id).first()
    if series:
        series.total_episodes = db.query(Episode).filter(Episode.series_id == series_id).count()

    db.commit()

    return None


@router.get("/{episode_id}/stream", response_model=StreamingURLResponse)
def get_streaming_url(episode_id: int, db: Session = Depends(get_db)):
    """Get the streaming URL for an episode."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found"
        )

    if episode.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Episode is not ready for streaming. Current status: {episode.status}"
        )

    if not episode.master_playlist_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master playlist not found for this episode"
        )

    # Construct streaming URL
    # Format: /hls/{video_file_id}/master.m3u8
    streaming_url = f"/hls/{episode.video_file_id}/master.m3u8"

    return {
        "master_playlist_url": streaming_url,
        "episode": episode
    }


@router.post("/{episode_id}/subtitles", response_model=SubtitleResponse, status_code=status.HTTP_201_CREATED)
def add_subtitle(
    episode_id: int,
    subtitle_data: SubtitleCreate,
    db: Session = Depends(get_db)
):
    """Add a subtitle track to an episode."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found"
        )

    # Ensure episode_id matches
    if subtitle_data.episode_id != episode_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="episode_id in URL and body must match"
        )

    subtitle = Subtitle(**subtitle_data.model_dump())
    db.add(subtitle)
    db.commit()
    db.refresh(subtitle)

    return subtitle


@router.get("/{episode_id}/subtitles", response_model=List[SubtitleResponse])
def get_episode_subtitles(episode_id: int, db: Session = Depends(get_db)):
    """Get all subtitles for an episode."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()

    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found"
        )

    subtitles = db.query(Subtitle).filter(Subtitle.episode_id == episode_id).all()

    return subtitles


@router.delete("/subtitles/{subtitle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subtitle(subtitle_id: int, db: Session = Depends(get_db)):
    """Delete a subtitle track."""
    subtitle = db.query(Subtitle).filter(Subtitle.id == subtitle_id).first()

    if not subtitle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subtitle with id {subtitle_id} not found"
        )

    db.delete(subtitle)
    db.commit()

    return None
