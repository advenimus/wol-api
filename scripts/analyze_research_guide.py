#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def analyze_research_guide():
    """Analyze the specific research guide section structure"""
    url = "https://wol.jw.org/en/wol/b/r1/lp-e/nwtsty/1/1#study=discover"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("=== Analyzing Research Guide Structure ===\n")
    
    # Find the studyDiscover section
    study_discover = soup.find(id='studyDiscover')
    if not study_discover:
        print("No #studyDiscover section found")
        return
    
    print("Found #studyDiscover section\n")
    
    # Look for the specific selector path
    # #studyDiscover > div.section.selected > div.group.index.collapsible > ul > li.item.ref-rsg
    
    # Find div.section.selected
    selected_sections = study_discover.find_all('div', class_='section selected')
    print(f"Found {len(selected_sections)} div.section.selected elements")
    
    for i, section in enumerate(selected_sections):
        print(f"\n--- Section {i+1} ---")
        
        # Look for div.group.index.collapsible
        group_divs = section.find_all('div', class_='group index collapsible')
        print(f"Found {len(group_divs)} div.group.index.collapsible elements")
        
        for j, group in enumerate(group_divs):
            print(f"\n  Group {j+1}:")
            
            # Look for ul elements
            ul_elements = group.find_all('ul')
            print(f"  Found {len(ul_elements)} ul elements")
            
            for k, ul in enumerate(ul_elements):
                print(f"\n    UL {k+1}:")
                
                # Look for li.item.ref-rsg
                research_guide_items = ul.find_all('li', class_='item ref-rsg')
                print(f"    Found {len(research_guide_items)} li.item.ref-rsg elements")
                
                for l, item in enumerate(research_guide_items):
                    print(f"\n      Research Guide Item {l+1}:")
                    
                    # Extract links from this item
                    links = item.find_all('a', href=True)
                    for link in links:
                        href = link.get('href')
                        text = link.get_text(strip=True)
                        print(f"        Link: {text}")
                        print(f"        URL: {href}")
                    
                    # Show the full structure of this item
                    print(f"        Full HTML: {str(item)[:200]}...")

if __name__ == "__main__":
    analyze_research_guide()