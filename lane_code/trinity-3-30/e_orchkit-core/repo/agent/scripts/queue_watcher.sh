#!/usr/bin/env bash
# Queue watcher: exits (rc=0) when EXPERIMENT_REQUEST_QUEUE.md changes, so the
# orchestrator's background-task notification fires and it can act on the new
# request, then re-arm. Checks every minute (USER directive 2026-07-29).
# Usage: queue_watcher.sh [queue_path] [interval_seconds]
set -u
QUEUE=${1:-/home/jjyeung/agent_project/agent/agentic_information_5.0/EXPERIMENT_REQUEST_QUEUE.md}
INTERVAL=${2:-60}
baseline=$(sha256sum "$QUEUE" 2>/dev/null | cut -d' ' -f1)
while true; do
  sleep "$INTERVAL"
  current=$(sha256sum "$QUEUE" 2>/dev/null | cut -d' ' -f1)
  if [[ -n "$current" && "$current" != "$baseline" ]]; then
    echo "QUEUE_CHANGED $(date -u +%FT%TZ) sha=$current"
    exit 0
  fi
done
