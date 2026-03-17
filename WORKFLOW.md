# Anime CDN Workflow Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Complete Workflow: Video Upload to Playback](#complete-workflow)
4. [API Request Flows](#api-request-flows)
5. [Database Schema](#database-schema)
6. [Authentication Flow](#authentication-flow)

---

## System Overview

The Anime CDN is a complete video streaming platform that:
- Automatically processes uploaded videos into multiple quality variants (360p, 720p, 1080p)
- Stores metadata in a SQLite database
- Provides a REST API for content management and streaming
- Supports user authentication, watch history, and watchlists
- Delivers adaptive bitrate streaming via HLS (HTTP Live Streaming)

---

## Architecture Components

### 1. **Video Processing Pipeline** (`main.py`)
- Monitors `.local/raw_uploads/` directory for new `.mp4` files
- Parses filenames to extract series and episode metadata
- Creates/updates database records automatically
- Triggers FFmpeg transcoding to multiple quality variants
- Generates HLS master playlist

### 2. **REST API Server** (`api_server.py`)
- FastAPI-based REST API (port 8000)
- Manages series, episodes, users, and streaming
- Handles authentication with JWT tokens
- Serves HLS video files as static content at `/hls/*`

### 3. **Database** (SQLite)
- Stores series, episodes, subtitles, users, watch history, watchlist, and analytics
- Located at `.local/anime_cdn.db`
- Auto-initialized on startup

### 4. **Filename Parser** (`scripts/filename_parser.py`)
- Extracts metadata from video filenames
- Supported formats:
  - `series-name-s01e01.mp4` → Series: "series-name", Season 1, Episode 1
  - `series-name-S01E01.mp4` (case insensitive)
  - `series-name-1x01.mp4` (alternate format)
  - `series-name-ep01.mp4` (assumes season 1)

---

## Complete Workflow: Video Upload to Playback

### **Step 1: System Startup**

```bash
python run_all.py
```

**What happens:**
1. Database is initialized (creates tables if they don't exist)
2. API server starts on `http://localhost:8000`
3. Video pipeline starts monitoring `.local/raw_uploads/`
4. Both services share the same database

**Console Output:**
```
==================================================================
               ANIME CDN - UNIFIED STARTUP
==================================================================

Starting both services:
  1. API Server (port 8000)
  2. Video Processing Pipeline

==================================================================

[API SERVER] Starting on http://0.0.0.0:8000
[VIDEO PIPELINE] Initializing database...
  VIDEO PROCESSING PIPELINE ACTIVE
  Watching: C:\path\to\.local\raw_uploads
  Output:   C:\path\to\.local\processed
```

---

### **Step 2: Video Upload**

**User Action:** Copy a video file to `.local/raw_uploads/`

Example filename: `attack-on-titan-s01e01.mp4`

**What happens:**

1. **File Detection** (watchdog library)
   - `NewVideoHandler.on_closed()` triggered when file copy completes
   - Filename: `attack-on-titan-s01e01.mp4`

2. **Filename Parsing**
   ```python
   parsed = parse_video_filename("attack-on-titan-s01e01.mp4")
   # Returns:
   {
       'success': True,
       'series_slug': 'attack-on-titan',
       'series_title': 'Attack On Titan',
       'season_number': 1,
       'episode_number': 1
   }
   ```

3. **Database Operations**

   **a) Find or Create Series:**
   ```sql
   SELECT * FROM series WHERE slug = 'attack-on-titan';
   ```
   - If not found, creates new series:
     ```sql
     INSERT INTO series (title, slug, status, total_episodes)
     VALUES ('Attack On Titan', 'attack-on-titan', 'ongoing', 0);
     ```

   **b) Find or Create Episode:**
   ```sql
   SELECT * FROM episodes
   WHERE series_id = ? AND season_number = 1 AND episode_number = 1;
   ```
   - If not found, creates new episode:
     ```sql
     INSERT INTO episodes (
         series_id, episode_number, season_number, title,
         video_file_id, status
     ) VALUES (?, 1, 1, 'Attack On Titan - S01E01',
               'attack-on-titan-s01e01', 'processing');
     ```
   - If found, updates status to `'processing'`

4. **Video Processing** (`scripts/processor.py`)

   Target directory: `.local/processed/attack-on-titan-s01e01/`

   **a) Transcode to 360p:**
   ```bash
   ffmpeg -i input.mp4 \
     -preset fast -g 60 -sc_threshold 0 \
     -s 640x360 -b:v 800k \
     -f hls -hls_time 2 -hls_playlist_type vod \
     -hls_segment_filename .local/processed/attack-on-titan-s01e01/360p/seg_%03d.ts \
     .local/processed/attack-on-titan-s01e01/360p/index.m3u8
   ```

   **b) Transcode to 720p:**
   ```bash
   ffmpeg -i input.mp4 \
     -preset fast -g 60 -sc_threshold 0 \
     -s 1280x720 -b:v 2800k \
     -f hls -hls_time 2 -hls_playlist_type vod \
     -hls_segment_filename .local/processed/attack-on-titan-s01e01/720p/seg_%03d.ts \
     .local/processed/attack-on-titan-s01e01/720p/index.m3u8
   ```

   **c) Transcode to 1080p:**
   ```bash
   ffmpeg -i input.mp4 \
     -preset fast -g 60 -sc_threshold 0 \
     -s 1920x1080 -b:v 5000k \
     -f hls -hls_time 2 -hls_playlist_type vod \
     -hls_segment_filename .local/processed/attack-on-titan-s01e01/1080p/seg_%03d.ts \
     .local/processed/attack-on-titan-s01e01/1080p/index.m3u8
   ```

