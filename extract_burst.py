#!/usr/bin/env python3
"""
Extract burst of frames from the start of each shot.
Detects shot changes, then grabs N frames at specified FPS from each shot start.

Usage:
    python3 extract_burst.py video.mp4 --name "Movie Title" --output aguirre
    python3 extract_burst.py video.mp4 --frames 6 --fps 12
"""

import subprocess
import sys
import os
import json
import argparse
import re
from pathlib import Path

def detect_shots(video_path, threshold=0.4):
    """Detect shot changes using FFmpeg's scene detection."""
    print(f"Analyzing video for shot changes (threshold: {threshold})...")
    
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-vf', f"select='gt(scene,{threshold})',showinfo",
        '-f', 'null', '-'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    timestamps = [0.0]  # Always include first frame
    
    for line in result.stderr.split('\n'):
        if 'pts_time:' in line:
            match = re.search(r'pts_time:(\d+\.?\d*)', line)
            if match:
                timestamps.append(float(match.group(1)))
    
    timestamps = sorted(list(set(timestamps)))
    print(f"Found {len(timestamps)} shots")
    return timestamps

def extract_burst_frames(video_path, shot_timestamps, output_dir, frames_per_shot=6, fps=12, thumb_width=240):
    """Extract burst of frames from start of each shot"""
    
    thumbs_dir = output_dir / 'thumbs'
    full_dir = output_dir / 'full'
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    
    frames = []
    frame_num = 0
    total_shots = len(shot_timestamps)
    frame_interval = 1.0 / fps  # Time between frames
    
    print(f"\nExtracting {frames_per_shot} frames per shot at {fps}fps...")
    print(f"Total: ~{total_shots * frames_per_shot} frames from {total_shots} shots")
    
    for shot_idx, shot_start in enumerate(shot_timestamps):
        # Extract burst of frames from this shot
        for burst_idx in range(frames_per_shot):
            frame_num += 1
            ts = shot_start + (burst_idx * frame_interval)
            filename = f'frame_{frame_num:05d}.jpg'
            thumb_path = thumbs_dir / filename
            full_path = full_dir / filename
            
            # Extract thumbnail
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
            
            # Extract full-size
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
                hours = int(ts // 3600)
                minutes = int((ts % 3600) // 60)
                seconds = int(ts % 60)
                ms = int((ts % 1) * 1000)
                timecode = f'{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}'
                
                frames.append({
                    'number': frame_num,
                    'shot': shot_idx + 1,
                    'burst_frame': burst_idx + 1,
                    'thumbnail': f'/static/frames/{output_dir.name}/thumbs/{filename}',
                    'full': f'/static/frames/{output_dir.name}/full/{filename}',
                    'timecode': timecode,
                    'timestamp': ts
                })
        
        # Progress
        if (shot_idx + 1) % 20 == 0 or shot_idx == total_shots - 1:
            print(f"  Processed {shot_idx + 1}/{total_shots} shots ({frame_num} frames)")
    
    return frames

def main():
    parser = argparse.ArgumentParser(description='Extract burst of frames from shot starts')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--name', '-n', help='Movie name')
    parser.add_argument('--output', '-o', required=True, help='Output folder name (e.g., aguirre)')
    parser.add_argument('--frames', '-f', type=int, default=6, help='Frames per shot (default: 6)')
    parser.add_argument('--fps', type=int, default=12, help='FPS for burst (default: 12)')
    parser.add_argument('--threshold', '-t', type=float, default=0.4, help='Scene detection threshold')
    parser.add_argument('--width', '-w', type=int, default=240, help='Thumbnail width (default: 240)')
    
    args = parser.parse_args()
    
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)
    
    movie_name = args.name or video_path.stem
    output_dir = Path('static/frames') / args.output
    
    print(f"Processing: {video_path}")
    print(f"Movie name: {movie_name}")
    print(f"Output: {output_dir}")
    
    # Detect shots
    timestamps = detect_shots(video_path, args.threshold)
    
    # Clear existing frames
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    
    # Extract burst frames
    frames = extract_burst_frames(
        video_path, timestamps, output_dir,
        frames_per_shot=args.frames,
        fps=args.fps,
        thumb_width=args.width
    )
    
    # Generate manifest
    manifest = {
        'movie_name': movie_name,
        'total_frames': len(frames),
        'total_shots': len(timestamps),
        'frames_per_shot': args.frames,
        'fps': args.fps,
        'extraction_type': 'burst',
        'frames': frames
    }
    
    manifest_path = output_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDone! Extracted {len(frames)} frames from {len(timestamps)} shots.")
    print(f"Manifest saved to: {manifest_path}")

if __name__ == '__main__':
    main()

