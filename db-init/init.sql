-- PostgreSQL initialization script for WOL API
-- This script runs automatically when the database container starts for the first time

-- Create tables if they don't exist
CREATE TABLE IF NOT EXISTS verses (
    book_num INTEGER NOT NULL,
    book_name TEXT NOT NULL, 
    chapter INTEGER NOT NULL,
    verse_num INTEGER NOT NULL,
    verse_text TEXT NOT NULL,
    study_notes JSONB
);

CREATE TABLE IF NOT EXISTS study_content (
    id SERIAL PRIMARY KEY,
    book_num INTEGER NOT NULL,
    chapter INTEGER NOT NULL, 
    outline TEXT[],
    study_articles JSONB,
    cross_references JSONB
);

-- Check if verses table is empty and needs to be populated
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM verses LIMIT 1) THEN
        RAISE NOTICE 'Verses table is empty. Database will need to be populated manually.';
        RAISE NOTICE 'Run: docker exec -it wol-api_backend_1 python3 scripts/db_manager_docker.py';
        RAISE NOTICE 'Then select option 1 to setup database.';
    ELSE
        RAISE NOTICE 'Verses table already contains data. Initialization complete.';
    END IF;
END
$$;