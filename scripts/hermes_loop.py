"""
hermes_loop.py - The self-healing orchestration engine.

Flow:
1. Hermes posts a task to #agent-main.
2. Hermes waits for OpenClaw's "COMPLETE" message in #agent-code.
3. Hermes checks the latest CI result (posted by GitHub Actions into #agent-monitor).
4. If CI is red -> Hermes creates a fix-task and reassigns (up to max_auto_retries).
5. If CI is green -> Hermes posts a session summary.

This is the piece that goes beyond the qualifier's mini-challenge: it shows a
closed-loop, self-correcting multi-agent system instead of a single one-shot task.
"""
import json
import time
from pathlib import Path

from slack_client import SlackClient
from model_router import route

TASK_QUEUE_FILE = "task_queue.json"


def load_tasks():
    path = Path(TASK_QUEUE_FILE)
    if not path.exists():
        default_tasks = [
            {"id": "001", "goal": "Add a docstring to fetch_titles.py", "priority": "low"},
        ]
        path.write_text(json.dumps(default_tasks, indent=2))
    return json.loads(path.read_text())


def assign_task(hermes: SlackClient, task: dict):
    msg = (
        f"TASK ASSIGNED [task-{task['id']}]\n"
        f"To: @OpenClaw\n"
        f"Goal: {task['goal']}\n"
        f"Priority: {task['priority']}"
    )
    return hermes.post("main", msg)


def wait_for_completion(hermes: SlackClient, task_id: str, since_ts: float):
    msg = hermes.wait_for_new_message("code", since_ts, poll=10, timeout=180)
    if msg and f"task-{task_id}" in msg.get("text", "") and "COMPLETE" in msg.get("text", ""):
        return True
    return False


def check_ci_result(hermes: SlackClient, since_ts: float):
    msg = hermes.wait_for_new_message("monitor", since_ts, poll=10, timeout=180)
    if not msg:
        return "unknown"
    text = msg.get("text", "")
    if "VERIFIED" in text:
        return "green"
    if "BLOCKED" in text:
        return "red"
    return "unknown"


def run_loop():
    hermes = SlackClient("../config/hermes_config.json")
    tasks = load_tasks()
    max_retries = hermes.config.get("max_auto_retries", 2)

    completed, blocked = 0, 0

    for task in tasks:
        retries = 0
        while retries <= max_retries:
            ts = time.time()
            assign_task(hermes, task)

            done = wait_for_completion(hermes, task["id"], ts)
            if not done:
                hermes.post("monitor", f"No completion signal for task-{task['id']}, escalating to human.")
                blocked += 1
                break

            ci_status = check_ci_result(hermes, ts)

            if ci_status == "green":
                hermes.post("main", f"VERIFIED [task-{task['id']}] - CI passing.")
                completed += 1
                break
            elif ci_status == "red":
                retries += 1
                if retries > max_retries:
                    hermes.post("monitor", f"task-{task['id']} failed {max_retries} auto-retries. Escalating.")
                    blocked += 1
                else:
                    diagnosis = route(
                        f"A CI test just failed for this task: '{task['goal']}'. "
                        f"In one short sentence, suggest what the fix task should focus on."
                    )
                    hermes.post(
                        "monitor",
                        f"task-{task['id']} CI failed. Retry {retries}/{max_retries}.\n"
                        f"AI diagnosis ({diagnosis['model_used']}): {diagnosis['answer']}",
                    )
                    task = {**task, "goal": f"Fix CI failure from task-{task['id']}: {diagnosis['answer']}"}
            else:
                hermes.post("monitor", f"CI result unclear for task-{task['id']}, treating as blocked.")
                blocked += 1
                break

    hermes.post(
        "main",
        f"SESSION SUMMARY\nTasks completed: {completed}\nTasks blocked: {blocked}",
    )


if __name__ == "__main__":
    run_loop()