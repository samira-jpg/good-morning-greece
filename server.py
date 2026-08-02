import http.server
import socketserver
import urllib.request
import xml.etree.ElementTree as ET
import json
import os
import re
import datetime
import html
import threading
import time
from urllib.parse import urlparse

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'news_cache.json')

# Keywords to filter news for positive vibes and filter out negative ones
POSITIVE_KEYWORDS = [
    "success", "successful", "successfully", "succeed", "succeeded",
    "win", "wins", "winning", "winner", "winners", "won",
    "award", "awards", "awarded",
    "gold", "golden",
    "medal", "medals", "medalist",
    "champion", "champions", "championship",
    "innovate", "innovation", "innovations", "innovative", "innovator",
    "startup", "startups",
    "technology", "technologies", "technological", "tech",
    "discover", "discovery", "discoveries", "discovered",
    "archaeology", "archaeological", "archaeologist", "archaeologists",
    "ancient",
    "excavation", "excavations", "excavate",
    "protect", "protects", "protecting", "protection", "protective",
    "conservation", "conserve",
    "save", "saves", "saving", "saved",
    "rescue", "rescued", "rescues",
    "help", "helps", "helping", "helped", "helper",
    "volunteer", "volunteers", "volunteered", "volunteering",
    "solidarity",
    "donation", "donations", "donate", "donated",
    "growth", "grow", "growing", "grows",
    "increase", "increased", "increases", "increasing",
    "rise", "rises", "rising", "rose",
    "tourist", "tourists", "tourism",
    "culture", "cultural",
    "festival", "festivals",
    "art", "arts", "artistic", "artist", "artists",
    "exhibition", "exhibitions",
    "beautiful", "beauty",
    "sunshine", "sunny",
    "clean", "cleaned", "cleaning",
    "renewable", "renewables",
    "solar",
    "wind",
    "ecological", "ecology",
    "restore", "restored", "restoration", "restoring",
    "reforestation",
    "celebrate", "celebrates", "celebrated", "celebrating", "celebration",
    "historic", "historical", "history",
    "achievement", "achievements", "achieve", "achieved",
    "triumph", "triumphs", "triumphant",
    "olympic", "olympics",
    "kindness", "kind",
    "hero", "heroes", "heroic"
]

NEGATIVE_KEYWORDS = [
    "murder", "murders", "murdered", "murdering",
    "kill", "kills", "killed", "killing", "killer",
    "die", "dies", "died", "dying",
    "dead",
    "death", "deaths",
    "crash", "crashes", "crashed",
    "accident", "accidents",
    "arrest", "arrests", "arrested",
    "theft", "thefts",
    "steal", "steals", "stealing", "stole", "stolen",
    "rob", "robs", "robbed", "robbing", "robbery", "robberies",
    "fraud",
    "corruption",
    "crisis", "crises",
    "strike", "strikes",
    "protest", "protests", "proested",
    "riot", "riots",
    "clash", "clashes", "clashed",
    "bomb", "bombs", "bombed", "bombing",
    "attack", "attacks", "attacked", "attacking",
    "shooting", "shootings", "shoot", "shoots", "shot",
    "kidnap", "kidnaps", "kidnapped", "kidnapping",
    "disaster", "disasters", "disastrous",
    "earthquake", "earthquakes",
    "wildfire", "wildfires",
    "fire", "fires", "fired", "firefighter", "firefighters",
    "blaze", "blazes", "burning", "burns", "burned", "smoke",
    "flood", "floods", "flooded",
    "leak", "leaks", "leaked",
    "drown", "drowns", "drowned", "drowning",
    "bankrupt", "bankruptcy",
    "inflation",
    "recession",
    "threat", "threats", "threaten", "threatened", "threatening",
    "scam", "scams",
    "jail", "jails",
    "prison", "prisons",
    "assault", "assaults", "assaulted",
    "violence", "violent",
    "tragedy", "tragedies", "tragic",
    "tension", "tensions",
    "stab", "stabs", "stabbed", "stabbing",
    "wound", "wounds", "wounded",
    "injure", "injures", "injured", "injury", "injuries",
    "struggle", "struggles", "struggling",
    "migrant", "migrants",
    "drought", "droughts",
    "evacuate", "evacuations", "evacuation", "evacuated"
]

def compile_keyword_regex(keywords):
    pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
    return re.compile(pattern, re.IGNORECASE)

