#!/usr/bin/env python3
"""Pre-submit leak gate for AWS jobs (Trinity side). Refuses (exit 1) on any scanner hit.

usage: anon_gate.py SPEC.json [--report OUT.json] [--no-remote]
SPEC keys (all optional):
  local       [paths]  local mirrors of the staged kit dirs (scanned with text: rules)
  aws_walk    [dirs]   AWS dirs: every entry name below them, plus content of small text files (<= 2 MB:
                       .sh .py .json .txt .cfg and extension-less) at depth <= aws_text_depth (default 2)
  aws_walk_names [dirs] AWS data dirs: every entry name below them, no content
  aws_names   [paths]  AWS files or dirs: names only (dirs listed to depth 1)
  aws_caps    [globs]  cap.py outputs to scan (argv, env, names)
  aws_logs    [globs]  log files to scan line by line (newest aws_logs_max per glob, default 4)
  skip_names  [regex]  AWS entry names to leave out of the walk (e.g. huge frame stores already known clean)
  aws_text_skip [regex] paths under aws_walk whose content is data (publications, results): names only
Remote access is one ssh to code-aws (timeout 300 s); the remote side gets a word-free lister on stdin and returns a
tar on stdout. The word list never leaves Trinity.
"""
import argparse, io, json, os, subprocess, sys, tarfile, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anonscan  # noqa: E402

REMOTE = r'''
import glob, io, json, os, re, sys, tarfile
spec = json.loads(sys.stdin.readline())
buf = tarfile.open(fileobj=sys.stdout.buffer, mode='w|')
def add_bytes(name, data):
    ti = tarfile.TarInfo(name); ti.size = len(data); buf.addfile(ti, io.BytesIO(data))
skip = [re.compile(s) for s in spec.get('skip_names', [])]
names, texts = [], []
TEXT = ('.sh', '.py', '.json', '.txt', '.cfg', '')
depth_max = spec.get('aws_text_depth', 2)
for root in spec.get('aws_walk', []):
    root = root.rstrip('/')
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not any(s.search(d) for s in skip)]
        depth = dp[len(root):].count('/')
        for n in dns + fns:
            p = os.path.join(dp, n); names.append(p)
            if os.path.islink(p): names.append(p + ' -> ' + os.readlink(p))
        for n in fns:
            p = os.path.join(dp, n)
            if depth <= depth_max and os.path.splitext(n)[1] in TEXT and not os.path.islink(p) \
                    and not any(re.search(x, p) for x in spec.get('aws_text_skip', [])):
                try:
                    if os.path.getsize(p) <= (2 << 20): texts.append(p)
                except OSError: pass
for root in spec.get('aws_walk_names', []):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not any(s.search(d) for s in skip)]
        names += [os.path.join(dp, n) for n in dns + fns]
for p in spec.get('aws_names', []):
    names.append(p)
    if os.path.isdir(p):
        names += [os.path.join(p, n) for n in os.listdir(p)]
    elif os.path.islink(p):
        names.append(p + ' -> ' + os.readlink(p))
add_bytes('names.txt', '\n'.join(names).encode())
for i, p in enumerate(texts):
    try: add_bytes('text/%05d%s' % (i, os.path.splitext(p)[1]), open(p, 'rb').read())
    except OSError: pass
add_bytes('text_index.json', json.dumps(texts).encode())
k = 0
for g in spec.get('aws_caps', []):
    for p in sorted(glob.glob(g)):
        add_bytes('cap/%04d.json' % k, open(p, 'rb').read()); k += 1
for g in spec.get('aws_logs', []):
    for p in sorted(glob.glob(g), key=os.path.getmtime)[-spec.get('aws_logs_max', 4):]:
        data = open(p, 'rb').read()
        add_bytes('log/%04d.log' % k, data[-(8 << 20):]); k += 1
add_bytes('log_index.json', json.dumps(spec.get('aws_logs', [])).encode())
buf.close()
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('--report')
    ap.add_argument('--no-remote', action='store_true')
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    targets = ['text:' + p for p in spec.get('local', [])]
    os.makedirs(os.path.join(HERE, '..', 'scan', 'fetch'), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='g_', dir=os.path.join(HERE, '..', 'scan', 'fetch'))
    if not a.no_remote and any(spec.get(k) for k in ('aws_walk', 'aws_walk_names', 'aws_names', 'aws_caps', 'aws_logs')):
        payload = REMOTE.encode()
        cmd = ['timeout', '300', 'ssh', '-o', 'ConnectTimeout=20', 'code-aws', '']
        cmd[-1] = 'python3 -I -c "import sys; n=int(sys.stdin.readline()); exec(sys.stdin.read(n))"'
        inp = (str(len(payload)) + '\n').encode() + payload + (json.dumps({k: v for k, v in spec.items() if k.startswith('aws_') or k in ('skip_names',)}) + '\n').encode()
        r = subprocess.run(cmd, input=inp, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            print('ANON_GATE remote listing failed rc=%d: %s' % (r.returncode, r.stderr.decode()[-500:]))
            return 3
        with tarfile.open(fileobj=io.BytesIO(r.stdout), mode='r|') as tf:
            tf.extractall(tmp)
        targets.append('names:' + os.path.join(tmp, 'names.txt'))
        if os.path.isdir(os.path.join(tmp, 'text')):
            targets.append('text:' + os.path.join(tmp, 'text'))
        if os.path.isdir(os.path.join(tmp, 'cap')):
            targets += ['cap:' + os.path.join(tmp, 'cap', n) for n in sorted(os.listdir(os.path.join(tmp, 'cap')))]
        if os.path.isdir(os.path.join(tmp, 'log')):
            targets.append('log:' + os.path.join(tmp, 'log'))
    report = a.report or os.path.join(HERE, '..', 'scan', 'gate_%s.json' % time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
    rc = anonscan.main(['--report', report, '--max-print', '0'] + targets)
    idx = os.path.join(tmp, 'text_index.json')
    rep = json.load(open(report))
    if os.path.isfile(idx):
        paths = json.load(open(idx))
        for h in rep['hit_list'] + rep['advisory_list']:
            w = h['where']
            if w.startswith('text/') and w[5:10].isdigit():
                h['where'] = paths[int(w[5:10])] + w[w.find(':'):] if ':' in w else paths[int(w[5:10])]
        json.dump(rep, open(report, 'w'), indent=1)
    for h in rep['hit_list'][:40]:
        print('HIT %s [%s] %s :: %s' % (h['where'], h['kind'], ','.join(h['words']), h['text'][:160]))
    print('ANON_GATE %s report=%s fetched=%s' % ('PASS' if rc == 0 else 'REFUSE', os.path.abspath(report), tmp))
    return rc


if __name__ == '__main__':
    sys.exit(main())
