"""Read sync.log once for the owner; never start, stop, or retry a sync."""
import datetime
import re
import sys

STAMP = re.compile(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) (.*)$')
THRESHOLD = 0.05  # Policy choice: whole-source rejection above 5% risks starvation.


def lines(text):
    return text.splitlines() if isinstance(text, str) else text


def window(text, now=None):
    """Require the latest hourly invocation to have ended within 600 seconds."""
    now = now or datetime.datetime.utcnow()
    hourly = False
    ended = None
    for line in lines(text):
        match = STAMP.match(line.rstrip('\n'))
        if not match:
            continue
        message = match.group(2)
        if message.startswith('START '):
            hourly = message == 'START dry=0 queue_only=0'
            ended = None
        elif hourly and (message == 'END ok' or message.startswith('END with failures')):
            ended = datetime.datetime.strptime(match.group(1), '%Y-%m-%dT%H:%M:%SZ')
    if ended is None:
        raise ValueError('no completed latest hourly run with an END line')
    age = (now - ended).total_seconds()
    if not 0 <= age <= 600:
        raise ValueError('latest hourly END is %.1f seconds old; require 0..600 seconds' % age)
    return age


def pre_enable(text):
    runs = failures = 0
    for line in lines(text):
        if re.match(r'^\S+ START dry=0 queue_only=0\s*$', line):
            runs += 1
        if re.search(r'\btrinity-1-18 stage rc=4\b', line):
            failures += 1
    if runs == 0:
        raise ValueError('no hourly runs in sync.log; STAY LEGACY until evidence is available')
    rate = failures / float(runs)
    print('PRE-ENABLE runs=%d stage_rc4_lines=%d rate=%.2f%% threshold=%.2f%% (entire supplied sync.log)' %
          (runs, failures, 100 * rate, 100 * THRESHOLD))
    if rate > THRESHOLD:
        print('STAY LEGACY: whole-source rejection would exceed the 5% threshold; review source mutation before enabling.')
        return 2
    print('PRE-ENABLE within threshold; calibration is still required before enabling.')
    return 0


if __name__ == '__main__':
    try:
        mode, path = sys.argv[1:3]
        with open(path) as stream:
            if mode == 'window':
                age = window(stream)
                print('CALIBRATION WINDOW OK: latest hourly END age=%.1fs (maximum 600s)' % age)
                rc = 0
            elif mode == 'pre-enable':
                rc = pre_enable(stream)
            else:
                raise ValueError('expected window or pre-enable')
        sys.exit(rc)
    except Exception as error:
        print('OWNER CHECK REFUSED: ' + str(error), file=sys.stderr)
        sys.exit(2)
