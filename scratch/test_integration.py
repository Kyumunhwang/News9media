"""Integration Test for RSS Fetching.

Runs the fetch_media_rss function from naver_crawler module
for all 9 media IDs to verify the end-to-end extraction.
"""

import sys
import os

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
if project_dir not in sys.path:
    sys.path.append(project_dir)

import naver_crawler as nc

def main():
    media_ids = ["chosun", "donga", "hani", "khan", "maekyung", "hankyung", "yonhapnewstv", "ytn", "ohmynews"]
    
    print("Starting Integration Test for fetch_media_rss...")
    print("=" * 60)
    
    all_passed = True
    
    for media_id in media_ids:
        print(f"Testing media_id: '{media_id}'...")
        res = nc.fetch_media_rss(media_id)
        
        if res["success"]:
            print(f"  [SUCCESS] Name: {res['media_name_ko']} ({res['media_name_en']})")
            print(f"            Fallback Active: {res['fallback_active']}")
            print(f"            Articles Extracted: {len(res['articles'])}")
            if res["articles"]:
                first_art = res["articles"][0]
                print(f"            Sample Article Title: {first_art['title']}")
                print(f"            Sample Article Link: {first_art['link']}")
                print(f"            Sample Article PubDate: {first_art['pub_date']}")
        else:
            print(f"  [FAIL] Failed to fetch. Error: {res['error']}")
            all_passed = False
            
        print("-" * 60)
        
    if all_passed:
        print("\nAll 9 media integration checks PASSED successfully.")
    else:
        print("\nSome media integration checks FAILED. Please review the logs.")

if __name__ == "__main__":
    main()
