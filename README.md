# Wikipedia Crawler

This was created as part of the [Infomatic](https://github.com/rrtyagii/refactored-rotary-phone) project. We set a limit of 4000 articles from wikipedia starting from the seed url. 

We started with ~500 seed url to ensure quality over quantity. Once we have the seed url, we moved to create a "worker" that fetches, parses the content and extract the links from the content. We are delibrately sticking with wikipedia only hyperlinks. Afterwards, we have the crawler that has an article limit of 4k, a max-depth of 2 and makes sure we are crawling relevant results by leveraging a certain list of relevant keywords. 

Seed URL -> depth = 0
links from seed (LS) -> depth = 1
links of links -> depth = 2

We hit the wiki api, politely, check relevancy, store the content, and update our queues - links we have visited, and linke we need to visit. We are saving a progress-report in case of an error, key-interuppt or completion.

## Prerequisites

- Python 3.10+ (or compatible 3.x)
- A Wikimedia personal API token (Client ID, Client Secret, Access Token). Create one at: https://api.wikimedia.org/wiki/Special:AppManagement

Before running, log into en.wikipedia.org and create your user page — this activates the token and prevents 403/404 errors.

## Quickstart

Create and activate a virtual environment, install dependencies, and run the script:

```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 wikipedia_data_script.py
```

## Configuration

Create a `.env.development` in the project root with your token values:

```
WIKIPEDIA_CLIENT_ID=your_client_id
WIKIPEDIA_CLIENT_SECRET=your_client_secret
WIKIPEDIA_ACCESS_TOKEN=your_access_token
```

If your token has specific scopes, ensure the correct scopes are enabled in the API portal.

## Files and Output

- `seed.json` — starting URLs
- `corpus/` — output article files (named like `data_<article_title>.txt`)
- `progress.json` — crawl progress and resume state
- `wikipedia_data_script.py` — main crawler

## Troubleshooting

- 403/404 errors: confirm `.env.development` values and that your Wikipedia user page has been created to activate the token.
- Rate limiting: the script is polite but may be throttled by Wikimedia; consider slowing requests in code if needed.
- Resume: if interrupted, the script reads `progress.json` to continue where it left off.

## Contributing

Open issues or PRs to improve parsing, add keywords, or change crawl limits. When contributing, keep changes small and include tests or sample outputs where appropriate.

## License & Contact

- MIT — see [LICENSE.txt](LICENSE.txt) for full terms.
- Open an issue in this repository for questions or support.



