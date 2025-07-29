#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_study_articles_static():
    """Test with static HTML parsing"""
    url = "https://wol.jw.org/en/wol/b/r1/lp-e/nwtsty/1/1#study=discover"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("=== Static HTML Analysis ===")
    
    # Look for studyDiscover section
    study_discover = soup.find(id='studyDiscover')
    if study_discover:
        print("Found #studyDiscover section")
        print(study_discover.prettify()[:500] + "...")
    else:
        print("No #studyDiscover section found")
    
    # Look for any study-related divs
    study_divs = soup.find_all('div', class_=lambda x: x and 'study' in x.lower())
    print(f"Found {len(study_divs)} divs with 'study' in class name")
    
    # Look for article links
    article_links = soup.find_all('a', href=lambda x: x and '/wol/' in x and 'study' in x)
    print(f"Found {len(article_links)} potential study article links")
    
    return len(article_links) > 0

def test_study_articles_dynamic():
    """Test with Selenium to handle JavaScript"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://wol.jw.org/en/wol/b/r1/lp-e/nwtsty/1/1#study=discover")
        
        # Wait for page to load
        time.sleep(5)
        
        print("\n=== Dynamic HTML Analysis ===")
        
        # Look for studyDiscover section after JS loads
        try:
            study_discover = driver.find_element(By.ID, 'studyDiscover')
            print("Found #studyDiscover section with Selenium")
            
            # Look for study articles within
            study_links = study_discover.find_elements(By.TAG_NAME, 'a')
            print(f"Found {len(study_links)} links in studyDiscover section")
            
            for i, link in enumerate(study_links[:5]):  # Show first 5
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    print(f"  Link {i+1}: {text} -> {href}")
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"No #studyDiscover section found with Selenium: {e}")
            
        # Look for any study-related content
        study_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="study"], [id*="study"]')
        print(f"Found {len(study_elements)} elements with 'study' in class/id")
        
        driver.quit()
        return len(study_elements) > 0
        
    except Exception as e:
        print(f"Selenium test failed: {e}")
        return False

if __name__ == "__main__":
    static_found = test_study_articles_static()
    
    try:
        dynamic_found = test_study_articles_dynamic()
    except:
        print("Selenium not available, skipping dynamic test")
        dynamic_found = False
    
    print(f"\nResults:")
    print(f"Static parsing found study content: {static_found}")
    print(f"Dynamic parsing found study content: {dynamic_found}")