5. **Master Playlist Generation** (`scripts/playlist_gen.py`)

   Creates: `.local/processed/attack-on-titan-s01e01/master.m3u8`

   ```m3u8
   #EXTM3U
   #EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
   360p/index.m3u8
   #EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
   720p/index.m3u8
   #EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
   1080p/index.m3u8
   ```

6. **Database Update**
   ```sql
   UPDATE episodes
   SET master_playlist_path = 'attack-on-titan-s01e01/master.m3u8',
       status = 'ready'
   WHERE id = ?;
   ```

**Console Output:**
```
[NEW VIDEO] Detected: attack-on-titan-s01e01.mp4
[PARSED] Series: Attack On Titan (S01E01)
[DATABASE] Creating new series: Attack On Titan
[DATABASE] Series created with ID: 1
[DATABASE] Creating new episode entry...
[DATABASE] Episode created with ID: 1
[PROCESSING] Starting video transcode for Episode ID: 1
Starting transcoding for: attack-on-titan-s01e01...
  Transcoding 360p...
  ✓ 360p complete
  Transcoding 720p...
  ✓ 720p complete
  Transcoding 1080p...
  ✓ 1080p complete
Master playlist created: .local/processed/attack-on-titan-s01e01/master.m3u8
Successfully processed: attack-on-titan-s01e01
  Database updated for episode ID: 1
```

**File Structure:**
```
.local/processed/attack-on-titan-s01e01/
├── master.m3u8              # Master playlist (adaptive bitrate)
├── 360p/
│   ├── index.m3u8           # 360p playlist
│   ├── seg_000.ts           # Video segments
│   ├── seg_001.ts
│   └── ...
├── 720p/
│   ├── index.m3u8
│   ├── seg_000.ts
│   └── ...
└── 1080p/
    ├── index.m3u8
    ├── seg_000.ts
    └── ...
```

---

## API Request Flows

### **Flow 1: User Registration & Login**

#### **1.1 Register New User**

**Request:**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "securepassword123"
}
```

**Processing:**
1. Validate email format and uniqueness
2. Check username uniqueness
3. Hash password using bcrypt
   ```python
   password_hash = bcrypt.hash("securepassword123")
   ```
4. Insert user into database:
   ```sql
   INSERT INTO users (email, username, password_hash, subscription_tier, is_active)
   VALUES ('user@example.com', 'john_doe', '$2b$12$...', 'free', TRUE);
   ```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "subscription_tier": "free",
  "subscription_expires_at": null,
  "is_active": true,
  "created_at": "2026-03-16T12:00:00"
}
```

