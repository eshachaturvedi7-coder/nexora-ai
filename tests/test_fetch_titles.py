import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from fetch_titles import fetch_title, format_slack_summary  # noqa: E402


def test_format_slack_summary_basic():
    results = {"https://example.com": "Example Domain"}
    summary = format_slack_summary(results)
    assert "Example Domain" in summary
    assert "https://example.com" in summary


def test_fetch_title_handles_bad_url():
    title = fetch_title("https://this-domain-should-not-exist-12345.abc")
    assert "error" in title.lower()

def test_format_slack_summary_multiple_urls():
    results = {
        "https://a.com": "Site A",
        "https://b.com": "Site B",
    }
    summary = format_slack_summary(results)
    assert summary.count("-") >= 2