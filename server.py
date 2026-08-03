import http.server
import socketserver
import json
import os
import random
import datetime
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
import re
import html
from urllib.parse import urlparse, quote_plus

PORT = int(os.environ.get("PORT", 8000))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'news_cache.json')

# Curated positive Greek news database templates (Used as a fallback when no ANTHROPIC_API_KEY is configured or API fails)
NEWS_DATABASE = [
    {
        "title": "Greece Runs Entirely on 100% Clean Energy for the First Time in History",
        "description": "Greece reached a historic milestone as the country's electricity grid ran entirely on renewable energy for several hours, showing the success of solar and wind investment.",
        "source": "Greek Reporter",
        "location": "Peloponnese",
        "coords": [37.4856, 22.3653],
        "category": "Environment & Nature"
    },
    {
        "title": "Record Nesting Season for Loggerhead Sea Turtles in Zakynthos Marine Park",
        "description": "Conservationists report a record-breaking number of Caretta caretta sea turtle nests on the beaches of Zakynthos, citing successful eco-management and volunteer patrols.",
        "source": "eKathimerini",
        "location": "Zakynthos",
        "coords": [37.7870, 20.8999],
        "category": "Environment & Nature"
    },
    {
        "title": "Rhodes Implements Zero-Waste Island Program to Eliminate Single-Use Plastics",
        "description": "Rhodes has launched a comprehensive waste reduction plan in partnership with local businesses, offering recycled beach accessories and paper-only alternatives.",
        "source": "eKathimerini",
        "location": "Rhodes",
        "coords": [36.4341, 28.2176],
        "category": "Environment & Nature"
    },
    {
        "title": "Volunteers Plant 1,200 Native Trees on Mount Hymettus to Restore Forest",
        "description": "Over five hundred volunteers joined local environmental groups in Athens to plant native pine and oak saplings in a major effort to restore fire-impacted regions.",
        "source": "eKathimerini",
        "location": "Athens",
        "coords": [37.9838, 23.7275],
        "category": "Environment & Nature"
    },
    {
        "title": "Samos Vineyards Lead the Aegean in Transitioning to Biodynamic Farming",
        "description": "A growing cooperative of local winegrowers on Samos has shifted to organic, biodynamic agriculture, creating healthy soils and winning European agricultural design awards.",
        "source": "Organic Greece",
        "location": "Samos",
        "coords": [37.7561, 26.8524],
        "category": "Environment & Nature"
    },
    {
        "title": "Marine Conservation Teams Clear Five Tons of Discarded Fishing Gear Off Kefalonia",
        "description": "Local volunteer divers and fishermen completed a joint cleaning operation in the Ionian Sea, successfully retrieving ghost nets and securing dolphin and seal habitats.",
        "source": "Ocean Clean International",
        "location": "Kefalonia",
        "coords": [38.1754, 20.5692],
        "category": "Environment & Nature"
    },
    {
        "title": "Remarkable 2,500-Year-Old Temple Discovered Unspoiled in Ancient Delphi",
        "description": "Archaeologists working near Delphi have unearthed a beautifully preserved temple structure containing valuable bronze artifacts and intact inscriptions dedicated to Apollo.",
        "source": "Greek News Agenda",
        "location": "Delphi",
        "coords": [38.4801, 22.5010],
        "category": "Culture & Heritage"
    },
    {
        "title": "Ancient Sunken Harbor of Milos Mapped in High-Definition 3D by Marine Archaeologists",
        "description": "Using advanced sonar and underwater lasers, scientists have generated the first complete 3D digital model of the Roman-era harbor submerged off the island of Milos.",
        "source": "Greek News Agenda",
        "location": "Milos",
        "coords": [36.7294, 24.4286],
        "category": "Culture & Heritage"
    },
    {
        "title": "Acropolis Museum Unveils Newly Restored Caryatid Inscriptions",
        "description": "The Acropolis Museum has completed a meticulous laser restoration of ancient dedicatory texts, offering visitors fresh insight into the building of the Erechtheion.",
        "source": "Greek Reporter",
        "location": "Athens",
        "coords": [37.9838, 23.7275],
        "category": "Culture & Heritage"
    },
    {
        "title": "Historic Byzantine City Walls Restoration Completed in Thessaloniki",
        "description": "Restoration teams have successfully secured and lit a two-kilometer section of Thessaloniki's ancient fortress walls, opening new pedestrian parks and panoramic viewing points.",
        "source": "eKathimerini",
        "location": "Thessaloniki",
        "coords": [40.6401, 22.9444],
        "category": "Culture & Heritage"
    },
    {
        "title": "Greek Student Team Wins Gold Medal at International Robotics Olympiad",
        "description": "A brilliant team of high school students from Thessaloniki has won first place at the Robotics Olympiad, showcasing their autonomous rescue drone prototype.",
        "source": "Greek Reporter",
        "location": "Thessaloniki",
        "coords": [40.6401, 22.9444],
        "category": "Innovation & Tech"
    },
    {
        "title": "New High-Speed Train Link Connects Patras to Athens in Under Two Hours",
        "description": "The completion of the state-of-the-art double-track electric railway has officially reduced travel time, promoting eco-friendly public transport in Western Greece.",
        "source": "eKathimerini",
        "location": "Patras",
        "coords": [38.2466, 21.7346],
        "category": "Innovation & Tech"
    },
    {
        "title": "Patras University Lab Invents Biodegradable Water Filters from Olive Pit Waste",
        "description": "Greek chemical engineers have developed an organic filter that purifies drinking water using charcoal synthesized from local agricultural waste, creating a circular economy success.",
        "source": "TechGreece Journal",
        "location": "Patras",
        "coords": [38.2466, 21.7346],
        "category": "Innovation & Tech"
    },
    {
        "title": "Science & Technology Park of Crete Launches Five Innovative Green Startups",
        "description": "The research facility in Heraklion has approved funding and mentorship for new student startups developing intelligent agriculture tools and sea-based wave energy devices.",
        "source": "Crete Innovates",
        "location": "Heraklion",
        "coords": [35.3387, 25.1442],
        "category": "Innovation & Tech"
    },
    {
        "title": "Crete Farmers Win Top Honors at International Organic Olive Oil Awards",
        "description": "An agricultural cooperative in Chania, Crete has taken home three gold medals for its ultra-premium extra virgin olive oil, highlighting sustainable farming techniques.",
        "source": "Greek Reporter",
        "location": "Crete",
        "coords": [35.3387, 25.1442],
        "category": "Sports & Success"
    },
    {
        "title": "Santorini High School Student Wins Prestigious International Physics Prize",
        "description": "A local teenager has placed first at the European Physics Competition, designing a computational model for predicting orbital mechanics under solar radiation pressure.",
        "source": "Aegean Education",
        "location": "Santorini",
        "coords": [36.3932, 25.4615],
        "category": "Sports & Success"
    },
    {
        "title": "Larissa Mobile Library Service Reaches 45 Remote Mountain Villages",
        "description": "Equipped with thousands of books and free internet laptops, the mobile book van travels weekly across Mount Olympus valleys to bring culture and education to remote school kids.",
        "source": "Thessaly Society",
        "location": "Larissa",
        "coords": [39.6390, 22.4191],
        "category": "Society & Solidarity"
    },
    {
        "title": "Heraklion Community Kitchen Celebrates Serving 100,000 Free Organic Meals",
        "description": "A volunteer-led foundation in Heraklion has reached a major milestone, using locally donated farm surplus to cook healthy dinners for underprivileged families and students.",
        "source": "Crete Solidarity",
        "location": "Heraklion",
        "coords": [35.3387, 25.1442],
        "category": "Society & Solidarity"
    },
    {
        "title": "Volunteers Transform Abandoned Olive Mills in Chania Into Vibrant Youth Centers",
        "description": "Young architectural students and local citizens renovated a nineteenth-century mill, turning it into a free library, music studio, and safe community space.",
        "source": "Chania Community",
        "location": "Chania",
        "coords": [35.5138, 24.0180],
        "category": "Society & Solidarity"
    },
    {
        "title": "Volos Coding Academy Offers Free Tech Training to Rural Students",
        "description": "A volunteer association of software engineers has opened a classroom in Volos, teaching web programming and AI basics to fifty children from surrounding farming villages.",
        "source": "Volos Tech Society",
        "location": "Volos",
        "coords": [39.3621, 22.9422],
        "category": "Society & Solidarity"
    }
]

