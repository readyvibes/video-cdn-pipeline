"""
Unified startup script that runs both:
- FastAPI API Server (port 8000)
- Video Processing Pipeline (file monitor)
"""
import multiprocessing
import sys
import time


def run_api_server():
    """Run the FastAPI server."""
    import uvicorn
    from api_server import app

    print("[API SERVER] Starting on http://0.0.0.0:8000")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


def run_video_pipeline():
    """Run the video processing pipeline."""
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import os
    from scripts.processor import process_video
    from scripts.filename_parser import parse_video_filename, format_episode_title
    from database import SessionLocal, init_db
    from database.models import Series, Episode
    import config

    class NewVideoHandler(FileSystemEventHandler):
        def on_closed(self, event):
            """
            Triggered when a file is finished being copied/uploaded.
            Auto-creates database entries and processes the video.
            """
            if not event.is_directory and event.src_path.endswith(".mp4"):
                filename = os.path.basename(event.src_path)
                print(f"\n[NEW VIDEO] Detected: {filename}")

                # Parse filename to extract metadata
                parsed = parse_video_filename(filename)

                if not parsed['success']:
                    print(f"[ERROR] {parsed['error']}")
                    print("[INFO] Skipping database creation. Processing video anyway...")
                    process_video(event.src_path)
                    return

                print(f"[PARSED] Series: {parsed['series_title']} (S{parsed['season_number']:02d}E{parsed['episode_number']:02d})")

                # Create or update database entries
                db = SessionLocal()
                try:
                    # Find or create series
                    series = db.query(Series).filter(Series.slug == parsed['series_slug']).first()

                    if not series:
                        print(f"[DATABASE] Creating new series: {parsed['series_title']}")
                        series = Series(
                            title=parsed['series_title'],
                            slug=parsed['series_slug'],
                            status="ongoing"
                        )
                        db.add(series)
                        db.commit()
                        db.refresh(series)
                        print(f"[DATABASE] Series created with ID: {series.id}")
                    else:
                        print(f"[DATABASE] Found existing series: {series.title} (ID: {series.id})")

                    # Check if episode already exists
                    existing_episode = db.query(Episode).filter(
                        Episode.series_id == series.id,
                        Episode.season_number == parsed['season_number'],
                        Episode.episode_number == parsed['episode_number']
                    ).first()

                    if existing_episode:
                        print(f"[DATABASE] Episode already exists (ID: {existing_episode.id}). Updating...")
                        episode = existing_episode
                        episode.video_file_id = os.path.splitext(filename)[0]
                        episode.status = "processing"
                    else:
                        # Create new episode
                        print(f"[DATABASE] Creating new episode entry...")
                        episode_title = format_episode_title(
                            parsed['series_title'],
                            parsed['season_number'],
                            parsed['episode_number']
                        )

                        episode = Episode(
                            series_id=series.id,
                            episode_number=parsed['episode_number'],
                            season_number=parsed['season_number'],
                            title=episode_title,
                            video_file_id=os.path.splitext(filename)[0],
                            status="processing"
                        )
                        db.add(episode)
                        db.commit()
                        db.refresh(episode)
                        print(f"[DATABASE] Episode created with ID: {episode.id}")

                    db.commit()

                    # Process video with episode_id
                    print(f"[PROCESSING] Starting video transcode for Episode ID: {episode.id}")
                    process_video(event.src_path, episode_id=episode.id)

                except Exception as e:
                    print(f"[ERROR] Database error: {e}")
                    db.rollback()
                    print("[INFO] Processing video without database integration...")
                    process_video(event.src_path)
                finally:
                    db.close()

    # Initialize database
    print("[VIDEO PIPELINE] Initializing database...")
    init_db()

    # Start file observer
    observer = Observer()
    handler = NewVideoHandler()
    observer.schedule(handler, config.INPUT_DIR, recursive=False)
    observer.start()

    print(f"\n{'='*60}")
    print(f"  VIDEO PROCESSING PIPELINE ACTIVE")
    print(f"{'='*60}")
    print(f"  Watching: {config.INPUT_DIR}")
    print(f"  Output:   {config.OUTPUT_DIR}")
    print(f"\n  Supported filename formats:")
    print(f"    - series-name-s01e01.mp4")
    print(f"    - series-name-S01E01.mp4")
    print(f"    - series-name-1x01.mp4")
    print(f"    - series-name-ep01.mp4")
    print(f"\n  Drop .mp4 files to start processing...")
    print(f"{'='*60}\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping video pipeline...")
        observer.stop()
    observer.join()
    print("[SHUTDOWN] Video pipeline stopped.")


if __name__ == "__main__":
    print("="*70)
    print(" " * 15 + "ANIME CDN - UNIFIED STARTUP")
    print("="*70)
    print("\nStarting both services:")
    print("  1. API Server (port 8000)")
    print("  2. Video Processing Pipeline")
    print("\nPress Ctrl+C to stop all services\n")
    print("="*70 + "\n")

    # Give a moment for the message to display
    time.sleep(1)

    # Create processes for both services
    api_process = multiprocessing.Process(target=run_api_server, name="API-Server")
    pipeline_process = multiprocessing.Process(target=run_video_pipeline, name="Video-Pipeline")

    try:
        # Start both processes
        api_process.start()
        time.sleep(2)  # Give API server time to start
        pipeline_process.start()

        # Wait for both processes
        api_process.join()
        pipeline_process.join()

    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Stopping all services...")

        # Terminate both processes
        if api_process.is_alive():
            print("[SHUTDOWN] Terminating API server...")
            api_process.terminate()
            api_process.join(timeout=5)

        if pipeline_process.is_alive():
            print("[SHUTDOWN] Terminating video pipeline...")
            pipeline_process.terminate()
            pipeline_process.join(timeout=5)

        print("[SHUTDOWN] All services stopped.")
        sys.exit(0)
