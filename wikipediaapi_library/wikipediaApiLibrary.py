import requests
import re
import wikipediaapi
import pandas as pd
import os
from dotenv import dotenv_values
import math
import time

config = dotenv_values("../.env.development")

NUMBER_OF_SECONDS_IN_AN_HOUR = 3600
REQUESTS_PER_HOUR = 5000
REQUESTS_PER_SEC = math.floor(REQUESTS_PER_HOUR//NUMBER_OF_SECONDS_IN_AN_HOUR)

WIKIMEDIA_CLIENT_ID = config.get("WIKIMEDIA_CLIENT_ID")
WIKIMEDIA_CLIENT_SECRET = config.get("WIKIMEDIA_CLIENT_SECRET")
WIKIMEDIA_ACCESS_TOKEN = config.get("WIKIMEDIA_ACCESS_TOKEN")
WIKIMEDIA_USER_AGENT = config.get("WIKIMEDIA_USER_AGENT")

wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent=WIKIMEDIA_USER_AGENT
)

# Retry / rate-limit settings
MAX_FETCH_RETRIES = 3
BACKOFF_BASE = 1  # seconds
RATE_SLEEP = 1 / REQUESTS_PER_SEC if REQUESTS_PER_SEC and REQUESTS_PER_SEC > 0 else 0


def fetch_page_with_retries(title, max_retries=MAX_FETCH_RETRIES):
    """Fetch a wikipediaapi Page with simple retries, backoff, and rate-limiting.

    Returns the Page object or None on failure.
    """
    attempt = 0
    backoff = BACKOFF_BASE
    while attempt < max_retries:
        try:
            if RATE_SLEEP > 0:
                time.sleep(RATE_SLEEP)
            page = wiki_wiki.page(title)
            return page
        except Exception as e:
            attempt += 1
            print(f"Error fetching page '{title}': {e} (attempt {attempt}/{max_retries})")
            time.sleep(backoff)
            backoff *= 2

    print(f"Failed to fetch page '{title}' after {max_retries} attempts")
    return None


# Gets articles from a category and all of its subcategories
def get_articles(category_name, level=0, max_level=2):
    if level > max_level:
        return set()

    print("get_articles for category_name:", category_name, "at level:", level)
    cat = fetch_page_with_retries(category_name)
    if cat is None:
        print(f"Unable to load category page: {category_name}")
        return set()
    articles = set()
    try:
        members = list(cat.categorymembers.values())
    except Exception as e:
        print(f"Error accessing category members for '{category_name}': {e}")
        return articles

    for c in members:
        try:
            print("current category member:", getattr(c, 'title', str(c)), "(ns=", getattr(c, 'ns', 'unknown'), ")")
            if c.ns == wikipediaapi.Namespace.CATEGORY and level < max_level:
                print("Recursing into subcategory:", c.title)
                articles = articles.union(get_articles(c.title, level=level+1, max_level=max_level))
            if c.ns == wikipediaapi.Namespace.MAIN:
                print("Adding article:", c.title)
                articles.add(c.title)
        except Exception as e:
            print(f"Error processing category member: {e}")

    print(f"Found {len(articles)} articles for '{category_name}' at level {level}")
    return articles

def get_page_content(page_title):
    print("Fetching page content for:", page_title)
    page = fetch_page_with_retries(page_title)
    if page is None:
        print(f"Failed to fetch page content for: {page_title}")
        return None

    try:
        content = page.text
    except Exception as e:
        print(f"Error reading page.text for '{page_title}': {e}")
        return None

    if content is None:
        print("Warning: no content returned for:", page_title)
    else:
        print(f"Fetched content length {len(content)} for: {page_title}")
    return content

categories = ["Category:Artificial_intelligence"]

ai_articles = set()

print("Starting article collection for categories:", categories)
for category in categories:
    titles = get_articles(category)
    print(f"Processing {len(titles)} titles from category: {category}")
    idx = 0
    for title in titles:
        idx += 1
        print(f"({idx}/{len(titles)}) Processing title:", title)
        content = get_page_content(title)
        ai_articles.add((title, content))

# Ensure a DataFrame exists so the later print(df.head()) won't fail
df = pd.DataFrame(list(ai_articles), columns=['Title', 'Content'])

# Save the cheese data in a csv file
if not os.path.exists('ai_articles.csv'):
    df = pd.DataFrame(ai_articles, columns=['Title', 'Content'])
    df.to_csv('ai_articles.csv', index=False)

# Validate success
print(f"Total ai articles: {len(ai_articles)}")
print(df.head())