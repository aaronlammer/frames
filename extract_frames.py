#!/usr/bin/env python3
"""
Extract frames from a video file at 1 frame per second.
Creates thumbnails (40px wide) for the grid.

Usage:
    python3 extract_frames.py video.mp4
    python3 extract_frames.py video.mp4 --name "Movie Title"
"""

import subprocess
import sys
import os
import json
import argparse
from pathlib import Path

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def extract_frames(video_path, movie_name=None):
    """Extract frames from video at 1fps"""
    
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)
    
    # Use video filename as movie name if not provided
    if not movie_name:
        movie_name = video_path.stem
    
    # Create output directories
    frames_dir = Path('static/frames')
    thumbs_dir = frames_dir / 'thumbs'
    
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Extracting frames from: {video_path}")
    print(f"Movie name: {movie_name}")
    
    # Get duration
    duration = get_video_duration(str(video_path))
    total_frames = int(duration)
    print(f"Duration: {duration:.1f} seconds ({total_frames} frames to extract)")
    
    # Extract thumbnails (40px wide)
    print("\nExtracting thumbnails...")
    cmd_thumb = [
        'ffmpeg', '-i', str(video_path),
        '-vf', 'fps=1,scale=40:-1',
        '-q:v', '4',
        str(thumbs_dir / 'frame_%05d.jpg'),
        '-y'
    ]
    subprocess.run(cmd_thumb)
    
    # Generate manifest
    print("\nGenerating manifest...")
    frames = []
    for i in range(1, total_frames + 1):
        filename = f'frame_{i:05d}.jpg'
        thumb_path = thumbs_dir / filename
        
        if thumb_path.exists():
            # Calculate timecode
            hours = i // 3600
            minutes = (i % 3600) // 60
            seconds = i % 60
            timecode = f'{hours:02d}:{minutes:02d}:{seconds:02d}'
            
            frames.append({
                'number': i,
                'thumbnail': f'/static/frames/thumbs/{filename}',
                'timecode': timecode
            })
    
    manifest = {
        'movie_name': movie_name,
        'total_frames': len(frames),
        'frames': frames
    }
    
    manifest_path = frames_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDone! Extracted {len(frames)} frames.")
    print(f"Manifest saved to: {manifest_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract frames from a video file')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--name', '-n', help='Movie name (default: video filename)')
    
    args = parser.parse_args()
    extract_frames(args.video, args.name)
