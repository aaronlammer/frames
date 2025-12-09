#!/usr/bin/env python3
"""
Extract frames from a video at:
1. Each shot change (scene detection)
2. Each unique subtitle appearance

Usage:
    python3 extract_shots_subtitles.py video.mp4 --name "Movie Title" --output silver-globe
    python3 extract_shots_subtitles.py video.mp4 --srt subtitles.srt --output silver-globe
"""

import subprocess
import sys
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


def parse_srt(srt_path):
    """Parse SRT file and return list of (start_time, text) tuples for unique subtitles."""
    print(f"Parsing subtitles from: {srt_path}")
    
    with open(srt_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Split into subtitle blocks
    blocks = re.split(r'\n\n+', content.strip())
    
    subtitles = []
    seen_texts = set()
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Parse timecode line: 00:01:23,456 --> 00:01:25,789
        time_match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->', lines[1])
        if not time_match:
            continue
        
        hours, minutes, seconds, ms = map(int, time_match.groups())
        start_time = hours * 3600 + minutes * 60 + seconds + ms / 1000
        
        # Get subtitle text (join remaining lines)
        text = ' '.join(lines[2:]).strip()
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Only add if this is a unique subtitle
        if text and text not in seen_texts:
            seen_texts.add(text)
            subtitles.append((start_time, text))
    
    print(f"Found {len(subtitles)} unique subtitles")
    return subtitles


def extract_embedded_subtitles(video_path):
    """Try to extract subtitles embedded in video file."""
    print("Checking for embedded subtitles...")
    
    # Check for subtitle streams
    probe_cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 's',
        '-show_entries', 'stream=index,codec_name',
        '-of', 'csv=p=0',
        str(video_path)
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    
    if not result.stdout.strip():
        print("No embedded subtitles found")
        return []
    
    print(f"Found subtitle streams: {result.stdout.strip()}")
    
    # Extract first subtitle stream to temp SRT
    temp_srt = Path('/tmp/temp_subs.srt')
    extract_cmd = [
        'ffmpeg', '-i', str(video_path),
        '-map', '0:s:0',
        '-f', 'srt',
        str(temp_srt),
        '-y'
    ]
    subprocess.run(extract_cmd, capture_output=True)
    
    if temp_srt.exists():
        subtitles = parse_srt(temp_srt)
        temp_srt.unlink()
        return subtitles
    
    return []


def extract_frames(video_path, timestamps_with_data, output_dir, thumb_width=240):
    """Extract frames at specific timestamps."""
    
    thumbs_dir = output_dir / 'thumbs'
    full_dir = output_dir / 'full'
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    
    frames = []
    total = len(timestamps_with_data)
    
    print(f"\nExtracting {total} frames...")
    
    for i, data in enumerate(timestamps_with_data):
        ts = data['timestamp']
        frame_num = i + 1
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
            
            frame_data = {
                'number': frame_num,
                'thumbnail': f'/static/frames/{output_dir.name}/thumbs/{filename}',
                'full': f'/static/frames/{output_dir.name}/full/{filename}',
                'timecode': timecode,
                'timestamp': ts,
                'type': data['type']
            }
            
            # Add subtitle text if present
            if data.get('subtitle'):
                frame_data['subtitle'] = data['subtitle']
            
            frames.append(frame_data)
        
        # Progress
        if frame_num % 50 == 0 or frame_num == total:
            print(f"  Extracted {frame_num}/{total} frames")
    
    return frames


def main():
    parser = argparse.ArgumentParser(description='Extract frames at shot changes and unique subtitles')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--name', '-n', help='Movie name')
    parser.add_argument('--output', '-o', required=True, help='Output folder name (e.g., silver-globe)')
    parser.add_argument('--srt', help='Path to external SRT subtitle file')
    parser.add_argument('--threshold', '-t', type=float, default=0.4, help='Scene detection threshold (default: 0.4)')
    parser.add_argument('--width', '-w', type=int, default=240, help='Thumbnail width (default: 240)')
    parser.add_argument('--shots-only', action='store_true', help='Only extract shot changes, no subtitles')
    parser.add_argument('--subs-only', action='store_true', help='Only extract subtitle frames, no shots')
    
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
    
    # Collect all timestamps with metadata
    all_timestamps = {}  # timestamp -> data
    
    # Get shot timestamps
    if not args.subs_only:
        shot_timestamps = detect_shots(video_path, args.threshold)
        for ts in shot_timestamps:
            all_timestamps[ts] = {'timestamp': ts, 'type': 'shot', 'subtitle': None}
    
    # Get subtitle timestamps
    if not args.shots_only:
        if args.srt:
            srt_path = Path(args.srt)
            if not srt_path.exists():
                print(f"Error: SRT file not found: {srt_path}")
                sys.exit(1)
            subtitles = parse_srt(srt_path)
        else:
            subtitles = extract_embedded_subtitles(video_path)
        
        for ts, text in subtitles:
            if ts in all_timestamps:
                # Timestamp exists from shot, add subtitle info
                all_timestamps[ts]['subtitle'] = text
                all_timestamps[ts]['type'] = 'shot+subtitle'
            else:
                all_timestamps[ts] = {'timestamp': ts, 'type': 'subtitle', 'subtitle': text}
    
    # Sort by timestamp
    sorted_data = sorted(all_timestamps.values(), key=lambda x: x['timestamp'])
    
    print(f"\nTotal unique timestamps: {len(sorted_data)}")
    
    # Clear existing frames
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    
    # Extract frames
    frames = extract_frames(video_path, sorted_data, output_dir, thumb_width=args.width)
    
    # Count types
    shot_count = sum(1 for f in frames if 'shot' in f['type'])
    sub_count = sum(1 for f in frames if 'subtitle' in f['type'])
    
    # Generate manifest
    manifest = {
        'movie_name': movie_name,
        'total_frames': len(frames),
        'shot_frames': shot_count,
        'subtitle_frames': sub_count,
        'extraction_type': 'shots_and_subtitles',
        'frames': frames
    }
    
    manifest_path = output_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nDone! Extracted {len(frames)} frames.")
    print(f"  - Shot changes: {shot_count}")
    print(f"  - Unique subtitles: {sub_count}")
    print(f"Manifest saved to: {manifest_path}")


if __name__ == '__main__':
    main()