def get_greek_time():
    # August/summer time in Greece is UTC+3.
    # Return local date time by offsetting UTC.
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    return utc_now + datetime.timedelta(hours=3)

def generate_daily_news():
    greek_now = get_greek_time()
    date_str = greek_now.strftime("%Y-%m-%d")
    
    # Seed local random generator for consistent daily results
    rng = random.Random(date_str)
    
    # Deterministically select 12 stories from our database
    selected_stories = rng.sample(NEWS_DATABASE, min(12, len(NEWS_DATABASE)))
    rng.shuffle(selected_stories)
    
    processed_news = []
    for idx, story in enumerate(selected_stories):
        item = dict(story)
        
        # Distribute publication times over the past week relative to Greek time
        if idx < 3:
            days_ago = 0
            hour = max(0, greek_now.hour - (idx * 2 + 1))
            minute = (idx * 15 + 10) % 60
        elif idx < 7:
            days_ago = 1
            hour = 9 + idx
            minute = (idx * 12 + 5) % 60
        elif idx < 10:
            days_ago = 2
            hour = 8 + idx
            minute = (idx * 17 + 22) % 60
        else:
            days_ago = 3 + (idx - 10)
            hour = 10 + idx
            minute = (idx * 9 + 14) % 60
            
        pub_date = greek_now - datetime.timedelta(days=days_ago)
        pub_date = pub_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        item["pubDate"] = pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        item["link"] = "https://www.google.com/search?q=" + quote_plus(story["title"])
        processed_news.append(item)
        
    return processed_news