POSITIVE_REGEX = compile_keyword_regex(POSITIVE_KEYWORDS)
NEGATIVE_REGEX = compile_keyword_regex(NEGATIVE_KEYWORDS)

REGIONS = {
    "Athens": [37.9838, 23.7275],
    "Thessaloniki": [40.6401, 22.9444],
    "Patras": [38.2466, 21.7346],
    "Heraklion": [35.3387, 25.1442],
    "Chania": [35.5138, 24.0180],
    "Larissa": [39.6390, 22.4191],
    "Volos": [39.3621, 22.9422],
    "Rhodes": [36.4341, 28.2176],
    "Corfu": [39.6243, 19.9217],
    "Santorini": [36.3932, 25.4615],
    "Mykonos": [37.4467, 25.3289],
    "Crete": [35.2401, 24.8093],
    "Peloponnese": [37.4856, 22.3653],
    "Epirus": [39.6650, 20.8537],
    "Thessaly": [39.5089, 22.1462],
    "Delphi": [38.4801, 22.5010],
    "Olympia": [37.6384, 21.6300],
    "Meteora": [39.7217, 21.6303],
    "Lesbos": [39.2089, 26.2162],
    "Samos": [37.7561, 26.8524],
    "Chios": [38.3730, 26.1358],
    "Zakynthos": [37.7870, 20.8999],
    "Kefalonia": [38.1754, 20.5692],
    "Naxos": [37.1056, 25.3767],
    "Paros": [37.0853, 25.1489],
    "Milos": [36.7294, 24.4286],
    "Kos": [36.8931, 27.2872]
}

