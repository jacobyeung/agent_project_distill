"""Derive budgets from one successful robust --stage-only log; never enable the flag."""
import datetime
from pathlib import Path
import re
import sys

REQUIRED = {'trinity-1-18', 'trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs'}


def scan_counts(text):
    counts = {}
    for line in text.splitlines():
        match = re.match(r'^\s*\[copy ([^\]]+)\] SCAN scanned=(\d+)\b', line)
        if match:
            label, count = match.group(1), int(match.group(2))
            if label in counts or count <= 0:
                raise ValueError('duplicate or empty SCAN count for ' + label)
            counts[label] = count
    if not REQUIRED.issubset(counts):
        raise ValueError('missing positive SCAN count for ' + ', '.join(sorted(REQUIRED - set(counts))))
    return counts


def legacy_stats(stream):
    """Retain only the last STATS per label from invocations without ROBUST."""
    latest, pending, robust = {}, {}, False
    for line in stream:
        if re.match(r'^\S+ START ', line):
            if not robust:
                latest.update(pending)
            pending, robust = {}, False
        if re.match(r'^\S+ ROBUST ', line):
            robust = True
        match = re.search(r'\b(STATS (\S+) .*)', line)
        if match:
            pending[match.group(2)] = match.group(1).rstrip()
    if not robust:
        latest.update(pending)
    return latest


def derive(text):
    marks, durations, skipped = {}, {}, set()
    complete = False
    for line in text.splitlines():
        if re.search(r'\bFAIL\b', line):
            raise ValueError('calibration contains FAIL; do not enable or automatically rerun')
        match = re.match(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) (.*)$', line)
        if not match:
            continue
        timestamp = datetime.datetime.strptime(match.group(1), '%Y-%m-%dT%H:%M:%SZ')
        message = match.group(2)
        if message == 'STAGE-ONLY done':
            if complete:
                raise ValueError('multiple calibration completions')
            complete = True
            continue
        event = None
        for prefix, name in (('ROBUST stage ', 'stage'), ('ROBUST accept ', 'accept'),
                             ('STAGED ', 'staged'), ('ROBUST copy ', 'copy'), ('COPIED ', 'copied')):
            if message.startswith(prefix):
                event, label = name, message[len(prefix):].split()[0]
                if name in ('staged', 'copied') and not message.endswith(' rc=0'):
                    raise ValueError('unsuccessful measurement: ' + message)
                break
        if message.startswith('SKIP trinity-2-28 '):
            skipped.add('trinity-2-28')
        if event is None:
            continue
        if complete:
            raise ValueError('measurements after completion')
        history = marks.setdefault(label, {})
        order = ('stage', 'accept', 'staged', 'copy', 'copied')
        if len(history) >= len(order) or order[len(history)] != event:
            raise ValueError('missing, duplicate, or unordered measurement for ' + label + ': ' + event)
        if history and timestamp < max(history.values()):
            raise ValueError('negative interval for ' + label)
        history[event] = timestamp
        if event == 'copied':
            durations[label] = {
                'stage': int((history['accept'] - history['stage']).total_seconds()),
                'accept': int((history['staged'] - history['accept']).total_seconds()),
                'copy': int((history['copied'] - history['copy']).total_seconds())}
    if not complete or not REQUIRED.issubset(durations):
        raise ValueError('calibration lacks required stage, accept, copy measurements or STAGE-ONLY done')
    if skipped.intersection(durations) or set(marks) - set(durations) - skipped:
        raise ValueError('calibration contains incomplete source measurements')
    counts = scan_counts(text)
    if set(counts) != set(durations):
        raise ValueError('SCAN labels do not match completed source measurements')
    longest_stage = max(value['stage'] for value in durations.values())
    longest_copy = max(max(value['accept'], value['copy']) for value in durations.values())
    scan = max(120, 2 * longest_stage + 30)
    copy = max(120, 2 * longest_copy + 30)
    leg = max(150, scan + 125)
    remote = max(160, leg + 30)
    node = max(210, remote + 125)
    budgets = [('LCS_FILE_SECONDS', 3), ('LCS_SCAN_SECONDS', scan), ('LCS_COPY_SECONDS', copy),
               ('LCS_LEG_SECONDS', leg), ('LCS_REMOTE_SECONDS', remote), ('LCS_NODE_SECONDS', node),
               ('LCS_KILL_SECONDS', 5)]
    if any(value > 3600 for name, value in budgets):
        raise ValueError('derived budget exceeds 3600 seconds; owner must review before enabling')
    return durations, budgets


if __name__ == '__main__':
    try:
        text = Path(sys.argv[1]).read_text()
        durations, budgets = derive(text)
        counts, previous = scan_counts(text), {}
        if len(sys.argv) > 2:
            with open(sys.argv[2]) as stream:
                previous = legacy_stats(stream)
        for label, measured in sorted(durations.items()):
            print('COUNTS %s scanned=%d legacy=%s' %
                  (label, counts[label], previous.get(label, 'unavailable')), file=sys.stderr)
            for event in ('stage', 'accept', 'copy'):
                print('MEASURE %s_seconds %s=%d (one-second log resolution)' %
                      (event, label, measured[event]), file=sys.stderr)
        print('ESTIMATE budgets use twice the longest measured interval plus margins; COPY covers acceptance and copy.', file=sys.stderr)
        print('MARGINS SCAN/COPY=2*maximum+30s (floors 120s); LEG-SCAN>=125s REMOTE-LEG>=30s NODE-REMOTE>=125s KILL=5s tssh_pre_sleep<=35s; lock contention is bounded only by NODE.', file=sys.stderr)
        for name, value in budgets:
            print('%s=%d' % (name, value))
    except Exception as error:
        print('CALIBRATION REFUSED: ' + str(error), file=sys.stderr)
        sys.exit(2)
