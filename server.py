import http.server
import socketserver
import json
import os
import datetime
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
import re
import html
from urllib.parse import urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor

PORT = int(os.environ.get("PORT", 8000))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'news_cache.json')

REFRESH_SECONDS = 3600       # fetch fresh news every hour
RETRY_SECONDS = 600          # retry sooner when a fetch fails
MAX_STORIES = 24
MAX_STORY_AGE_DAYS = 4       # drop anything older than this, even if a feed still lists it

# Targeted Google News searches, each aimed at an inherently upbeat topic area, plus a
# couple of direct feeds. Real article links come straight from the feed (Google News
# links redirect to the original publisher article).
RSS_FEEDS = [
    ("Google News", "https://news.google.com/rss/search?q=Greece+(culture+OR+heritage+OR+archaeology+OR+museum)+when:3d&hl=en-US&gl=US&ceid=US:en", "en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(tourism+OR+travel+OR+island)+when:3d&hl=en-US&gl=US&ceid=US:en", "en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(innovation+OR+startup+OR+technology+OR+research)+when:3d&hl=en-US&gl=US&ceid=US:en", "en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(renewable+OR+environment+OR+conservation+OR+wildlife)+when:3d&hl=en-US&gl=US&ceid=US:en", "en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(award+OR+championship+OR+medal+OR+wins)+when:3d&hl=en-US&gl=US&ceid=US:en", "en"),
    ("Google News", "https://news.google.com/rss/search?q=Greece+(charity+OR+volunteer+OR+community)+when:3d&hl=en-US&gl=US&ceid=US:en", "en"),
    ("Keep Talking Greece", "https://www.keeptalkinggreece.com/feed/", "en"),
    ("Greek Reporter", "https://greekreporter.com/feed/", "en"),
]

# Greek-language search queries: fetched in Greek, translated to English for display and
# keyword filtering, with the original Greek text kept alongside so users can search in Greek too.
GREEK_QUERIES = [
    "Ελλάδα (πολιτισμός OR αρχαιολογία OR μουσείο) when:3d",
    "Ελλάδα (τουρισμός OR καινοτομία OR τεχνολογία) when:3d",
    "Ελλάδα (βραβείο OR πρωτάθλημα OR εθελοντές) when:3d",
    "Ελλάδα (περιβάλλον OR φύση OR ανακύκλωση) when:3d",
]
for _q in GREEK_QUERIES:
    RSS_FEEDS.append(("Google News", f"https://news.google.com/rss/search?q={quote_plus(_q)}&hl=el&gl=GR&ceid=GR:el", "el"))

# Keyword matching works on whole words, so "war" no longer blocks "award" or "software",
# and "art" no longer matches "start". A trailing "*" marks a stem that matches any ending
# ("injur*" -> injured, injuries). Plain words also match simple plurals/verb forms.

# Keywords that disqualify a story from the "good news" feed
NEGATIVE_KEYWORDS = [
    "crime", "murder*", "kill", "killed", "kills", "killing", "dead", "death*", "die", "dies", "died",
    "fire", "fires", "blaze", "disaster*", "earthquake*", "flood*", "collapse*", "risk*",
    "crash*", "drown*", "war", "wars", "attack*", "terror*", "injur*", "arrest*", "scandal*",
    "protest*", "strike", "strikes", "riot*", "corrupt*", "lawsuit*", "fraud*", "shooting*",
    "assault*", "abuse*", "migrant crisis", "recession*", "sanction*", "clash*",
    "election*", "opposition", "government*", "minister*", "parliament*", "party", "parties",
    "arms sales", "human rights", "missing", "warship*", "massacre*", "alarm*",
    "smuggl*", "illegal*", "detain*", "tension*", "dispute*", "controvers*", "suicide*",
    "body found", "suspect*", "trial", "trials", "court", "courts", "sentenced", "jail*", "prison*",
    "steal*", "stole", "stolen", "theft*", "robbed", "robber*", "loot*",
    "vandal*", "burglar*", "heist*", "hostage*", "kidnap*", "explosion*",
    "wildfire*", "damaged", "destroyed", "closure*", "shut down", "layoff*", "bankrupt*",
    "nightmare*", "harrowing", "seasick", "chaos", "chaotic", "stranded", "delay", "delays", "delayed",
    "cancel*", "warning*", "danger*", "emergenc*", "outbreak*", "sick", "illness*", "hospitali*",
    "tax", "taxes", "price hike*", "inflation", "deadline", "applications", "vouchers",
    "call for proposals", "beneficiar*", "heatwave*", "heat wave*", "storm*",
    "obituary", "passed away", "mourn*", "funeral*", "victim*", "shipwreck*",
]