def get_seeded_news():
    now = datetime.datetime.now(datetime.timezone.utc)
    
    def rel_date(days_ago, hour, minute):
        d = now - datetime.timedelta(days=days_ago)
        d = d.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return d.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
    return [
        {
            "title": "Greece Runs Entirely on 100% Clean Energy for the First Time in History",
            "link": "https://greekreporter.com/2022/10/11/greece-runs-100-percent-clean-energy-first-time/",
            "description": "Greece reached a historic milestone as the country's electricity grid ran entirely on renewable energy for several hours, showing the success of solar and wind investment.",
            "source": "Greek Reporter",
            "pubDate": rel_date(0, 9, 0),
            "location": "Peloponnese",
            "coords": [37.4856, 22.3653],
            "category": "Environment & Nature"
        },
        {
            "title": "Remarkable 2,500-Year-Old Temple Discovered Unspoiled in Ancient Delphi",
            "link": "https://greekreporter.com/2025/08/12/ancient-greek-temple-delphi/",
            "description": "Archaeologists working near Delphi have unearthed a beautifully preserved temple structure containing valuable bronze artifacts and intact inscriptions dedicated to Apollo.",
            "source": "Greek News Agenda",
            "pubDate": rel_date(1, 14, 0),
            "location": "Delphi",
            "coords": [38.4801, 22.5010],
            "category": "Culture & Heritage"
        },
        {
            "title": "Record Nesting Season for Loggerhead Sea Turtles in Zakynthos Marine Park",
            "link": "https://greekreporter.com/2026/07/20/sea-turtles-zakynthos-greece/",
            "description": "Conservationists report a record-breaking number of Caretta caretta sea turtle nests on the beaches of Zakynthos, citing successful eco-management and volunteer patrols.",
            "source": "eKathimerini",
            "pubDate": rel_date(2, 10, 30),
            "location": "Zakynthos",
            "coords": [37.7870, 20.8999],
            "category": "Environment & Nature"
        },
        {
            "title": "Greek Student Team Wins Gold Medal at International Robotics Olympiad",
            "link": "https://greekreporter.com/2026/07/15/greek-students-robotics-gold/",
            "description": "A brilliant team of high school students from Thessaloniki has won first place at the Robotics Olympiad, showcasing their autonomous rescue drone prototype.",
            "source": "Greek Reporter",
            "pubDate": rel_date(3, 18, 20),
            "location": "Thessaloniki",
            "coords": [40.6401, 22.9444],
            "category": "Innovation & Tech"
        },
        {
            "title": "Crete Farmers Win Top Honors at International Organic Olive Oil Awards",
            "link": "https://greekreporter.com/2026/06/18/crete-organic-olive-oil-gold/",
            "description": "An agricultural cooperative in Chania, Crete has taken home three gold medals for its ultra-premium extra virgin olive oil, highlighting sustainable farming techniques.",
            "source": "Greek Reporter",
            "pubDate": rel_date(4, 11, 45),
            "location": "Crete",
            "coords": [35.3387, 25.1442],
            "category": "Sports & Success"
        },
        {
            "title": "Athens Named Top Cultural Destination in Europe for 2026",
            "link": "https://greekreporter.com/2026/05/20/athens-top-destination-europe/",
            "description": "The World Travel Awards has crowned Athens as the leading cultural city destination, praising its pedestrian-friendly historic path and world-class museums.",
            "source": "Greek Reporter",
            "pubDate": rel_date(5, 8, 15),
            "location": "Athens",
            "coords": [37.9838, 23.7275],
            "category": "Tourism & Travel"
        },
        {
            "title": "Volunteers Plant 1,200 Native Trees on Mount Hymettus to Restore Forest",
            "link": "https://greekreporter.com/2026/04/12/volunteer-reforestation-athens/",
            "description": "Over five hundred volunteers joined local environmental groups in Athens to plant native pine and oak saplings in a major effort to restore fire-impacted regions.",
            "source": "eKathimerini",
            "pubDate": rel_date(6, 16, 30),
            "location": "Athens",
            "coords": [37.9838, 23.7275],
            "category": "Society & Solidarity"
        },
        {
            "title": "Rhodes Implements Zero-Waste Island Program to Eliminate Single-Use Plastics",
            "link": "https://greekreporter.com/2026/03/10/rhodes-zero-waste-island/",
            "description": "Rhodes has launched a comprehensive waste reduction plan in partnership with local businesses, offering recycled beach accessories and paper-only alternatives.",
            "source": "eKathimerini",
            "pubDate": rel_date(7, 12, 0),
            "location": "Rhodes",
            "coords": [36.4341, 28.2176],
            "category": "Environment & Nature"
        },
        {
            "title": "New High-Speed Train Link Connects Patras to Athens in Under Two Hours",
            "link": "https://greekreporter.com/2026/02/15/athens-patras-railway/",
            "description": "The completion of the state-of-the-art double-track electric railway has officially reduced travel time, promoting eco-friendly public transport in Western Greece.",
            "source": "eKathimerini",
            "pubDate": rel_date(8, 9, 30),
            "location": "Patras",
            "coords": [38.2466, 21.7346],
            "category": "Innovation & Tech"
        },
        {
            "title": "Ancient Sunken Harbor of Milos Mapped in High-Definition 3D by Marine Archaeologists",
            "link": "https://greekreporter.com/2026/01/22/sunken-harbor-milos-3d/",
            "description": "Using advanced sonar and underwater lasers, scientists have generated the first complete 3D digital model of the Roman-era harbor submerged off the island of Milos.",
            "source": "Greek News Agenda",
            "pubDate": rel_date(9, 15, 40),
            "location": "Milos",
            "coords": [36.7294, 24.4286],
            "category": "Culture & Heritage"
        }
    ]

def extract_location_and_coords(text):
    text_lower = text.lower()
    for loc, coords in REGIONS.items():
        if loc.lower() in text_lower:
            return loc, coords
    return "Greece", [39.0742, 21.8243]

def determine_category(text):
    text_lower = text.lower()
    categories = {
        "Culture & Heritage": ["archaeology", "archaeologist", "archaeological", "ancient", "history", "museum", "culture", "cultural", "art", "arts", "artist", "artists", "festival", "festivals", "music", "cinema"],
        "Tourism & Travel": ["tourism", "tourist", "tourists", "travel", "beach", "beaches", "hotel", "hotels", "island", "islands", "visit"],
        "Innovation & Tech": ["tech", "technology", "technologies", "startup", "startups", "innovate", "innovation", "innovations", "innovative", "science", "robotics", "digital", "research"],
        "Environment & Nature": ["green", "renewable", "renewables", "solar", "wind", "conservation", "wildlife", "turtle", "turtles", "forest", "forests", "clean", "ecology", "ecological"],
        "Society & Solidarity": ["help", "helps", "helping", "helped", "volunteer", "volunteers", "volunteering", "solidarity", "donation", "donations", "donate", "donated", "community", "communities", "kindness", "support", "hero", "heroes"],
        "Sports & Success": ["medal", "medals", "win", "wins", "winning", "won", "champion", "champions", "olympic", "olympics", "sports", "athlete", "athletes", "football", "basketball"]
    }
    
    for category, keywords in categories.items():
        pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
        if re.search(pattern, text_lower):
            return category
            
    return "General Positive"

