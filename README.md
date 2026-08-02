# Good Morning Greece! 🇬🇷☀️

An interactive, light-themed positive news and optimism dashboard focused on Greece. Styled with the colors of the Greek flag (Aegean blues and white) and warm gold accents.

## 🌟 Features
*   **Interactive Positivity Map**: Pulsing hotspots mapping positive events across Greece (Athens, Crete, Thessaloniki, Rhodes, Zakynthos, Delphi, Milos, and more).
*   **Curated News Scraper**: Combines live English-language feeds from *Greek Reporter* and *eKathimerini*, filtering out negative sentiment and stories.
*   **Greece Optimism Index**: An animated radial dial displaying a daily positivity score based on active stories and weather conditions.
*   **Sunshine & Weather Tracker**: Live weather conditions and sunshine statistics for major Greek cities via the Open-Meteo API.
*   **Ancient Wisdom Widget**: Rotating quotes from ancient Greek philosophers (Socrates, Plato, Aristotle, Epicurus, Democritus) in Greek script, phonetics, and English translation.
*   **Daily Hero Spotlight**: Features local foundations and heroes driving positive change in Greece.
*   **Solidarity Ticker**: Running bottom marquee displaying micro-news of kindness, environmental recoveries, and local community successes.

---

## 🚀 Local Execution
To run the server locally, ensure you have Python 3.x installed and execute:
```bash
python server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## ☁️ Deploying to Render

Render makes it incredibly easy to host Python applications directly from GitHub for free.

### Step 1: Create a GitHub Repository
1. Go to [GitHub](https://github.com) and log in.
2. Create a new repository (e.g., `good-morning-greece`).
3. Push your project files to your new GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Good Morning Greece dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/good-morning-greece.git
   git push -u origin main
   ```

### Step 2: Create a Web Service on Render
1. Go to [Render](https://render.com) and sign in.
2. In the dashboard, click the **New +** button and select **Web Service**.
3. Select **Connect repository** and choose your `good-morning-greece` repository.

### Step 3: Configure Settings
Configure the following options on the creation screen:
*   **Name**: `good-morning-greece` (or any name you prefer)
*   **Language**: `Python`
*   **Branch**: `main`
*   **Region**: Select the region closest to you
*   **Build Command**: `pip install -r requirements.txt` (or leave it blank)
*   **Start Command**: `python server.py`
*   **Instance Type**: `Free`

### Step 4: Deploy!
1. Click **Deploy Web Service** at the bottom of the page.
2. Render will spin up the environment, download Python, and start your server.
3. Once the build log says `Good Morning Greece! Server running...`, your public URL (shown at the top left of the Render console) is live!
