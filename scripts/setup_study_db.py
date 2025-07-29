#!/usr/bin/env python3
import json
import psycopg2
from psycopg2.extras import execute_values

def setup_study_database():
    # Database connection
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="wol-api",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    
    # Create study_content table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_content (
            id SERIAL PRIMARY KEY,
            book_num INTEGER NOT NULL,
            chapter INTEGER NOT NULL,
            outline TEXT[],
            study_articles JSONB,
            cross_references JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create index for faster lookups
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_study_content_book_chapter 
        ON study_content (book_num, chapter);
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("Study content database setup complete!")

if __name__ == "__main__":
    setup_study_database()