import requests, math, json, time
from bs4 import BeautifulSoup as beautifulSoup
from dotenv import dotenv_values

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

def search_pages_from_wiki(query:str, limit:int, offset:int): 
    search_page_endpoint = endpoints["search_page"]

    req_url = f"{BASE_URL}/{search_page_endpoint['provider']}/{search_page_endpoint['language']}/{search_page_endpoint['endpoint']}"

    parameters = {'q': query, 'limit': limit, "offset": offset}

    try:
        response = requests.get(req_url, headers=HEADERS, params=parameters)
        response.raise_for_status()
    except requests.exceptions.RequestException as reqEx:
        print("request failed due to an exception:", reqEx)
        return None

    if response.status_code != 200:
        print("Something went wrong:", response.status_code)

    return response.json()


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

# searched seed with the following queries:
# 1. Deep Learning
# 2. Artificial Intelligence
# 3. Machine Learning
# 4. Generative Pre-trained Transformer
# 5. Neural_network_(machine_learning)
# 6. Computer Vision

search_pages_request_manager("Computer Vision") 

def fetch_content(
        title:str, 
        with_html=True
    ):
    fetch_content = endpoints["fetch_content"]

    # need to fetch html, parse via beautifulSoup, do it for the rest of the links on the HTML page with a "delay" to not touch rate limits.

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
    
    



#fetch_content("Artificial_intelligence")

