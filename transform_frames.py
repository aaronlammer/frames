#!/usr/bin/env python3
"""
Transform movie frames into hand-painted anime style using OpenAI APIs.
Uses GPT-4 Vision to describe frames, then DALL-E 3 to generate stylized versions.

Usage:
    python3 transform_frames.py aguirre --style anime
    python3 transform_frames.py aguirre --start 1 --end 10  (process subset)
"""

import os
import sys
import json
import base64
import argparse
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Style prompt for hand-painted Japanese animation aesthetic
# (soft watercolors, detailed backgrounds, expressive, natural landscapes, atmospheric)
ANIME_STYLE_PROMPT = """Transform this into a hand-painted animation cel style with:
- Soft watercolor textures and gentle color gradients
- Detailed, painterly backgrounds with atmospheric depth
- Rich natural lighting with attention to sky, clouds, and environmental details
- Warm, dreamy color palette with soft edges
- The aesthetic of classic hand-drawn Japanese animation from the 1980s-2000s
- Maintain the exact composition, framing, and subjects from the original"""

def encode_image_to_base64(image_path):
    """Read image and encode to base64"""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def describe_frame(client, image_path):
    """Use GPT-4 Vision to describe the frame in detail"""
    base64_image = encode_image_to_base64(image_path)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this movie frame in detail for an artist to recreate. Include: subjects, poses, expressions, clothing, environment, lighting, colors, camera angle, and mood. Be specific and visual. Keep it under 200 words."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    
    return response.choices[0].message.content

def generate_anime_frame(client, description, original_path):
    """Use DALL-E 3 to generate anime-style version"""
    
    prompt = f"""{ANIME_STYLE_PROMPT}

Scene description: {description}"""
    
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",  # Widescreen for film frames
        quality="hd",
        n=1
    )
    
    return response.data[0].url

def download_image(url, output_path):
    """Download image from URL to local file"""
    import urllib.request
    urllib.request.urlretrieve(url, output_path)

def transform_frames(movie_slug, start=None, end=None, dry_run=False):
    """Transform frames for a movie"""
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env file")
        print("Add your OpenAI API key to .env: OPENAI_API_KEY=sk-...")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Paths
    source_dir = Path(f"static/frames/{movie_slug}")
    output_dir = Path(f"static/frames/{movie_slug}-anime")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "full").mkdir(exist_ok=True)
    
    # Load source manifest
    manifest_path = source_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}")
        sys.exit(1)
    
    with open(manifest_path) as f:
        source_manifest = json.load(f)
    
    frames = source_manifest["frames"]
    
    # Filter frames if range specified
    if start is not None:
        frames = [f for f in frames if f["number"] >= start]
    if end is not None:
        frames = [f for f in frames if f["number"] <= end]
    
    print(f"Processing {len(frames)} frames from {movie_slug}")
    print(f"Output: {output_dir}")
    
    if dry_run:
        print("DRY RUN - no API calls will be made")
        return
    
    # Process each frame
    transformed_frames = []
    
    for i, frame in enumerate(frames):
        frame_num = frame["number"]
        # Source is full-size image
        source_path = Path("static") / frame["full"].lstrip("/static/")
        
        if not source_path.exists():
            # Try thumbnail if full doesn't exist
            source_path = Path("static") / frame["thumbnail"].lstrip("/static/")
        
        if not source_path.exists():
            print(f"  Skipping frame {frame_num} - source not found")
            continue
        
        output_filename = f"frame_{frame_num:05d}.png"
        output_path = output_dir / "full" / output_filename
        
        # Skip if already processed
        if output_path.exists():
            print(f"  Frame {frame_num} already exists, skipping")
            transformed_frames.append({
                "number": frame_num,
                "original": frame["full"],
                "anime": f"/static/frames/{movie_slug}-anime/full/{output_filename}",
                "timecode": frame["timecode"]
            })
            continue
        
        print(f"  [{i+1}/{len(frames)}] Processing frame {frame_num}...")
        
        try:
            # Step 1: Describe the frame
            print(f"    Analyzing frame...")
            description = describe_frame(client, source_path)
            
            # Step 2: Generate anime version
            print(f"    Generating anime version...")
            image_url = generate_anime_frame(client, description, source_path)
            
            # Step 3: Download the generated image
            print(f"    Downloading result...")
            download_image(image_url, output_path)
            
            transformed_frames.append({
                "number": frame_num,
                "original": frame["full"],
                "anime": f"/static/frames/{movie_slug}-anime/full/{output_filename}",
                "timecode": frame["timecode"],
                "description": description
            })
            
            print(f"    Done!")
            
            # Rate limiting - be nice to the API
            time.sleep(1)
            
        except Exception as e:
            print(f"    ERROR: {e}")
            continue
    
    # Save manifest
    output_manifest = {
        "movie_name": source_manifest["movie_name"] + " (Anime)",
        "source_movie": movie_slug,
        "total_frames": len(transformed_frames),
        "style": "hand-painted anime",
        "frames": transformed_frames
    }
    
    manifest_output = output_dir / "manifest.json"
    with open(manifest_output, "w") as f:
        json.dump(output_manifest, f, indent=2)
    
    print(f"\nDone! Transformed {len(transformed_frames)} frames")
    print(f"Manifest saved to: {manifest_output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform frames to anime style")
    parser.add_argument("movie", help="Movie slug (e.g., aguirre)")
    parser.add_argument("--start", type=int, help="Start frame number")
    parser.add_argument("--end", type=int, help="End frame number")
    parser.add_argument("--dry-run", action="store_true", help="Don't make API calls")
    
    args = parser.parse_args()
    transform_frames(args.movie, args.start, args.end, args.dry_run)

