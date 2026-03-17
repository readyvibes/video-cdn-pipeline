-- Anime CDN Database Schema

-- Series/Anime table
CREATE TABLE series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,  -- URL-friendly identifier
    description TEXT,
    poster_url VARCHAR(512),  -- Main poster image
    banner_url VARCHAR(512),  -- Banner/cover image
    release_year INTEGER,
    status VARCHAR(50),  -- 'ongoing', 'completed', 'upcoming'
    total_episodes INTEGER DEFAULT 0,
    genres VARCHAR(255),  -- Comma-separated for simplicity, or use separate table
    studio VARCHAR(255),
    rating VARCHAR(10),  -- 'TV-14', 'TV-MA', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Episodes table
CREATE TABLE episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    season_number INTEGER DEFAULT 1,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    thumbnail_url VARCHAR(512),
    duration_seconds INTEGER,  -- Total video duration
    master_playlist_path VARCHAR(512),  -- Path to master.m3u8
    video_file_id VARCHAR(255),  -- Original filename or unique identifier
    status VARCHAR(50) DEFAULT 'processing',  -- 'processing', 'ready', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
    UNIQUE(series_id, season_number, episode_number)
);

-- Subtitles/Captions table
CREATE TABLE subtitles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER NOT NULL,
    language_code VARCHAR(10) NOT NULL,  -- 'en', 'ja', 'es', etc.
    language_name VARCHAR(50) NOT NULL,  -- 'English', 'Japanese', etc.
    subtitle_type VARCHAR(20) DEFAULT 'subtitle',  -- 'subtitle' or 'caption'
    file_path VARCHAR(512) NOT NULL,  -- Path to .vtt file
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE CASCADE
);

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'free',  -- 'free', 'premium', etc.
    subscription_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Watch history table
CREATE TABLE watch_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    episode_id INTEGER NOT NULL,
    progress_seconds INTEGER DEFAULT 0,  -- Last watched position
    completed BOOLEAN DEFAULT FALSE,
    last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE CASCADE,
    UNIQUE(user_id, episode_id)
);

-- User favorites/watchlist
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    series_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
    UNIQUE(user_id, series_id)
);

-- Video analytics table
CREATE TABLE video_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER NOT NULL,
    user_id INTEGER,  -- NULL for anonymous views
    view_date DATE NOT NULL,
    watch_duration_seconds INTEGER DEFAULT 0,
    quality_level VARCHAR(20),  -- '360p', '720p', '1080p'
    device_type VARCHAR(50),  -- 'web', 'mobile', 'tv', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX idx_episodes_series_id ON episodes(series_id);
CREATE INDEX idx_episodes_status ON episodes(status);
CREATE INDEX idx_subtitles_episode_id ON subtitles(episode_id);
CREATE INDEX idx_watch_history_user_id ON watch_history(user_id);
CREATE INDEX idx_watch_history_episode_id ON watch_history(episode_id);
CREATE INDEX idx_watchlist_user_id ON watchlist(user_id);
CREATE INDEX idx_video_analytics_episode_id ON video_analytics(episode_id);
CREATE INDEX idx_video_analytics_view_date ON video_analytics(view_date);