# Targeted Google News searches, each aimed at an inherently upbeat topic area, plus a
# couple of direct feeds. Real article links come straight from the feed (Google News
# links redirect to the original publisher article).
RSS_FEEDS = [
    ("Google News", "https://news.google.com/rss/search?q=Greece+(culture+OR+heritage+OR+archaeology+OR+museum)+when:5d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(tourism+OR+travel+OR+island)+when:5d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(innovation+OR+startup+OR+technology+OR+research)+when:5d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(renewable+OR+environment+OR+conservation+OR+wildlife)+when:5d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(award+OR+championship+OR+medal+OR+wins)+when:5d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(charity+OR+volunteer+OR+community)+when:5d&hl=en-US&gl=US&ceid=US:en"),
    ("Keep Talking Greece", "https://www.keeptalkinggreece.com/feed/"),
]

# Keywords that disqualify a story from the "good news" feed
NEGATIVE_KEYWORDS = [
    "crime", "murder", "killed", "kills", "kill ", "dead", "death", "dies", "died",
    "fire", "blaze", "disaster", "earthquake", "flood", "collapse", "risk",
    "crash", "drown", "war", "attack", "terror", "injur", "arrest", "scandal",
    "protest", "strike", "riot", "corruption", "lawsuit", "fraud", "shooting",
    "assault", "abuse", "migrant crisis", "recession", "sanction", "clash",
    "election", "opposition", "government", "minister", "parliament", "party",
    "arms sales", "human rights", "missing", "warship", "massacre", "alarm",
    "smuggl", "illegal", "detain", "tension", "dispute", "controversy", "suicide",
    "body found", "suspect", "trial", "court", "sentenced", "jail", "prison",
]