# Keyword -> category mapping, checked in order against title+description
CATEGORY_KEYWORDS = [
    ("Environment & Nature", ["environment*", "climate", "renewable*", "solar", "wind farm*", "wildlife", "turtle*",
                              "forest*", "recycl*", "clean energy", "nature", "conservation", "biodiversity",
                              "organic", "reforest*", "tree planting", "marine park*", "dolphin*", "monk seal*", "bird*"]),
    ("Innovation & Tech", ["tech", "technology", "startup*", "innovat*", "research*", "scien*", "robot*", "ai",
                           "artificial intelligence", "digital", "satellite*", "engineer*", "university",
                           "universities", "invent*", "app", "apps", "data center*", "space"]),
    ("Sports & Success", ["olympi*", "champion*", "medal*", "award*", "win", "wins", "winning", "won", "victory",
                          "athlete*", "football", "basketball", "tournament*", "record", "gold", "prize*", "trophy"]),
    ("Society & Solidarity", ["volunteer*", "charity", "charities", "community", "donat*", "solidarity", "school*",
                              "children", "education", "food bank*", "kindness", "rescue*", "adopt*"]),
    ("Tourism & Travel", ["tourism", "tourist*", "travel*", "visitor*", "hotel*", "flight*", "airline*", "island*", "beach*", "cruise*",
                          "destination*"]),
    ("Culture & Heritage", ["ancient", "archaeolog*", "museum*", "heritage", "byzantine", "temple*", "festival*",
                            "art", "arts", "artist*", "history", "historic*", "unesco", "acropolis", "excavat*",
                            "concert*", "theatre", "theater", "film*", "cinema", "music*", "exhibition*",
                            "gastronomy", "cuisine", "chef*", "wine*", "olive oil"]),
]

def _keyword_regex(keywords):
    parts = []
    for kw in keywords:
        if kw.endswith("*"):
            parts.append(re.escape(kw[:-1]) + r"\w*")
        else:
            parts.append(re.escape(kw) + r"(?:s|es|ed|ing)?")
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b", re.IGNORECASE)

NEGATIVE_RE = _keyword_regex(NEGATIVE_KEYWORDS)
CATEGORY_RES = [(category, _keyword_regex(kws)) for category, kws in CATEGORY_KEYWORDS]

