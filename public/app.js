// Good Morning Greece! Dashboard Client Application

// 1. Philosophical Quotes Seed Data
const WISDOM_QUOTES = [
    {
        greek: "« Ἡ εὐδαιμονία τῶν αὐτάρκων ἐστί. »",
        phonetic: "He eudaimonia ton autarkon esti.",
        english: "Happiness depends upon ourselves.",
        author: "Aristotle"
    },
    {
        greek: "« Ἓν οἶδα ὅτι οὐδὲν οἶδα. »",
        phonetic: "En oida hoti ouden oida.",
        english: "The only true wisdom is in knowing you know nothing.",
        author: "Socrates"
    },
    {
        greek: "« Ἀρχὴ ἥμισυ παντός. »",
        phonetic: "Arche hemisy pantos.",
        english: "The beginning is the half of every action.",
        author: "Plato"
    },
    {
        greek: "« Μηδὲν ὧν οὐκ ἔχεις ἐπιθυμεῖν, ἀλλ’ ἀναλογίζεσθαι ὅτι τῶν ἐχόντων τὰ πλεῖστα πάλαι ἂν ηὔχου. »",
        phonetic: "Meden hon ouk eheis epithymein...",
        english: "Do not spoil what you have by desiring what you have not; remember that what you now have was once among the things you only hoped for.",
        author: "Epicurus"
    },
    {
        greek: "« Τὰ πάντα ῥεῖ. »",
        phonetic: "Ta panta rhei.",
        english: "Everything flows, nothing stands still.",
        author: "Heraclitus"
    },
    {
        greek: "« Εὐδαιμονίη οὐκ ἐν βοσκήμασιν οἰκεῖ οὐδὲ ἐν χρυσῷ· ψυχὴ οἰκητήριον δαίμονος. »",
        phonetic: "Eudaimonie ouk en boskemasin oikei...",
        english: "Happiness resides not in possessions, and not in gold, happiness dwells in the soul.",
        author: "Democritus"
    },
    {
        greek: "« Ὁ δὲ ἀνεξέταστος βίος οὐ βιωτὸς ἀνθρώπῳ. »",
        phonetic: "Ho de anexetastos bios ou biotos anthropo.",
        english: "The unexamined life is not worth living.",
        author: "Socrates"
    }
];

// 2. Ticker Feeds Fallback Seed Data (used only if news hasn't loaded yet)
const TICKER_FALLBACK_ITEMS = [
    "Crete: Local community raises €15,000 for children's hospital wing.",
    "Patras: Youth volunteer group cleans and restores 3km of coastal cycling paths.",
    "Naxos: Organic potato harvest exceeds expectations, securing local agricultural jobs.",
    "Thessaloniki: University researchers develop new eco-friendly water purification filter.",
    "Epirus: Rare Balkan Chamois goat population rebounds in Vikos Gorge National Park.",
    "Athens: Urban garden collective transforms 3 abandoned lots into green spaces.",
    "Paros: Wind surfing champions organize free clinic for local youngsters.",
    "Samos: Wine cooperative wins international bio-agriculture prize in Brussels.",
    "Larissa: Rural libraries launch mobile book trucks to reach distant villages."
];

// Global State
let map;
let markers = [];
let newsData = [];
let activeCategory = 'all';
let searchQuery = '';
let currentQuoteIndex = 0;

// Weather Station Configuration
const CITIES = [
    { name: "Athens", lat: 37.9838, lon: 23.7275, sunHrs: 12.0 },
    { name: "Thessaloniki", lat: 40.6401, lon: 22.9444, sunHrs: 11.5 },
    { name: "Heraklion", lat: 35.3387, lon: 25.1442, sunHrs: 13.0 },
    { name: "Patras", lat: 38.2466, lon: 21.7346, sunHrs: 12.2 },
    { name: "Rhodes", lat: 36.4341, lon: 28.2176, sunHrs: 13.5 }
];

// 3. Document Ready Initialization
document.addEventListener("DOMContentLoaded", () => {
    initClock();
    initMap();
    initQuotes();
    initTicker();
    fetchNews();
    fetchWeather();

    // Event Listeners
    document.getElementById("news-search").addEventListener("input", handleSearch);
    document.getElementById("category-filters").addEventListener("click", handleCategoryFilter);
    document.getElementById("next-quote").addEventListener("click", rotateQuote);
});

