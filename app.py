"""Premium News RSS Reader - Pinterest Design System.

Dedicated RSS feed aggregator designed for 9 top Korean media outlets.
Styling complies fully with the Pinterest Design System tokens (Design.md).
All UI elements are in English.
"""

import streamlit as st
import os
import json
import naver_crawler as nc

# Set page configuration - Wide layout for clean grid display
st.set_page_config(
    page_title="Premium News Grid Reader",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Pinterest Theme Styles
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        /* Base typography & Canvas Off-White wash */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', 'Noto Sans KR', sans-serif;
            background-color: #fbfbf9 !important; /* colors.surface-soft */
        }
        
        .main {
            background-color: #fbfbf9 !important;
        }
        
        /* App Branding - Pinterest tight letter-spacing display headline */
        .app-title-container {
            text-align: center;
            padding: 40px 0 15px 0;
        }
        
        .app-title {
            font-size: 2.8rem;
            font-weight: 700;
            color: #262622; /* colors.charcoal */
            letter-spacing: -1.2px; /* tight tracking display signature */
            margin-bottom: 6px;
        }
        
        .app-subtitle {
            font-size: 1.02rem;
            color: #62625b; /* colors.mute */
            font-weight: 400;
            margin-bottom: 25px;
        }
        
        /* Responsive Grid layout */
        .rss-grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
            gap: 24px;
            margin-top: 10px;
            padding: 0 15px;
        }
        
        /* Level 0 Flat Card - no shadow, 1px solid hairline */
        .rss-card {
            background-color: #ffffff; /* colors.canvas */
            border: 1px solid #dadad3; /* colors.hairline */
            border-radius: 16px; /* rounded.md */
            padding: 24px;
            box-shadow: none !important; /* Elevation 0 - flat content surface */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 480px;
            transition: border-color 0.15s ease;
        }
        
        .rss-card:hover {
            border-color: #e60023; /* hover accent to Pinterest Red */
        }
        
        .rss-card-header {
            font-size: 1.25rem;
            font-weight: 700;
            color: #000000; /* colors.ink */
            letter-spacing: -0.8px;
            border-bottom: 2px solid #dadad3; /* colors.hairline */
            padding-bottom: 10px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        /* Pill Badges - rounded.full */
        .rss-badge {
            font-size: 0.7rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 9999px; /* rounded.full */
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Scroll Badge/Button - uses brand Pinterest Red, interactive button */
        .rss-badge-scroll {
            background-color: #e60023; /* colors.primary */
            color: #ffffff; /* colors.on-dark */
            border: none;
            cursor: pointer;
            outline: none;
            transition: background-color 0.15s ease, transform 0.1s ease;
        }
        
        .rss-badge-scroll:hover {
            background-color: #ad0016; /* Darker red */
        }
        
        .rss-badge-scroll:active {
            transform: scale(0.95);
        }
        
        /* Fallback modifier for Scroll Badge/Button */
        .rss-badge-fallback {
            background-color: #e5e5e0 !important; /* colors.secondary-bg */
            color: #62625b !important; /* colors.mute */
        }
        
        .articles-container {
            flex-grow: 1;
            overflow-y: scroll;
            -webkit-overflow-scrolling: touch;
            padding-right: 4px;
        }
        
        .articles-container::-webkit-scrollbar {
            width: 4px;
        }
        .articles-container::-webkit-scrollbar-thumb {
            background-color: #e5e5e0;
            border-radius: 4px;
        }
        
        /* Article item block */
        .article-item {
            padding: 12px 0;
            border-bottom: 1px solid #e5e5e0; /* colors.hairline-soft */
        }
        
        .article-item:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }
        
        /* Article Title - Charcoal color, Hover turns to Pinterest Red */
        .article-title {
            color: #262622 !important; /* colors.charcoal */
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 700;
            display: block;
            margin-bottom: 5px;
            line-height: 1.35;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: color 0.15s ease;
        }
        
        .article-title:hover {
            color: #e60023 !important; /* colors.primary */
            text-decoration: underline;
        }
        
        .article-desc {
            font-size: 0.82rem;
            color: #33332e; /* colors.body */
            line-height: 1.45;
            margin-bottom: 5px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .article-meta {
            font-size: 0.72rem;
            color: #62625b; /* colors.mute */
        }
        
        /* ==========================================================================
           Dark Mode Variables & Rules (Pinterest Dark Theme compatible)
           ========================================================================== */
        /* Force background overrides for Streamlit base layout in dark mode */
        body.dark-mode,
        body.dark-mode .stApp,
        body.dark-mode [data-testid="stApp"],
        body.dark-mode .main,
        body.dark-mode [class*="st-"] {
            background-color: #181816 !important; /* Dark Canvas */
            color: #f5f5f0 !important;
        }
        
        /* stApp has its own dark-mode class toggled directly */
        .stApp.dark-mode,
        [data-testid="stApp"].dark-mode {
            background-color: #181816 !important;
            color: #f5f5f0 !important;
        }
        
        body.dark-mode .app-title {
            color: #f5f5f0 !important;
        }
        
        body.dark-mode .app-subtitle {
            color: #a5a59e !important;
        }
        
        body.dark-mode .rss-card {
            background-color: #262624 !important; /* Dark Card */
            border-color: #44443f !important;
        }
        
        body.dark-mode .rss-card-header {
            color: #ffffff !important;
            border-bottom-color: #44443f !important;
        }
        
        body.dark-mode .article-title {
            color: #e5e5e0 !important;
        }
        
        body.dark-mode .article-title:hover {
            color: #ff3b5c !important; /* Premium bright red for dark mode hover */
        }
        
        body.dark-mode .article-desc {
            color: #c5c5be !important;
        }
        
        body.dark-mode .article-meta {
            color: #8c8c85 !important;
        }
        
        body.dark-mode .article-item {
            border-bottom-color: #44443f !important;
        }
        
        body.dark-mode .rss-badge-fallback {
            background-color: #3e3e3a !important;
            color: #a5a59e !important;
        }
        
        /* Dark mode toggle button styles */
        .theme-toggle-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background-color: #ffffff;
            border: 1px solid #dadad3;
            border-radius: 9999px;
            padding: 8px 16px;
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: all 0.15s ease, transform 0.1s ease;
            z-index: 999;
        }
        
        .theme-toggle-btn:hover {
            background-color: #f0f0f0;
            transform: translateY(-1px);
        }
        
        .theme-toggle-btn:active {
            transform: scale(0.95);
        }
        
        /* When body is dark-mode, apply styles to button */
        body.dark-mode .theme-toggle-btn,
        .stApp.dark-mode .theme-toggle-btn {
            background-color: #262624 !important;
            border-color: #44443f !important;
            color: #ffffff !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
        }
        
        body.dark-mode .theme-toggle-btn:hover,
        .stApp.dark-mode .theme-toggle-btn:hover {
            background-color: #333330 !important;
        }
        
        /* Mobile adjustment for toggle button */
        @media (max-width: 480px) {
            .theme-toggle-btn {
                position: static;
                display: block;
                margin: 0 auto 15px auto;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Header Title Widget with interactive theme toggle
st.markdown(
    """
    <div class="app-title-container" style="position: relative;">
        <button type="button" id="theme-btn" class="theme-toggle-btn">🌙 Dark</button>
        <h1 class="app-title">Premium News RSS Grid</h1>
        <p class="app-subtitle">Real-time aggregate feeds from 9 major Korean media channels. Auto-realigns on mobile screens.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Outlets Index configuration
media_list = [
    {"id": "chosun", "name": "Chosun Ilbo (조선일보)"},
    {"id": "donga", "name": "Donga Ilbo (동아일보)"},
    {"id": "hani", "name": "Hankyoreh (한겨레)"},
    {"id": "khan", "name": "Kyunghyang (경향신문)"},
    {"id": "maekyung", "name": "Maeil Business (매일경제)"},
    {"id": "hankyung", "name": "Korea Economic (한국경제)"},
    {"id": "yonhapnewstv", "name": "Yonhap News TV (연합뉴스TV)"},
    {"id": "ytn", "name": "YTN (구글뉴스 RSS)"},
    {"id": "ohmynews", "name": "OhmyNews (오마이뉴스)"}
]

# RSS Fetch wrapper with st.cache_data to handle network speed for all 9 concurrent feeds
@st.cache_data(ttl=300)
def get_cached_rss_feed(media_id: str):
    return nc.fetch_media_rss(media_id)

# Perform concurrent data fetching with visual progress bar
with st.spinner("Fetching all 9 news channel feeds..."):
    cards_html = ""
    for media in media_list:
        feed = get_cached_rss_feed(media["id"])
        
        if feed["success"]:
            # Badge button rendering based on connection mode, both text to "Scroll" with styling
            if feed["fallback_active"]:
                badge_html = f'<button type="button" class="rss-badge rss-badge-scroll rss-badge-fallback" onclick="scrollFeed(\'{media["id"]}\')">Scroll</button>'
            else:
                badge_html = f'<button type="button" class="rss-badge rss-badge-scroll" onclick="scrollFeed(\'{media["id"]}\')">Scroll</button>'
                
            # Render up to 15 articles inside the card for scrolling list
            articles_html = ""
            for art in feed["articles"][:15]:
                articles_html += f"""
                <div class="article-item">
                    <a class="article-title" href="{art['link']}" target="_blank" title="{art['title']}">
                        {art['title']}
                    </a>
                    <div class="article-desc">
                        {art['description'] or 'No summary text available.'}
                    </div>
                    <div class="article-meta">
                        {art['pub_date']}
                    </div>
                </div>
                """
                
            cards_html += f"""
            <div class="rss-card" id="card-{media['id']}">
                <div class="rss-card-header">
                    <div>{feed['media_name_en']}</div>
                    {badge_html}
                </div>
                <div class="articles-container">
                    {articles_html if articles_html else '<p style="font-size:0.85rem; color:#62625b; text-align:center; padding-top:40px;">No articles found.</p>'}
                </div>
                <div style="font-size:0.75rem; color:#62625b; text-align:right; border-top:1px solid #e5e5e0; padding-top:8px; margin-top:8px; font-weight:500;">
                    {feed['media_name_ko']}
                </div>
            </div>
            """
        else:
            cards_html += f"""
            <div class="rss-card" id="card-{media['id']}">
                <div class="rss-card-header" style="border-bottom-color: #9e0a0a;">
                    <div>{media['name']}</div>
                    <span class="rss-badge" style="background-color: #ffe3e3; color: #9e0a0a;">Error</span>
                </div>
                <p style="font-size:0.85rem; color:#9e0a0a; padding-top:20px; font-weight: 500;">
                    Failed to fetch RSS: {feed['error']}
                </p>
            </div>
            """

    # Print the responsive grid container with clean closing tag
    full_html = f'<div class="rss-grid-container">{cards_html}</div>'
    
    # Javascript code for handling feed scroll animation and dynamic dark-mode toggling
    js_code = """
    <script>
    function scrollFeed(mediaId) {
        const card = document.getElementById('card-' + mediaId);
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            const container = card.querySelector('.articles-container');
            if (container) {
                const currentScroll = container.scrollTop;
                const maxScroll = container.scrollHeight - container.clientHeight;
                if (currentScroll >= maxScroll - 5) {
                    container.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                    container.scrollBy({ top: 180, behavior: 'smooth' });
                }
            }
        }
    }
    
    // Global event delegation to bypass React element recreation
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'theme-btn') {
            toggleTheme();
        }
    });

    function toggleTheme() {
        const body = document.body;
        const isDark = body.classList.contains('dark-mode');
        
        if (isDark) {
            localStorage.setItem('dark-theme', 'disabled');
            applyThemeState(false);
        } else {
            localStorage.setItem('dark-theme', 'enabled');
            applyThemeState(true);
        }
    }
    
    function applyThemeState(isDark) {
        const body = document.body;
        const app = document.querySelector('.stApp') || document.querySelector('[data-testid="stApp"]');
        const btn = document.getElementById('theme-btn');
        
        if (isDark) {
            if (!body.classList.contains('dark-mode')) body.classList.add('dark-mode');
            if (app && !app.classList.contains('dark-mode')) app.classList.add('dark-mode');
            if (btn) btn.innerHTML = '☀️ Light';
        } else {
            if (body.classList.contains('dark-mode')) body.classList.remove('dark-mode');
            if (app && app.classList.contains('dark-mode')) app.classList.remove('dark-mode');
            if (btn) btn.innerHTML = '🌙 Dark';
        }
    }
    
    // MutationObserver: Locks the dark-mode class against React virtual DOM overwrites
    const themeObserver = new MutationObserver(function(mutations) {
        const darkTheme = localStorage.getItem('dark-theme');
        const shouldBeDark = (darkTheme === 'enabled');
        const body = document.body;
        const hasDarkClass = body.classList.contains('dark-mode');
        
        if (shouldBeDark !== hasDarkClass) {
            applyThemeState(shouldBeDark);
        } else if (shouldBeDark) {
            const app = document.querySelector('.stApp') || document.querySelector('[data-testid="stApp"]');
            if (app && !app.classList.contains('dark-mode')) {
                app.classList.add('dark-mode');
            }
            const btn = document.getElementById('theme-btn');
            if (btn && btn.innerHTML !== '☀️ Light') {
                btn.innerHTML = '☀️ Light';
            }
        }
    });
    
    themeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
    
    // Interval check: Double-ensures the state remains synced during dynamic transitions
    setInterval(function() {
        const darkTheme = localStorage.getItem('dark-theme');
        applyThemeState(darkTheme === 'enabled');
    }, 250);
    </script>
    """
    
    # Strip newlines and extra spaces to prevent markdown parser from outputting raw tags on screen
    clean_html = " ".join(full_html.split())
    st.markdown(clean_html + js_code, unsafe_allow_html=True)
