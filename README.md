# URL Shortener

A URL shortening API built with **FastAPI** and **PostgreSQL**. It creates short links, redirects visitors, tracks clicks, and supports custom aliases and link expiry.

**Live demo:**  https://url-shortener-bebz.onrender.com/docs

## Features

- Shorten any URL into a random 6-character code (cryptographically secure, via `secrets`)
- Custom aliases (3-10 letters/digits) with reserved-word protection
- Optional link expiry (1-365 days), returns `410 Gone` after expiry
- Click tracking per link
- Input validation with Pydantic (invalid URLs are rejected)
- Automated tests with pytest

## Tech Stack

Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL, Pydantic, Uvicorn, pytest

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/shorten` | Create a short link |
| GET | `/{code}` | Redirect to the original URL (302) |
| GET | `/stats/{code}` | Click count and link details |

**Example request**

```json
POST /shorten
{
  "url": "https://github.com",
  "alias": "gh",
  "expires_in_days": 7
}
```

**Status codes:** `200` created, `302` redirect, `400` reserved alias, `404` not found, `409` alias taken, `410` expired, `422` invalid input.

## Design Decisions

- **302 instead of 301 redirects**, so browsers don't cache the redirect and every click is counted.
- **Index on the `code` column**, since every redirect is a lookup by code.
- **Collision check** before saving a generated code.
- **Config through environment variables**, so no secrets live in the code.

## Run Locally

```bash
git clone https://github.com/swanu006-code/url-shortener.git
cd url-shortener
python -m venv venv
venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create a PostgreSQL database named `shortener`, then copy `.env.example` to `.env` and put in your password:

```
DATABASE_URL=postgresql+psycopg2://postgres:yourpassword@localhost:5432/shortener
```

Start the server:

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API docs.

## Run Tests

```bash
python -m pytest -v
```

Tests use a separate SQLite database, so your real data is never touched.

## Project Structure

```
app/
├── main.py       # app setup
├── database.py   # engine and session
├── models.py     # Link table
├── schemas.py    # request validation
├── routes.py     # endpoints
└── utils.py      # code generation, expiry check
tests/            # pytest suite
```