# Greek places -> [lat, lon]. Checked against the story text to pin it on the map.
# Several spellings point to the same place; "display" names are title-cased keys.
LOCATION_COORDS = {
    # Cities & towns
    "athens": [37.9838, 23.7275], "piraeus": [37.9475, 23.6367], "glyfada": [37.8600, 23.7530],
    "thessaloniki": [40.6401, 22.9444], "patras": [38.2466, 21.7346], "heraklion": [35.3387, 25.1442],
    "chania": [35.5138, 24.0180], "rethymno": [35.3644, 24.4822], "agios nikolaos": [35.1904, 25.7164],
    "larissa": [39.6390, 22.4191], "volos": [39.3621, 22.9422], "ioannina": [39.6650, 20.8537],
    "kavala": [40.9396, 24.4069], "alexandroupoli": [40.8457, 25.8730], "kalamata": [37.0389, 22.1142],
    "nafplio": [37.5675, 22.8017], "corinth": [37.9386, 22.9322], "sparta": [37.0733, 22.4270],
    "lamia": [38.9006, 22.4339], "trikala": [39.5550, 21.7679],
    "kozani": [40.3007, 21.7887], "serres": [41.0857, 23.5487],
    "xanthi": [41.1349, 24.8880], "komotini": [41.1222, 25.4064], "kastoria": [40.5193, 21.2687],
    "florina": [40.7820, 21.4098], "veria": [40.5242, 22.2029], "katerini": [40.2719, 22.5025],
    "chalkida": [38.4636, 23.6019], "agrinio": [38.6218, 21.4078], "preveza": [38.9597, 20.7517],
    "parga": [39.2850, 20.4000], "missolonghi": [38.3687, 21.4295], "monemvasia": [36.6872, 23.0560],
    "nafpaktos": [38.3924, 21.8277], "metsovo": [39.7700, 21.1820], "edessa": [40.8020, 22.0470],
    # Islands
    "crete": [35.2401, 24.8093], "rhodes": [36.4341, 28.2176], "santorini": [36.3932, 25.4615],
    "thira": [36.3932, 25.4615], "mykonos": [37.4467, 25.3289], "zakynthos": [37.7870, 20.8999],
    "zante": [37.7870, 20.8999], "kefalonia": [38.1754, 20.5692], "cephalonia": [38.1754, 20.5692],
    "corfu": [39.6243, 19.9217], "kerkyra": [39.6243, 19.9217], "samos": [37.7561, 26.8524],
    "milos": [36.7294, 24.4286], "naxos": [37.1036, 25.3766], "paros": [37.0853, 25.1488],
    "lesvos": [39.1100, 26.5547], "lesbos": [39.1100, 26.5547], "chios": [38.3680, 26.1358],
    "kos": [36.8930, 27.2877], "syros": [37.4500, 24.9000], "tinos": [37.5400, 25.1600],
    "andros": [37.8333, 24.9333], "sifnos": [36.9720, 24.7090],
    "folegandros": [36.6200, 24.9200], "amorgos": [36.8333, 25.9000], "hydra": [37.3500, 23.4667],
    "aegina": [37.7467, 23.4285], "spetses": [37.2620, 23.1580], "poros": [37.5000, 23.4500],
    "skiathos": [39.1622, 23.4906], "skopelos": [39.1214, 23.7270], "alonissos": [39.1490, 23.8670],
    "skyros": [38.9000, 24.5667], "evia": [38.4636, 23.6019], "euboea": [38.4636, 23.6019],
    "lefkada": [38.8333, 20.7000], "ithaca": [38.3667, 20.7167], "paxos": [39.2000, 20.1833],
    "kythira": [36.2500, 23.0000], "karpathos": [35.5070, 27.2130], "symi": [36.6150, 27.8380],
    "patmos": [37.3167, 26.5500], "leros": [37.1500, 26.8500], "kalymnos": [36.9500, 26.9833],
    "ikaria": [37.6000, 26.1667], "lemnos": [39.9167, 25.2500], "limnos": [39.9167, 25.2500],
    "thasos": [40.7800, 24.7100], "samothrace": [40.4833, 25.5333], "kastellorizo": [36.1480, 29.5940],
    "elafonisos": [36.4870, 22.9690], "gavdos": [34.8420, 24.0850],
    # Regions, mountains & landmarks
    "acropolis": [37.9715, 23.7267], "delphi": [38.4801, 22.5010], "olympia": [37.6384, 21.6303],
    "meteora": [39.7217, 21.6303], "mount olympus": [40.0855, 22.3585], "olympus": [40.0855, 22.3585],
    "mount athos": [40.1570, 24.3260], "athos": [40.1570, 24.3260], "epidaurus": [37.5960, 23.0790],
    "mycenae": [37.7308, 22.7562], "knossos": [35.2980, 25.1630], "vergina": [40.4870, 22.3190],
    "sounion": [37.6500, 24.0250],
    "zagori": [39.8700, 20.8000], "vikos": [39.9600, 20.7300], "pelion": [39.4000, 23.0500],
    "halkidiki": [40.3500, 23.5000], "chalkidiki": [40.3500, 23.5000], "mani": [36.6500, 22.4000],
    "peloponnese": [37.4856, 22.3653], "attica": [38.0500, 23.8000], "epirus": [39.6650, 20.8537],
    "thessaly": [39.6390, 22.4191], "thrace": [41.1222, 25.4064],
    "cyclades": [37.0853, 25.1488], "dodecanese": [36.4341, 28.2176], "ionian islands": [38.5, 20.5],
    "sporades": [39.1622, 23.4906], "prespa": [40.7800, 21.0500], "lake kerkini": [41.2100, 23.1300],
    "nestos": [41.0000, 24.8000], "samaria": [35.2960, 23.9580], "elafonissi": [35.2710, 23.5410],
    "balos": [35.5830, 23.5880], "navagio": [37.8590, 20.6250], "oia": [36.4618, 25.3753],
}
# A whole-word regex per place, longest names first so "mount olympus" wins over "olympus".
LOCATION_RES = [
    (place, coords, re.compile(r"\b" + re.escape(place) + r"\b", re.IGNORECASE))
    for place, coords in sorted(LOCATION_COORDS.items(), key=lambda kv: -len(kv[0]))
]

