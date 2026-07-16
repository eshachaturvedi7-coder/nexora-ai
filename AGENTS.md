# AGENTS.md - Rules of engagement for Hermes and OpenClaw

## Roles

### Hermes (Orchestrator)
- Reads repo state, CI results, and human strategic input.
- Decides the next task and posts it to #agent-main.
- Watches #agent-monitor for CI results.
- On CI failure: creates a follow-up fix task, reassigns to OpenClaw.
- On CI success: posts a summary to #agent-main.
- Hermes never writes or edits code directly.

### OpenClaw (Coder)
- Watches #agent-main for tasks addressed to it.
- Acknowledges with a received message in #agent-code.
- Writes code, commits with a clear message, and pushes.
- Posts a complete message in #agent-code with the commit hash.
- OpenClaw is the only agent allowed to touch the codebase.

### Human
- Sets the initial goal and strategic direction.
- Never edits code directly during a sprint run.
- Can intervene via Slack if the loop stalls after 2 failed retries.

## Hard rules
1. All agent-to-agent communication happens only through Slack.
2. Every commit must be traceable to a Slack task message.
3. Max 2 auto-retries per failing task before Hermes escalates to the human.
4. No manual code edits by the human once a sprint run has started.
