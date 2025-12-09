#!/usr/bin/env python3
"""
Transform a single frame using Stability AI's img2img.
This actually transforms the image while keeping composition.

Usage:
    python3 transform_stability.py aguirre --frame 1
"""

import os
import sys
import base64
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STYLE_PROMPT = """hand-painted animation cel, soft watercolor textures, 
gentle color gradients, painterly backgrounds with atmospheric depth, 
rich natural lighting, warm dreamy color palette, soft edges, 
classic hand-drawn Japanese animation style from 1980s-2000s"""

def transform_frame(source_path, output_path, api_key):
    """Transform a single frame using Stability AI img2img"""
    
    # Read source image
    with open(source_path, "rb") as f:
        image_data = f.read()
    
    # Stability AI API endpoint for img2img
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    # Send request
    response = requests.post(
        url,
        headers=headers,
        files={
            "init_image": ("image.jpg", image_data, "image/jpeg")
        },
        data={
            "text_prompts[0][text]": STYLE_PROMPT,
            "text_prompts[0][weight]": 1,
            "cfg_scale": 7,
            "samples": 1,
            "steps": 30,
            "image_strength": 0.35,  # Lower = more like original (0.0-1.0)
            "style_preset": "anime"
        }
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    
    # Save the generated image
    for i, image in enumerate(data["artifacts"]):
        img_data = base64.b64decode(image["base64"])
        with open(output_path, "wb") as f:
            f.write(img_data)
        print(f"Saved: {output_path}")
        return True
    
    return False

def main():
    parser = argparse.ArgumentParser(description="Transform single frame with Stability AI")
    parser.add_argument("movie", help="Movie slug (e.g., aguirre)")
    parser.add_argument("--frame", "-f", type=int, default=1, help="Frame number to transform")
    
    args = parser.parse_args()
    
    # Check API key
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        print("ERROR: STABILITY_API_KEY not found in .env file")
        print("Get your key from: https://platform.stability.ai/account/keys")
        print("Add to .env: STABILITY_API_KEY=sk-...")
        sys.exit(1)
    
    # Find source frame
    source_dir = Path(f"static/frames/{args.movie}")
    source_path = source_dir / "full" / f"frame_{args.frame:05d}.jpg"
    
    if not source_path.exists():
        print(f"ERROR: Source frame not found: {source_path}")
        sys.exit(1)
    
    # Output path
    output_dir = Path(f"static/frames/{args.movie}-anime")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"test_frame_{args.frame:05d}.png"
    
    print(f"Transforming: {source_path}")
    print(f"Output: {output_path}")
    
    success = transform_frame(source_path, output_path, api_key)
    
    if success:
        print("\nDone! View the result at:")
        print(f"  http://localhost:8000/static/frames/{args.movie}-anime/test_frame_{args.frame:05d}.png")
    else:
        print("\nTransformation failed.")

if __name__ == "__main__":
    main()

