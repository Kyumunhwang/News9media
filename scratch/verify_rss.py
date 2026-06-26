"""RSS Verification Script.

Validates the connectivity and XML structures of both primary RSS feeds
and Google News RSS fallback URLs defined in media_rss_index.json.
"""

import os
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

def verify_feed(name: str, url: str, feed_type: str) -> bool:
    """Sends an HTTP GET request to the feed URL and verifies if it returns a valid XML.

    Args:
        name: Name of the media.
        url: The feed URL.
        feed_type: The type of feed ('primary' or 'google_news').

    Returns:
        bool: True if validation succeeds, False otherwise.
    """
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    )
    
    try:
        # Using a 10 seconds timeout to prevent hanging on slow feeds
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            content = response.read()
            
            if status != 200:
                print(f"  [FAIL] {name} ({feed_type}): HTTP Status {status}")
                return False
                
            # Attempt to parse as XML to ensure valid feed format
            try:
                root = ET.fromstring(content)
                # Google News RSS uses <rss>, standard RSS uses <rss> or Atom <feed>
                if root.tag not in ('rss', 'feed', '{http://www.w3.org/2005/Atom}feed'):
                    print(f"  [FAIL] {name} ({feed_type}): Invalid root tag '{root.tag}'")
                    return False
                print(f"  [SUCCESS] {name} ({feed_type}): Connected and XML parsed successfully.")
                return True
            except ET.ParseError as pe:
                print(f"  [FAIL] {name} ({feed_type}): XML parsing error - {pe}")
                return False
                
    except urllib.error.URLError as ue:
        print(f"  [FAIL] {name} ({feed_type}): Connection failed - {ue.reason}")
        return False
    except Exception as e:
        print(f"  [FAIL] {name} ({feed_type}): Unexpected error - {e}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    json_path = os.path.join(project_dir, "media_rss_index.json")
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} does not exist.")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        media_list = json.load(f)
        
    print(f"Starting RSS Feed Verification for {len(media_list)} Media Outlets...")
    print("=" * 60)
    
    success_count = 0
    total_checks = 0
    
    for media in media_list:
        name = media["name_en"]
        primary = media["primary_rss"]
        gnews = media["google_news_rss_url"]
        
        if primary:
            total_checks += 1
            if verify_feed(name, primary, "Primary"):
                success_count += 1
                
        if gnews:
            total_checks += 1
            if verify_feed(name, gnews, "Google News"):
                success_count += 1
                
        print("-" * 60)
        
    print(f"Verification Completed: {success_count}/{total_checks} feeds passed.")

if __name__ == "__main__":
    main()
