"""Adapt the local progress journal to the normalized stall-watch schema."""
import json
import time
from pathlib import Path


def publish(out, started, finished=False):
    out = Path(out)
    now = time.time()
    event = dict(unix=started, event='loading', canonical=None)
    progress = out / 'PROGRESS.jsonl'
    if progress.exists():
        for line in progress.read_text().splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
    active = not finished and event['event'] not in ('complete', 'stopped', 'failed')
    episode = dict(id=event.get('canonical') or 'k1_model_load', started_unix=started,
                   last_event_unix=event['unix'], calls=[], phase=event.get('phase'),
                   progress_event=event['event'], heartbeat=dict(updated_unix=event['unix'], interval_s=300))
    state = dict(schema=1, updated_unix=now, heartbeat_interval_s=5, queued=0,
                 episodes=[episode] if active else [])
    temporary = out / 'STALL_STATE.pending'
    temporary.write_text(json.dumps(state) + '\n')
    temporary.replace(out / 'STALL_STATE.json')
    return state
