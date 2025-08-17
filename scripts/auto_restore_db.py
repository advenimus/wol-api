#!/usr/bin/env python3
"""
Auto Database Restore Script
Automatically restores the WOL API database if tables are missing or empty.
This script runs periodically to ensure database integrity.
"""
import os
import sys
import time
import subprocess
import psycopg2
from psycopg2 import sql

def check_database_health():
    """Check if database tables exist and have data"""
    try:
        conn = psycopg2.connect(
            host="db",
            database="wol-api",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        
        # Check if verses table exists and has data
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'verses'
        """)
        table_exists = cur.fetchone()[0] > 0
        
        if table_exists:
            cur.execute("SELECT COUNT(*) FROM verses")
            verse_count = cur.fetchone()[0]
        else:
            verse_count = 0
            
        cur.close()
        conn.close()
        
        return table_exists, verse_count
        
    except Exception as e:
        print(f"❌ Error checking database health: {e}")
        return False, 0

def restore_database():
    """Restore database using the database manager"""
    try:
        print("🔧 Auto-restoring database...")
        
        # Run the database setup script
        result = subprocess.run([
            "python3", "/home/appuser/scripts/db_manager.py", "--auto-setup"
        ], capture_output=True, text=True, cwd="/home/appuser")
        
        if result.returncode == 0:
            print("✅ Database auto-restored successfully!")
            return True
        else:
            print(f"❌ Database restore failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during database restore: {e}")
        return False

def main():
    """Main auto-restore logic"""
    print("🔍 Checking database health...")
    
    table_exists, verse_count = check_database_health()
    
    if not table_exists:
        print("⚠️  Tables missing! Auto-restoring database...")
        restore_database()
    elif verse_count == 0:
        print("⚠️  Tables exist but empty! Auto-restoring data...")
        restore_database()
    else:
        print(f"✅ Database healthy - {verse_count:,} verses found")

if __name__ == "__main__":
    main()