#### **1.2 Login**

**Request:**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Processing:**
1. Fetch user by email:
   ```sql
   SELECT * FROM users WHERE email = 'user@example.com';
   ```
2. Verify password:
   ```python
   is_valid = bcrypt.verify("securepassword123", stored_hash)
   ```
3. Generate JWT token:
   ```python
   token = jwt.encode(
       {"sub": user_id, "exp": datetime.utcnow() + timedelta(days=7)},
       SECRET_KEY,
       algorithm="HS256"
   )
   ```
4. Update last login:
   ```sql
   UPDATE users SET last_login_at = NOW() WHERE id = ?;
   ```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "john_doe",
    "subscription_tier": "free",
    "is_active": true
  }
}
```

---

### **Flow 2: Browse Anime Catalog**

#### **2.1 Get All Series**

**Request:**
```http
GET /api/series?skip=0&limit=20&status_filter=ongoing
```

**Processing:**
1. Query database:
   ```sql
   SELECT * FROM series
   WHERE status = 'ongoing'
   ORDER BY id
   LIMIT 20 OFFSET 0;
   ```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Attack On Titan",
    "slug": "attack-on-titan",
    "description": null,
    "poster_url": null,
    "banner_url": null,
    "release_year": null,
    "status": "ongoing",
    "total_episodes": 1,
    "genres": null,
    "studio": null,
    "rating": null,
    "created_at": "2026-03-16T12:00:00",
    "updated_at": "2026-03-16T12:00:00"
  }
]
```

#### **2.2 Get Series with Episodes**

**Request:**
```http
GET /api/series/1
```

**Processing:**
1. Fetch series with relationships:
   ```sql
   SELECT * FROM series WHERE id = 1;
   SELECT * FROM episodes WHERE series_id = 1 ORDER BY season_number, episode_number;
   ```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Attack On Titan",
  "slug": "attack-on-titan",
  "status": "ongoing",
  "total_episodes": 1,
  "created_at": "2026-03-16T12:00:00",
  "updated_at": "2026-03-16T12:00:00",
  "episodes": [
    {
      "id": 1,
      "series_id": 1,
      "episode_number": 1,
      "season_number": 1,
      "title": "Attack On Titan - S01E01",
      "description": null,
      "thumbnail_url": null,
      "duration_seconds": null,
      "master_playlist_path": "attack-on-titan-s01e01/master.m3u8",
      "video_file_id": "attack-on-titan-s01e01",
      "status": "ready",
      "created_at": "2026-03-16T12:00:00",
      "updated_at": "2026-03-16T12:05:00"
    }
  ]
}
```

---

### **Flow 3: Stream Episode (Authenticated)**

#### **3.1 Get Streaming URL**

**Request:**
```http
GET /api/episodes/1/stream
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Processing:**
1. Validate JWT token (extract user_id from token)
2. Fetch episode:
   ```sql
   SELECT * FROM episodes WHERE id = 1;
   ```
3. Check episode status is `'ready'`
4. Fetch subtitles:
   ```sql
   SELECT * FROM subtitles WHERE episode_id = 1;
   ```
5. Construct streaming URL: `/hls/attack-on-titan-s01e01/master.m3u8`

**Response (200 OK):**
```json
{
  "master_playlist_url": "/hls/attack-on-titan-s01e01/master.m3u8",
  "episode": {
    "id": 1,
    "series_id": 1,
    "episode_number": 1,
    "season_number": 1,
    "title": "Attack On Titan - S01E01",
    "master_playlist_path": "attack-on-titan-s01e01/master.m3u8",
    "video_file_id": "attack-on-titan-s01e01",
    "status": "ready",
    "subtitles": []
  }
}
```

#### **3.2 Video Player Requests**

**a) Fetch Master Playlist:**
```http
GET /hls/attack-on-titan-s01e01/master.m3u8
```

**Response:**
```m3u8
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
720p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p/index.m3u8
```

**b) Player selects quality (e.g., 720p):**
```http
GET /hls/attack-on-titan-s01e01/720p/index.m3u8
```