def categorize(text):
    """Returns the matched category, or None if nothing indicates a positive story."""
    for category, pattern in CATEGORY_RES:
        if pattern.search(text):
            return category
    return None

VALID_CATEGORIES = [c for c, _ in CATEGORY_KEYWORDS]

def llm_filter_positive_stories(entries):
    """Second-pass sentiment check via Claude: the keyword filter above only excludes
    known-bad topics, so it misses nuance (e.g. a crime story about an otherwise
    positive-sounding place). Confirms each keyword-passed story is genuinely positive
    news and re-checks its category. Falls back to the keyword-only result if no
    ANTHROPIC_API_KEY is configured or the API call fails."""
    if not entries:
        return entries
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return entries

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        stories_text = "\n".join(
            f"{i}. [{e['category']}] {e['title']} — {e['description']}"
            for i, e in enumerate(entries)
        )

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            system=(
                "You review a feed of Greek/Greece-related news stories that have already passed a "
                "keyword filter. For each numbered story, decide if it is genuinely positive, uplifting, "
                "or good news (not merely neutral, and not negative news that happens to mention a "
                "positive-sounding topic like a museum, a school, or a tourist site). Also confirm or "
                "correct its category."
            ),
            output_config={"format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "index": {"type": "integer"},
                                    "is_positive": {"type": "boolean"},
                                    "category": {"type": "string", "enum": VALID_CATEGORIES},
                                },
                                "required": ["index", "is_positive", "category"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["results"],
                    "additionalProperties": False,
                },
            }},
            messages=[{"role": "user", "content": stories_text}],
        )

        text_block = next(b.text for b in response.content if b.type == "text")
        verdicts = {r["index"]: r for r in json.loads(text_block)["results"]}

        filtered = []
        for i, entry in enumerate(entries):
            verdict = verdicts.get(i)
            if verdict is None or not verdict["is_positive"]:
                continue
            entry["category"] = verdict["category"]
            filtered.append(entry)
        return filtered
    except Exception as e:
        print(f"LLM sentiment filter failed, using keyword-only filtering: {e}")
        return entries

def locate(title, description=""):
    """Find the place a story is about. The title is checked first (it's the strongest signal),
    then the description; within a text, the earliest-mentioned place wins.
    Returns (location_name, coords), or ("Greece", None) for nationwide stories that don't
    name a place - those are listed in the feed but not pinned at a made-up spot on the map."""
    for text in (title, description):
        best = None
        for place, coords, pattern in LOCATION_RES:
            m = pattern.search(text or "")
            if m and (best is None or m.start() < best[0]):
                best = (m.start(), place, coords)
        if best:
            return best[1].title(), best[2]
    return "Greece", None

