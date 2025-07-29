#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def analyze_study_notes():
    """Analyze study notes structure for Matthew 24:14"""
    url = "https://wol.jw.org/en/wol/b/r1/lp-e/nwtsty/40/24#study=discover"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("=== Analyzing Study Notes for Matthew 24 ===\n")
    
    # Find sections with study notes
    sections = soup.find_all('div', class_='section')
    
    for i, section in enumerate(sections):
        # Check if this section has study notes
        study_note_groups = section.find_all('div', class_='studyNoteGroup')
        
        if study_note_groups:
            # Get the verse reference from data attributes or title
            verse_ref = section.get('data-key', 'Unknown')
            title_elem = section.find('h3', class_='title')
            title = title_elem.get_text(strip=True) if title_elem else 'No title'
            
            print(f"Section {i+1}: {title} (data-key: {verse_ref})")
            
            for j, study_group in enumerate(study_note_groups):
                print(f"  Study Note Group {j+1}:")
                
                # Find study note items
                study_notes = study_group.find_all('li', class_='item studyNote')
                print(f"    Found {len(study_notes)} study notes")
                
                for k, note in enumerate(study_notes):
                    # Extract the text content
                    text = note.get_text(strip=True)
                    print(f"      Note {k+1}: {text[:100]}{'...' if len(text) > 100 else ''}")
                    
                    # Look for specific elements within the note
                    paragraphs = note.find_all('p')
                    for p_idx, p in enumerate(paragraphs):
                        p_text = p.get_text(strip=True)
                        if p_text:
                            print(f"        Paragraph {p_idx+1}: {p_text[:80]}{'...' if len(p_text) > 80 else ''}")
            
            print()

if __name__ == "__main__":
    analyze_study_notes()