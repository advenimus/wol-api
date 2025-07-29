#!/usr/bin/env python3
import psycopg2

def add_study_notes_column():
    """Add study_notes column to verses table"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="wol-api",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        
        # Add study_notes column as JSONB
        cur.execute("""
            ALTER TABLE verses 
            ADD COLUMN IF NOT EXISTS study_notes JSONB;
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("Successfully added study_notes column to verses table")
        
    except Exception as e:
        print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_study_notes_column()