// 4. Clock and Date Component
function initClock() {
    const clockEl = document.getElementById("live-clock");
    const dateEl = document.getElementById("live-date");
    
    function updateClock() {
        const now = new Date();
        
        // Format time in Athens timezone
        const optionsTime = { timeZone: "Europe/Athens", hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
        clockEl.textContent = now.toLocaleTimeString("en-US", optionsTime);
        
        // Format date in Athens timezone
        const optionsDate = { timeZone: "Europe/Athens", weekday: 'long', day: 'numeric', month: 'short' };
        dateEl.textContent = now.toLocaleDateString("en-US", optionsDate);
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

// 5. Leaflet Map Component
function initMap() {
    // Center map on Greece's mainland and Aegean region
    map = L.map('map', {
        center: [39.0742, 22.8243],
        zoom: 6.5,
        zoomControl: true,
        scrollWheelZoom: false // disable scroll wheel zoom by default to prevent accidental scroll
    });

    // Style tiles in a modern clean light format
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
        minZoom: 5
    }).addTo(map);
}

// 6. Dynamic Optimism Index Circular Gauge Component
function updateOptimismIndex(newsItems) {
    const fillEl = document.getElementById("gauge-index-fill");
    const textEl = document.getElementById("gauge-index-text");
    const headerValEl = document.getElementById("header-index-val");
    const statusEl = document.getElementById("gauge-status");
    const descEl = document.getElementById("gauge-description");

    // Dynamic Positivity Index Calculation
    // Base is 76% (Greece is generally positive!). Adding increments for positive news count
    const countBonus = Math.min(12, newsItems.length * 0.8);
    const score = Math.round(76 + countBonus);
    
    // Animate radial gauge
    // Circumference of radial progress circle (r=40) is 2 * PI * 40 = 251.2
    const circumference = 251.2;
    const offset = circumference - (score / 100) * circumference;
    
    fillEl.style.strokeDashoffset = offset;
    textEl.textContent = `${score}%`;
    headerValEl.textContent = `${score}%`;

    // Dynamic statuses and text descriptions
    if (score >= 90) {
        statusEl.textContent = "Radiant Optimism";
        statusEl.style.color = "var(--color-green)";
        descEl.textContent = "Greece is absolutely glowing! Outstanding levels of solar output, massive cultural achievements, and widespread community solidarity projects drive today's historic rating.";
    } else if (score >= 80) {
        statusEl.textContent = "Very Optimistic";
        statusEl.style.color = "var(--color-greek-blue)";
        descEl.textContent = "A wonderful morning in Greece! High solar generation combined with exciting archaeological findings and athletic triumphs have generated a highly positive outlook across the country.";
    } else {
        statusEl.textContent = "Optimistic";
        statusEl.style.color = "var(--color-gold)";
        descEl.textContent = "Positive trends are developing. Local solidary networks are active, and tourism returns bring cheer and financial support to island communities.";
    }
}

// 7. Ancient Philosophy Quote Component
function initQuotes() {
    rotateQuote();
}

function rotateQuote() {
    const grEl = document.getElementById("quote-gr");
    const phonEl = document.getElementById("quote-phonetic");
    const enEl = document.getElementById("quote-en");
    const authEl = document.getElementById("quote-author");

    const quote = WISDOM_QUOTES[currentQuoteIndex];
    
    // Add slide-out fade effect
    const cardEl = document.querySelector(".quote-card");
    cardEl.style.opacity = "0.2";
    cardEl.style.transform = "translateY(5px)";
    cardEl.style.transition = "all 0.25s ease";

    setTimeout(() => {
        grEl.textContent = quote.greek;
        phonEl.textContent = quote.phonetic;
        enEl.textContent = `"${quote.english}"`;
        authEl.textContent = `— ${quote.author}`;
        
        cardEl.style.opacity = "1";
        cardEl.style.transform = "translateY(0)";
    }, 250);

    currentQuoteIndex = (currentQuoteIndex + 1) % WISDOM_QUOTES.length;
}

// 8. Live Weather & Sunshine Tracker Component
async function fetchWeather() {
    const tableBody = document.getElementById("weather-table-body");
    const headerSunshine = document.getElementById("header-sunshine");
    
    try {
        let totalSunHrs = 0;
        let validCities = 0;
        let rowsHtml = "";

        // Fetch forecasts from free Open-Meteo API
        const promises = CITIES.map(async (city) => {
            const response = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${city.lat}&longitude=${city.lon}&current=temperature_2m,weather_code&timezone=auto`);
            const data = await response.json();
            return {
                name: city.name,
                temp: Math.round(data.current.temperature_2m),
                code: data.current.weather_code,
                sunHrs: city.sunHrs
            };
        });

        const weatherResults = await Promise.all(promises);
        
        tableBody.innerHTML = "";
        
        weatherResults.forEach(cityData => {
            const skyDetails = getWeatherCodeDetails(cityData.code);
            totalSunHrs += cityData.sunHrs;
            validCities++;

            rowsHtml += `
                <tr>
                    <td class="weather-city">${cityData.name}</td>
                    <td class="weather-temp">${cityData.temp}°C</td>
                    <td class="weather-sky"><i class="${skyDetails.icon}"></i> ${skyDetails.text}</td>
                    <td class="weather-sun">${cityData.sunHrs}h</td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = rowsHtml;

        // Calculate average sunshine
        if (validCities > 0) {
            const avgSun = (totalSunHrs / validCities).toFixed(1);
            headerSunshine.textContent = `${avgSun} hrs`;
        }
    } catch (error) {
        console.error("Error fetching weather data:", error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; color: var(--color-red);">
                    <i class="fa-solid fa-triangle-exclamation"></i> Offline weather forecast.
                </td>
            </tr>
        `;
    }
}

// Map Open-Meteo weather codes to UI descriptors and fontawesome icons
function getWeatherCodeDetails(code) {
    if (code === 0) return { text: "Sunny", icon: "fa-solid fa-sun icon-gold animate-pulse" };
    if (code === 1 || code === 2 || code === 3) return { text: "Clear", icon: "fa-solid fa-cloud-sun icon-blue" };
    if (code === 45 || code === 48) return { text: "Misty", icon: "fa-solid fa-smog icon-blue" };
    if (code >= 51 && code <= 67) return { text: "Shower", icon: "fa-solid fa-cloud-showers-heavy icon-blue" };
    if (code >= 80 && code <= 82) return { text: "Rain", icon: "fa-solid fa-cloud-rain icon-blue" };
    return { text: "Cloudy", icon: "fa-solid fa-cloud icon-blue" };
}

// 9. Scrolling Positivity Ticker Component
function initTicker(items) {
    const tickerEl = document.getElementById("positivity-ticker");
    tickerEl.innerHTML = "";

    const tickerItems = (items && items.length > 0) ? items : TICKER_FALLBACK_ITEMS;

    tickerItems.forEach(text => {
        const itemSpan = document.createElement("span");
        itemSpan.className = "ticker-item";
        itemSpan.textContent = text;
        tickerEl.appendChild(itemSpan);
    });
}

// 10. Fetch & Aggregate Good News Component
async function fetchNews() {
    const feedContainer = document.getElementById("news-feed");
    const countEl = document.getElementById("news-count");
    
    try {
        const response = await fetch('/api/news');
        newsData = await response.json();

        renderNews();
        updateOptimismIndex(newsData);
        initTicker(newsData.map(item => `${item.location}: ${item.title}`));
    } catch (error) {
        console.error("Error fetching news:", error);
        feedContainer.innerHTML = `
            <div class="feed-loader" style="color: var(--color-red);">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; margin-bottom: 8px;"></i>
                <p>Could not connect to news feed server.</p>
                <button onclick="fetchNews()" class="next-quote-btn" style="margin-top: 10px;">Retry</button>
            </div>
        `;
    }
}

// Render filtered news items in list and map markers
function renderNews() {
    const feedContainer = document.getElementById("news-feed");
    const countEl = document.getElementById("news-count");
    
    // Clear current lists and markers
    feedContainer.innerHTML = "";
    clearMapMarkers();

    // Apply category & search query filters
    const filteredNews = newsData.filter(item => {
        const matchesCategory = activeCategory === 'all' || item.category === activeCategory;
        const searchString = `${item.title} ${item.description} ${item.location} ${item.source} ${item.originalTitle || ''} ${item.originalDescription || ''}`.toLowerCase();
        const matchesSearch = searchString.includes(searchQuery.toLowerCase());
        return matchesCategory && matchesSearch;
    });

    // Update count badge
    countEl.textContent = `${filteredNews.length} Stories`;

    if (filteredNews.length === 0) {
        feedContainer.innerHTML = `
            <div class="feed-loader">
                <i class="fa-regular fa-face-smile-wink" style="font-size: 32px; margin-bottom: 8px; color: var(--color-text-muted);"></i>
                <p>No matching stories found. Check other positive tags!</p>
            </div>
        `;
        return;
    }

    // Render cards
    filteredNews.forEach((item, index) => {
        const card = document.createElement("div");
        card.className = "news-card";
        card.setAttribute("data-cat", item.category);
        card.setAttribute("data-id", index);

        // Format nice tag class
        let tagClass = "culture";
        if (item.category.includes("Nature")) tagClass = "nature";
        else if (item.category.includes("Tech")) tagClass = "tech";
        else if (item.category.includes("Solidarity")) tagClass = "solidarity";
        else if (item.category.includes("Success")) tagClass = "sports";

        card.innerHTML = `
            <div class="card-top-meta">
                <span class="card-category ${tagClass}">${item.category}</span>
                <span class="card-source">${item.source}</span>
            </div>
            <h3>${item.title}</h3>
            ${item.originalTitle ? `<p class="card-original-title"><i class="fa-solid fa-language"></i> ${item.originalTitle}</p>` : ''}
            <p>${item.description}</p>
            <div class="card-bottom-meta">
                <span class="card-location"><i class="fa-solid fa-location-dot"></i> ${item.location}</span>
                <span>${formatDate(item.pubDate)}</span>
            </div>
            <a href="${item.link}" target="_blank" rel="noopener" class="hero-link card-read-link">Read Full <i class="fa-solid fa-arrow-up-right-from-square"></i></a>
        `;

        // Card Click Handler: pan/select on the card body, but let the "Read Full" link behave normally
        card.addEventListener("click", (e) => {
            if (e.target.closest(".card-read-link")) return;
            selectNewsItem(item, card);
        });

        feedContainer.appendChild(card);

        // Add Marker on map if coordinate is valid and not generic center of Greece
        if (item.coords && item.coords.length === 2 && !(item.coords[0] === 39.0742 && item.coords[1] === 21.8243)) {
            addMapMarker(item, index, card);
        }
    });
}

// 11. Interactive Map Marker Helpers
function addMapMarker(item, idIndex, cardElement) {
    const customIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div class="pulsing-marker-pin" id="marker-pin-${idIndex}" title="${item.location}"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });

    const marker = L.marker(item.coords, { icon: customIcon }).addTo(map);
    
    // Bind Leaflet popup card
    const popupContent = `
        <div class="map-popup-card">
            <span>${item.category}</span>
            <h4>${item.location}</h4>
            <p>${item.title}</p>
            <a href="${item.link}" target="_blank" class="hero-link">Read Full <i class="fa-solid fa-arrow-up-right-from-square"></i></a>
        </div>
    `;
    
    marker.bindPopup(popupContent, { offset: [0, -5] });
    
    // Pin click hooks selection in feed
    marker.on("click", () => {
        // Highlight corresponding card in feed list
        document.querySelectorAll(".news-card").forEach(c => c.classList.remove("selected-card"));
        cardElement.classList.add("selected-card");
        cardElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });

    markers.push(marker);
}

function clearMapMarkers() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
}

function selectNewsItem(item, cardElement) {
    // Toggle styles
    document.querySelectorAll(".news-card").forEach(c => c.classList.remove("selected-card"));
    cardElement.classList.add("selected-card");
    
    // Pan map to location with slight zoom
    if (item.coords && item.coords.length === 2) {
        map.setView(item.coords, 9, { animate: true, duration: 1.2 });
        
        // Find matching marker and pop open popup card
        markers.forEach(m => {
            const latLng = m.getLatLng();
            if (latLng.lat === item.coords[0] && latLng.lng === item.coords[1]) {
                setTimeout(() => m.openPopup(), 1200);
            }
        });
    }
}

// 12. Filtering Event Handlers
function handleSearch(e) {
    searchQuery = e.target.value;
    renderNews();
}

function handleCategoryFilter(e) {
    const btn = e.target.closest(".filter-btn");
    if (!btn) return;

    // Toggle active class
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    activeCategory = btn.getAttribute("data-category");
    renderNews();
}

// Helper: Format Date String
function formatDate(dateStr) {
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString("en-US", { day: 'numeric', month: 'short' });
    } catch {
        return dateStr;
    }
}
