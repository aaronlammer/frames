#!/usr/bin/env python3
"""
Extract one frame per shot from a video file using scene detection.
Uses FFmpeg's scene detection filter to identify shot changes.

Usage:
    python3 extract_shots.py video.mp4
    python3 extract_shots.py video.mp4 --name "Movie Title"
    python3 extract_shots.py video.mp4 --threshold 0.3  (lower = more shots detected)
"""

import subprocess
import sys
import os
import json
import argparse
import re
from pathlib import Path

def detect_shots(video_path, threshold=0.4):
    """
    Detect shot changes using FFmpeg's scene detection.
    Returns list of timestamps where shots change.
    """
    print(f"Analyzing video for shot changes (threshold: {threshold})...")
    
    # Use FFmpeg to detect scene changes and output timestamps
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-vf', f"select='gt(scene,{threshold})',showinfo",
        '-f', 'null', '-'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse the output to find timestamps
    # Look for lines like: [Parsed_showinfo_1 @ ...] n:   0 pts:   1001 pts_time:0.041708
    timestamps = [0.0]  # Always include first frame
    
    for line in result.stderr.split('\n'):
        if 'pts_time:' in line:
            match = re.search(r'pts_time:(\d+\.?\d*)', line)
            if match:
                timestamps.append(float(match.group(1)))
    
    # Remove duplicates and sort
    timestamps = sorted(list(set(timestamps)))
    
    print(f"Found {len(timestamps)} shots")
    return timestamps

def extract_frames_at_timestamps(video_path, timestamps, output_dir, thumb_width=240):
    """Extract frames at specific timestamps"""
    
    thumbs_dir = output_dir / 'thumbs'
    full_dir = output_dir / 'full'
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    
    frames = []
    total = len(timestamps)
    
    print(f"\nExtracting {total} frames (thumbnails + full size)...")
    
    for i, ts in enumerate(timestamps):
        frame_num = i + 1
        filename = f'frame_{frame_num:05d}.jpg'
        thumb_path = thumbs_dir / filename
        full_path = full_dir / filename
        
        # Extract thumbnail at this timestamp
        cmd_thumb = [
            'ffmpeg', '-ss', str(ts),
            '-i', str(video_path),
            '-vf', f'scale={thumb_width}:-1',
            '-vframes', '1',
            '-q:v', '4',
            str(thumb_path),
            '-y'
        ]
        subprocess.run(cmd_thumb, capture_output=True)
        
        # Extract full-size frame
        cmd_full = [
            'ffmpeg', '-ss', str(ts),
            '-i', str(video_path),
            '-vframes', '1',
            '-q:v', '2',
            str(full_path),
            '-y'
        ]
        subprocess.run(cmd_full, capture_output=True)
        
        if thumb_path.exists():
            # Calculate timecode
            hours = int(ts // 3600)
            minutes = int((ts % 3600) // 60)
            seconds = int(ts % 60)
            timecode = f'{hours:02d}:{minutes:02d}:{seconds:02d}'
            
            frames.append({
                'number': frame_num,
                'thumbnail': f'/static/frames/thumbs/{filename}',
                'full': f'/static/frames/full/{filename}',
                'timecode': timecode,
                'timestamp': ts
            })
        
        # Progress indicator
        if frame_num % 50 == 0 or frame_num == total:
            print(f"  Extracted {frame_num}/{total} frames")
    
    return frames

def extract_shots(video_path, movie_name=None, threshold=0.4):
    """Main extraction function"""
    
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)
    
    # Use video filename as movie name if not provided
    if not movie_name:
        movie_name = video_path.stem
    
    print(f"Processing: {video_path}")
    print(f"Movie name: {movie_name}")
    
    # Detect shots
    timestamps = detect_shots(video_path, threshold)
    
    if len(timestamps) == 0:
        print("No shots detected. Try lowering the threshold.")
        sys.exit(1)
    
    # Create output directory
    frames_dir = Path('static/frames')
    
    # Clear existing thumbnails
    thumbs_dir = frames_dir / 'thumbs'
    if thumbs_dir.exists():
        for f in thumbs_dir.glob('*.jpg'):
            f.unlink()
    
    # Extract frames
    frames = extract_frames_at_timestamps(video_path, timestamps, frames_dir)
    
    # Generate manifest
    manifest = {
        'movie_name': movie_name,
        'total_frames': len(frames),
        'extraction_type': 'shot_detection',
        'threshold': threshold,
        'frames': frames
    }
    
    manifest_path = frames_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDone! Extracted {len(frames)} shot frames.")
    print(f"Manifest saved to: {manifest_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract one frame per shot from a video')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--name', '-n', help='Movie name (default: video filename)')
    parser.add_argument('--threshold', '-t', type=float, default=0.4,
                        help='Scene detection threshold 0.0-1.0 (lower = more shots, default: 0.4)')
    
    args = parser.parse_args()
    extract_shots(args.video, args.name, args.threshold)

