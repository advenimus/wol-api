#!/usr/bin/env python3
import json
import psycopg2
from psycopg2.extras import execute_values

def setup_database():
    # Database connection
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="wol-api",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    
    # Create table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS verses (
            book_num INTEGER NOT NULL,
            book_name VARCHAR NOT NULL,
            chapter INTEGER NOT NULL,
            verse_num INTEGER NOT NULL,
            verse_text TEXT NOT NULL
        );
    """)
    
    # Load verses data
    with open('../data/verses.json', 'r') as f:
        data = json.load(f)
    
    # Prepare data for insertion
    verse_records = []
    book_names = {
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
    
    for chapter_data in data['data']:
        book_num = chapter_data['book']
        chapter_num = chapter_data['chapter']
        book_name = book_names.get(book_num, f"Book {book_num}")
        
        for verse_num, verse_text in chapter_data['verses'].items():
            verse_records.append((book_num, book_name, chapter_num, int(verse_num), verse_text))
    
    # Insert data
    execute_values(
        cur,
        "INSERT INTO verses (book_num, book_name, chapter, verse_num, verse_text) VALUES %s",
        verse_records,
        template=None,
        page_size=100
    )
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Database setup complete! Inserted {len(verse_records)} verses.")

if __name__ == "__main__":
    setup_database()