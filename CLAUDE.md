# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Rust-based API that serves Bible verses from the Watchtower Online Library (wol.jw.org). The API is built with Rocket framework and uses PostgreSQL for data storage.

## API Endpoints

### `/api/v1/verse/<book>/<chapter>/<verse>` (GET)
Basic verse retrieval endpoint that returns plain text verse content.

**Path Parameters:**
- `book` (integer): Bible book number (1-66)
- `chapter` (integer): Chapter number
- `verse` (integer): Verse number

**Response:** Plain text verse content

**Example:**
```bash
# Local development
curl "http://localhost:8000/api/v1/verse/40/24/14"

# Production server
curl "http://svrclapp1.cloudwise.ca:8000/api/v1/verse/40/24/14"
```

### `/api/v1/study/<book>/<chapter>/<verse>` (GET)
Enhanced verse endpoint with study content, field filtering, and dynamic scraping.

**Path Parameters:**
- `book` (integer): Bible book number (1-66)
- `chapter` (integer): Chapter number  
- `verse` (integer): Verse number

**Query Parameters:**
- `fields` (string, optional): Comma-separated list of fields to return
- `limit` (integer, optional): Maximum number of items to return for array fields
- `fetch` (boolean, optional): Force fresh data fetch from wol.jw.org
  - `true`: Clears cache and scrapes fresh data (slower ~10-15s)
  - `false` or omitted: Uses cached data (faster ~200ms)

**Available Fields:**
- `verse.verse_text`: The Bible verse text
- `verse.book_name`: Book name (e.g., "Matthew")
- `verse.book_num`: Book number
- `verse.chapter`: Chapter number
- `verse.verse_num`: Verse number
- `verse.study_notes.content.text`: Verse-specific study notes
- `study_content.study_articles`: Research guide articles
- `study_content.outline`: Chapter outline
- `study_content.cross_references`: Cross references

**Response:** JSON object with requested fields

**Examples:**
```bash
# Get verse text and study notes
curl "http://localhost:8000/api/v1/study/40/24/14?fields=verse.verse_text,verse.study_notes.content.text"

# Get study articles with limit
curl "http://localhost:8000/api/v1/study/40/24/14?fields=study_content.study_articles&limit=5"

# Force fresh data from wol.jw.org
curl "http://localhost:8000/api/v1/study/40/24/14?fields=verse.verse_text,study_content.study_articles&fetch=true"

# Complete example (production)
curl "http://svrclapp1.cloudwise.ca:8000/api/v1/study/40/24/14?fields=verse.verse_text,verse.book_name,verse.book_num,verse.chapter,verse.study_notes.content.text,study_content.study_articles&limit=5"
```

### `/health` and `/api/v1/health` (GET)
Health check endpoints for monitoring service status.

**Response:** JSON with service status and database connectivity
```json
{
  "status": "ok",
  "database": "connected",
  "service": "wol-api", 
  "version": "1.0.0"
}
```

## Architecture

The backend follows a layered architecture:

- **Routes** (`backend/src/routes/`): HTTP endpoints defined above
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
- **Database connection**: `postgresql://postgres:postgres@db:5432/wol-api`

### Environments

#### Local Development
- **URL**: `http://localhost:8000`
- **Command**: `docker-compose up --build` (in project root)
- **Database**: Local PostgreSQL container
- **Use for**: Development, testing, and verification before production deploy

#### Production Server  
- **URL**: `http://svrclapp1.cloudwise.ca:8000`
- **Server**: svrclapp1.cloudwise.ca
- **Deployment**: GitHub Actions triggered on push to main branch
- **Deploy process**: Uses rsync to copy files and docker-compose to rebuild containers
- **Database**: Production PostgreSQL container with persistent storage

### Deployment Process
1. **Local Testing**: Always test changes with `docker-compose up --build` locally first
2. **Commit & Push**: Push changes to main branch to trigger GitHub Actions
3. **Automatic Deploy**: GitHub Actions deploys to svrclapp1.cloudwise.ca:8000
4. **Verification**: Test production endpoints to confirm deployment success

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

## Database Management

### Interactive Database Manager
The project includes a comprehensive database management script:
- **`scripts/db_manager.py`**: Interactive database manager for local development
- **`scripts/db_manager_docker.py`**: Docker version for container environments

**Usage:**
```bash
# Local environment
python3 scripts/db_manager.py

# Docker environment (local)
docker exec -it wol-api-backend-1 python3 scripts/db_manager_docker.py

# Docker environment (production server)
docker exec -it wol-api_backend_1 python3 scripts/db_manager_docker.py
```

**Features:**
1. **Setup Database**: Creates tables and populates with verse data from `data/verses.json`
2. **Delete Database**: Safely removes all tables and data (with confirmation)
3. **Run Custom Query**: Execute SQL queries with safety checks and formatted output

### Scraping Scripts

The project includes Python scraping scripts in the `scripts/` directory:
- **`scrape_with_study_notes_docker.py`**: Main scraper for verses and study content (Docker version)
- **`scrape_with_study_notes.py`**: Local version of the main scraper
- **`scrape_research_guide_only.py`**: Specialized scraper for research guide content
- **`setup_db.py`** and **`setup_study_db.py`**: Database setup utilities (legacy)

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

## Quick Reference

### Essential Commands
```bash
# Local development
docker-compose up --build

# Database management (local)
docker exec -it wol-api-backend-1 python3 scripts/db_manager_docker.py

# Database management (production)
docker exec -it wol-api_backend_1 python3 scripts/db_manager_docker.py

# Test API locally
curl "http://localhost:8000/api/v1/study/40/24/14?fields=verse.verse_text,study_content.study_articles&limit=5"

# Test API production  
curl "http://svrclapp1.cloudwise.ca:8000/api/v1/study/40/24/14?fields=verse.verse_text,study_content.study_articles&limit=5"
```

### Key API Parameters Summary
- **Path**: `book/chapter/verse` (all integers)
- **fields**: Comma-separated field list for JSON filtering
- **limit**: Maximum items for arrays
- **fetch**: `true` forces fresh scraping (~10-15s), `false`/omitted uses cache (~200ms)

### Environment URLs
- **Local**: `http://localhost:8000`
- **Production**: `http://svrclapp1.cloudwise.ca:8000`

### Container Names
- **Local**: `wol-api-backend-1`, `wol-api-db-1`
- **Production**: `wol-api_backend_1`, `wol-api_db_1`