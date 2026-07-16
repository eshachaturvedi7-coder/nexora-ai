"""
Minimal Slack wrapper used by both Hermes and OpenClaw.
Keeps all Slack I/O in one place so the agent logic stays clean and testable.
"""
import json
import time
from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackClient:
    def __init__(self, config_path: str):
        self.config = json.loads(Path(config_path).read_text())
        self.name = self.config["agent_name"]
        self.channels = self.config["channels"]
        self.client = WebClient(token=self.config["slack_bot_token"])

    def post(self, channel_key: str, text: str):
        """channel_key is one of: main, code, monitor"""
        channel = self.channels[channel_key]
        try:
            resp = self.client.chat_postMessage(channel=channel, text=text)
            return resp["ts"]
        except SlackApiError as e:
            print(f"[{self.name}] Slack post failed: {e.response['error']}")
            return None

    def read_latest(self, channel_key: str, limit: int = 10):
        channel = self.channels[channel_key]
        try:
            resp = self.client.conversations_history(channel=channel, limit=limit)
            return resp["messages"]
        except SlackApiError as e:
            print(f"[{self.name}] Slack read failed: {e.response['error']}")
            return []

    def wait_for_new_message(self, channel_key: str, since_ts: float, poll: int = 10, timeout: int = 300):
        """Blocks until a new message appears in channel_key, or timeout."""
        waited = 0
        while waited < timeout:
            messages = self.read_latest(channel_key, limit=5)
            for m in messages:
                if float(m.get("ts", 0)) > since_ts:
                    return m
            time.sleep(poll)
            waited += poll
        return None