# Keyword -> category mapping, checked in order against title+description
CATEGORY_KEYWORDS = [
    ("Environment & Nature", ["environment", "climate", "renewable", "solar", "wind farm", "wildlife", "turtle",
                              "forest", "recycl", "clean energy", "nature", "conservation", "biodiversity", "organic"]),
    ("Innovation & Tech", ["tech", "startup", "innovation", "research", "science", "robot", "ai ", "digital",
                           "satellite", "engineer", "university", "invent", "app "]),
    ("Sports & Success", ["olymp", "champion", "medal", "award", "win", "wins", "won", "victory", "athlete",
                          "football", "basketball", "tournament"]),
    ("Society & Solidarity", ["volunteer", "charity", "community", "donat", "solidarity", "school", "children",
                              "education", "refugee support", "food bank"]),
    ("Tourism & Travel", ["tourism", "travel", "visitor", "hotel", "island", "beach", "flight", "cruise", "destination"]),
    ("Culture & Heritage", ["ancient", "archaeolog", "museum", "heritage", "byzantine", "temple", "festival",
                            "art", "history", "unesco", "acropolis"]),
]

# Greek place names -> [lat, lon], checked against title+description to pin the story on the map
LOCATION_COORDS = {
    "athens": [37.9838, 23.7275], "acropolis": [37.9715, 23.7267], "piraeus": [37.9475, 23.6367],
    "thessaloniki": [40.6401, 22.9444], "patras": [38.2466, 21.7346], "heraklion": [35.3387, 25.1442],
    "crete": [35.2401, 24.8093], "chania": [35.5138, 24.0180], "rhodes": [36.4341, 28.2176],
    "santorini": [36.3932, 25.4615], "mykonos": [37.4467, 25.3289], "zakynthos": [37.7870, 20.8999],
    "kefalonia": [38.1754, 20.5692], "corfu": [39.6243, 19.9217], "samos": [37.7561, 26.8524],
    "delphi": [38.4801, 22.5010], "milos": [36.7294, 24.4286], "larissa": [39.6390, 22.4191],
    "volos": [39.3621, 22.9422], "ioannina": [39.6650, 20.8537], "sparta": [37.0733, 22.4270],
    "olympia": [37.6384, 21.6303], "naxos": [37.1036, 25.3766], "paros": [37.0853, 25.1488],
    "peloponnese": [37.4856, 22.3653], "meteora": [39.7217, 21.6303], "olympus": [40.0855, 22.3585],
    "aegean": [37.8, 25.5], "ionian": [38.5, 20.5],
}
DEFAULT_COORDS = [39.0742, 21.8243]

def categorize(text):
    """Returns the matched category, or None if nothing indicates a positive story."""
    lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(k in lower for k in keywords):
            return category
    return None

def locate(text):
    lower = text.lower()
    for place, coords in LOCATION_COORDS.items():
        if place in lower:
            return place.title(), coords
    return "Greece", DEFAULT_COORDS

def is_positive_story(text):
    lower = text.lower()
    return not any(neg in lower for neg in NEGATIVE_KEYWORDS)

