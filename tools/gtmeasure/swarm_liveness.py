import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time


def process_start(pid):
    path = Path('/proc') / str(pid) / 'stat'
    return path.read_text().rsplit(')', 1)[1].split()[19] if path.exists() else None


def tick(lane, production, state_path):
    result = subprocess.run(['git', '-C', str(production), 'status', '--short'], text=True,
                            capture_output=True, timeout=45)
    state = json.loads(state_path.read_text())
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    phase = ' '.join(str(state['phase']).split()[:12])
    lines = [f'# {lane.name}', *[str(line).replace('\n', ' ') for line in state['progress']]]
    status = result.stdout.strip() if result.returncode == 0 else 'status command failed: ' + result.stderr.strip()
    lines.append('- Production tree: ' + ('Clean at ' + now + '.' if not status else status.replace('\n', '; ')[:800]))
    lines.append('- Heartbeat: ' + now + '.')
    if len(lines) > 15:
        raise ValueError('Progress exceeds 15 lines')
    out = lane / 'out'
    if (out / 'REPORT.md').exists():
        return False
    with (out / 'HEARTBEAT.log').open('a') as handle:
        handle.write(now + ' | ' + phase + '\n')
    (out / 'PROGRESS.md').write_text('\n'.join(lines) + '\n')
    ruling = lane.parents[1] / 'RULINGS.md'
    print(json.dumps({'utc': now, 'phase': phase, 'production_clean': not status,
                      'rulings_mtime_ns': ruling.stat().st_mtime_ns if ruling.exists() else None}), flush=True)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lane', type=Path, required=True)
    parser.add_argument('--production', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--owner-pid', type=int, required=True)
    parser.add_argument('--interval', type=int, default=180)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    lane = args.lane.resolve()
    if not lane.is_relative_to('/data2') or not args.state.resolve().is_relative_to(lane) or not 1 <= args.interval <= 240:
        raise ValueError('Liveness paths and interval must remain lane-scoped')
    identity = process_start(args.owner_pid)
    if identity is None:
        raise ValueError('The owning session is not live on this host')
    receipt = lane / 'out' / f'LIVENESS_PID_{os.getpid()}.json'
    with receipt.open('x') as handle:
        json.dump({'pid': os.getpid(), 'owner_pid': args.owner_pid, 'owner_start_ticks': identity}, handle)
    while process_start(args.owner_pid) == identity and not (lane / 'STOP').exists() and not (lane / 'out/REPORT.md').exists():
        if not tick(lane, args.production, args.state) or args.once:
            break
        time.sleep(args.interval)
    print('LIVENESS_STOPPED', flush=True)


if __name__ == '__main__':
    main()
