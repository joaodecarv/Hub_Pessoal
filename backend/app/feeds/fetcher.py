import feedparser
from app.feeds.sources import feeds_for

MAX_ARTICLES = 40  # max articles to return per topic
SUMMARY_CHARS = 300  # max chars to keep in summary (truncate longer summaries)

def _clean_entry(entry,source_name):
    """Turn one raw feed entry into a dict with the fields we care about."""
    summary=entry.get("summary", " ")
    return{
        "title": entry.get("title", " ").strip(),
        "link": entry.get("link", " "),
        "published": entry.get("published", " "),
        "summary": summary,
        "source": source_name
    }
    
    
def fetch_topic(topic):
    """Fetch, clean, and dedupe all articles for a topic ('ai' or 'finance')."""
    articles=[]
    seen_links=set()  # to dedupe articles by link
    
    for feed in feeds_for(topic):
          parsed = feedparser.parse(feed["url"])
          for entry in parsed.entries:
              link = entry.get("link", "")
              if not link or link in seen_links:
                  continue
              seen_links.add(link)
              articles.append(_clean_entry(entry, feed["name"]))
  
    return articles[:MAX_ARTICLES]