def is_positive_story(text):
    return NEGATIVE_RE.search(text) is None

def translate_to_english(text, source_lang="el"):
    """Best-effort translation via Google's public translate endpoint. Falls back to the
    original text on any failure so a translation hiccup never drops a whole story."""
    if not text:
        return text
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl={source_lang}&tl=en&dt=t&q={quote_plus(text)}"
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            return ''.join(segment[0] for segment in data[0] if segment[0])
    except Exception as e:
        print(f"Translation failed, using original text: {e}")
        return text

def parse_rss_date(date_str):
    if not date_str:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def _title_words(title):
    return {w for w in re.findall(r"\w+", title.lower()) if len(w) > 2}

def _is_near_duplicate(title, kept_word_sets, threshold=0.55):
    """Catches the same story syndicated under slightly different headlines
    (e.g. "Over 30 million airline seats for Greece" vs "Over 30 million seats offered on flights")."""
    words = _title_words(title)
    if not words:
        return False
    for other in kept_word_sets:
        overlap = len(words & other) / len(words | other)
        if overlap >= threshold:
            return True
    return False

def _clean_description(desc_html, title_text):
    """Google News descriptions are just the headline + publisher wrapped in HTML, which made
    cards repeat their title. Return '' in that case so the card shows the headline only."""
    text = html.unescape(re.sub('<[^<]+?>', ' ', desc_html or ""))
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if text.lower().startswith(title_text.lower()[:40]):
        return ""
    return text

