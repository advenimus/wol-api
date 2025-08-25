#!/usr/bin/env python3
"""
Auto Setup Database Script
Automatically sets up the WOL API database without user interaction.
Used by auto-recovery systems and startup scripts.
"""
import sys
import os

# Add the current directory to path so we can import the db_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_manager_docker import DatabaseManager

def auto_setup():
    """Automatically setup database without user interaction"""
    print("🔧 Auto-setting up WOL API Database...")
    
    # Use Docker database host
    db_manager = DatabaseManager(host="db")
    
    # Test connection
    print("🔌 Connecting to database...")
    if not db_manager.connect():
        print("❌ Failed to connect to database.")
        sys.exit(1)
    
    print("✅ Connected successfully!")
    
    try:
        # Run setup without confirmation
        print("📋 Creating database tables...")
        
        # Import the setup logic from the original script
        cur = db_manager.conn.cursor()
        
        # Create tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS verses (
                book_num INTEGER NOT NULL,
                book_name TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                verse_num INTEGER NOT NULL,
                verse_text TEXT NOT NULL,
                study_notes JSONB
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS study_content (
                id SERIAL PRIMARY KEY,
                book_num INTEGER NOT NULL,
                chapter INTEGER NOT NULL, 
                outline TEXT[],
                study_articles JSONB,
                cross_references JSONB
            );
        """)
        
        db_manager.conn.commit()
        print("✅ Tables created successfully.")
        
        # Check if we need to load data
        cur.execute("SELECT COUNT(*) FROM verses")
        verse_count = cur.fetchone()[0]
        
        if verse_count == 0:
            print("📖 Loading verses from verses.json...")
            
            # Load the verses data
            verses_path = '/home/appuser/data/verses.json'
            if not os.path.exists(verses_path):
                print(f"❌ Verses file not found at {verses_path}")
                return False
                
            import json
            with open(verses_path, 'r') as f:
                verses_data = json.load(f)
            
            print(f"💾 Inserting {len(verses_data)} verses...")
            
            # Insert verses one by one to match the original format
            insert_query = """
                INSERT INTO verses (book_num, book_name, chapter, verse_num, verse_text, study_notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            for i, verse in enumerate(verses_data):
                cur.execute(insert_query, (
                    verse['book_num'],
                    verse['book_name'], 
                    verse['chapter'],
                    verse['verse_num'],
                    verse['verse_text'],
                    None  # study_notes initially null
                ))
                
                if (i + 1) % 1000 == 0:
                    print(f"📖 Inserted {i + 1} verses...")
                
            db_manager.conn.commit()
            print(f"✅ Database setup complete! Loaded {len(verses_data):,} verses.")
        else:
            print(f"✅ Database already contains {verse_count:,} verses.")
            
        cur.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        if db_manager.conn:
            db_manager.conn.rollback()
        return False
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    success = auto_setup()
    sys.exit(0 if success else 1)
