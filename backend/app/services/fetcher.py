import httpx
from ..core.config import settings


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

        import feedparser

        feed = feedparser.parse(response.text)

        papers = []
        for entry in feed.entries:
            papers.append(
                {
                    "title": entry.title.replace("\n", " ").strip(),
                    "summary": entry.summary.replace("\n", " ").strip(),
                    "link": entry.link,
                    "source": "arXiv",
                    "published": entry.get("published", ""),
                }
            )
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
            articles.append(
                {
                    "title": article.get("title", ""),
                    "summary": article.get("description", "")
                    or article.get("content", "")
                    or "",
                    "link": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "NewsAPI"),
                    "published": article.get("publishedAt", ""),
                }
            )
        return articles
    except Exception as e:
        print(f"Error fetching from NewsAPI: {e}")
        return []


def fetch_all_items(max_total: int = 10) -> list[dict]:
    """Fetches from both sources and return combined list."""
    per_source = max_total // 2

    arxiv_items = fetch_arxiv_papers(per_source)
    news_items = fetch_news_articles(per_source)

    all_items = arxiv_items + news_items

    filtered = [item for item in all_items if item["title"] and item["summary"]]

    print(f"[fetcher] Fetched {len(filtered)} items total")
    return filtered
