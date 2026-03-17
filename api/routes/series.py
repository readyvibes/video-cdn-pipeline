"""
API routes for series/anime management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from database.models import Series, Episode
from api.schemas import SeriesCreate, SeriesUpdate, SeriesResponse, SeriesWithEpisodes

router = APIRouter(prefix="/series", tags=["Series"])


@router.get("/", response_model=List[SeriesResponse])
def get_all_series(
    skip: int = 0,
    limit: int = 50,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """Get all anime series with optional filtering."""
    query = db.query(Series)

    if status_filter:
        query = query.filter(Series.status == status_filter)

    series = query.offset(skip).limit(limit).all()
    return series


@router.get("/{series_id}", response_model=SeriesWithEpisodes)
def get_series(series_id: int, db: Session = Depends(get_db)):
    """Get a specific series by ID with all episodes."""
    series = db.query(Series).filter(Series.id == series_id).first()

    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id {series_id} not found"
        )

    return series


@router.get("/slug/{slug}", response_model=SeriesWithEpisodes)
def get_series_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a specific series by slug with all episodes."""
    series = db.query(Series).filter(Series.slug == slug).first()

    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with slug '{slug}' not found"
        )

    return series


@router.post("/", response_model=SeriesResponse, status_code=status.HTTP_201_CREATED)
def create_series(series_data: SeriesCreate, db: Session = Depends(get_db)):
    """Create a new anime series."""
    # Check if slug already exists
    existing = db.query(Series).filter(Series.slug == series_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Series with slug '{series_data.slug}' already exists"
        )

    series = Series(**series_data.model_dump())
    db.add(series)
    db.commit()
    db.refresh(series)

    return series


@router.put("/{series_id}", response_model=SeriesResponse)
def update_series(
    series_id: int,
    series_data: SeriesUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing series."""
    series = db.query(Series).filter(Series.id == series_id).first()

    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id {series_id} not found"
        )

    # Update only provided fields
    for field, value in series_data.model_dump(exclude_unset=True).items():
        setattr(series, field, value)

    db.commit()
    db.refresh(series)

    return series


@router.delete("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_series(series_id: int, db: Session = Depends(get_db)):
    """Delete a series and all associated episodes."""
    series = db.query(Series).filter(Series.id == series_id).first()

    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id {series_id} not found"
        )

    db.delete(series)
    db.commit()

    return None


@router.get("/{series_id}/episodes", response_model=List[SeriesResponse])
def get_series_episodes(
    series_id: int,
    season: int = None,
    db: Session = Depends(get_db)
):
    """Get all episodes for a series, optionally filtered by season."""
    series = db.query(Series).filter(Series.id == series_id).first()

    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id {series_id} not found"
        )

    query = db.query(Episode).filter(Episode.series_id == series_id)

    if season:
        query = query.filter(Episode.season_number == season)

    episodes = query.order_by(Episode.season_number, Episode.episode_number).all()

    return episodes