**Response:**
```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:2
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:2.0,
seg_000.ts
#EXTINF:2.0,
seg_001.ts
#EXTINF:2.0,
seg_002.ts
...
#EXT-X-ENDLIST
```

**c) Player fetches video segments:**
```http
GET /hls/attack-on-titan-s01e01/720p/seg_000.ts
GET /hls/attack-on-titan-s01e01/720p/seg_001.ts
GET /hls/attack-on-titan-s01e01/720p/seg_002.ts
...
```

Each segment is ~2 seconds of video (configured in `config.SEGMENT_TIME`)

---

### **Flow 4: Track Watch Progress**

#### **4.1 Update Watch Progress**

**Request:**
```http
POST /api/users/1/history/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "progress_seconds": 145,
  "completed": false
}
```

**Processing:**
1. Verify JWT token (user_id must match URL parameter)
2. Check authorization: current_user.id == 1
3. Verify episode exists
4. Find or create watch history:
   ```sql
   SELECT * FROM watch_history
   WHERE user_id = 1 AND episode_id = 1;
   ```
5. Update or insert:
   ```sql
   -- If exists:
   UPDATE watch_history
   SET progress_seconds = 145,
       completed = FALSE,
       last_watched_at = NOW()
   WHERE user_id = 1 AND episode_id = 1;

   -- If not exists:
   INSERT INTO watch_history (user_id, episode_id, progress_seconds, completed)
   VALUES (1, 1, 145, FALSE);
   ```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "episode_id": 1,
  "progress_seconds": 145,
  "completed": false,
  "last_watched_at": "2026-03-16T12:30:00"
}
```

#### **4.2 Get Watch History**

**Request:**
```http
GET /api/users/1/history?limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Processing:**
1. Verify authorization
2. Query watch history with episode details:
   ```sql
   SELECT wh.*, e.*
   FROM watch_history wh
   JOIN episodes e ON wh.episode_id = e.id
   WHERE wh.user_id = 1
   ORDER BY wh.last_watched_at DESC
   LIMIT 10;
   ```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "episode_id": 1,
    "progress_seconds": 145,
    "completed": false,
    "last_watched_at": "2026-03-16T12:30:00",
    "episode": {
      "id": 1,
      "series_id": 1,
      "episode_number": 1,
      "season_number": 1,
      "title": "Attack On Titan - S01E01",
      "status": "ready"
    }
  }
]
```

---

### **Flow 5: Manage Watchlist**

#### **5.1 Add Series to Watchlist**

**Request:**
```http
POST /api/users/1/watchlist
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "series_id": 1
}
```

**Processing:**
1. Verify authorization
2. Check series exists
3. Check not already in watchlist:
   ```sql
   SELECT * FROM watchlist WHERE user_id = 1 AND series_id = 1;
   ```
4. Insert:
   ```sql
   INSERT INTO watchlist (user_id, series_id, added_at)
   VALUES (1, 1, NOW());
   ```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "series_id": 1,
  "added_at": "2026-03-16T12:35:00"
}
```

#### **5.2 Get Watchlist**

**Request:**
```http
GET /api/users/1/watchlist
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Processing:**
1. Verify authorization
2. Query watchlist with series details:
   ```sql
   SELECT w.*, s.*
   FROM watchlist w
   JOIN series s ON w.series_id = s.id
   WHERE w.user_id = 1
   ORDER BY w.added_at DESC;
   ```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "series_id": 1,
    "added_at": "2026-03-16T12:35:00",
    "series": {
      "id": 1,
      "title": "Attack On Titan",
      "slug": "attack-on-titan",
      "status": "ongoing",
      "total_episodes": 1
    }
  }
]
```

---

## Database Schema

### **Entity Relationship Diagram**