def parse_rss_date(date_str):
    if not date_str:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def fetch_positive_rss_news():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    collected = []
    for source_name, url in RSS_FEEDS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                channel = root.find('channel')
                if channel is None:
                    continue

                for item in channel.findall('item')[:15]:
                    title = item.find('title')
                    title_text = html.unescape((title.text or "").strip()) if title is not None else ""
                    if not title_text:
                        continue

                    link = item.find('link')
                    link_text = (link.text or "").strip() if link is not None else ""
                    if not link_text:
                        continue

                    # Google News titles look like "Headline - Publisher"; split that out as the source.
                    item_source = source_name
                    title_match = re.match(r'^(.*)\s+-\s+([^-]+)$', title_text)
                    if source_name == "Google News" and title_match:
                        title_text = title_match.group(1).strip()
                        item_source = title_match.group(2).strip()

                    desc = item.find('description')
                    desc_text = desc.text if desc is not None else ""
                    clean_desc = html.unescape(re.sub('<[^<]+?>', '', desc_text or "").strip())
                    if not clean_desc:
                        clean_desc = title_text

                    combined_text = f"{title_text} {clean_desc}"
                    if not is_positive_story(combined_text):
                        continue

                    category = categorize(combined_text)
                    if category is None:
                        continue

                    pub_date_el = item.find('pubDate')
                    pub_dt = parse_rss_date(pub_date_el.text if pub_date_el is not None else None)
                    if pub_dt is None:
                        pub_dt = datetime.datetime.now(datetime.timezone.utc)

                    location, coords = locate(combined_text)

                    collected.append({
                        "title": title_text,
                        "link": link_text,
                        "description": clean_desc[:320],
                        "source": item_source,
                        "location": location,
                        "coords": coords,
                        "category": category,
                        "pubDate": pub_dt.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                        "_sort_dt": pub_dt.timestamp() if pub_dt.tzinfo else pub_dt.replace(tzinfo=datetime.timezone.utc).timestamp(),
                    })
        except Exception as e:
            print(f"Error fetching RSS from {source_name}: {e}")

    # Dedupe by normalized title, newest first, cap at 15 stories
    seen_titles = set()
    deduped = []
    for entry in sorted(collected, key=lambda x: x["_sort_dt"], reverse=True):
        key = re.sub(r'\W+', '', entry["title"].lower())[:60]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        entry.pop("_sort_dt", None)
        deduped.append(entry)
        if len(deduped) >= 15:
            break

    return deduped

# Background Cache Management Setup
news_cache = []
cache_lock = threading.Lock()

def update_cache_from_rss():
    print("Fetching fresh positive Greek news from RSS feeds...")
    news = fetch_positive_rss_news()

    if news and len(news) > 0:
        with cache_lock:
            global news_cache
            news_cache = news
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(news, f, ensure_ascii=False, indent=2)
            print(f"Successfully cached {len(news)} fresh news stories.")
        except Exception as e:
            print(f"Error saving news cache to file: {e}")
        return True

    print("Warning: RSS fetch returned no usable stories.")
    return False

def cache_is_fresh():
    """Cache counts as fresh if it exists and was written today (Greek time)."""
    if not os.path.exists(CACHE_FILE):
        return False
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_FILE), tz=datetime.timezone.utc) + datetime.timedelta(hours=3)
    return mtime.strftime("%Y-%m-%d") == get_greek_time().strftime("%Y-%m-%d")

def init_news_cache():
    global news_cache
    if cache_is_fresh():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    with cache_lock:
                        news_cache = data
                    print(f"Loaded {len(news_cache)} fresh news stories from today's cache file.")
                    return
        except Exception as e:
            print(f"Error loading news cache file: {e}")

    print("Cache missing or stale, fetching fresh news now...")
    if update_cache_from_rss():
        return

    # Last-resort local fallback if RSS is unreachable (e.g. no internet)
    with cache_lock:
        news_cache = generate_daily_news()
    print("RSS fetch failed. Initialized news cache with local date-seeded fallback news.")

def background_news_loop():
    time.sleep(1)
    while True:
        try:
            success = update_cache_from_rss()
            sleep_time = 10800 if success else 600  # refresh every 3 hours, retry sooner on failure
        except Exception as e:
            print(f"Error in background news loop: {e}")
            sleep_time = 600
        time.sleep(sleep_time)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path)
        rel_path = parsed.path.lstrip('/')
        if not rel_path or rel_path == 'index.html':
            return os.path.join(PUBLIC_DIR, 'index.html')
        return os.path.join(PUBLIC_DIR, rel_path)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/api/news':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with cache_lock:
                current_news = list(news_cache)
                
            if not current_news:
                current_news = generate_daily_news()
                
            self.wfile.write(json.dumps(current_news).encode('utf-8'))
            return
            
        super().do_GET()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    init_news_cache()
    
    updater_thread = threading.Thread(target=background_news_loop, daemon=True)
    updater_thread.start()
    
    with socketserver.ThreadingTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Good Morning Greece! Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
