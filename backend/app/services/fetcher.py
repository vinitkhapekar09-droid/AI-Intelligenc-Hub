import httpx
import feedparser
from datetime import datetime, timezone, timedelta
from ..core.config import settings

# Only fetch articles published within this many hours
MAX_AGE_HOURS = 48


def _is_recent(published: str, max_age_hours: int = MAX_AGE_HOURS) -> bool:
    """Check if an article is recent enough to include."""
    if not published:
        return True  # include if no date
    try:
        from email.utils import parsedate_to_datetime
        try:
            pub_date = parsedate_to_datetime(published)
        except Exception:
            pub_date = datetime.fromisoformat(
                published.replace("Z", "+00:00")
            )
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        return pub_date > cutoff
    except Exception:
        return True  # include if can't parse date


def fetch_arxiv_papers(max_results: int = 5) -> list[dict]:
    """Fetches latest AI papers from arXiv API."""
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": "cat:cs.AI OR cat:cs.LG OR cat:stat.ML",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
        feed = feedparser.parse(response.text)
        papers = []
        for entry in feed.entries:
            papers.append({
                "title": entry.title.replace("\n", " ").strip(),
                "summary": entry.summary.replace("\n", " ").strip(),
                "link": entry.link,
                "source": "arXiv",
                "published": entry.get("published", ""),
            })
        return papers
    except Exception as e:
        print(f"Error fetching from arXiv: {e}")
        return []


def fetch_news_articles(max_results: int = 5) -> list[dict]:
    """Fetches latest AI/ML news articles from NewsAPI."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "artificial intelligence OR machine learning OR LLM",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_results,
        "apiKey": settings.NEWS_API_KEY,
    }
    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
        data = response.json()
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "summary": article.get("description", "")
                    or article.get("content", "") or "",
                "link": article.get("url", ""),
                "source": article.get("source", {}).get("name", "NewsAPI"),
                "published": article.get("publishedAt", ""),
            })
        return articles
    except Exception as e:
        print(f"Error fetching from NewsAPI: {e}")
        return []


def fetch_rss_feed(url: str, source_name: str, max_results: int = 3) -> list[dict]:
    """Generic RSS feed fetcher."""
    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
        feed = feedparser.parse(response.text)
        articles = []
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "").strip()
            summary = (
                entry.get("summary", "")
                or entry.get("description", "")
                or ""
            ).strip()
            link = entry.get("link", "")
            published = entry.get("published", "") or entry.get("updated", "")

            if not title or not link:
                continue

            # Strip HTML tags from summary
            import re
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            summary = summary[:500] if summary else title

            articles.append({
                "title": title,
                "summary": summary,
                "link": link,
                "source": source_name,
                "published": published,
            })
        return articles
    except Exception as e:
        print(f"Error fetching RSS from {source_name}: {e}")
        return []


# Free RSS feeds — no API key needed
RSS_SOURCES = [
    ("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch AI"),
    ("https://venturebeat.com/category/ai/feed/", "VentureBeat AI"),
    ("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "The Verge AI"),
    ("https://www.technologyreview.com/feed/", "MIT Technology Review"),
    ("https://openai.com/news/rss/", "OpenAI"),
    ("https://blogs.microsoft.com/ai/feed/", "Microsoft AI"),
    ("https://blog.google/technology/ai/rss/", "Google AI"),
]


def fetch_rss_sources(max_per_source: int = 2) -> list[dict]:
    """Fetch from multiple RSS sources."""
    all_articles = []
    for url, name in RSS_SOURCES:
        articles = fetch_rss_feed(url, name, max_per_source)
        recent = [a for a in articles if _is_recent(a["published"])]
        all_articles.extend(recent)
        print(f"[fetcher] {name}: {len(recent)} recent articles")
    return all_articles


def fetch_all_items(max_total: int = 15) -> list[dict]:
    """Fetches from all sources and returns combined deduplicated list."""
    # Fetch from all sources
    arxiv_items = fetch_arxiv_papers(5)
    news_items = fetch_news_articles(5)
    rss_items = fetch_rss_sources(max_per_source=2)

    all_items = arxiv_items + rss_items + news_items

    # Filter empty items
    filtered = [
        item for item in all_items
        if item["title"] and item["summary"] and item["link"]
    ]

    # Deduplicate by link
    seen_links = set()
    deduped = []
    for item in filtered:
        if item["link"] not in seen_links:
            seen_links.add(item["link"])
            deduped.append(item)

    # Filter recent items (keep arXiv always since dates work differently)
    final = []
    for item in deduped:
        if item["source"] == "arXiv" or _is_recent(item["published"]):
            final.append(item)

    print(f"[fetcher] Fetched {len(final)} items total from all sources")
    return final[:max_total]
