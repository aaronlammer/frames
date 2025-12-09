#!/usr/bin/env python3
"""
Extract frames from a video at:
1. Each shot change (scene detection)
2. Each unique hardcoded subtitle (using OCR)

Requires: pytesseract, Pillow
Install: pip install pytesseract Pillow
Also needs Tesseract installed: brew install tesseract

Usage:
    python3 extract_ocr_subtitles.py video.mp4 --name "Movie Title" --output silver-globe
"""

import subprocess
import sys
import json
import argparse
import re
import tempfile
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install pytesseract Pillow")
    print("Also: brew install tesseract")
    sys.exit(1)


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


def get_video_duration(video_path):
    """Get video duration in seconds."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def extract_frame_for_ocr(video_path, timestamp, temp_dir):
    """Extract a single frame for OCR processing."""
    frame_path = temp_dir / f'ocr_frame_{timestamp:.3f}.jpg'
    
    cmd = [
        'ffmpeg', '-ss', str(timestamp),
        '-i', str(video_path),
        '-vframes', '1',
        '-q:v', '2',
        str(frame_path),
        '-y'
    ]
    subprocess.run(cmd, capture_output=True)
    
    return frame_path if frame_path.exists() else None


def ocr_subtitle_region(image_path, crop_bottom_percent=25):
    """
    Crop the bottom portion of the frame and run OCR.
    Returns cleaned subtitle text.
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        # Crop bottom portion where subtitles typically are
        crop_height = int(height * crop_bottom_percent / 100)
        subtitle_region = img.crop((0, height - crop_height, width, height))
        
        # Run OCR
        text = pytesseract.image_to_string(subtitle_region, lang='eng')
        
        # Clean up the text
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\w\s\'".,!?-]', '', text)  # Remove weird characters
        
        return text if len(text) > 2 else ''  # Ignore very short detections
        
    except Exception as e:
        return ''


def scan_for_subtitle_changes(video_path, sample_interval=0.5, crop_percent=25):
    """
    Scan video at regular intervals and detect when subtitle text changes.
    Returns list of (timestamp, subtitle_text) for each unique subtitle.
    """
    print(f"\nScanning for hardcoded subtitles (sampling every {sample_interval}s)...")
    
    duration = get_video_duration(video_path)
    print(f"Video duration: {duration:.1f} seconds")
    
    subtitle_changes = []
    last_subtitle = ''
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        current_time = 0.0
        sample_count = 0
        total_samples = int(duration / sample_interval)
        
        while current_time < duration:
            sample_count += 1
            
            # Extract frame
            frame_path = extract_frame_for_ocr(video_path, current_time, temp_path)
            
            if frame_path:
                # OCR the subtitle region
                subtitle_text = ocr_subtitle_region(frame_path, crop_percent)
                
                # Check if subtitle changed
                if subtitle_text != last_subtitle:
                    if subtitle_text:  # Only record if there's actual text
                        subtitle_changes.append((current_time, subtitle_text))
                        print(f"  [{current_time:.1f}s] New subtitle: {subtitle_text[:50]}...")
                    last_subtitle = subtitle_text
                
                # Clean up temp frame
                frame_path.unlink()
            
            # Progress indicator
            if sample_count % 100 == 0:
                print(f"  Scanned {sample_count}/{total_samples} samples ({current_time:.0f}s / {duration:.0f}s)")
            
            current_time += sample_interval
    
    print(f"\nFound {len(subtitle_changes)} unique subtitles")
    return subtitle_changes


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
    parser = argparse.ArgumentParser(description='Extract frames at shot changes and OCR-detected subtitles')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--name', '-n', help='Movie name')
    parser.add_argument('--output', '-o', required=True, help='Output folder name (e.g., silver-globe)')
    parser.add_argument('--threshold', '-t', type=float, default=0.4, help='Scene detection threshold (default: 0.4)')
    parser.add_argument('--width', '-w', type=int, default=240, help='Thumbnail width (default: 240)')
    parser.add_argument('--sample-interval', '-s', type=float, default=0.5, 
                        help='Seconds between OCR samples (default: 0.5)')
    parser.add_argument('--crop-percent', '-c', type=int, default=25,
                        help='Percent of frame height to crop from bottom for OCR (default: 25)')
    parser.add_argument('--shots-only', action='store_true', help='Only extract shot changes, no OCR')
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
    
    # Get subtitle timestamps via OCR
    if not args.shots_only:
        subtitle_changes = scan_for_subtitle_changes(
            video_path, 
            sample_interval=args.sample_interval,
            crop_percent=args.crop_percent
        )
        
        for ts, text in subtitle_changes:
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
        'extraction_type': 'shots_and_ocr_subtitles',
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

