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
    """Run the video processing pipeline by executing main.py logic."""
    # Import main.py's functionality
    from watchdog.observers import Observer
    from main import NewVideoHandler
    from database import init_db
    import config

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
