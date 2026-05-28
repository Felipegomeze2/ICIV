"""International news snapshot for the ICIV dashboard.

This feed is informational only: it enriches the news tab and does not enter the
ICIV or Pulse score. It uses Google News RSS as a public aggregator and keeps
only international, non-Venezuelan sources from an explicit whitelist.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import pandas as pd
import requests

import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from iciv.config import settings  # noqa: E402


QUERIES = [
    "Venezuela investment climate economy",
    "Venezuela oil production sanctions economy",
    "Venezuela inflation currency economy",
    "Venezuela business investment risk",
]

SOURCE_WHITELIST = [
    "Reuters",
    "Associated Press",
    "AP News",
    "BBC",
    "Financial Times",
    "Bloomberg",
    "CNBC",
    "CNN",
    "NPR",
    "The Guardian",
    "Al Jazeera",
    "France 24",
    "DW",
    "Deutsche Welle",
    "The New York Times",
    "The Washington Post",
    "The Economist",
    "Miami Herald",
    "Yahoo Finance",
    "MarketWatch",
    "Barron's",
    "The Wall Street Journal",
    "Forbes",
    "Voice of America",
    "The Independent",
    "ABC News",
    "CBS News",
    "NBC News",
    "Politico",
    "Semafor",
    "Euronews",
]

LOCAL_SOURCE_BLOCKLIST = [
    ".ve",
    "El Nacional",
    "TalCual",
    "Efecto Cocuyo",
    "La Patilla",
    "Runrunes",
    "Ultimas Noticias",
    "Últimas Noticias",
    "Globovision",
    "Globovisión",
    "Venezuela Analysis",
    "Venezuelanalysis",
    "Telesur",
]

HEADERS = {
    "User-Agent": "ICIV academic dashboard news snapshot/1.0",
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
}


@dataclass(frozen=True)
class NewsItem:
    published_at: str
    title: str
    url: str
    source: str
    query: str
    feed: str
    fuente: str = "Google News RSS filtered to international whitelist"


def _empty() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["published_at", "title", "url", "source", "query", "feed", "fuente"]
    )


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _parse_source(item: ET.Element) -> tuple[str, str]:
    source = item.find("source")
    if source is None:
        return "", ""
    return _clean_text(source.text), source.attrib.get("url", "")


def _source_allowed(source_name: str, source_url: str) -> bool:
    source_blob = f"{source_name} {source_url}".lower()
    if any(block.lower() in source_blob for block in LOCAL_SOURCE_BLOCKLIST):
        return False
    return any(name.lower() in source_blob for name in SOURCE_WHITELIST)


def _parse_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return ""


def _fetch_query(query: str, timeout: int = 30) -> list[NewsItem]:
    encoded = quote_plus(query)
    feed_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    response = requests.get(feed_url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items: list[NewsItem] = []
    for item in root.findall(".//item"):
        source_name, source_url = _parse_source(item)
        if not _source_allowed(source_name, source_url):
            continue

        title = _clean_text(item.findtext("title"))
        link = _clean_text(item.findtext("link"))
        if not title or not link:
            continue

        items.append(
            NewsItem(
                published_at=_parse_date(item.findtext("pubDate")),
                title=title,
                url=link,
                source=source_name,
                query=query,
                feed=feed_url,
            )
        )
    return items


def fetch_international_news() -> pd.DataFrame:
    rows: list[NewsItem] = []
    errors: list[str] = []

    for query in QUERIES:
        try:
            rows.extend(_fetch_query(query))
        except Exception as exc:
            errors.append(f"{query}: {exc}")

    if not rows:
        if errors:
            print("International news: sin filas reales; " + " | ".join(errors[:3]))
        df = _empty()
        df.to_csv(settings.paths.raw_international_news, index=False, encoding="utf-8-sig")
        return df

    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        if row.url in seen:
            continue
        seen.add(row.url)
        deduped.append(row.__dict__)

    df = pd.DataFrame(deduped)
    df["published_at_sort"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    df = df.sort_values("published_at_sort", ascending=False).drop(columns=["published_at_sort"])
    df = df.head(40).reset_index(drop=True)
    df.to_csv(settings.paths.raw_international_news, index=False, encoding="utf-8-sig")
    print(f"International news: {len(df)} filas reales -> {settings.paths.raw_international_news}")
    if errors:
        print("International news warnings: " + " | ".join(errors[:3]))
    return df


if __name__ == "__main__":
    fetch_international_news()
