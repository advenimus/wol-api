#!/usr/bin/env python3
"""
Enhanced scraping service that extracts both study content and verse-specific study notes
"""
import requests
from bs4 import BeautifulSoup
import json
import psycopg2
from psycopg2.extras import Json
import sys

class EnhancedStudyExtractor:
    def __init__(self):
        self.session = requests.Session()
    
    def extract_chapter_content(self, book_num, chapter_num):
        """Extract study content and study notes for a chapter"""
        url = f"https://wol.jw.org/en/wol/b/r1/lp-e/nwtsty/{book_num}/{chapter_num}#study=discover"
        
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                return None, []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the studyDiscover section for chapter-level content
            study_discover = soup.find(id='studyDiscover')
            chapter_study_data = None
            
            if study_discover:
                chapter_study_data = {
                    'book_num': book_num,
                    'chapter_num': chapter_num,
                    'outline': self.extract_outline(study_discover),
                    'study_articles': self.extract_research_guide_articles(study_discover),
                    'cross_references': []
                }
            
            # Extract verse-specific study notes
            verse_study_notes = self.extract_verse_study_notes(soup, book_num, chapter_num)
            
            return chapter_study_data, verse_study_notes
            
        except Exception as e:
            print(f"Error extracting content for {book_num}:{chapter_num} - {e}")
            return None, []
    
    def extract_verse_study_notes(self, soup, book_num, chapter_num):
        """Extract study notes for individual verses"""
        verse_notes = []
        
        # Find all sections with verse-specific study notes
        sections = soup.find_all('div', class_='section')
        
        for section in sections:
            # Get verse reference from data-key attribute
            data_key = section.get('data-key')
            if not data_key:
                continue
            
            # Parse data-key to extract verse number (format: book-chapter-verse)
            try:
                parts = data_key.split('-')
                if len(parts) >= 3:
                    section_book = int(parts[0])
                    section_chapter = int(parts[1])
                    section_verse = int(parts[2])
                    
                    # Only process if it matches our target book/chapter
                    if section_book == book_num and section_chapter == chapter_num:
                        # Look for study note groups
                        study_note_groups = section.find_all('div', class_='studyNoteGroup')
                        
                        if study_note_groups:
                            study_notes = []
                            
                            for group in study_note_groups:
                                # Find individual study notes
                                notes = group.find_all('li', class_='item studyNote')
                                
                                for note in notes:
                                    # Extract paragraphs within the study note
                                    paragraphs = note.find_all('p')
                                    note_content = []
                                    
                                    for p in paragraphs:
                                        # Get text content and preserve links
                                        p_text = p.get_text(strip=True)
                                        if p_text:
                                            # Extract any links within the paragraph
                                            links = []
                                            for link in p.find_all('a', href=True):
                                                href = link.get('href')
                                                link_text = link.get_text(strip=True)
                                                if href and link_text:
                                                    if href.startswith('/'):
                                                        href = 'https://wol.jw.org' + href
                                                    links.append({
                                                        'text': link_text,
                                                        'url': href
                                                    })
                                            
                                            note_content.append({
                                                'text': p_text,
                                                'links': links
                                            })
                                    
                                    if note_content:
                                        study_notes.append({
                                            'content': note_content
                                        })
                            
                            if study_notes:
                                verse_notes.append({
                                    'book_num': section_book,
                                    'chapter_num': section_chapter,
                                    'verse_num': section_verse,
                                    'study_notes': study_notes
                                })
            
            except (ValueError, IndexError):
                # Skip sections with invalid data-key format
                continue
        
        return verse_notes
    
    def extract_outline(self, study_section):
        """Extract chapter outline"""
        outline_data = []
        outline_sections = study_section.find_all('div', class_='summaryOutline')
        
        for section in outline_sections:
            outline_items = section.find_all('li')
            for item in outline_items:
                text = item.get_text(strip=True)
                if text:
                    outline_data.append(text)
        
        return outline_data
    
    def extract_research_guide_articles(self, study_section):
        """Extract ONLY research guide articles with class 'item ref-rsg'"""
        articles = []
        research_guide_items = study_section.find_all('li', class_='item ref-rsg')
        
        for item in research_guide_items:
            links = item.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if href and text and len(text) > 3:
                    if href.startswith('/'):
                        href = 'https://wol.jw.org' + href
                    
                    articles.append({
                        'title': text,
                        'url': href,
                        'type': self.classify_article_type(href, text)
                    })
        
        return articles
    
    def classify_article_type(self, url, title):
        """Classify the type of study article"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if 'watchtower' in url_lower or 'watchtower' in title_lower:
            return 'watchtower'
        elif 'awake' in url_lower or 'awake' in title_lower:
            return 'awake'
        elif 'study' in url_lower or 'study' in title_lower:
            return 'study_article'
        elif 'publication' in url_lower:
            return 'publication'
        else:
            return 'other'

def scrape_and_store_enhanced_content(book_num, chapter_num):
    """Scrape and store both study content and verse study notes"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="wol-api",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        
        extractor = EnhancedStudyExtractor()
        
        print(f"Scraping enhanced content for book {book_num}, chapter {chapter_num}...")
        chapter_study_data, verse_study_notes = extractor.extract_chapter_content(book_num, chapter_num)
        
        # Store chapter-level study content
        if chapter_study_data:
            # Check if already exists
            cur.execute("SELECT id FROM study_content WHERE book_num = %s AND chapter = %s", (book_num, chapter_num))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO study_content (book_num, chapter, outline, study_articles, cross_references)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    chapter_study_data['book_num'],
                    chapter_study_data['chapter_num'],
                    chapter_study_data['outline'],
                    Json(chapter_study_data['study_articles']),
                    Json(chapter_study_data['cross_references'])
                ))
        
        # Store verse-level study notes
        study_notes_updated = 0
        for verse_data in verse_study_notes:
            cur.execute("""
                UPDATE verses 
                SET study_notes = %s 
                WHERE book_num = %s AND chapter = %s AND verse_num = %s
            """, (
                Json(verse_data['study_notes']),
                verse_data['book_num'],
                verse_data['chapter_num'],
                verse_data['verse_num']
            ))
            study_notes_updated += cur.rowcount
        
        conn.commit()
        
        print(f"Successfully stored:")
        if chapter_study_data:
            print(f"  - Chapter study content: {len(chapter_study_data['study_articles'])} articles")
        print(f"  - Verse study notes: {study_notes_updated} verses updated")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error scraping and storing enhanced content: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 scrape_with_study_notes.py <book_num> <chapter_num>")
        sys.exit(1)
    
    book_num = int(sys.argv[1])
    chapter_num = int(sys.argv[2])
    
    success = scrape_and_store_enhanced_content(book_num, chapter_num)
    sys.exit(0 if success else 1)