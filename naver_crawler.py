"""Naver Crawler Backend Module.

Responsible for retrieving real-time data from Naver and media RSS feeds
using python standard libraries (urllib) and BeautifulSoup.
All functions avoid heavy/binary compiled dependencies to ensure compatibility
with hosting environments like Streamlit Community Cloud.
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Default headers to mimic a real browser session
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9"
}

def _http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> bytes:
    """Helper function to perform a clean HTTP GET request using urllib.request."""
    req_headers = headers if headers is not None else DEFAULT_HEADERS
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()

def fetch_naver_main_data() -> Dict[str, Any]:
    """Fetches Naver main page HTML and extracts structured EAGER-DATA.
    
    Returns:
        Dict[str, Any]: A dictionary containing flash news and newsstand publishers.
    """
    result_data = {
        "flash_news": [],
        "publishers": [],
        "success": False,
        "error": None
    }
    
    try:
        content_bytes = _http_get("https://www.naver.com")
        soup = BeautifulSoup(content_bytes, "html.parser")
        scripts = soup.find_all("script")
        
        eager_data_str = None
        for script in scripts:
            content = script.string or ""
            if 'window["EAGER-DATA"]' in content:
                eager_data_str = content
                break
                
        if not eager_data_str:
            result_data["error"] = "Could not find eager-data in script tags."
            return result_data
            
        pattern = r'window\["EAGER-DATA"\]\["([^"]+)"\]\s*=\s*(.*?)(?=;?\s*window\["EAGER-DATA"\]|;?\s*<\/script>|;?\s*$)'
        matches = re.findall(pattern, eager_data_str, re.DOTALL)
        
        eager_data = {}
        for key, val_str in matches:
            val_str = val_str.strip()
            if val_str.endswith(';'):
                val_str = val_str[:-1]
            try:
                eager_data[key] = json.loads(val_str)
            except Exception:
                continue

        yonhap_block = eager_data.get("PC-NEWSSTAND-YONHAP", {})
        materials = yonhap_block.get("materials", [])
        for m in materials:
            if m.get("@type") == "MATERIAL-PC-NEWS-ONELINE" or "title" in m:
                result_data["flash_news"].append({
                    "title": m.get("title", "").strip(),
                    "url": m.get("url", ""),
                    "office": m.get("officeName", "Yonhap News")
                })
                
        media_wrapper = eager_data.get("PC-MEDIA-WRAPPER", {})
        
        def find_press_blocks(node: Any) -> List[Dict[str, Any]]:
            presses = []
            if isinstance(node, dict):
                if node.get("@type") == "PC-NEWSSTAND-PRESS-BLOCK":
                    presses.append({
                        "name": node.get("name", ""),
                        "pid": node.get("pid", ""),
                        "logo_url": node.get("logoLight", {}).get("url", node.get("logoDark", {}).get("url", ""))
                    })
                for k, v in node.items():
                    presses.extend(find_press_blocks(v))
            elif isinstance(node, list):
                for item in node:
                    presses.extend(find_press_blocks(item))
            return presses
            
        found_presses = find_press_blocks(media_wrapper)
        seen = set()
        for p in found_presses:
            if p["name"] and p["name"] not in seen:
                seen.add(p["name"])
                result_data["publishers"].append(p)
                
        result_data["success"] = True
    except Exception as e:
        result_data["error"] = str(e)
        
    return result_data


def fetch_naver_weather() -> Dict[str, Any]:
    """Fetches and parses current weather for Seoul/Korea via Naver Search.
    
    Returns:
        Dict[str, Any]: Dict containing temp, state, and temperature difference.
    """
    result = {
        "temp": "N/A",
        "state": "N/A",
        "comparison": "N/A",
        "humidity": "N/A",
        "dust": "N/A",
        "success": False
    }
    
    try:
        url = "https://search.naver.com/search.naver?query=" + quote("날씨")
        content_bytes = _http_get(url)
        soup = BeautifulSoup(content_bytes, "html.parser")
        
        temp_elem = soup.find("div", class_="temperature_text")
        if temp_elem:
            temp_text = temp_elem.get_text(strip=True)
            match = re.search(r"(-?\d+(?:\.\d+)?)\s*°", temp_text)
            if match:
                result["temp"] = f"{match.group(1)}°C"
            else:
                result["temp"] = temp_text.replace("현재 온도", "").strip()
        
        state_elem = soup.find("span", class_="weather")
        if state_elem:
            result["state"] = state_elem.get_text(strip=True)
            
        comp_elem = soup.find("p", class_="summary")
        if comp_elem:
            comp_text = comp_elem.get_text(strip=True)
            comp_text = " ".join(comp_text.split())
            result["comparison"] = comp_text
            
        dust_infos = []
        for item in soup.find_all("li", class_=lambda c: c and "item_today" in c):
            title = item.find("span", class_="title")
            value = item.find("span", class_="txt")
            if title and value:
                t_str = title.get_text(strip=True)
                v_str = value.get_text(strip=True)
                if "미세먼지" in t_str:
                    dust_infos.append(f"Fine Dust: {v_str}")
                elif "초미세먼지" in t_str:
                    dust_infos.append(f"Ultra Fine: {v_str}")
                elif "습도" in t_str:
                    result["humidity"] = v_str
        if dust_infos:
            result["dust"] = " | ".join(dust_infos)
            
        result["success"] = True
    except Exception as e:
        result["comparison"] = f"Error loading weather: {e}"
        
    return result


def fetch_naver_finance() -> List[Dict[str, Any]]:
    """Calls Naver's domestic index API to retrieve live stock market metrics.
    
    Returns:
        List[Dict[str, Any]]: List of index dicts for KOSPI and KOSDAQ.
    """
    url = "https://polling.finance.naver.com/api/realtime/domestic/index/KOSPI,KOSDAQ"
    indexes = []
    
    try:
        content_bytes = _http_get(url)
        res_json = json.loads(content_bytes.decode('utf-8'))
        datas = res_json.get("datas", [])
        for d in datas:
            indexes.append({
                "code": d.get("itemCode", ""),
                "name": "KOSPI" if d.get("itemCode") == "KOSPI" else "KOSDAQ",
                "price": d.get("closePrice", "0.00"),
                "change": d.get("compareToPreviousClosePrice", "0.00"),
                "direction": d.get("compareToPreviousPrice", {}).get("name", "STABLE"),
                "ratio": d.get("fluctuationsRatio", "0.00")
            })
    except Exception:
        indexes = [
            {"code": "KOSPI", "name": "KOSPI", "price": "N/A", "change": "0.00", "direction": "STABLE", "ratio": "0.00"},
            {"code": "KOSDAQ", "name": "KOSDAQ", "price": "N/A", "change": "0.00", "direction": "STABLE", "ratio": "0.00"}
        ]
        
    return indexes


def search_naver(query: str, search_type: str = "all") -> List[Dict[str, str]]:
    """Performs a customized Naver search mimicking a desktop browser session.
    
    Args:
        query: The search term.
        search_type: "all" (integrated), "news" (news tab), "blog" (blog tab).
        
    Returns:
        List[Dict[str, str]]: List of search result dictionaries containing title, snippet, and link.
    """
    results = []
    if not query:
        return results
        
    try:
        # Pre-visit Naver main once to simulate session warmth
        try:
            _http_get("https://www.naver.com/")
        except Exception:
            pass
            
        encoded_query = quote(query)
        if search_type == "news":
            url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}"
        elif search_type == "blog":
            url = f"https://search.naver.com/search.naver?where=post&query={encoded_query}"
        else:
            url = f"https://search.naver.com/search.naver?query={encoded_query}"
            
        content_bytes = _http_get(url)
        soup = BeautifulSoup(content_bytes, "html.parser")
        
        if search_type == "news":
            items = soup.find_all("li", class_="bx")
            for item in items:
                title_link = item.find("a", class_="news_tit")
                dsc_link = item.find("a", class_="news_dsc") or item.find("div", class_="news_dsc")
                
                if title_link:
                    title = title_link.get_text(strip=True)
                    link = title_link.get("href", "")
                    snippet = dsc_link.get_text(strip=True) if dsc_link else ""
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "source": item.find("a", class_="info").get_text(strip=True) if item.find("a", class_="info") else "News"
                    })
        elif search_type == "blog":
            items = soup.find_all("li", class_="bx")
            for item in items:
                title_link = item.find("a", class_=lambda c: c and "title_link" in c) or item.find("a", class_=lambda c: c and "total_tit" in c)
                dsc_link = item.find("div", class_=lambda c: c and "dsc_link" in c) or item.find("div", class_=lambda c: c and "dsc_txt" in c)
                
                if title_link:
                    title = title_link.get_text(strip=True)
                    link = title_link.get("href", "")
                    snippet = dsc_link.get_text(strip=True) if dsc_link else ""
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "source": "Blog"
                    })
        else:
            for news in soup.find_all("a", class_="news_tit")[:5]:
                results.append({
                    "title": news.get_text(strip=True),
                    "link": news.get("href", ""),
                    "snippet": "News Flash Article",
                    "source": "News"
                })
            for title_link in soup.find_all("a", class_=lambda c: c and ("title_link" in c or "total_tit" in c)):
                if len(results) >= 15:
                    break
                link = title_link.get("href", "")
                title = title_link.get_text(strip=True)
                if any(r["link"] == link for r in results):
                    continue
                snippet = ""
                parent = title_link.find_parent("li")
                if parent:
                    dsc = parent.find("div", class_=lambda c: c and ("dsc" in c or "api_txt_lines" in c))
                    if dsc:
                        snippet = dsc.get_text(strip=True)
                        
                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "source": "Search Result"
                })
                
    except Exception as e:
        results.append({
            "title": f"Failed to perform search: {e}",
            "link": "#",
            "snippet": "An error occurred during Naver search integration.",
            "source": "System"
        })
        
    return results


def fetch_media_rss(media_id: str) -> Dict[str, Any]:
    """Retrieves and parses RSS feeds for a given media outlet, falling back to Google News if needed.
    
    Args:
        media_id: The unique identifier for the media outlet.
        
    Returns:
        Dict[str, Any]: Structured data containing articles list and fallback status.
    """
    result = {
        "success": False,
        "media_name_ko": "",
        "media_name_en": "",
        "fallback_active": False,
        "articles": [],
        "error": None
    }
    
    # 1. Load media index
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "media_rss_index.json")
        if not os.path.exists(json_path):
            result["error"] = "Media RSS index file not found."
            return result
            
        with open(json_path, 'r', encoding='utf-8') as f:
            media_list = json.load(f)
            
        media_item = next((item for item in media_list if item["id"] == media_id), None)
        if not media_item:
            result["error"] = f"Media outlet '{media_id}' not found in index."
            return result
            
        result["media_name_ko"] = media_item["name_ko"]
        result["media_name_en"] = media_item["name_en"]
        
    except Exception as e:
        result["error"] = f"Failed to load media index: {e}"
        return result
        
    # 2. Try fetching primary RSS if available
    xml_content = None
    url_used = None
    
    if media_item.get("primary_rss"):
        url_used = media_item["primary_rss"]
        try:
            xml_content = _http_get(url_used, timeout=8)
        except Exception:
            # Fail silently and let fallback handle it
            pass
            
    # 3. Fallback to Google News RSS if primary failed or not provided
    if xml_content is None:
        result["fallback_active"] = True
        url_used = media_item["google_news_rss_url"]
        try:
            xml_content = _http_get(url_used, timeout=8)
        except Exception as e:
            result["error"] = f"Failed to fetch fallback feed: {e}"
            return result
            
    # 4. Parse XML content
    try:
        root = ET.fromstring(xml_content)
        articles = []
        for item in root.findall(".//item")[:15]:  # Limit to 15 articles for scrollable lists
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            desc_elem = item.find("description")
            
            title = title_elem.text if title_elem is not None and title_elem.text is not None else "No Title"
            link = link_elem.text if link_elem is not None and link_elem.text is not None else "#"
            pub_date = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text is not None else ""
            desc = desc_elem.text if desc_elem is not None and desc_elem.text is not None else ""
            
            # Clean description HTML tags
            if desc:
                desc = BeautifulSoup(desc, "html.parser").get_text(strip=True)
                
            # Clean Google News titles (typically end with " - Publisher")
            if result["fallback_active"] and " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                
            articles.append({
                "title": title.strip() if title else "No Title",
                "link": link.strip() if link else "#",
                "pub_date": pub_date.strip() if pub_date else "",
                "description": desc.strip() if desc else ""
            })
            
        result["articles"] = articles
        result["success"] = True
    except ET.ParseError as pe:
        result["error"] = f"XML Parse Error: {pe}"
    except Exception as e:
        result["error"] = f"Unexpected parsing error: {e}"
        
    return result
