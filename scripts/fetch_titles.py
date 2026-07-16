"""
Qualifier mini-challenge:
Hermes tells OpenClaw to fetch page titles from 3 URLs.
OpenClaw runs this script and reports results back over Slack.
Everything is logged in Slack - no manual edits.
"""
import re
import sys
import requests

DEFAULT_URLS = [
    "https://www.anthropic.com",
    "https://www.python.org",
    "https://www.wikipedia.org",
]


def fetch_title(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        match = re.search(r"<title[^>]*>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else "(no title found)"
    except requests.RequestException as e:
        return f"(error: {e})"


def fetch_all(urls) -> dict:
    return {url: fetch_title(url) for url in urls}


def format_slack_summary(results: dict) -> str:
    lines = ["Page title fetch results:"]
    for url, title in results.items():
        lines.append(f"- {url} -> {title}")
    return "\n".join(lines)


if __name__ == "__main__":
    urls = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_URLS
    results = fetch_all(urls)
    summary = format_slack_summary(results)
    print(summary)

    try:
        from slack_client import SlackClient
        client = SlackClient("../config/openclaw_config.json")
        client.post("code", f"COMPLETE [mini-challenge]\n{summary}")
    except Exception as e:
        print(f"(Slack post skipped: {e})")