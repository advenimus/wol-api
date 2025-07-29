#!/usr/bin/env python3
"""
WOL API Database Manager
Interactive script for managing the WOL API database with safety confirmations.
"""
import json
import psycopg2
from psycopg2.extras import execute_values
import sys
import os
from typing import Optional

class DatabaseManager:
    def __init__(self, host="localhost", port=5432, database="wol-api", user="postgres", password="postgres"):
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        self.conn: Optional[psycopg2.connection] = None
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            return True
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def get_confirmation(self, message: str, danger_level: str = "normal") -> bool:
        """Get user confirmation with different danger levels"""
        danger_colors = {
            "normal": "\033[33m",    # Yellow
            "high": "\033[31m",      # Red
            "critical": "\033[91m"   # Bright Red
        }
        reset_color = "\033[0m"
        
        color = danger_colors.get(danger_level, danger_colors["normal"])
        print(f"\n{color}⚠️  {message}{reset_color}")
        
        if danger_level == "critical":
            print("This action is IRREVERSIBLE and will permanently delete data!")
            confirmation = input("Type 'DELETE EVERYTHING' to confirm: ").strip()
            return confirmation == "DELETE EVERYTHING"
        else:
            confirmation = input("Continue? (y/N): ").strip().lower()
            return confirmation in ['y', 'yes']
    
    def setup_database(self):
        """Setup database with tables and initial data"""
        print("\n🔧 Setting up WOL API Database...")
        
        if not self.get_confirmation("This will create tables and populate with verse data"):
            print("❌ Database setup cancelled.")
            return
        
        try:
            cur = self.conn.cursor()
            
            # Create tables
            print("📋 Creating database tables...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS verses (
                    book_num INTEGER NOT NULL,
                    book_name TEXT NOT NULL,
                    chapter INTEGER NOT NULL,
                    verse_num INTEGER NOT NULL,
                    verse_text TEXT NOT NULL,
                    study_notes JSONB,
                    UNIQUE(book_num, chapter, verse_num)
                );
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS study_content (
                    id SERIAL PRIMARY KEY,
                    book_num INTEGER NOT NULL,
                    chapter INTEGER NOT NULL,
                    outline TEXT[],
                    study_articles JSONB,
                    cross_references JSONB,
                    UNIQUE(book_num, chapter)
                );
            """)
            
            print("✅ Tables created successfully.")
            
            # Load and insert verse data
            verses_file = self._find_verses_file()
            if not verses_file:
                print("❌ Could not find verses.json file.")
                return
                
            print(f"📖 Loading verses from {verses_file}...")
            with open(verses_file, 'r') as f:
                data = json.load(f)
            
            # Prepare verse records
            verse_records = []
            book_names = self._get_book_names()
            
            for chapter_data in data['data']:
                book_num = chapter_data['book']
                chapter_num = chapter_data['chapter']
                book_name = book_names.get(book_num, f"Book {book_num}")
                
                for verse_num, verse_text in chapter_data['verses'].items():
                    verse_records.append((book_num, book_name, chapter_num, int(verse_num), verse_text))
            
            # Insert verses in batches
            print(f"💾 Inserting {len(verse_records)} verses...")
            execute_values(
                cur,
                "INSERT INTO verses (book_num, book_name, chapter, verse_num, verse_text) VALUES %s ON CONFLICT DO NOTHING",
                verse_records,
                template=None,
                page_size=1000
            )
            
            self.conn.commit()
            
            # Get final counts
            cur.execute("SELECT COUNT(*) FROM verses")
            verse_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM study_content")
            study_count = cur.fetchone()[0]
            
            print(f"✅ Database setup complete!")
            print(f"   📖 Verses: {verse_count:,}")
            print(f"   📚 Study content: {study_count:,}")
            
            cur.close()
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            if self.conn:
                self.conn.rollback()
    
    def delete_database(self):
        """Delete all database tables and data"""
        print("\n🗑️  Database Deletion")
        
        if not self.get_confirmation(
            "This will permanently delete ALL database tables and data", 
            "critical"
        ):
            print("❌ Database deletion cancelled.")
            return
        
        try:
            cur = self.conn.cursor()
            
            print("🗑️  Dropping tables...")
            cur.execute("DROP TABLE IF EXISTS study_content CASCADE;")
            cur.execute("DROP TABLE IF EXISTS verses CASCADE;")
            
            self.conn.commit()
            cur.close()
            
            print("✅ Database tables deleted successfully.")
            
        except Exception as e:
            print(f"❌ Database deletion failed: {e}")
            if self.conn:
                self.conn.rollback()
    
    def run_custom_query(self):
        """Execute a custom SQL query"""
        print("\n🔍 Custom SQL Query")
        print("Enter your SQL query (type 'EXIT' to cancel):")
        print("Examples:")
        print("  SELECT COUNT(*) FROM verses;")
        print("  SELECT book_name, COUNT(*) FROM verses GROUP BY book_name LIMIT 5;")
        print("  SELECT * FROM verses WHERE book_num = 40 AND chapter = 24 LIMIT 3;")
        
        query_lines = []
        while True:
            line = input("SQL> " if not query_lines else "  -> ").strip()
            if line.upper() == 'EXIT':
                print("❌ Query cancelled.")
                return
            
            query_lines.append(line)
            
            # Check if query seems complete (ends with semicolon)
            if line.endswith(';'):
                break
        
        query = ' '.join(query_lines)
        
        if not query.strip():
            print("❌ No query provided.")
            return
        
        # Safety check for destructive operations
        query_upper = query.upper()
        if any(dangerous in query_upper for dangerous in ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']):
            if not self.get_confirmation(
                f"This query contains potentially destructive operations: {query}", 
                "high"
            ):
                print("❌ Query cancelled.")
                return
        
        try:
            cur = self.conn.cursor()
            
            print(f"\n🔍 Executing: {query}")
            cur.execute(query)
            
            # Handle different query types
            if query_upper.strip().startswith('SELECT'):
                results = cur.fetchall()
                if results:
                    # Get column names
                    columns = [desc[0] for desc in cur.description]
                    
                    # Print results in a table format
                    print(f"\n📊 Results ({len(results)} rows):")
                    print("-" * 80)
                    
                    # Print header
                    header = " | ".join(f"{col:<15}" for col in columns)
                    print(header)
                    print("-" * len(header))
                    
                    # Print rows (limit to first 50 for readability)
                    for i, row in enumerate(results[:50]):
                        row_str = " | ".join(f"{str(val):<15}" for val in row)
                        print(row_str)
                    
                    if len(results) > 50:
                        print(f"... and {len(results) - 50} more rows")
                else:
                    print("📊 No results returned.")
            else:
                # For non-SELECT queries, show affected rows
                affected = cur.rowcount
                print(f"✅ Query executed successfully. Rows affected: {affected}")
                self.conn.commit()
            
            cur.close()
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            if self.conn:
                self.conn.rollback()
    
    def _find_verses_file(self) -> Optional[str]:
        """Find the verses.json file in common locations"""
        possible_paths = [
            "data/verses.json",
            "../data/verses.json",
            "verses.json",
            "/home/appuser/verses.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _get_book_names(self) -> dict:
        """Get mapping of book numbers to names"""
        return {
            1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
            6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
            11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles", 
            15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms", 
            20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
            24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
            28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah",
            33: "Micah", 34: "Nahum", 35: "Habakkuk", 36: "Zephaniah", 37: "Haggai",
            38: "Zechariah", 39: "Malachi", 40: "Matthew", 41: "Mark", 42: "Luke",
            43: "John", 44: "Acts", 45: "Romans", 46: "1 Corinthians", 47: "2 Corinthians",
            48: "Galatians", 49: "Ephesians", 50: "Philippians", 51: "Colossians",
            52: "1 Thessalonians", 53: "2 Thessalonians", 54: "1 Timothy", 55: "2 Timothy",
            56: "Titus", 57: "Philemon", 58: "Hebrews", 59: "James", 60: "1 Peter",
            61: "2 Peter", 62: "1 John", 63: "2 John", 64: "3 John", 65: "Jude", 66: "Revelation"
        }

def main():
    print("🗄️  WOL API Database Manager")
    print("=" * 50)
    
    # Determine environment and connection settings
    if len(sys.argv) > 1 and sys.argv[1] == "--docker":
        print("🐳 Docker environment detected")
        db_manager = DatabaseManager(host="db")
    else:
        print("💻 Local environment")
        db_manager = DatabaseManager(host="localhost")
    
    # Test connection
    print("\n🔌 Connecting to database...")
    if not db_manager.connect():
        print("❌ Failed to connect to database. Exiting.")
        sys.exit(1)
    
    print("✅ Connected successfully!")
    
    try:
        while True:
            print("\n" + "=" * 50)
            print("📋 Database Management Options:")
            print("1️⃣  Setup Database (create tables & load data)")
            print("2️⃣  Delete Database (remove all tables & data)")
            print("3️⃣  Run Custom Query (execute SQL)")
            print("4️⃣  Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                db_manager.setup_database()
            elif choice == "2":
                db_manager.delete_database()
            elif choice == "3":
                db_manager.run_custom_query()
            elif choice == "4":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
                
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    main()