```
┌─────────────┐
│   Series    │
│─────────────│
│ id (PK)     │
│ title       │
│ slug (UK)   │────┐
│ description │    │
│ status      │    │
│ ...         │    │
└─────────────┘    │
                   │ 1:N
                   │
                   ▼
             ┌─────────────┐
             │  Episodes   │
             │─────────────│
             │ id (PK)     │
             │ series_id   │────┐
             │ ep_number   │    │
             │ season_num  │    │
             │ status      │    │ 1:N
             │ playlist    │    │
             │ ...         │    ├───────┐
             └─────────────┘    │       │
                   │            │       │
                   │ 1:N        │       │
                   │            ▼       ▼
                   │      ┌──────────┐ ┌──────────────┐
                   │      │Subtitles │ │Watch_History │
                   │      │──────────│ │──────────────│
                   │      │ id (PK)  │ │ id (PK)      │
                   │      │ ep_id    │ │ user_id      │
                   │      │ language │ │ episode_id   │
                   │      │ file     │ │ progress_sec │
                   │      └──────────┘ │ completed    │
                   │                   └──────────────┘
                   │                          │
                   │ 1:N                      │ N:1
                   │                          │
                   ▼                          ▼
         ┌─────────────────┐          ┌─────────────┐
         │Video_Analytics  │          │    Users    │
         │─────────────────│          │─────────────│
         │ id (PK)         │          │ id (PK)     │
         │ episode_id      │          │ email (UK)  │
         │ user_id         │◄─────────│ username    │
         │ view_date       │   N:1    │ password    │
         │ watch_duration  │          │ sub_tier    │
         │ quality_level   │          │ ...         │
         └─────────────────┘          └─────────────┘
                                             │
                                             │ 1:N
                                             ▼
                                      ┌─────────────┐
                                      │  Watchlist  │
                                      │─────────────│
                                      │ id (PK)     │
                                      │ user_id     │
                                      │ series_id   │
                                      │ added_at    │
                                      └─────────────┘
```

---

## Authentication Flow

### **JWT Token Structure**

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": 1,  // user_id
  "exp": 1742342400  // expiration timestamp (7 days from issue)
}
```

**Signature:**
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  SECRET_KEY
)
```

### **Protected Endpoint Flow**

1. **Client sends request with token:**
   ```http
   GET /api/users/1/history
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **API extracts and validates token:**
   ```python
   # Extract token from Authorization header
   token = request.headers["Authorization"].split(" ")[1]

   # Decode and verify
   payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
   user_id = payload["sub"]

   # Fetch user from database
   user = db.query(User).filter(User.id == user_id).first()

   # Check user is active
   if not user or not user.is_active:
       raise HTTPException(401, "Unauthorized")
   ```

3. **Authorization check:**
   ```python
   # Ensure user can only access their own data
   if current_user.id != path_user_id:
       raise HTTPException(403, "Forbidden")
   ```

4. **Execute request and return response**

---

## Summary

### **Key Takeaways:**

1. **Video Upload → Database:**
   - Drop video → Filename parsed → Database record created → Video processed → Status updated

2. **API Request → Response:**
   - JWT authentication → Authorization check → Database query → JSON response

3. **Video Streaming:**
   - Master playlist → Quality selection → Segment playlist → Video segments

4. **User Features:**
   - Authentication (JWT tokens, 7-day expiry)
   - Watch history (resume playback)
   - Watchlist (favorite series)
   - Analytics (viewing data)

5. **Adaptive Streaming:**
   - 3 quality levels (360p, 720p, 1080p)
   - HLS protocol for adaptive bitrate switching
   - 2-second segments for smooth playback

### **Running the System:**

```bash
# Install dependencies
pip install -r requirements.txt

# Start both services
python run_all.py

# Or run separately:
python api_server.py   # API only (port 8000)
python main.py         # Video pipeline only
```

### **Testing Workflow:**

```bash
# 1. Drop a video
cp my-anime-s01e01.mp4 .local/raw_uploads/

# 2. Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"test","password":"pass123"}'

# 3. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# 4. Get series
curl http://localhost:8000/api/series

# 5. Get streaming URL
curl http://localhost:8000/api/episodes/1/stream \
  -H "Authorization: Bearer YOUR_TOKEN"

# 6. Open in browser
# http://localhost:8000/hls/my-anime-s01e01/master.m3u8
```

---

**For more information, see:**
- API Documentation: `http://localhost:8000/docs` (FastAPI auto-generated)
- Database Schema: `database/schema.sql`
- Source Code: All files in this repository
