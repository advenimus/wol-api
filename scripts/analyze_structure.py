#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def analyze_structure():
    """Analyze the full structure to find research guide items"""
    url = "https://wol.jw.org/en/wol/b/r1/lp-e/nwtsty/1/1#study=discover"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("=== Full Structure Analysis ===\n")
    
    # Find the studyDiscover section
    study_discover = soup.find(id='studyDiscover')
    if not study_discover:
        print("No #studyDiscover section found")
        return
    
    print("Found #studyDiscover section\n")
    
    # Look for any elements with 'ref-rsg' class
    ref_rsg_items = study_discover.find_all(class_='ref-rsg')
    print(f"Found {len(ref_rsg_items)} elements with 'ref-rsg' class")
    
    if ref_rsg_items:
        for i, item in enumerate(ref_rsg_items[:3]):  # Show first 3
            print(f"\nref-rsg item {i+1}:")
            print(f"Classes: {item.get('class')}")
            print(f"Tag: {item.name}")
            print(f"Text: {item.get_text(strip=True)[:100]}...")
            
            # Find links in this item
            links = item.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                print(f"  Link: {text} -> {href}")
    
    # Also look for any 'selected' sections
    selected_sections = study_discover.find_all(class_='selected')
    print(f"\nFound {len(selected_sections)} elements with 'selected' class")
    
    # Look for 'section' divs
    section_divs = study_discover.find_all('div', class_='section')
    print(f"Found {len(section_divs)} div.section elements")
    
    for i, section in enumerate(section_divs):
        classes = section.get('class', [])
        print(f"  Section {i+1} classes: {classes}")
        
        # Check if it has selected class or becomes selected
        if 'selected' in classes:
            print(f"    This section is selected!")
            
            # Look for research guide items in this section
            rsg_items = section.find_all(class_='ref-rsg')
            print(f"    Found {len(rsg_items)} ref-rsg items in this section")

if __name__ == "__main__":
    analyze_structure()