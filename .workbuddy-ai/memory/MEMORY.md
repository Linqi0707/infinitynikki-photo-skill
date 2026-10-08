# InfinityNikki Photo Skill - Project Memory

## Tech Stack
- Python 3.13.12 (managed venv at ~/.workbuddy-ai/binaries/python/envs/default)
- Flask for web UI backend
- SQLite database at data/infinitynikki_photos.db
- Qwen2.5-VL for photo semantic analysis

## Database Schema
- photos: photo_id, filename, path, shoot_time, width, height, orientation, sha256, analysis_status
- photo_semantics: photo_type, portrait_framing, portrait_view, scene_category, game_time, color_tone, background
- outfits: outfit_code, outfit_description
- camera_params: camera_code, description

## Project Conventions
- Photos stored in data/photos/ as copies, DB path field points to original game directory
- src/ contains core modules (database.py, semantic.py, vlm.py) — do not modify
- scripts/ contains CLI tools (skill_tool.py is the main entry point)
- web/ contains the Flask web UI (created 2026-10-08)
- WorkBuddy Skill definition in SKILL.md and workbuddy_skill/

## Web UI (web/)
- Run: python web/app.py (Flask debug, http://localhost:5000)
- No external JS frameworks — vanilla JS single-page app
- 8 tag filter dimensions, keyword search, paginated photo wall, detail modal
