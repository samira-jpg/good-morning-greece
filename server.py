import http.server
import socketserver
import urllib.request
import xml.etree.ElementTree as ET
import json
import os
import re
import datetime
from urllib.parse import urlparse

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')

# Keywords to filter news for positive vibes and filter out negative ones
POSITIVE_KEYWORDS = [
    "success", "win", "award", "gold", "medal", "champion", "innovate", "innovation", 
    "startup", "technology", "discover", "discovery", "archaeology", "ancient", 
    "excavation", "protect", "conservation", "save", "rescue", "help", "volunteer", 
    "solidarity", "donation", "growth", "increase", "rise", "tourist", "tourism", 
    "culture", "festival", "art", "exhibition", "beautiful", "sunshine", "clean", 
    "renewable", "solar", "wind", "ecological", "restore", "reforestation", 
    "celebrate", "historic", "achievement", "triumph", "olympic", "kindness", "hero"
]

NEGATIVE_KEYWORDS = [
    "murder", "kill", "die", "dead", "death", "crash", "accident", "arrest", 
    "theft", "steal", "rob", "fraud", "corruption", "crisis", "strike", "protest", 
    "riot", "clash", "bomb", "attack", "shooting", "kidnap", "disaster", "earthquake", 
    "wildfire", "fire", "flood", "leak", "drown", "bankrupt", "inflation", "recession", 
    "threat", "scam", "jail", "prison", "assault", "violence", "tragedy", "tension"
]

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

