#!/usr/bin/env python3
"""
WOL API Database Manager - Docker Version
Interactive script for managing the WOL API database from within Docker containers.
"""
import sys
import os

# Add the parent directory to path so we can import the main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import DatabaseManager

def main():
    print("🐳 WOL API Database Manager (Docker)")
    print("=" * 50)
    
    # Use Docker database host
    db_manager = DatabaseManager(host="db")
    
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