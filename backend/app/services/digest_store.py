from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from ..models.content_item import ContentItem
from ..models.daily_issue import DailyIssue
from ..pipeline.normalizer import UnifiedDocument


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _serialize_item(item: ContentItem) -> dict:
    published_at = item.published_at.isoformat() if item.published_at else None
    return {
        "id": item.id,
        "doc_id": item.doc_id,
        "title": item.title,
        "summary": item.summary,
        "why_it_matters": item.why_it_matters,
        "source": item.source,
        "doc_type": item.doc_type,
        "url": item.url,
        "timestamp": published_at,
        "issue_date": item.issue_date.isoformat(),
        "rank": item.rank,
    }


def _serialize_issue(issue: DailyIssue, items: list[ContentItem]) -> dict:
    return {
        "id": issue.id,
        "issue_date": issue.issue_date.isoformat(),
        "title": issue.title,
        "summary": issue.summary,
        "status": issue.status,
        "published_at": issue.published_at.isoformat() if issue.published_at else None,
        "items": [_serialize_item(item) for item in items],
    }


def _build_issue_summary(items: list[dict], issue_date: date) -> str:
    research_count = sum(1 for item in items if item["doc_type"] == "research")
    news_count = sum(1 for item in items if item["doc_type"] == "news")
    lead_titles = ", ".join(item["title"] for item in items[:2])
    lead_text = f" Highlights include {lead_titles}." if lead_titles else ""
    return (
        f"{issue_date.strftime('%B %d, %Y')} covers {len(items)} important AI items: "
        f"{research_count} research papers and {news_count} news updates."
        f"{lead_text}"
    )


def store_daily_issue(
    db: Session,
    issue_date: date,
    documents: list[UnifiedDocument],
    summaries: list[dict],
) -> dict:
    summary_by_link = {
        summary.get("link"): summary
        for summary in summaries
        if summary.get("link")
    }

    issue = db.query(DailyIssue).filter(DailyIssue.issue_date == issue_date).first()
    issue_title = f"AI Research Briefing for {issue_date.strftime('%B %d, %Y')}"

    if issue is None:
        issue = DailyIssue(
            issue_date=issue_date,
            title=issue_title,
            status="published",
        )
        db.add(issue)
        db.flush()
    else:
        issue.title = issue_title
        issue.status = "published"
        db.query(ContentItem).filter(ContentItem.issue_id == issue.id).delete()
        db.flush()

    stored_items = []
    for rank, document in enumerate(documents, start=1):
	# Skip if doc_id already exists in another issue
        existing = db.query(ContentItem).filter(
            ContentItem.doc_id == document.doc_id
        ).first()
        if existing:
            continue

        matched_summary = summary_by_link.get(document.url, {})
        item = ContentItem(
            issue_id=issue.id,
            issue_date=issue_date,
            rank=rank,
            doc_id=document.doc_id,
            title=document.title,
            summary=matched_summary.get("simple_summary") or document.content,
            why_it_matters=matched_summary.get("why_it_matters"),
            source=document.source,
            doc_type=document.doc_type,
            url=document.url,
            published_at=_parse_datetime(document.timestamp),
        )
        db.add(item)
        stored_items.append(item)

    issue.summary = _build_issue_summary(
        [
            {"title": item.title, "doc_type": item.doc_type}
            for item in stored_items
        ],
        issue_date,
    )
    db.commit()

    refreshed_items = (
        db.query(ContentItem)
        .filter(ContentItem.issue_id == issue.id)
        .order_by(ContentItem.rank.asc())
        .all()
    )
    db.refresh(issue)
    return _serialize_issue(issue, refreshed_items)


def get_latest_issue(db: Session) -> dict | None:
    issue = (
        db.query(DailyIssue)
        .order_by(DailyIssue.issue_date.desc())
        .first()
    )
    if issue is None:
        return None

    items = (
        db.query(ContentItem)
        .filter(ContentItem.issue_id == issue.id)
        .order_by(ContentItem.rank.asc())
        .all()
    )
    return _serialize_issue(issue, items)


def get_issue_by_date(db: Session, issue_date: date) -> dict | None:
    issue = db.query(DailyIssue).filter(DailyIssue.issue_date == issue_date).first()
    if issue is None:
        return None

    items = (
        db.query(ContentItem)
        .filter(ContentItem.issue_id == issue.id)
        .order_by(ContentItem.rank.asc())
        .all()
    )
    return _serialize_issue(issue, items)


def list_recent_issues(db: Session, limit: int = 7) -> list[dict]:
    issues = (
        db.query(DailyIssue)
        .order_by(DailyIssue.issue_date.desc())
        .limit(limit)
        .all()
    )
    issue_ids = [issue.id for issue in issues]
    if not issue_ids:
        return []

    items = (
        db.query(ContentItem)
        .filter(ContentItem.issue_id.in_(issue_ids))
        .order_by(ContentItem.issue_date.desc(), ContentItem.rank.asc())
        .all()
    )

    items_by_issue_id: dict[int, list[ContentItem]] = {}
    for item in items:
        items_by_issue_id.setdefault(item.issue_id, []).append(item)

    return [
        _serialize_issue(issue, items_by_issue_id.get(issue.id, []))
        for issue in issues
    ]


def list_feed_items(
    db: Session,
    limit: int = 30,
    issue_date: date | None = None,
    doc_type: str | None = None,
) -> list[dict]:
    query = db.query(ContentItem)

    if issue_date is not None:
        query = query.filter(ContentItem.issue_date == issue_date)
    if doc_type:
        query = query.filter(ContentItem.doc_type == doc_type)

    items = (
        query.order_by(ContentItem.issue_date.desc(), ContentItem.rank.asc())
        .limit(limit)
        .all()
    )
    return [_serialize_item(item) for item in items]
