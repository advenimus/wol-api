#!/usr/bin/env python3 
"""
Scraping service for on-demand study content collection
Can be called by the Rust API when study content is missing
"""
import requests
from bs4 import BeautifulSoup
import json
import psycopg2
from psycopg2.extras import Json
import sys

class ResearchGuideExtractor:
    def __init__(self):
        self.session = requests.Session()
    
    def extract_research_guide_for_chapter(self, book_num, chapter_num):
        """Extract only research guide content for a specific chapter"""
        url = f"https://wol.jw.org/en/wol/b/r1/lp-e/nwtsty/{book_num}/{chapter_num}#study=discover"
        
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the studyDiscover section
            study_discover = soup.find(id='studyDiscover')
            if not study_discover:
                return None
            
            study_data = {
                'book_num': book_num,
                'chapter_num': chapter_num,
                'outline': self.extract_outline(study_discover),
                'study_articles': self.extract_research_guide_articles(study_discover),
                'cross_references': []
            }
            
            return study_data
            
        except Exception as e:
            print(f"Error extracting research guide content for {book_num}:{chapter_num} - {e}")
            return None
    
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

def scrape_and_store_study_content(book_num, chapter_num):
    """Scrape and store study content for a specific chapter"""
    try:
        # Database connection
        conn = psycopg2.connect(
            host="db",
            port=5432,
            database="wol-api",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        
        extractor = ResearchGuideExtractor()
        
        # Check if already exists
        cur.execute("SELECT id FROM study_content WHERE book_num = %s AND chapter = %s", (book_num, chapter_num))
        if cur.fetchone():
            print(f"Study content already exists for book {book_num}, chapter {chapter_num}")
            cur.close()
            conn.close()
            return True
        
        # Scrape the content
        print(f"Scraping study content for book {book_num}, chapter {chapter_num}...")
        study_data = extractor.extract_research_guide_for_chapter(book_num, chapter_num)
        
        if study_data:
            # Insert into database
            cur.execute("""
                INSERT INTO study_content (book_num, chapter, outline, study_articles, cross_references)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                study_data['book_num'],
                study_data['chapter_num'],
                study_data['outline'],
                Json(study_data['study_articles']),
                Json(study_data['cross_references'])
            ))
            
            conn.commit()
            print(f"Successfully stored study content: {len(study_data['study_articles'])} articles")
            cur.close()
            conn.close()
            return True
        else:
            print("Failed to scrape study content")
            cur.close()
            conn.close()
            return False
            
    except Exception as e:
        print(f"Error scraping and storing: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 scraping_service.py <book_num> <chapter_num>")
        sys.exit(1)
    
    book_num = int(sys.argv[1])
    chapter_num = int(sys.argv[2])
    
    success = scrape_and_store_study_content(book_num, chapter_num)
    sys.exit(0 if success else 1)