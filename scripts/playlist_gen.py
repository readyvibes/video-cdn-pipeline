import os

def create_master_playlist(target_dir, variants):
    """
    Creates a Master M3U8 file that points to different quality variants.
    :param target_dir: The directory where the master file will be saved.
    :param variants: A list of dicts containing 'name', 'resolution', and 'bandwidth'.
    """
    master_path = os.path.join(target_dir, "master.m3u8")

    with open(master_path, "w") as f:
        f.write("#EXTM3U\n")  # Start of the playlist

        for v in variants:
            # Add metadata for the stream quality
            f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={v['bandwidth']},RESOLUTION={v['resolution']}\n")
            # Point to the index file for this specific quality
            f.write(f"{v['name']}/index.m3u8\n")

    print(f"Master playlist created: {master_path}")