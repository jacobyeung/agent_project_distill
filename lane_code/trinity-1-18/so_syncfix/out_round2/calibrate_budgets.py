"""Derive conservative budget estimates from one successful robust --dry log; never enable the flag."""
import datetime
import math
from pathlib import Path
import re
import sys


def derive(text):
    starts, durations = {}, {}
    complete = False
    for line in text.splitlines():
        if re.search(r'\bFAIL\b', line):
            raise ValueError('calibration contains FAIL; do not enable or automatically rerun')
        match = re.match(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) (.*)$', line)
        if not match:
            continue
        timestamp = datetime.datetime.strptime(match.group(1), '%Y-%m-%dT%H:%M:%SZ')
        message = match.group(2)
        if message.startswith('ROBUST stage '):
            starts[message.split()[2]] = timestamp
        elif message.startswith('STAGED ') and message.endswith(' rc=0'):
            label = message.split()[1]
            if label not in starts:
                raise ValueError('missing stage start: ' + label)
            durations[label] = max(1, int((timestamp - starts[label]).total_seconds()))
        elif message == 'DRY done':
            complete = True
    required = {'trinity-1-18', 'trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs'}
    if not complete or not required.issubset(durations):
        raise ValueError('calibration lacks successful required stages or DRY done')
    longest = max(durations.values())
    scan = max(120, int(math.ceil(2 * longest)) + 30)
    copy = max(120, int(math.ceil(3 * longest)) + 60)
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
        durations, budgets = derive(Path(sys.argv[1]).read_text())
        for label, duration in sorted(durations.items()):
            print('MEASURE dry_stage_seconds %s=%d (one-second log resolution)' % (label, duration), file=sys.stderr)
        print('ESTIMATE budgets include margins; dry mode does not measure transfer, acceptance, or copy.', file=sys.stderr)
        for name, value in budgets:
            print('%s=%d' % (name, value))
    except Exception as error:
        print('CALIBRATION REFUSED: ' + str(error), file=sys.stderr)
        sys.exit(2)
