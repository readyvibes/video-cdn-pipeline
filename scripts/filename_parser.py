"""
Utility for parsing video filenames to extract series and episode metadata.
"""
import re
import os


def parse_video_filename(filename: str) -> dict:
    """
    Parse video filename to extract series and episode information.

    Supported formats:
    - series-name-s01e01.mp4
    - series-name-S01E01.mp4
    - series-name-1x01.mp4
    - series-name-ep01.mp4

    Args:
        filename: Video filename (with or without extension)

    Returns:
        Dictionary with keys:
        - series_slug: URL-friendly series name
        - series_title: Human-readable series name
        - season_number: Season number (int)
        - episode_number: Episode number (int)
        - success: Boolean indicating if parsing succeeded
    """
    # Remove file extension
    name = os.path.splitext(filename)[0]

    # Pattern 1: series-name-s01e01 or series-name-S01E01
    pattern1 = r'^(.+?)-[sS](\d+)[eE](\d+)$'
    match = re.match(pattern1, name)

    if match:
        series_slug = match.group(1)
        season = int(match.group(2))
        episode = int(match.group(3))

        return {
            'success': True,
            'series_slug': series_slug,
            'series_title': series_slug.replace('-', ' ').title(),
            'season_number': season,
            'episode_number': episode
        }

    # Pattern 2: series-name-1x01
    pattern2 = r'^(.+?)-(\d+)x(\d+)$'
    match = re.match(pattern2, name)

    if match:
        series_slug = match.group(1)
        season = int(match.group(2))
        episode = int(match.group(3))

        return {
            'success': True,
            'series_slug': series_slug,
            'series_title': series_slug.replace('-', ' ').title(),
            'season_number': season,
            'episode_number': episode
        }

    # Pattern 3: series-name-ep01 (assumes season 1)
    pattern3 = r'^(.+?)-[eE][pP](\d+)$'
    match = re.match(pattern3, name)

    if match:
        series_slug = match.group(1)
        episode = int(match.group(2))

        return {
            'success': True,
            'series_slug': series_slug,
            'series_title': series_slug.replace('-', ' ').title(),
            'season_number': 1,
            'episode_number': episode
        }

    # No pattern matched
    return {
        'success': False,
        'series_slug': None,
        'series_title': None,
        'season_number': None,
        'episode_number': None,
        'error': f"Could not parse filename '{filename}'. Expected format: series-name-s01e01.mp4"
    }


def format_episode_title(series_title: str, season: int, episode: int) -> str:
    """
    Generate a default episode title.

    Args:
        series_title: Human-readable series name
        season: Season number
        episode: Episode number

    Returns:
        Formatted episode title (e.g., "Attack On Titan - S01E01")
    """
    return f"{series_title} - S{season:02d}E{episode:02d}"


# Example usage and test
if __name__ == "__main__":
    test_filenames = [
        "attack-on-titan-s01e01.mp4",
        "one-piece-S02E15.mp4",
        "demon-slayer-1x03.mp4",
        "naruto-ep42.mp4",
        "invalid-filename.mp4"
    ]

    for filename in test_filenames:
        result = parse_video_filename(filename)
        print(f"\nFilename: {filename}")
        if result['success']:
            print(f"  Series: {result['series_title']} ({result['series_slug']})")
            print(f"  Season {result['season_number']}, Episode {result['episode_number']}")
            print(f"  Default title: {format_episode_title(result['series_title'], result['season_number'], result['episode_number'])}")
        else:
            print(f"  Error: {result['error']}")
