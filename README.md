# FRAMES

A shot-by-shot movie viewer. Extracts one frame per shot using scene detection and displays them in a grid.

## Live

https://web-production-726b.up.railway.app/the-brutalist

## Extract shots from a movie

```bash
python3 extract_shots.py /path/to/movie.mp4 --name "Movie Title"
```

Options:
- `--threshold 0.3` — more sensitive, detects more shots
- `--threshold 0.5` — less sensitive, fewer shots

## Run locally

```bash
pip install -r requirements.txt
python3 run.py
```

Open http://localhost:8000
