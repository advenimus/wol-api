#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import re
from tqdm import tqdm

class StudyContentExtractor:
    def __init__(self):
        self.session = requests.Session()
    
    def extract_study_content_for_chapter(self, book_num, chapter_num):
        """Extract study content for a specific chapter"""
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
                'study_articles': self.extract_study_articles(study_discover),
                'cross_references': self.extract_cross_references(study_discover)
            }
            
            return study_data
            
        except Exception as e:
            print(f"Error extracting study content for {book_num}:{chapter_num} - {e}")
            return None
    
    def extract_outline(self, study_section):
        """Extract chapter outline"""
        outline_data = []
        
        # Look for outline sections
        outline_sections = study_section.find_all('div', class_='summaryOutline')
        
        for section in outline_sections:
            outline_items = section.find_all('li')
            for item in outline_items:
                text = item.get_text(strip=True)
                if text:
                    outline_data.append(text)
        
        return outline_data
    
    def extract_study_articles(self, study_section):
        """Extract links to study articles"""
        articles = []
        
        # Look for article links in various sections
        sections = study_section.find_all('div', class_=['section', 'group'])
        
        for section in sections:
            # Find all links that might be study articles
            links = section.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # Filter for study-related content
                if href and ('/wol/' in href or href.startswith('/')):
                    # Make absolute URL if relative
                    if href.startswith('/'):
                        href = 'https://wol.jw.org' + href
                    
                    if text and len(text) > 5:  # Meaningful text
                        articles.append({
                            'title': text,
                            'url': href,
                            'type': self.classify_article_type(href, text)
                        })
        
        return articles
    
    def extract_cross_references(self, study_section):
        """Extract cross-references"""
        cross_refs = []
        
        # Look for cross-reference sections
        ref_sections = study_section.find_all('div', class_=['crossReferences', 'references'])
        
        for section in ref_sections:
            refs = section.find_all('a', href=True)
            for ref in refs:
                href = ref.get('href')
                text = ref.get_text(strip=True)
                
                if href and text:
                    cross_refs.append({
                        'reference': text,
                        'url': href if href.startswith('http') else 'https://wol.jw.org' + href
                    })
        
        return cross_refs
    
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

def main():
    extractor = StudyContentExtractor()
    
    # Test with Genesis 1 first
    print("Testing with Genesis 1...")
    study_data = extractor.extract_study_content_for_chapter(1, 1)
    
    if study_data:
        print(f"Found study content for Genesis 1:")
        print(f"- Outline items: {len(study_data['outline'])}")
        print(f"- Study articles: {len(study_data['study_articles'])}")
        print(f"- Cross references: {len(study_data['cross_references'])}")
        
        # Show sample data
        if study_data['outline']:
            print(f"\nSample outline items:")
            for item in study_data['outline'][:3]:
                print(f"  - {item}")
        
        if study_data['study_articles']:
            print(f"\nSample study articles:")
            for article in study_data['study_articles'][:3]:
                print(f"  - {article['title']} ({article['type']})")
                print(f"    {article['url']}")
        
        # Save to file
        with open('sample_study_content.json', 'w') as f:
            json.dump(study_data, f, indent=2)
        
        print(f"\nSaved sample data to sample_study_content.json")
    else:
        print("No study content found")

if __name__ == "__main__":
    main()