import requests, math, json, time, re, os
from bs4 import BeautifulSoup
from dotenv import dotenv_values
from collections import deque

config = dotenv_values(".env.development")

NUMBER_OF_SECONDS_IN_AN_HOUR = 3600
REQUESTS_PER_HOUR = 5000
REQUESTS_PER_SEC = math.floor(REQUESTS_PER_HOUR//NUMBER_OF_SECONDS_IN_AN_HOUR)

WIKIMEDIA_CLIENT_ID = config.get("WIKIMEDIA_CLIENT_ID")
WIKIMEDIA_CLIENT_SECRET = config.get("WIKIMEDIA_CLIENT_SECRET")
WIKIMEDIA_ACCESS_TOKEN = config.get("WIKIMEDIA_ACCESS_TOKEN")
WIKIMEDIA_USER_AGENT = config.get("WIKIMEDIA_USER_AGENT")

endpoints = {
    "search_page": {
        "provider" : "wikipedia",
        "language": "en",
        "endpoint": "search/page"
    },
    "fetch_content": {
        "provider" : "wikipedia",
        "language": "en",
        "endpoint": "page"
    }
}

BASE_URL = 'https://api.wikimedia.org/core/v1'
HEADERS = {
    "Authorization": f"Bearer {WIKIMEDIA_ACCESS_TOKEN}",
    'User-Agent': f"{WIKIMEDIA_USER_AGENT}",
}

def convert_wikipedia_key_into_file_safe(text):
    return re.sub(r'[^\w\s-]', '_', text).strip()

def load_existing_keys(filePath="seed.json"):
    try:
        with open(filePath, "r") as f:
            data = json.load(f)
            return {item["key"] for item in data}, data
    except (FileNotFoundError, json.JSONDecodeError):
        return set(), []

def save_keys(data, filepath="seed.json"):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def save_checkpoint(seen, queue, filepath):
    with open(filepath, "w") as f:
        json.dump({
            "seen_visited": list(seen),
            "to_visit_queue": queue
        }, f, indent=4)
    print(f"Checkpoint saved to {filepath}")

def search_pages_from_wiki(query:str, limit:int, offset:int): 
    search_page_endpoint = endpoints["search_page"]

    req_url = f"{BASE_URL}/{search_page_endpoint['provider']}/{search_page_endpoint['language']}/{search_page_endpoint['endpoint']}"

    parameters = {'q': query, 'limit': limit, "offset": offset}

    try:
        response = requests.get(req_url, headers=HEADERS, params=parameters)
        response.raise_for_status()
    except requests.exceptions.RequestException as reqEx:
        print("request failed due to an exception:\n", reqEx)
        return None

    if response.status_code != 200:
        print("Something went wrong:", response.status_code)

    return response.json()

# searched seed with the following queries to prepare seed links (seed.json):
#
# 1. Deep Learning
# 2. Artificial Intelligence
# 3. Machine Learning
# 4. Generative Pre-trained Transformer
# 5. Neural_network_(machine_learning)
# 6. Computer Vision
#
def search_pages_request_manager(query:str):
    try:
        (keys_set, json_output) = load_existing_keys()
        
        for offset in range(0, 2001, 100):
            data = search_pages_from_wiki(query, 100, offset)

            if not data or 'pages' not in data:
                break

            pages = data['pages']

            if not pages:
                print("No more pages found. Stopping.")
                break

            for page in pages:
                key = page['key']
                print("Key found in page : ", key)
                id = page['id']
                if key not in keys_set:
                    print(f"Adding key: { key }  to the set : ")
                    keys_set.add(key)
                    json_output.append({
                        "id": id,
                        "key": key
                    })

            print("current_offset is: ", offset)
            print(f"sleeping for:: {1/REQUESTS_PER_SEC} seconds")
            time.sleep(1 / REQUESTS_PER_SEC)

    except Exception as e:
            print(f"An unexpected error occurred during search_pages_equest_manager:\n {e}")
    finally:
        print(f"Saving {len(json_output)} total keys to seed.json...")
        save_keys(json_output)

def fetch_content(
        title:str, 
        with_html=True
    ):
    fetch_content = endpoints["fetch_content"]

    req_url = f"{BASE_URL}/{fetch_content['provider']}/{fetch_content['language']}/{fetch_content['endpoint']}/{title}"

    if with_html:
        req_url = req_url + "/with_html"
    else:
        req_url = req_url + "/bare"

    try:
        response = requests.get(req_url, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as reqEx:
        print("request failed due to an exception:", reqEx)
        return None

    if response.status_code != 200:
        print("Something went wrong:", response.status_code)

    valid_next_titles = []

    html_doc = response.json()['html']
    soup = BeautifulSoup(html_doc, 'html.parser')

    page_text = soup.get_text()
    all_links = soup.find_all('a')

    for link in all_links:
        href = link.get('href')

        if href and href.startswith("./"):
            title_key = href[2:]

            if ':' not in title_key and '#' not in title_key:
                valid_next_titles.append(title_key)
    
    return page_text, valid_next_titles

def crawler():
    ARTICLE_LIMIT = 4000
    MAX_DEPTH = 2
    PROGRESS_FILE = "progress.json"
    DATA_DIR = "corpus"
    KEYWORDS = ["intelligence", "learning", "neural", "network", "data", "algorithm"]

    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)

    seed, _ = load_existing_keys()

    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            checkpoint = json.load(f)
            seen_visited = set(checkpoint.get("seen_visited", []))

            loaded_list = checkpoint.get("to_visit_queue", [])
            to_visit_queue = deque(loaded_list)
            
            enqueued = {item[0] for item in to_visit_queue}
            print(f"Resuming from checkpoint: {len(seen_visited)} visited, {len(to_visit_queue)} in queue.")
    else:
        seen_visited = set()
        to_visit_queue = deque([[key, 0] for key in seed])
        enqueued = {key for key in seed}
        print("Starting fresh crawl from seed.json.")

    try:
        while to_visit_queue and len(seen_visited) < ARTICLE_LIMIT:
            current_element, current_depth = to_visit_queue.popleft()

            if not isinstance(current_element, str) or current_element in seen_visited or "#" in current_element:
                continue

            print(f"Crawling ({len(seen_visited)}/{ARTICLE_LIMIT}): {current_element}")

            result = fetch_content(current_element)
            if not result:
                seen_visited.add(current_element)
                continue

            page_text, valid_next_titles = result
            is_relevant = any( word in page_text.lower() for word in KEYWORDS)
            
            if is_relevant:
                print(f"Crawling (Depth {current_depth}): {current_element}")

                fileName = convert_wikipedia_key_into_file_safe(current_element)
                
                with open(f"{DATA_DIR}/data_{fileName}.txt", "w", encoding="utf-8") as f:
                    f.write(page_text)
                
                seen_visited.add(current_element)

                if(current_depth < MAX_DEPTH):
                    for title in valid_next_titles:
                        if title not in seen_visited and title not in enqueued:
                            to_visit_queue.append([title, current_depth + 1])
                            enqueued.add(title)
            else:
                seen_visited.add(current_element)
            
            time.sleep(1.5)

    except KeyboardInterrupt:
        print("\nStopping manually. Saving progress...")
    except Exception as e:
        print(f"An unexpected error occurred during search_pages_equest_manager:\n {e}")
    finally:
        print(f"Saving seen_visited so that we can resume later.")
        save_checkpoint(seen_visited, list(to_visit_queue), PROGRESS_FILE)


if __name__ == "__main__":
    crawler()