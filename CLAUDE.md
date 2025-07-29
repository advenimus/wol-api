# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Rust-based API that serves Bible verses from the Watchtower Online Library (wol.jw.org). The API is built with Rocket framework and uses PostgreSQL for data storage.

## Architecture

The backend follows a layered architecture:

- **Routes** (`backend/src/routes/`): HTTP endpoints, currently only `/api/v1/verse/<book>/<chapter>/<verse>`
- **Services** (`backend/src/services/`): Business logic for verse retrieval
- **Models** (`backend/src/models/`): Data structures, primarily `BibleVerse` with sqlx derive macros
- **Guards** (`backend/src/guards/`): Request guards like `DbGuard` for database connection management

The main application entry point is `backend/src/main.rs` which initializes the Rocket server and PostgreSQL connection pool using sqlx.

## Development Commands

### Backend (Rust)
- **Build**: `cargo build` (from `backend/` directory)
- **Run**: `cargo run` (from `backend/` directory) 
- **Test**: `cargo test` (from `backend/` directory)
- **Format**: `cargo fmt` (rustfmt.toml config available)

### Docker Development
- **Start services**: `docker-compose up`
- **Database**: PostgreSQL runs on port 5432, API on port 8000
- **Database connection**: `postgresql://postgres:postgres@localhost:5432/postgres`

## Database

Uses PostgreSQL with a `verses` table containing:
- `book_num` (i32): Book number
- `book_name` (String): Book name  
- `chapter` (i32): Chapter number
- `verse_num` (i32): Verse number
- `verse_text` (String): The actual verse content

## Key Dependencies

- **Rocket**: Web framework (version 0.5.0-rc.3)
- **sqlx**: Database access with PostgreSQL support
- **serde**: Serialization support

## Testing

Currently has basic integration tests in `backend/src/test_home.rs`. Tests use Rocket's testing client to verify endpoints.