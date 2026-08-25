 # Curated RSS feeds, grouped by topic.
  # Each feed is a dict: a friendly name + the section-specific RSS URL.
  # We deliberately use SECTION feeds (not homepage firehoses) to stay on-topic.

FEEDS = [
      # --- Brazilian finance / markets (Portuguese) ---
      {"topic": "finance", "name": "Seu Dinheiro",          "url": "https://www.seudinheiro.com/feed/"},
      {"topic": "finance", "name": "Estadão E-Investidor",  "url": "https://einvestidor.estadao.com.br/feed/"},
      {"topic": "finance", "name": "Money Times",          "url": "https://www.moneytimes.com.br/feed/"},
      {"topic": "finance", "name": "Brazil Journal",       "url": "https://braziljournal.com/feed/"},
  
      # --- AI industry (English) ---
      {"topic": "ai", "name": "TechCrunch — AI",     "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
      {"topic": "ai", "name": "VentureBeat — AI",    "url": "https://venturebeat.com/category/ai/feed/"},
      {"topic": "ai", "name": "Ars Technica — AI",   "url": "https://arstechnica.com/ai/feed/"},
      {"topic": "ai", "name": "Hugging Face — Blog", "url": "https://huggingface.co/blog/feed.xml"},
]


def feeds_for(topic):
    """Return the list of feeds matching the given topic."""
    return [feed for feed in FEEDS if feed["topic"] == topic]