def fetch_external_news():
    feeds = [
        ("Greek News Agenda", "https://www.greeknewsagenda.gr/feed/"),
        ("Google News (Greece)", "https://news.google.com/rss/search?q=Greece&hl=en-US&gl=US&ceid=US:en")
    ]
    
    parsed_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    for source_name, url in feeds:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                channel = root.find('channel')
                if channel is None:
                    continue
                
                for item in channel.findall('item'):
                    title = item.find('title')
                    title_text = title.text if title is not None else ""
                    
                    link = item.find('link')
                    link_text = link.text if link is not None else ""
                    
                    desc = item.find('description')
                    desc_text = desc.text if desc is not None else ""
                    
                    pub_date = item.find('pubDate')
                    pub_date_text = pub_date.text if pub_date is not None else ""
                    
                    # Clean HTML tags and unescape HTML/XML entities
                    clean_desc = html.unescape(re.sub('<[^<]+?>', '', desc_text).strip())
                    
                    # Sentiment filter using regular expressions with word boundary matching
                    has_negative = bool(NEGATIVE_REGEX.search(title_text) or NEGATIVE_REGEX.search(clean_desc))
                    has_positive = bool(POSITIVE_REGEX.search(title_text) or POSITIVE_REGEX.search(clean_desc))
                    
                    if has_negative:
                        continue
                    if not has_positive:
                        continue
                        
                    # Geotagging
                    loc, coords = extract_location_and_coords(title_text + " " + clean_desc)
                    
                    parsed_items.append({
                        "title": title_text,
                        "link": link_text,
                        "description": clean_desc[:220] + "..." if len(clean_desc) > 220 else clean_desc,
                        "source": source_name,
                        "pubDate": pub_date_text,
                        "location": loc,
                        "coords": coords,
                        "category": determine_category(title_text + " " + clean_desc)
                    })
        except Exception as e:
            print(f"Error fetching/parsing {source_name}: {e}")
            
    return parsed_items

# Background Cache Management Setup
news_cache = []
cache_lock = threading.Lock()

def load_cached_news():
    global news_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    with cache_lock:
                        news_cache = data
                    print(f"Loaded {len(news_cache)} news stories from cache file.")
                    return
        except Exception as e:
            print(f"Error loading news cache file: {e}")
            
    # Fallback if cache file does not exist, is empty, or fails to load
    with cache_lock:
        news_cache = get_seeded_news()
    print("Initialized news cache with fallback seeded news.")

def save_cached_news(news_list):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
        print("Successfully saved news cache to file.")
    except Exception as e:
        print(f"Error saving news cache to file: {e}")

def update_news():
    print("Initiating background news update...")
    dynamic_news = fetch_external_news()
    seed_news = get_seeded_news()
    
    seen_titles = set()
    merged_news = []
    
    # First insert dynamic feeds, then add seeded fallback stories
    for item in dynamic_news + seed_news:
        title_normalized = item["title"].strip().lower()
        if title_normalized not in seen_titles:
            seen_titles.add(title_normalized)
            merged_news.append(item)
            
    with cache_lock:
        global news_cache
        news_cache = merged_news
        
    save_cached_news(merged_news)
    print(f"News update completed. {len(merged_news)} stories in cache.")

def news_updater_loop():
    # Keep running in a daemon thread
    while True:
        try:
            update_news()
            # If successful, wait 60 minutes (3600 seconds)
            sleep_time = 3600
        except Exception as e:
            print(f"Error in background news updater: {e}")
            # If failed, retry in 5 minutes (300 seconds)
            sleep_time = 300
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
            
            # Instantly return cached news from memory
            with cache_lock:
                current_news = list(news_cache)
                
            self.wfile.write(json.dumps(current_news).encode('utf-8'))
            return
            
        super().do_GET()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    # Ensure public folder exists
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    
    # Load cache or seeded news immediately
    load_cached_news()
    
    # Start the background news updater thread
    updater_thread = threading.Thread(target=news_updater_loop, daemon=True)
    updater_thread.start()
    
    # Start web server
    with socketserver.ThreadingTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Good Morning Greece! Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
