import subprocess
import os
import config
from scripts.playlist_gen import create_master_playlist
from database import SessionLocal
from database.models import Episode
from sqlalchemy.orm import Session


def process_video(input_path, episode_id: int = None):
    """
    Process video file and optionally update episode in database.

    Args:
        input_path: Path to the input video file
        episode_id: Optional episode ID to update in database when processing is complete
    """
    file_name = os.path.splitext(os.path.basename(input_path))[0]
    target_dir = os.path.join(config.OUTPUT_DIR, file_name)
    os.makedirs(target_dir, exist_ok=True)

    # Define quality variants
    variants = [
        {'name': '360p', 'resolution': '640x360', 'bandwidth': 800000, 'bitrate': '800k'},
        {'name': '720p', 'resolution': '1280x720', 'bandwidth': 2800000, 'bitrate': '2800k'},
        {'name': '1080p', 'resolution': '1920x1080', 'bandwidth': 5000000, 'bitrate': '5000k'}
    ]

    db: Session = None

    try:
        print(f"Starting transcoding for: {file_name}...")

        # Update episode status to processing if episode_id provided
        if episode_id:
            db = SessionLocal()
            episode = db.query(Episode).filter(Episode.id == episode_id).first()
            if episode:
                episode.status = "processing"
                db.commit()

        # Process each quality variant
        for variant in variants:
            variant_dir = os.path.join(target_dir, variant['name'])
            os.makedirs(variant_dir, exist_ok=True)

            output_m3u8 = os.path.join(variant_dir, "index.m3u8")

            command = [
                "ffmpeg", "-i", input_path,
                "-preset", "fast",
                "-g", str(config.GOP),
                "-sc_threshold", "0",
                "-s", variant['resolution'],
                "-b:v", variant['bitrate'],
                "-f", "hls",
                "-hls_time", str(config.SEGMENT_TIME),
                "-hls_playlist_type", "vod",
                "-hls_segment_filename", os.path.join(variant_dir, "seg_%03d.ts"),
                output_m3u8
            ]

            print(f"  Transcoding {variant['name']}...")
            subprocess.run(command, check=True)
            print(f"  ✓ {variant['name']} complete")

        # Create master playlist
        master_playlist_path = os.path.join(target_dir, "master.m3u8")
        create_master_playlist(target_dir, variants)
        print(f"Successfully processed: {file_name}")

        # Update episode in database if episode_id provided
        if episode_id and db:
            episode = db.query(Episode).filter(Episode.id == episode_id).first()
            if episode:
                # Store relative path from OUTPUT_DIR
                relative_path = os.path.join(file_name, "master.m3u8")
                episode.master_playlist_path = relative_path
                episode.status = "ready"
                db.commit()
                print(f"  Database updated for episode ID: {episode_id}")

    except subprocess.CalledProcessError as e:
        print(f"Error during transcoding: {e}")

        # Mark episode as failed if episode_id provided
        if episode_id and db:
            episode = db.query(Episode).filter(Episode.id == episode_id).first()
            if episode:
                episode.status = "failed"
                db.commit()

    finally:
        if db:
            db.close()