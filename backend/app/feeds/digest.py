from google import genai
from app.feeds import gemini_key
from app.feeds.fetcher import fetch_topic


class MissingKeyError(Exception):
    """No Gemini key is configured."""

TOPIC_LANGUAGE = {
    "finance": "pt",  # Portuguese
    "ai": "en",       # English
}

def _format_articles(articles):
    """Turn the list of article dicts into a numbered text block for the prompt."""
    lines=[]
    for i, a in enumerate(articles, start=1):
        lines.append(f"{i}. [{a['source']}] {a['title']}\n   {a['summary']}\n   {a['link']}")
    return "\n".join(lines)

def build_digest(topic):
      """Fetch articles for a topic and ask Gemini for a Markdown summary."""
      key = gemini_key.get_key()
      if not key:
          raise MissingKeyError
      articles = fetch_topic(topic)
      language = TOPIC_LANGUAGE[topic]
  
      prompt = (
          f"Write your ENTIRE response in {language}. Every heading, sentence, and word "
          f"must be in {language}.\n\n"
          f"You are a news editor. Below are {len(articles)} recent articles about '{topic}'. "
          f"Produce a concise digest in Markdown. Output ONLY the digest itself — no preamble, "
          f"no 'Here is...' opener, no closing remark.\n\n"
          f"Lead with the most important stories, group related ones under short '## ' headings, "
          f"and use bullet points so it's skimmable. Link sources by their URL where useful. "
          f"Don't invent anything that isn't in the articles.\n\n"
          f"Articles:\n{_format_articles(articles)}"
      )


      resp = genai.Client(api_key=key).models.generate_content(
          model="gemini-2.5-flash",
          contents=prompt,
      )
      return resp.text

