# KeebTracker

A self-hosted web application for managing mechanical keyboard inventory.

## Features

- Track cases, PCBs, switches, keycaps
- Create and manage builds
- Revision history for build changes
- Media uploads (images and sound tests)

## Setup

1. Clone the repository
2. Create virtual environment: `python3 -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `uvicorn app.main:app --reload`

For production, use Docker:

```bash
docker-compose up --build
```

## Usage

- Visit http://localhost:8000 (or 8001 if running locally)
- Navigate through inventory categories
- Add items and create builds

## API

- GET /inventory/{category} - List items
- POST /inventory/{category} - Add item
- GET /builds - List builds
- POST /builds - Create build
- POST /builds/{id}/media - Upload media