def fetch_feed(source_name, url, feed_lang, cutoff):
    """Fetch one RSS feed and return the positive, recent stories in it."""
    stories = []
    try:
        req = urllib.request.Request(url, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
    except Exception as e:
        print(f"Error fetching RSS from {source_name} ({url[:80]}...): {e}")
        return stories

    channel = root.find('channel')
    if channel is None:
        return stories

    for item in channel.findall('item')[:20]:
        title = item.find('title')
        title_text = html.unescape((title.text or "").strip()) if title is not None else ""
        link = item.find('link')
        link_text = (link.text or "").strip() if link is not None else ""
        if not title_text or not link_text:
            continue

        # Skip old stories before doing any (slow) translation work.
        pub_date_el = item.find('pubDate')
        pub_dt = parse_rss_date(pub_date_el.text if pub_date_el is not None else None)
        if pub_dt is None:
            continue  # undated items can't be shown as "fresh", so leave them out
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
        if pub_dt < cutoff:
            continue

        # Google News titles look like "Headline - Publisher"; split that out as the source.
        item_source = source_name
        title_match = re.match(r'^(.*)\s+-\s+([^-]+)$', title_text)
        if source_name == "Google News" and title_match:
            title_text = title_match.group(1).strip()
            item_source = title_match.group(2).strip()

        desc = item.find('description')
        clean_desc = _clean_description(desc.text if desc is not None else "", title_text)

        # Greek-language items get translated for filtering/display; the original
        # Greek stays around so a Greek search term can still match the story.
        original_title, original_desc = None, None
        if feed_lang != "en":
            original_title, original_desc = title_text, clean_desc
            title_text = translate_to_english(title_text, feed_lang)
            clean_desc = translate_to_english(clean_desc, feed_lang) if clean_desc else ""

        combined_text = f"{title_text} {clean_desc}"
        if not is_positive_story(combined_text):
            continue
        category = categorize(combined_text)
        if category is None:
            continue

        location, coords = locate(title_text, clean_desc)
        stories.append({
            "title": title_text,
            "link": link_text,
            "description": clean_desc[:320],
            "source": item_source,
            "location": location,
            "coords": coords,
            "category": category,
            "pubDate": pub_dt.astimezone(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "originalTitle": original_title,
            "originalDescription": original_desc[:320] if original_desc else None,
            "_sort_dt": pub_dt.timestamp(),
        })
    return stories

def fetch_positive_rss_news():
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=MAX_STORY_AGE_DAYS)

    # Fetch all feeds in parallel - doing them one after another (plus translations) took minutes.
    collected = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch_feed, name, url, lang, cutoff) for name, url, lang in RSS_FEEDS]
        for fut in futures:
            collected.extend(fut.result())

    # Newest first, drop exact and near-duplicate headlines.
    candidates, kept_words = [], []
    for entry in sorted(collected, key=lambda x: x["_sort_dt"], reverse=True):
        if _is_near_duplicate(entry["title"], kept_words):
            continue
        kept_words.append(_title_words(entry["title"]))
        entry.pop("_sort_dt", None)
        candidates.append(entry)
        if len(candidates) >= MAX_STORIES * 2:
            break

    filtered = llm_filter_positive_stories(candidates)

    # Keep a mix of topics so one busy category (e.g. a sports championship) can't fill the feed.
    per_category_cap = max(4, MAX_STORIES // 3)
    counts, final = {}, []
    for entry in filtered:
        if counts.get(entry["category"], 0) >= per_category_cap:
            continue
        counts[entry["category"]] = counts.get(entry["category"], 0) + 1
        final.append(entry)
        if len(final) >= MAX_STORIES:
            break
    return final

# Background cache management
# The cache holds real fetched stories only. If a fetch fails we keep serving the last good
# batch (with its timestamp, so the page can say how old it is) instead of inventing stories.
news_cache = {"updatedAt": None, "stories": []}
cache_lock = threading.Lock()

def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

def update_cache_from_rss():
    global news_cache
    print("Fetching fresh positive Greek news from RSS feeds...")
    stories = fetch_positive_rss_news()
    if not stories:
        print("Warning: RSS fetch returned no usable stories; keeping the previous batch.")
        return False

    payload = {"updatedAt": _now_iso(), "stories": stories}
    with cache_lock:
        news_cache = payload
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving news cache to file: {e}")
    print(f"Cached {len(stories)} fresh news stories.")
    return True

def load_cache_file():
    """Load the last saved batch (any age) so the page has something real to show while
    the first fetch runs. Old-format caches (a bare list with no timestamp) are ignored."""
    global news_cache
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("stories"):
            with cache_lock:
                news_cache = data
            print(f"Loaded {len(data['stories'])} stories from cache (updated {data.get('updatedAt')}).")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error loading news cache file: {e}")

def background_news_loop():
    while True:
        try:
            success = update_cache_from_rss()
        except Exception as e:
            print(f"Error in background news loop: {e}")
            success = False
        time.sleep(REFRESH_SECONDS if success else RETRY_SECONDS)

# ---- "On This Day" history widget ----
# Wikipedia's "On this day" feed lists notable events, births and holidays for a calendar date.
# We put Greece-related entries first, then fill up with a few world events.
try:
    from zoneinfo import ZoneInfo
    ATHENS_TZ = ZoneInfo("Europe/Athens")
except Exception:  # tz database unavailable: fall back to a fixed offset
    ATHENS_TZ = datetime.timezone(datetime.timedelta(hours=2))

ONTHISDAY_URL = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month:02d}/{day:02d}"
WIKI_HEADERS = {
    # Wikimedia asks API clients to identify themselves.
    "User-Agent": "GoodMorningGreece/1.0 (https://github.com/samira-jpg/good-morning-greece)",
    "Accept": "application/json",
}
GREEK_HISTORY_RE = re.compile(
    r"\b(?:Greece|Greek|Greeks|Hellenic|Hellenistic|Athens|Athenian|Sparta|Spartan|Byzantine|Byzantium|"
    r"Constantinople|Crete|Cretan|Thessaloniki|Salonica|Rhodes|Corfu|Peloponnese|Delphi|Olympia|"
    r"Macedon|Ancient Macedonia|Aegean|Ionian|Piraeus|Epirus|Thessaly|Thrace|Dodecanese|Cyclades|"
    r"Acropolis|Parthenon|Minoan|Mycenaean|Venizelos|Kapodistrias)\b"
)
MAX_GREEK_ITEMS = 6
MAX_WORLD_ITEMS = 4

