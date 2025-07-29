# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Rust-based API that serves Bible verses from the Watchtower Online Library (wol.jw.org). The API is built with Rocket framework and uses PostgreSQL for data storage.

## Architecture

The backend follows a layered architecture:

- **Routes** (`backend/src/routes/`): HTTP endpoints including:
  - `/api/v1/verse/<book>/<chapter>/<verse>` - Basic verse retrieval
  - `/api/v1/study/<book>/<chapter>/<verse>` - Enhanced verse with study content
  - `/health` - Health check endpoint
- **Services** (`backend/src/services/`): Business logic for verse retrieval and dynamic scraping
- **Models** (`backend/src/models/`): Data structures including `BibleVerse`, `StudyContent`, and `VerseWithStudy`
- **Guards** (`backend/src/guards/`): Request guards like `DbGuard` for database connection management

The main application entry point is `backend/src/main.rs` which initializes the Rocket server and PostgreSQL connection pool using sqlx.

### Dynamic Content Fetching

The API implements dynamic content fetching from wol.jw.org when content is not cached:
- **Verse Fetching**: If a verse is not found in the database, the system automatically scrapes it using `scrape_with_study_notes_docker.py`
- **Study Content**: If study content is missing, it's scraped and cached automatically
- **Caching**: All scraped content is stored in PostgreSQL for future requests

## Development Commands

### Backend (Rust)
- **Build**: `cargo build` (from `backend/` directory)
- **Run**: `cargo run` (from `backend/` directory) 
- **Test**: `cargo test` (from `backend/` directory)
- **Format**: `cargo fmt` (rustfmt.toml config available)

### Docker Development
- **Start services**: `docker-compose up`
- **Build and start**: `docker-compose up --build`
- **Database**: PostgreSQL runs on port 5432, API on port 8000
- **Database connection**: `postgresql://postgres:postgres@db:5432/wol-api` (production uses `wol-api` database)

### Deployment
- **GitHub Actions**: Automatic deployment triggered on push to main branch
- **Production server**: svrclapp1.cloudwise.ca:8000
- **Deploy script**: Uses rsync to copy files and docker-compose to rebuild containers

## Database

Uses PostgreSQL with the `wol-api` database containing two main tables:

### `verses` table:
- `book_num` (INTEGER): Book number
- `book_name` (TEXT): Book name  
- `chapter` (INTEGER): Chapter number
- `verse_num` (INTEGER): Verse number
- `verse_text` (TEXT): The actual verse content
- `study_notes` (JSONB): Verse-specific study notes

### `study_content` table:
- `id` (SERIAL PRIMARY KEY): Auto-incrementing ID
- `book_num` (INTEGER): Book number
- `chapter` (INTEGER): Chapter number
- `outline` (TEXT[]): Chapter outline as array
- `study_articles` (JSONB): Related study articles
- `cross_references` (JSONB): Cross-reference data

### Database Initialization
**Important**: The database tables must be created manually after deployment:
```sql
CREATE TABLE verses (
    book_num INTEGER NOT NULL,
    book_name TEXT NOT NULL, 
    chapter INTEGER NOT NULL,
    verse_num INTEGER NOT NULL,
    verse_text TEXT NOT NULL,
    study_notes JSONB
);

CREATE TABLE study_content (
    id SERIAL PRIMARY KEY,
    book_num INTEGER NOT NULL,
    chapter INTEGER NOT NULL, 
    outline TEXT[],
    study_articles JSONB,
    cross_references JSONB
);
```

## Key Dependencies

- **Rocket**: Web framework (version 0.5.0-rc.3)
- **sqlx**: Database access with PostgreSQL support
- **serde**: Serialization support

## Scraping Scripts

The project includes Python scraping scripts in the `scripts/` directory:
- **`scrape_with_study_notes_docker.py`**: Main scraper for verses and study content (Docker version)
- **`scrape_with_study_notes.py`**: Local version of the main scraper
- **`scrape_research_guide_only.py`**: Specialized scraper for research guide content
- **`setup_db.py`** and **`setup_study_db.py`**: Database setup utilities

## Testing

Currently has basic integration tests in `backend/src/test_home.rs`. Tests use Rocket's testing client to verify endpoints.

## Troubleshooting

### Common Issues

1. **"Database error: relation 'verses' does not exist"**
   - The database tables haven't been created yet
   - Connect to the database and run the SQL commands in the Database Initialization section

2. **"Verse not found" but scraping logs show success**
   - The Python scraper may not be saving data to the database properly
   - Check database connection in the scraping script
   - Verify the scraper is using the correct database (`wol-api`, not `postgres`)

3. **Deployment conflicts with existing containers**
   - Clean up any manually created containers: `docker rm -f <container_id>`
   - Use GitHub Actions for deployment instead of manual Docker commands

4. **Connection refused on port 8000**
   - Ensure the backend container is running: `docker ps | grep backend`
   - Check firewall rules: `sudo ufw allow 8000`
   - Verify the container is bound to the correct port