"""Runs a kit's batch entry inside the dry-run sandbox, then checks staging closure there.

dryrun.py copies this file into OUTDIR/shims/runner.py and starts it inside bwrap as
`/usr/bin/python3 -I runner.py OUTDIR/run.json`. It runs in the job's namespace, so the closure
check sees the job's private /tmp and every bound logical path exactly as the entry left them.

Standard library only; Python 3.6-safe.
"""
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        while True:
            block = handle.read(1 << 20)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def load_trace(path):
    spec = importlib.util.spec_from_file_location('orchkit_dryrun_trace_rewrite', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def closure(spec):
    """Every planned path must exist after the run; a pinned file must also match its sha256."""
    rows = []
    for item in spec.get('closure', []):
        path = item['path']
        row = {'source': item['source'], 'logical_path': item['logical_path'], 'path': path}
        if not os.path.exists(path):
            row['problem'] = 'missing'
        elif item.get('sha256'):
            if not os.path.isfile(path):
                row['problem'] = 'not_a_file'
            else:
                actual = sha256(path)
                if actual != item['sha256']:
                    row.update(problem='sha256_mismatch', actual=actual, expected=item['sha256'])
        rows.append(row)
    return rows


def main(run_json):
    with open(run_json) as handle:
        spec = json.load(handle)
    trace = load_trace(spec['trace_py'])
    argv = trace.rewrite(spec['argv']) if spec.get('trace') else list(spec['argv'])
    stage_res = [(s['name'], re.compile(s['regex'])) for s in spec.get('stages', [])]
    item_re = re.compile(spec['item_regex']) if spec.get('item_regex') else None
    result = {'argv': argv, 'stages': {}, 'items': 0, 'rc': None, 'timed_out': False}
    start = time.time()
    log = open(spec['log'], 'wb')
    try:
        proc = subprocess.Popen(argv, cwd=spec['cwd'], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, start_new_session=True)
    except OSError as err:
        result.update(rc=127, error='%s: %s' % (type(err).__name__, err))
        proc = None

    def expire():
        result['timed_out'] = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
    if proc is not None:
        timer = threading.Timer(float(spec.get('timeout_s', 3600)), expire)
        timer.daemon = True
        timer.start()
        for raw in iter(proc.stdout.readline, b''):
            log.write(raw)
            line = raw.decode('utf-8', 'replace').rstrip('\n')
            for name, pattern in stage_res:
                if name not in result['stages'] and pattern.search(line):
                    result['stages'][name] = round(time.time() - start, 3)
            if item_re is not None and item_re.search(line):
                result['items'] += 1
        result['rc'] = proc.wait()
        timer.cancel()
    log.close()
    result['seconds'] = round(time.time() - start, 3)
    result['closure'] = closure(spec)
    tmp = spec['result'] + '.tmp'
    with open(tmp, 'w') as handle:
        json.dump(result, handle, sort_keys=True)
    os.rename(tmp, spec['result'])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