onthisday_cache = {"date": None, "payload": None, "failed_at": 0}
onthisday_lock = threading.Lock()

def _wiki_entry(raw, kind):
    pages = raw.get("pages") or []
    page = pages[0] if pages else {}
    page_titles = " ".join((p.get("titles") or {}).get("normalized", "") for p in pages)
    thumb = (page.get("thumbnail") or {}).get("source")
    return {
        "year": raw.get("year"),
        "text": raw.get("text", "").strip(),
        "kind": kind,  # "event", "birth" or "holiday"
        "link": ((page.get("content_urls") or {}).get("desktop") or {}).get("page"),
        "pageTitle": (page.get("titles") or {}).get("normalized"),
        "thumbnail": thumb,
        "greek": bool(GREEK_HISTORY_RE.search(raw.get("text", "") + " " + page_titles)),
    }

def fetch_on_this_day(today):
    url = ONTHISDAY_URL.format(month=today.month, day=today.day)
    req = urllib.request.Request(url, headers=WIKI_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    entries, seen = [], set()
    for kind, key in (("event", "selected"), ("event", "events"), ("birth", "births"), ("holiday", "holidays")):
        for raw in data.get(key) or []:
            entry = _wiki_entry(raw, kind)
            dedupe_key = (entry["year"], entry["text"][:60])
            if not entry["text"] or dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            entries.append(entry)

    # Greek history first (events before births/holidays), then a handful of world events.
    kind_order = {"event": 0, "holiday": 1, "birth": 2}
    greek = sorted((e for e in entries if e["greek"]), key=lambda e: kind_order[e["kind"]])[:MAX_GREEK_ITEMS]
    world = [e for e in entries if not e["greek"] and e["kind"] == "event"][:MAX_WORLD_ITEMS]
    items = sorted(greek + world, key=lambda e: (not e["greek"], kind_order[e["kind"]], -(e["year"] or 0)))
    return {
        "date": today.strftime("%Y-%m-%d"),
        "label": f"{today.day} {today.strftime('%B')}",
        "items": items,
        "source": "Wikipedia",
    }

def get_on_this_day():
    """Returns today's (Athens time) history entries, fetched at most once per day."""
    today = datetime.datetime.now(ATHENS_TZ).date()
    with onthisday_lock:
        if onthisday_cache["date"] == today and onthisday_cache["payload"]:
            return onthisday_cache["payload"]
        # After a failure, wait 10 minutes before asking Wikipedia again.
        if time.time() - onthisday_cache["failed_at"] < 600:
            return _onthisday_error(today)
        try:
            payload = fetch_on_this_day(today)
            onthisday_cache.update(date=today, payload=payload)
            return payload
        except Exception as e:
            print(f"Error fetching On This Day from Wikipedia: {e}")
            onthisday_cache["failed_at"] = time.time()
            return _onthisday_error(today)

def _onthisday_error(today):
    return {"date": today.strftime("%Y-%m-%d"), "label": f"{today.day} {today.strftime('%B')}",
            "items": [], "error": "History is unavailable right now."}

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path)
        rel_path = parsed.path.lstrip('/')
        if not rel_path or rel_path == 'index.html':
            return os.path.join(PUBLIC_DIR, 'index.html')
        return os.path.join(PUBLIC_DIR, rel_path)

    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path in ('/api/news', '/api/onthisday'):
            if parsed_url.path == '/api/news':
                with cache_lock:
                    payload = dict(news_cache)
            else:
                payload = get_on_this_day()
            body = json.dumps(payload).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
            return

        super().do_GET()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    load_cache_file()

    # Fetch in the background so the server starts answering immediately
    # (hosts like Render fail a deploy if the port doesn't open quickly).
    updater_thread = threading.Thread(target=background_news_loop, daemon=True)
    updater_thread.start()

    with socketserver.ThreadingTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Good Morning Greece! Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
