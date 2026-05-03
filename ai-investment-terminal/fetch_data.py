#!/usr/bin/env python3
"""
AI Investment Intelligence Terminal — Daily Data Fetcher
Fetches stock data, YouTube videos, and news sentiment.
Run: python3 fetch_data.py
Run without YouTube: python3 fetch_data.py --skip-youtube
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import yfinance as yf
import feedparser
import requests

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

THEMES = [
    {
        "id": 1,
        "name": "AI Infrastructure & GPUs",
        "icon": "🖥️",
        "description": "The foundational compute layer powering every AI model. NVIDIA dominates with 80%+ data center GPU share. Sovereign AI buying is accelerating globally.",
        "market_size": {"2020": 15, "2023": 110, "2026e": 400, "2030e": 900},
        "upside_multiplier": 8.2,
        "relevance_trend": "PEAK",
        "why_now": "Every AI model needs compute. NVDA has 80% market share. Sovereign AI buying accelerating.",
        "key_voices": ["Jensen Huang", "Lisa Su", "Cathie Wood"],
        "top_stocks": ["NVDA", "AMD", "AVGO", "ASML", "MU", "TSM"],
        "youtube_query": "AI GPU stocks investing 2025 Jensen Huang NVDA",
    },
    {
        "id": 2,
        "name": "AI Agents & Autonomous Software",
        "icon": "🤖",
        "description": "The software intelligence layer — AI that acts autonomously. Every enterprise is replacing SaaS seats with AI agents that do the work end-to-end.",
        "market_size": {"2020": 2, "2023": 18, "2026e": 120, "2030e": 850},
        "upside_multiplier": 47.0,
        "relevance_trend": "RISING",
        "why_now": "2025 is the year of AI agents. Every enterprise replacing SaaS seats with agents.",
        "key_voices": ["Sam Altman", "Satya Nadella", "Jensen Huang"],
        "top_stocks": ["META", "GOOGL", "MSFT", "PLTR", "CRM", "SNOW"],
        "youtube_query": "AI agents autonomous software investing 2025",
    },
    {
        "id": 3,
        "name": "Physical AI & Robotics",
        "icon": "🦾",
        "description": "AI moving from screens into the physical world. Tesla Optimus, Figure, 1X are all shipping humanoid robots into factories in 2025.",
        "market_size": {"2020": 8, "2023": 35, "2026e": 150, "2030e": 1200},
        "upside_multiplier": 34.0,
        "relevance_trend": "RISING",
        "why_now": "Humanoid robots entering factories in 2025. Tesla Optimus, Figure, 1X all shipping.",
        "key_voices": ["Elon Musk", "Jensen Huang", "Masayoshi Son"],
        "top_stocks": ["TSLA", "ARM", "QCOM", "HON", "ABB"],
        "youtube_query": "physical AI robotics Tesla Optimus investing",
    },
    {
        "id": 4,
        "name": "AI Cybersecurity",
        "icon": "🛡️",
        "description": "AI-powered attack vectors demand AI-powered defense. Every breach makes security budgets grow 30%+. CrowdStrike is the category king.",
        "market_size": {"2020": 20, "2023": 55, "2026e": 140, "2030e": 350},
        "upside_multiplier": 6.4,
        "relevance_trend": "RISING",
        "why_now": "AI attacks require AI defense. Every breach makes security budgets grow 30%+.",
        "key_voices": ["George Kurtz", "Nikesh Arora"],
        "top_stocks": ["CRWD", "PANW", "ZS", "S", "FTNT"],
        "youtube_query": "AI cybersecurity stocks CRWD 2025",
    },
    {
        "id": 5,
        "name": "Power & Energy for AI",
        "icon": "⚡",
        "description": "Data centers are doubling power demand. Nuclear renaissance is underway. The grid is the bottleneck that AI can't train past.",
        "market_size": {"2020": 12, "2023": 28, "2026e": 95, "2030e": 400},
        "upside_multiplier": 14.0,
        "relevance_trend": "RISING",
        "why_now": "Data centers doubling power demand. Nuclear renaissance underway. Grid is the bottleneck.",
        "key_voices": ["Sam Altman", "Jensen Huang", "Bill Gates"],
        "top_stocks": ["CEG", "VST", "NRG", "VRT", "NEE", "ETR"],
        "youtube_query": "nuclear energy AI data centers power stocks",
    },
    {
        "id": 6,
        "name": "AI Networking & Data Centers",
        "icon": "🌐",
        "description": "Every GPU cluster needs ultra-low latency networking. Arista is winning the hyperscaler buildout. Vertiv powers the cooling and power infrastructure.",
        "market_size": {"2020": 45, "2023": 120, "2026e": 320, "2030e": 700},
        "upside_multiplier": 5.8,
        "relevance_trend": "PEAK",
        "why_now": "Every GPU cluster needs ultra-low latency networking. Arista winning the hyperscaler buildout.",
        "key_voices": ["Jensen Huang", "Andy Jassy"],
        "top_stocks": ["ANET", "CSCO", "DELL", "SMCI", "VRT"],
        "youtube_query": "AI data center networking stocks Arista",
    },
    {
        "id": 7,
        "name": "Sovereign AI & Geopolitical AI Race",
        "icon": "🌍",
        "description": "Every nation is building its own AI stack. $500B+ in sovereign AI deals were announced in 2024–2025 alone. The geopolitical AI arms race is accelerating.",
        "market_size": {"2020": 5, "2023": 30, "2026e": 200, "2030e": 1000},
        "upside_multiplier": 33.0,
        "relevance_trend": "EMERGING",
        "why_now": "Every nation building its own AI stack. $500B+ in sovereign AI deals announced 2024-2025.",
        "key_voices": ["Jensen Huang", "Dario Amodei", "Sam Altman"],
        "top_stocks": ["TSM", "NVDA", "GOOGL", "MSFT", "AMZN"],
        "youtube_query": "sovereign AI geopolitical tech race investing",
    },
    {
        "id": 8,
        "name": "AI in Healthcare & Drug Discovery",
        "icon": "🧬",
        "description": "AlphaFold cracked protein folding. AI is cutting drug discovery from 10 years to 18 months. The $600B healthcare AI market is just beginning.",
        "market_size": {"2020": 6, "2023": 22, "2026e": 90, "2030e": 613},
        "upside_multiplier": 27.0,
        "relevance_trend": "EMERGING",
        "why_now": "AlphaFold cracked protein folding. AI cutting drug discovery from 10 years to 18 months.",
        "key_voices": ["Demis Hassabis", "Dario Amodei", "Cathie Wood"],
        "top_stocks": ["ISRG", "RXRX", "NVDA", "ILMN", "TMO"],
        "youtube_query": "AI drug discovery healthcare stocks 2025",
    },
    {
        "id": 9,
        "name": "AI Finance & Fintech",
        "icon": "💰",
        "description": "AI is writing code, doing compliance, detecting fraud in real time. Banks and fintechs are spending billions. Palantir is the intelligence layer for finance.",
        "market_size": {"2020": 8, "2023": 38, "2026e": 130, "2030e": 420},
        "upside_multiplier": 11.0,
        "relevance_trend": "RISING",
        "why_now": "AI writing code, doing compliance, detecting fraud in real time. Banks spending billions.",
        "key_voices": ["Cathie Wood", "Alex Karp"],
        "top_stocks": ["PLTR", "HOOD", "COIN", "V", "MA"],
        "youtube_query": "AI fintech stocks Palantir finance 2025",
    },
    {
        "id": 10,
        "name": "Space & Satellite AI",
        "icon": "🚀",
        "description": "Starlink proved the model. Low earth orbit satellite internet is changing global connectivity. Rocket Lab is the NVDA of small satellite launches.",
        "market_size": {"2020": 4, "2023": 18, "2026e": 65, "2030e": 280},
        "upside_multiplier": 15.0,
        "relevance_trend": "EMERGING",
        "why_now": "Starlink proved the model. Low earth orbit satellite internet changing global connectivity.",
        "key_voices": ["Elon Musk", "Peter Beck"],
        "top_stocks": ["RKLB", "LUNR", "ASTS", "SPCE"],
        "youtube_query": "space satellite AI stocks RKLB 2025",
    },
    {
        "id": 11,
        "name": "Humanoid Robots",
        "icon": "🦿",
        "description": "Goldman predicts 1M humanoid robots by 2030. Tesla Optimus at $20K per unit changes labor economics forever. The 187x upside theme of the decade.",
        "market_size": {"2020": 1, "2023": 8, "2026e": 60, "2030e": 1500},
        "upside_multiplier": 187.0,
        "relevance_trend": "EMERGING",
        "why_now": "Goldman predicts 1M humanoid robots by 2030. Tesla Optimus at $20K per unit changes labor economics.",
        "key_voices": ["Elon Musk", "Jensen Huang", "Masayoshi Son"],
        "top_stocks": ["TSLA", "NVDA", "HON", "ABB"],
        "youtube_query": "humanoid robot stocks investing 2025",
    },
    {
        "id": 12,
        "name": "AI in Consumer & Media",
        "icon": "📱",
        "description": "Meta AI has 1B users. AI-generated content, personalized recommendations, and AI ads are driving a new wave of consumer tech revenue growth.",
        "market_size": {"2020": 10, "2023": 45, "2026e": 160, "2030e": 500},
        "upside_multiplier": 11.0,
        "relevance_trend": "RISING",
        "why_now": "Meta AI has 1B users. AI-generated content, recommendations, and ads driving revenue.",
        "key_voices": ["Mark Zuckerberg", "Sundar Pichai"],
        "top_stocks": ["META", "GOOGL", "NFLX", "SPOT", "SNAP"],
        "youtube_query": "AI consumer media META GOOGL stocks",
    },
]

PORTFOLIO_STOCKS = ["NVDA", "TSLA", "META", "TSM", "GOOGL", "PLTR", "CRWD", "AMD", "MU", "AVGO", "VRT", "ASML", "CEG", "ANET", "MSFT", "AMZN"]

KEY_VOICE_QUERIES = [
    "Jensen Huang investing AI 2025",
    "Elon Musk AI robotics stocks",
    "Sam Altman OpenAI investment thesis",
    "Cathie Wood ARK invest AI themes 2025",
    "Tom Nash stocks AI 2025",
]

RSS_FEEDS = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=TSLA",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=META",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=MSFT",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GOOGL",
    "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://techcrunch.com/feed/",
]

POSITIVE_WORDS = {"surge", "record", "breakthrough", "bullish", "growth", "rally", "beat", "profit",
                  "expand", "launch", "partnership", "wins", "dominates", "milestone", "soars",
                  "outperform", "upgrade", "raises", "strong", "exceeds", "positive", "gains"}
NEGATIVE_WORDS = {"crash", "warning", "miss", "bearish", "decline", "layoffs", "loss", "investigation",
                  "ban", "delay", "disappoints", "cuts", "drops", "falls", "sinks", "downgrade",
                  "weak", "concern", "risk", "volatility", "sell", "retreats", "tumbles"}

THEME_KEYWORDS = {
    1: ["GPU", "NVDA", "nvidia", "AMD", "semiconductor", "chip", "AVGO", "broadcom", "ASML", "memory", "MU", "TSM", "TSMC"],
    2: ["agent", "autonomous", "software", "Palantir", "PLTR", "CRM", "salesforce", "SNOW", "snowflake", "enterprise AI"],
    3: ["robot", "robotics", "Tesla", "TSLA", "Optimus", "humanoid", "ARM", "physical AI", "automation"],
    4: ["cybersecurity", "security", "CRWD", "crowdstrike", "PANW", "palo alto", "zero trust", "breach", "threat"],
    5: ["energy", "power", "nuclear", "CEG", "constellation", "VRT", "vertiv", "data center power", "grid", "VST"],
    6: ["networking", "data center", "ANET", "arista", "CSCO", "cisco", "DELL", "SMCI", "infrastructure"],
    7: ["sovereign", "geopolitical", "national AI", "government AI", "TSM", "TSMC", "chip war"],
    8: ["healthcare", "drug discovery", "ISRG", "RXRX", "recursion", "ILMN", "illumina", "biotech", "medical AI"],
    9: ["fintech", "finance", "PLTR", "palantir", "HOOD", "robinhood", "COIN", "coinbase", "trading AI"],
    10: ["space", "satellite", "RKLB", "rocket lab", "LUNR", "ASTS", "orbit", "SpaceX", "Starlink"],
    11: ["humanoid", "robot", "Tesla Optimus", "TSLA", "Figure", "bipedal", "labor"],
    12: ["consumer", "media", "META", "facebook", "GOOGL", "google", "NFLX", "netflix", "SPOT", "spotify", "SNAP"],
}

# ─── STOCK DATA ───────────────────────────────────────────────────────────────

def get_all_tickers():
    tickers = set(PORTFOLIO_STOCKS)
    for t in THEMES:
        tickers.update(t["top_stocks"])
    tickers.update(["^GSPC", "^IXIC", "^VIX"])
    return list(tickers)

def fetch_stock_data(tickers):
    print("📊 Fetching stock data...")
    results = {}
    portfolio_tickers = [t for t in tickers if not t.startswith("^")]

    # Batch download for speed
    try:
        data = yf.download(portfolio_tickers, period="3mo", interval="1d", progress=False, threads=True)
        print(f"   Downloaded price history for {len(portfolio_tickers)} tickers")
    except Exception as e:
        print(f"   ⚠️ Batch download failed: {e}")
        data = None

    for ticker in portfolio_tickers:
        try:
            info = {}
            try:
                tk = yf.Ticker(ticker)
                info = tk.info or {}
            except Exception as e:
                print(f"   ⚠️ Info fetch failed for {ticker}: {e}")

            price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose") or 0
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
            high_52w = info.get("fiftyTwoWeekHigh") or 0
            low_52w = info.get("fiftyTwoWeekLow") or 0
            market_cap = info.get("marketCap") or 0
            pe_trailing = info.get("trailingPE") or 0
            pe_forward = info.get("forwardPE") or 0

            # Compute period changes from history
            change_1d = change_1w = change_1m = change_3m = 0.0
            try:
                if data is not None and "Close" in data.columns.names:
                    # Multi-ticker download
                    if ticker in data["Close"].columns:
                        closes = data["Close"][ticker].dropna()
                    else:
                        closes = None
                else:
                    closes = None

                if closes is None or len(closes) < 2:
                    tk2 = yf.Ticker(ticker)
                    hist = tk2.history(period="3mo")
                    closes = hist["Close"].dropna() if not hist.empty else None

                if closes is not None and len(closes) >= 2:
                    latest = float(closes.iloc[-1])
                    if len(closes) >= 2:
                        change_1d = round((latest - float(closes.iloc[-2])) / float(closes.iloc[-2]) * 100, 2)
                    if len(closes) >= 6:
                        change_1w = round((latest - float(closes.iloc[-6])) / float(closes.iloc[-6]) * 100, 2)
                    if len(closes) >= 22:
                        change_1m = round((latest - float(closes.iloc[-22])) / float(closes.iloc[-22]) * 100, 2)
                    if len(closes) >= 63:
                        change_3m = round((latest - float(closes.iloc[-63])) / float(closes.iloc[-63]) * 100, 2)
                    if price == 0:
                        price = latest
                    if prev_close == 0 and len(closes) >= 2:
                        prev_close = float(closes.iloc[-2])
            except Exception as e:
                print(f"   ⚠️ History calc failed for {ticker}: {e}")

            # Signal
            if high_52w > 0 and price > 0:
                if price < 0.80 * high_52w:
                    signal = "BUY"
                elif price > 0.97 * high_52w:
                    signal = "SELL"
                else:
                    signal = "HOLD"
            else:
                signal = "HOLD"

            # Theme membership
            theme_ids = [t["id"] for t in THEMES if ticker in t["top_stocks"]]

            results[ticker] = {
                "price": round(float(price), 2),
                "prev_close": round(float(prev_close), 2),
                "change_1d": change_1d,
                "change_1w": change_1w,
                "change_1m": change_1m,
                "change_3m": change_3m,
                "52w_high": round(float(high_52w), 2),
                "52w_low": round(float(low_52w), 2),
                "market_cap": int(market_cap),
                "pe_ratio": round(float(pe_trailing), 2) if pe_trailing else 0,
                "forward_pe": round(float(pe_forward), 2) if pe_forward else 0,
                "signal": signal,
                "themes": theme_ids,
            }
            print(f"   ✓ {ticker}: ${price:.2f} ({change_1d:+.2f}%) [{signal}]")
        except Exception as e:
            print(f"   ✗ Failed {ticker}: {e}")
            results[ticker] = {
                "price": 0, "prev_close": 0, "change_1d": 0, "change_1w": 0,
                "change_1m": 0, "change_3m": 0, "52w_high": 0, "52w_low": 0,
                "market_cap": 0, "pe_ratio": 0, "forward_pe": 0, "signal": "HOLD", "themes": []
            }

    return results

def fetch_market_summary():
    print("📈 Fetching market summary...")
    result = {"sp500_change": 0.0, "nasdaq_change": 0.0, "vix": 0.0}
    try:
        sp = yf.Ticker("^GSPC")
        sp_hist = sp.history(period="2d")
        if len(sp_hist) >= 2:
            result["sp500_change"] = round((sp_hist["Close"].iloc[-1] - sp_hist["Close"].iloc[-2]) / sp_hist["Close"].iloc[-2] * 100, 2)
    except Exception as e:
        print(f"   ⚠️ S&P 500 failed: {e}")
    try:
        nq = yf.Ticker("^IXIC")
        nq_hist = nq.history(period="2d")
        if len(nq_hist) >= 2:
            result["nasdaq_change"] = round((nq_hist["Close"].iloc[-1] - nq_hist["Close"].iloc[-2]) / nq_hist["Close"].iloc[-2] * 100, 2)
    except Exception as e:
        print(f"   ⚠️ NASDAQ failed: {e}")
    try:
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="1d")
        if not vix_hist.empty:
            result["vix"] = round(float(vix_hist["Close"].iloc[-1]), 2)
    except Exception as e:
        print(f"   ⚠️ VIX failed: {e}")
    print(f"   S&P: {result['sp500_change']:+.2f}% | NASDAQ: {result['nasdaq_change']:+.2f}% | VIX: {result['vix']}")
    return result

# ─── YOUTUBE ──────────────────────────────────────────────────────────────────

def youtube_search(api_key, query, max_results=8, days_back=45):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "viewCount",
        "publishedAfter": cutoff,
        "key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        video_ids = [i["id"]["videoId"] for i in items]
        if not video_ids:
            return []

        # Get stats
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        stats_params = {"part": "statistics,snippet", "id": ",".join(video_ids), "key": api_key}
        stats_resp = requests.get(stats_url, params=stats_params, timeout=15)
        stats_resp.raise_for_status()
        stats_items = {v["id"]: v for v in stats_resp.json().get("items", [])}

        videos = []
        now = datetime.now(timezone.utc)
        for item in items:
            vid_id = item["id"]["videoId"]
            snippet = item["snippet"]
            stats = stats_items.get(vid_id, {}).get("statistics", {})
            published_str = snippet.get("publishedAt", "")
            try:
                published_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                days_ago = (now - published_dt).days
            except Exception:
                days_ago = 99

            view_count = int(stats.get("viewCount", 0))
            like_count = int(stats.get("likeCount", 0))

            # Recency weight
            if days_ago < 7:
                weight = 1.0
            elif days_ago < 15:
                weight = 0.7
            elif days_ago < 30:
                weight = 0.4
            else:
                weight = 0.2

            videos.append({
                "videoId": vid_id,
                "title": snippet.get("title", ""),
                "channelTitle": snippet.get("channelTitle", ""),
                "publishedAt": published_str,
                "days_ago": days_ago,
                "viewCount": view_count,
                "likeCount": like_count,
                "description": snippet.get("description", "")[:300],
                "thumbnail": f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg",
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "recency_weight": weight,
                "weighted_views": int(view_count * weight),
            })
        return videos
    except Exception as e:
        print(f"   ⚠️ YouTube search failed for '{query}': {e}")
        return []

def compute_buzz_score(videos_list):
    if not videos_list:
        return 0
    total_weighted = sum(v.get("weighted_views", 0) for v in videos_list)
    # Normalize: 1M weighted views = 100, scale logarithmically
    import math
    if total_weighted <= 0:
        return 0
    score = min(100, int(math.log10(max(total_weighted, 1)) / math.log10(1_000_000) * 100))
    return score

def fetch_youtube_data(api_key, skip=False):
    if skip or not api_key:
        if not api_key:
            print("⚠️  YOUTUBE_API_KEY not found — skipping YouTube data")
        else:
            print("⏭️  Skipping YouTube (--skip-youtube flag)")
        theme_videos = {t["id"]: {"videos": [], "buzz_score": 0} for t in THEMES}
        key_voice_videos = []
        return theme_videos, key_voice_videos

    print("🎥 Fetching YouTube data...")
    theme_videos = {}

    for theme in THEMES:
        print(f"   Searching theme {theme['id']}: {theme['name'][:30]}...")
        videos = youtube_search(api_key, theme["youtube_query"], max_results=8, days_back=45)
        buzz = compute_buzz_score(videos)
        theme_videos[theme["id"]] = {"videos": videos, "buzz_score": buzz}
        print(f"   → {len(videos)} videos, buzz: {buzz}/100")
        time.sleep(0.2)  # Rate limit courtesy

    print("   Fetching key voice videos...")
    key_voice_videos = []
    for query in KEY_VOICE_QUERIES:
        videos = youtube_search(api_key, query, max_results=3, days_back=30)
        for v in videos:
            v["query"] = query
        key_voice_videos.extend(videos)
        time.sleep(0.2)

    # Deduplicate by videoId
    seen = set()
    deduped = []
    for v in key_voice_videos:
        if v["videoId"] not in seen:
            seen.add(v["videoId"])
            deduped.append(v)
    key_voice_videos = sorted(deduped, key=lambda x: x.get("weighted_views", 0), reverse=True)[:12]

    print(f"   ✓ {len(key_voice_videos)} key voice videos")
    return theme_videos, key_voice_videos

# ─── NEWS SENTIMENT ───────────────────────────────────────────────────────────

def fetch_news():
    print("📰 Fetching news feeds...")
    articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                text = (title + " " + summary).lower()

                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                if pub:
                    try:
                        pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
                        if pub_dt < cutoff:
                            continue
                    except Exception:
                        pass

                articles.append({"title": title, "summary": summary, "text": text})
            print(f"   ✓ {feed_url[:50]}... → {len(feed.entries)} entries")
        except Exception as e:
            print(f"   ⚠️ Feed failed {feed_url[:50]}: {e}")

    return articles

def compute_theme_sentiment(theme_id, articles):
    keywords = THEME_KEYWORDS.get(theme_id, [])
    if not keywords:
        return 0.0, "NEUTRAL"

    relevant = [a for a in articles if any(kw.lower() in a["text"] for kw in keywords)]
    if not relevant:
        return 0.0, "NEUTRAL"

    pos = sum(1 for a in relevant for w in POSITIVE_WORDS if w in a["text"])
    neg = sum(1 for a in relevant for w in NEGATIVE_WORDS if w in a["text"])
    total = max(pos + neg, 1)
    score = round((pos - neg) / total * 100, 1)

    if score > 20:
        label = "BULLISH"
    elif score < -20:
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    return score, label

# ─── ASSEMBLE OUTPUT ──────────────────────────────────────────────────────────

def build_output(stock_data, market_summary, theme_yt, key_voice_videos, articles, portfolio_stocks):
    themes_out = []
    for theme in THEMES:
        theme_id = theme["id"]
        yt = theme_yt.get(theme_id, {"videos": [], "buzz_score": 0})
        sentiment_score, sentiment_label = compute_theme_sentiment(theme_id, articles)

        # Theme 1d change = avg of all theme stocks
        changes = [stock_data.get(t, {}).get("change_1d", 0) for t in theme["top_stocks"] if t in stock_data]
        theme_1d = round(sum(changes) / len(changes), 2) if changes else 0.0

        # My stocks in theme (from portfolio)
        my_stocks = [s for s in theme["top_stocks"] if s in portfolio_stocks]

        themes_out.append({
            "id": theme_id,
            "name": theme["name"],
            "icon": theme["icon"],
            "description": theme["description"],
            "market_size": theme["market_size"],
            "upside_multiplier": theme["upside_multiplier"],
            "relevance_trend": theme["relevance_trend"],
            "why_now": theme["why_now"],
            "key_voices": theme["key_voices"],
            "top_stocks": theme["top_stocks"],
            "my_stocks": my_stocks,
            "youtube_buzz_score": yt["buzz_score"],
            "youtube_videos": yt["videos"],
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "theme_1d_change": theme_1d,
        })

    portfolio_out = {t: stock_data[t] for t in portfolio_stocks if t in stock_data}

    return {
        "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "market_summary": market_summary,
        "themes": themes_out,
        "portfolio_stocks": portfolio_out,
        "all_stocks": stock_data,
        "key_voice_videos": key_voice_videos,
    }

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Investment Terminal Data Fetcher")
    parser.add_argument("--skip-youtube", action="store_true", help="Skip YouTube API calls (for testing)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🚀 AI Investment Intelligence Terminal — Data Fetcher")
    print("="*60 + "\n")

    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    skip_yt = args.skip_youtube

    # Step 1: Stocks
    all_tickers = get_all_tickers()
    stock_data = fetch_stock_data([t for t in all_tickers if not t.startswith("^")])

    # Step 2: Market summary
    market_summary = fetch_market_summary()

    # Step 3: YouTube
    theme_yt, key_voice_videos = fetch_youtube_data(api_key, skip=skip_yt)

    # Step 4: News
    articles = fetch_news()

    # Step 5: Build output
    print("\n📦 Assembling data.json...")
    output = build_output(stock_data, market_summary, theme_yt, key_voice_videos, articles, PORTFOLIO_STOCKS)

    # Write file
    out_path = Path(__file__).parent / "data" / "data.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    total_videos = sum(len(t["youtube_videos"]) for t in output["themes"])
    print(f"\n✅ Done. Updated {len(output['themes'])} themes, {len(stock_data)} stocks, {total_videos} theme videos + {len(key_voice_videos)} key voice videos.")
    print(f"📁 File: {out_path}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