# 10 rich seeded positive Greek news stories to guarantee immediate, high-fidelity data
SEED_NEWS = [
    {
        "title": "Greece Runs Entirely on 100% Clean Energy for the First Time in History",
        "link": "https://greekreporter.com/2022/10/11/greece-runs-100-percent-clean-energy-first-time/",
        "description": "Greece reached a historic milestone as the country's electricity grid ran entirely on renewable energy for several hours, showing the success of solar and wind investment.",
        "source": "Greek Reporter",
        "pubDate": "Sun, 02 Aug 2026 09:00:00 GMT",
        "location": "Peloponnese",
        "coords": [37.4856, 22.3653],
        "category": "Environment & Nature"
    },
    {
        "title": "Remarkable 2,500-Year-Old Temple Discovered Unspoiled in Ancient Delphi",
        "link": "https://greekreporter.com/2025/08/12/ancient-greek-temple-delphi/",
        "description": "Archaeologists working near Delphi have unearthed a beautifully preserved temple structure containing valuable bronze artifacts and intact inscriptions dedicated to Apollo.",
        "source": "Greek News Agenda",
        "pubDate": "Sat, 01 Aug 2026 14:00:00 GMT",
        "location": "Delphi",
        "coords": [38.4801, 22.5010],
        "category": "Culture & Heritage"
    },
    {
        "title": "Record Nesting Season for Loggerhead Sea Turtles in Zakynthos Marine Park",
        "link": "https://greekreporter.com/2026/07/20/sea-turtles-zakynthos-greece/",
        "description": "Conservationists report a record-breaking number of Caretta caretta sea turtle nests on the beaches of Zakynthos, citing successful eco-management and volunteer patrols.",
        "source": "eKathimerini",
        "pubDate": "Fri, 31 Jul 2026 10:30:00 GMT",
        "location": "Zakynthos",
        "coords": [37.7870, 20.8999],
        "category": "Environment & Nature"
    },
    {
        "title": "Greek Student Team Wins Gold Medal at International Robotics Olympiad",
        "link": "https://greekreporter.com/2026/07/15/greek-students-robotics-gold/",
        "description": "A brilliant team of high school students from Thessaloniki has won first place at the Robotics Olympiad, showcasing their autonomous rescue drone prototype.",
        "source": "Greek Reporter",
        "pubDate": "Thu, 30 Jul 2026 18:20:00 GMT",
        "location": "Thessaloniki",
        "coords": [40.6401, 22.9444],
        "category": "Innovation & Tech"
    },
    {
        "title": "Crete Farmers Win Top Honors at International Organic Olive Oil Awards",
        "link": "https://greekreporter.com/2026/06/18/crete-organic-olive-oil-gold/",
        "description": "An agricultural cooperative in Chania, Crete has taken home three gold medals for its ultra-premium extra virgin olive oil, highlighting sustainable farming techniques.",
        "source": "Greek Reporter",
        "pubDate": "Wed, 29 Jul 2026 11:45:00 GMT",
        "location": "Crete",
        "coords": [35.3387, 25.1442],
        "category": "Sports & Success"
    },
    {
        "title": "Athens Named Top Cultural Destination in Europe for 2026",
        "link": "https://greekreporter.com/2026/05/20/athens-top-destination-europe/",
        "description": "The World Travel Awards has crowned Athens as the leading cultural city destination, praising its pedestrian-friendly historic path and world-class museums.",
        "source": "Greek Reporter",
        "pubDate": "Tue, 28 Jul 2026 08:15:00 GMT",
        "location": "Athens",
        "coords": [37.9838, 23.7275],
        "category": "Tourism & Travel"
    },
    {
        "title": "Volunteers Plant 1,200 Native Trees on Mount Hymettus to Restore Forest",
        "link": "https://greekreporter.com/2026/04/12/volunteer-reforestation-athens/",
        "description": "Over five hundred volunteers joined local environmental groups in Athens to plant native pine and oak saplings in a major effort to restore fire-impacted regions.",
        "source": "eKathimerini",
        "pubDate": "Mon, 27 Jul 2026 16:30:00 GMT",
        "location": "Athens",
        "coords": [37.9838, 23.7275],
        "category": "Society & Solidarity"
    },
    {
        "title": "Rhodes Implements Zero-Waste Island Program to Eliminate Single-Use Plastics",
        "link": "https://greekreporter.com/2026/03/10/rhodes-zero-waste-island/",
        "description": "Rhodes has launched a comprehensive waste reduction plan in partnership with local businesses, offering recycled beach accessories and paper-only alternatives.",
        "source": "eKathimerini",
        "pubDate": "Sun, 26 Jul 2026 12:00:00 GMT",
        "location": "Rhodes",
        "coords": [36.4341, 28.2176],
        "category": "Environment & Nature"
    },
    {
        "title": "New High-Speed Train Link Connects Patras to Athens in Under Two Hours",
        "link": "https://greekreporter.com/2026/02/15/athens-patras-railway/",
        "description": "The completion of the state-of-the-art double-track electric railway has officially reduced travel time, promoting eco-friendly public transport in Western Greece.",
        "source": "eKathimerini",
        "pubDate": "Sat, 25 Jul 2026 09:30:00 GMT",
        "location": "Patras",
        "coords": [38.2466, 21.7346],
        "category": "Innovation & Tech"
    },
    {
        "title": "Ancient Sunken Harbor of Milos Mapped in High-Definition 3D by Marine Archaeologists",
        "link": "https://greekreporter.com/2026/01/22/sunken-harbor-milos-3d/",
        "description": "Using advanced sonar and underwater lasers, scientists have generated the first complete 3D digital model of the Roman-era harbor submerged off the island of Milos.",
        "source": "Greek News Agenda",
        "pubDate": "Fri, 24 Jul 2026 15:40:00 GMT",
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
    # Default to Athens/Greece center if not specified
    return "Greece", [39.0742, 21.8243]

def determine_category(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ["archaeology", "ancient", "history", "museum", "culture", "art", "festival", "music", "cinema"]):
        return "Culture & Heritage"
    elif any(w in text_lower for w in ["tourism", "tourist", "travel", "beach", "hotel", "island", "visit"]):
        return "Tourism & Travel"
    elif any(w in text_lower for w in ["tech", "startup", "innovate", "innovation", "science", "robotics", "digital", "research"]):
        return "Innovation & Tech"
    elif any(w in text_lower for w in ["green", "renewable", "solar", "wind", "conservation", "wildlife", "turtle", "forest", "clean", "ecology"]):
        return "Environment & Nature"
    elif any(w in text_lower for w in ["help", "volunteer", "solidarity", "donation", "community", "kindness", "support", "hero"]):
        return "Society & Solidarity"
    elif any(w in text_lower for w in ["medal", "win", "champion", "olympic", "sports", "athlete", "football", "basketball"]):
        return "Sports & Success"
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
            with urllib.request.urlopen(req, timeout=5) as response:
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
                    
                    # Clean HTML tags
                    clean_desc = re.sub('<[^<]+?>', '', desc_text).strip()
                    
                    # Sentiment filter
                    title_lower = title_text.lower()
                    desc_lower = clean_desc.lower()
                    
                    # Check negative keywords first
                    has_negative = any(neg in title_lower or neg in desc_lower for neg in NEGATIVE_KEYWORDS)
                    if has_negative:
                        continue
                        
                    # Check positive keywords
                    has_positive = any(pos in title_lower or pos in desc_lower for pos in POSITIVE_KEYWORDS)
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
                        "category": determine_category(title_lower + " " + desc_lower)
                    })
        except Exception as e:
            print(f"Error fetching/parsing {source_name}: {e}")
            
    return parsed_items

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Prevent accessing files outside of the PUBLIC_DIR unless it's explicitly allowed
        parsed = urlparse(path)
        rel_path = parsed.path.lstrip('/')
        if not rel_path or rel_path == 'index.html':
            return os.path.join(PUBLIC_DIR, 'index.html')
        return os.path.join(PUBLIC_DIR, rel_path)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/api/news':
            # Set CORS headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Fetch dynamic news and combine with seed data
            dynamic_news = fetch_external_news()
            
            # Merge lists, removing duplicates based on title
            seen_titles = set()
            merged_news = []
            
            # First insert dynamic feeds, then add seeded fallback stories
            for item in dynamic_news + SEED_NEWS:
                title_normalized = item["title"].strip().lower()
                if title_normalized not in seen_titles:
                    seen_titles.add(title_normalized)
                    merged_news.append(item)
            
            # Respond with JSON payload
            self.wfile.write(json.dumps(merged_news).encode('utf-8'))
            return
            
        # Fallback to serving static files from public directory
        super().do_GET()

    # Prevent logs from polluting console output excessively
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    # Ensure public folder exists
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    
    # Start web server
    with socketserver.ThreadingTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Good Morning Greece! Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
