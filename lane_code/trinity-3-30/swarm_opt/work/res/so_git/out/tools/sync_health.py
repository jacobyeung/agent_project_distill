"""Read only local sync evidence; emit one event per incident and recovery."""
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys

UTC = timezone.utc


def within(path, boundary):
    try:
        path.relative_to(boundary)
        return True
    except ValueError:
        return False


def iso(value):
    return value.strftime('%Y-%m-%dT%H:%M:%SZ')


def parse(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)


def stamp(value):
    return value.strftime('%Y%m%dT%H%M%SZ')


def read_log(path):
    if not path.exists():
        return []
    # Bound reads of long-running logs; a truncated history is conservatively stale.
    with path.open('rb') as f:
        size = f.seek(0, 2)
        f.seek(max(0, size - 8 * 1024 * 1024))
        raw = f.read()
        if size > len(raw):
            raw = raw.partition(b'\n')[2]
    result = []
    for line in raw.decode('utf-8', errors='replace').splitlines():
        when, _, text = line.partition(' ')
        try:
            result.append((parse(when), text))
        except ValueError:
            continue
    return result


def evidence(lines):
    verified = None
    current = None
    completed = None
    for when, text in lines:
        if re.fullmatch(r'verified GitHub lane-code = (?:[0-9a-f]{40}|[0-9a-f]{64})', text):
            if verified is None or when >= verified:
                verified = when
            if current is not None:
                current['verified'] = when
        if text.startswith('START '):
            current = {'start': when, 'verified': None}
        if text.startswith(('END ', 'QUEUE-ONLY END ')):
            current = current or {'start': when, 'verified': None}
            current['end'] = when
            current['failed'] = 'with failures' in text
            current['ok'] = text == 'END ok'
            completed = current
            current = None
    return verified, completed


def own_blocker(events, run):
    # The sync's STAMP filename has minute precision; its first line has the true end time.
    for p in events.glob('*_BLOCKER_sync_failed.md'):
        if p.is_symlink() or not p.is_file():
            continue
        with p.open('r', errors='replace') as f:
            first = f.readline(4096)
        when, _, text = first.partition(' ')
        try:
            when = parse(when)
        except ValueError:
            continue
        if run['start'] <= when <= run['end'] + timedelta(seconds=2) and text.startswith('code_sync run failed'):
            return True
    return False


def save(path, data):
    tmp = path.with_name(f'state.{os.getpid()}.new')
    with tmp.open('w') as f:
        json.dump(data, f, sort_keys=True, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def check(state_root, events, log, now):
    health = state_root / 'health'
    health.mkdir(parents=True, exist_ok=True)
    events.mkdir(parents=True, exist_ok=True)
    with (health / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = health / 'state.json'
        data = json.loads(path.read_text()) if path.exists() else {'active': {}, 'events': {}, 'first_seen': iso(now)}
        # Legacy journal strings describe events the old monitor already emitted.
        for name, entry in list(data['events'].items()):
            if isinstance(entry, str):
                data['events'][name] = dict(content=entry, delivered=True)
        previous = parse(data.get('checked', data['first_seen']))
        if now < previous:
            raise ValueError('clock moved backwards; state unchanged')
        lines = read_log(log)
        verified, completed = evidence(lines)
        lock_skips = [(when, text) for when, text in lines
                      if text == 'FAIL previous run still holds the lock']
        active = data['active']
        recovered = []
        for kind, incident in list(active.items()):
            after = parse(incident['observed'])
            good = verified is not None and verified > after and verified <= now
            if kind == 'failed':
                good = (good and completed is not None and completed['ok'] and
                        completed['verified'] is not None and completed['verified'] > after)
            if good:
                recovered.append(kind)
                active.pop(kind)
        if recovered:
            # Stable name makes event replay safe after process interruption.
            event = f'{stamp(verified)}_RESULT_code_sync_recovered.md'
            data['events'].setdefault(event, f'{iso(now)} code_sync recovered: {", ".join(recovered)}; verified GitHub push {iso(verified)}\n')
        stale = verified is None or now - verified > timedelta(minutes=90)
        if stale and 'stale' not in active:
            event = f'{stamp(now)}_BLOCKER_code_sync_stale.md'
            active['stale'] = {'observed': iso(now), 'event': event}
            last = iso(verified) if verified else 'no verified GitHub lane-code line in available log'
            data['events'][event] = f'{iso(now)} code_sync stale: last success {last}; limit 90 minutes; log {log}\n'
            if lock_skips:
                when, text = lock_skips[-1]
                data['events'][event] += f'Latest hourly lock skip: {iso(when)} {text}\n'
        if completed and completed['failed'] and 'failed' not in active and not own_blocker(events, completed):
            # Deduplicate a completed failure even after its incident has recovered.
            key = iso(completed['end'])
            if data.get('last_failed_run') != key:
                event = f'{stamp(now)}_BLOCKER_code_sync_failed.md'
                active['failed'] = {'observed': iso(now), 'event': event, 'run': key}
                data['events'][event] = f'{iso(now)} code_sync failed: run ended {key} without its own BLOCKER; log {log}\n'
                data['last_failed_run'] = key
        data['checked'] = iso(now)
        # Newly queued strings have not been delivered yet.
        for name, entry in list(data['events'].items()):
            if isinstance(entry, str):
                data['events'][name] = dict(content=entry, delivered=False)
        # Persist pending events before writing; acknowledge each successful delivery locally.
        save(path, data)
        for name, entry in data['events'].items():
            if entry['delivered']:
                continue
            content = entry['content']
            dest = events / name
            if dest.exists():
                if dest.is_symlink() or dest.read_text() != content:
                    raise ValueError(f'event collision: {dest}')
            else:
                with dest.open('x') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                print(f'EVENT {dest}')
            entry['delivered'] = True
            save(path, data)
        print(f'HEALTH last_verified={iso(verified) if verified else "none"} active={",".join(sorted(active)) or "none"}')


def main():
    if os.environ.get('LCS_ENABLE_SYNC_HEALTH') != '1':
        raise ValueError('disabled; owner must set LCS_ENABLE_SYNC_HEALTH=1')
    state = Path(os.environ.get('LCS_S', '/scratch/jjyeung/distill_sync')).resolve()
    base = Path(os.environ.get('LCS_B', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30'))
    events = Path(os.environ.get('LCS_EV', str(base / 'events' / 'code_sync'))).resolve()
    log = Path(os.environ.get('LCS_LOG', str(state / 'sync.log'))).resolve()
    now = datetime.now(UTC).replace(microsecond=0)
    if os.environ.get('LCS_TEST_ROOT'):
        boundary = Path(os.environ['LCS_TEST_ROOT']).resolve(strict=True)
        if not str(boundary).startswith('/scratch/') or not all(within(p, boundary) for p in (state, events)):
            raise ValueError('test writes must stay within /scratch test root')
        if os.environ.get('LCS_HEALTH_NOW'):
            now = parse(os.environ['LCS_HEALTH_NOW'])
    else:
        if socket.gethostname().split('.')[0] != 'trinity-3-30':
            raise ValueError('owner monitor runs only on trinity-3-30')
        if 'LCS_HEALTH_NOW' in os.environ:
            raise ValueError('fake clock requires LCS_TEST_ROOT')
    check(state, events, log, now)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        sys.exit(2)
