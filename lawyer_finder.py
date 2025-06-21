# eb1_visa_lawyer_finder.py
# This script reads the scraped immigration lawyers CSV and checks their profiles for EB-1 expertise

import csv
import requests
from bs4 import BeautifulSoup
import time
import re

def check_eb1_expertise(profile_url):
    """
    Check if a lawyer's profile mentions EB-1 visa expertise.
    
    Args:
        profile_url (str): URL of the lawyer's profile
        
    Returns:
        dict: Contains EB-1 related information found on the profile
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
        
        response = requests.get(profile_url, headers=headers)
        if response.status_code != 200:
            return {'has_eb1': False, 'details': 'Could not access profile'}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Search for EB-1 mentions in the profile
        eb1_patterns = [
            r'EB-?1', r'EB-?1[ABC]?', r'extraordinary ability', r'outstanding professor',
            r'outstanding researcher', r'multinational manager', r'multinational executive',
            r'first preference', r'employment.{0,20}first.{0,20}preference'
        ]
        
        # Compile regex pattern
        pattern = re.compile('|'.join(eb1_patterns), re.IGNORECASE)
        
        # Check different sections of the profile
        eb1_mentions = []
        
        # Check practice areas
        practice_areas = soup.find_all(['div', 'section'], class_=lambda x: x and 'practice' in str(x).lower())
        for area in practice_areas:
            text = area.get_text()
            if pattern.search(text):
                eb1_mentions.append(f"Practice area: {text[:200]}...")
        
        # Check biography/about section
        bio_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(word in str(x).lower() for word in ['bio', 'about', 'description']))
        for bio in bio_sections:
            text = bio.get_text()
            matches = pattern.findall(text)
            if matches:
                # Get context around the match
                for match in matches[:3]:  # Limit to first 3 matches
                    idx = text.lower().find(match.lower())
                    context = text[max(0, idx-50):idx+50]
                    eb1_mentions.append(f"Bio mention: ...{context}...")
        
        # Check if they list specific visa types
        visa_sections = soup.find_all(string=pattern)
        for visa_text in visa_sections[:5]:  # Limit to first 5 mentions
            if len(visa_text) > 20:  # Only include substantial text
                eb1_mentions.append(f"Visa expertise: {visa_text[:100]}...")
        
        return {
            'has_eb1': len(eb1_mentions) > 0,
            'mentions': eb1_mentions,
            'mention_count': len(eb1_mentions)
        }
        
    except Exception as e:
        return {'has_eb1': False, 'details': f'Error checking profile: {str(e)}'}


def find_eb1_lawyers(csv_filename='lawyers_5_pages.csv', output_filename='eb1_lawyers.csv'):
    """
    Read the scraped lawyers CSV and identify those with EB-1 expertise.
    
    Args:
        csv_filename (str): Input CSV file with lawyer data
        output_filename (str): Output CSV file for EB-1 specialists
    """
    eb1_lawyers = []
    
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        lawyers = list(reader)
        
        print(f"Checking {len(lawyers)} lawyers for EB-1 expertise...")
        
        for idx, lawyer in enumerate(lawyers):
            # Skip invalid entries
            if lawyer['Name'] == 'Name not found' or not lawyer['Profile Link'].startswith('http'):
                continue
            
            print(f"Checking {idx+1}/{len(lawyers)}: {lawyer['Name']}...")
            
            # Check their profile for EB-1 expertise
            eb1_info = check_eb1_expertise(lawyer['Profile Link'])
            
            if eb1_info['has_eb1']:
                lawyer['EB-1 Expertise'] = 'Yes'
                lawyer['EB-1 Details'] = '; '.join(eb1_info['mentions'][:3])  # Include first 3 mentions
                lawyer['Mention Count'] = eb1_info['mention_count']
                eb1_lawyers.append(lawyer)
                print(f"  ✓ Found EB-1 expertise! ({eb1_info['mention_count']} mentions)")
            
            # Be respectful to the server
            time.sleep(1)
            
            # Optional: Stop after finding a certain number
            if len(eb1_lawyers) >= 20:
                print("\nFound 20 EB-1 lawyers. Stopping search.")
                break
    
    # Save EB-1 lawyers to new CSV
    if eb1_lawyers:
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'Profile Link', 'Location', 'Avvo Rating', 'EB-1 Expertise', 'Mention Count', 'EB-1 Details']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for lawyer in eb1_lawyers:
                writer.writerow({
                    'Name': lawyer['Name'],
                    'Profile Link': lawyer['Profile Link'],
                    'Location': lawyer['Location'],
                    'Avvo Rating': lawyer['Avvo Rating'],
                    'EB-1 Expertise': lawyer['EB-1 Expertise'],
                    'Mention Count': lawyer['Mention Count'],
                    'EB-1 Details': lawyer['EB-1 Details'][:200]  # Limit details length
                })
        
        print(f"\nFound {len(eb1_lawyers)} lawyers with EB-1 expertise!")
        print(f"Results saved to {output_filename}")
    else:
        print("\nNo lawyers with EB-1 expertise found in the current list.")
        print("Try searching for more immigration lawyers or in different locations.")
    
    return eb1_lawyers


# Example: Quick check for EB-1 keywords in a list of lawyers
def quick_eb1_filter(csv_filename='lawyers.csv'):
    """
    Quickly filter lawyers whose snippets might mention EB-1 related terms.
    This is faster but less accurate than checking full profiles.
    """
    potential_eb1_lawyers = []
    
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for lawyer in reader:
            # Check if snippet contains EB-1 related keywords
            snippet = lawyer.get('Details Snippet', '').lower()
            if any(keyword in snippet for keyword in ['eb-1', 'eb1', 'extraordinary', 'multinational']):
                potential_eb1_lawyers.append(lawyer)
                print(f"Potential EB-1 lawyer: {lawyer['Name']}")
    
    return potential_eb1_lawyers


if __name__ == "__main__":
    # First, try quick filtering based on snippets
    print("Quick scan for potential EB-1 lawyers...")
    quick_results = quick_eb1_filter('lawyers_5_pages.csv')
    
    if quick_results:
        print(f"\nFound {len(quick_results)} potential EB-1 lawyers in snippets.")
    
    # Then do detailed profile checking
    print("\n" + "="*50)
    print("Starting detailed EB-1 expertise check...")
    print("="*50 + "\n")
    
    eb1_specialists = find_eb1_lawyers('lawyers_5_pages.csv', 'eb1_lawyers.csv')