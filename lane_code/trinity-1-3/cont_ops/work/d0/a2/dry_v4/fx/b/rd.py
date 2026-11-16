"""Summarize the last Python traceback in RAW (file basename:line:function plus the exception line). Absolute paths
become basenames; any token matching a hashed listed word or substring is redacted. usage: rd.py RAW HASHES OUT RC"""
import hashlib, json, re, sys
raw, hashes, out, rc = sys.argv[1:5]
text = open(raw, errors='replace').read()
H = json.load(open(hashes)); words = set(H['word']); subs = {int(k): set(v) for k, v in H['substr'].items()}
h = lambda s: hashlib.sha256(s.lower().encode()).hexdigest()
def bad(tok):
    if h(tok) in words: return True
    t = tok.lower()
    return any(h(t[i:i + n]) in v for n, v in subs.items() for i in range(0, len(t) - n + 1))
def red(s):
    s = re.sub(r'(/[^\s\'",:()]+)+', lambda m: m.group(0).rstrip('/').split('/')[-1], s)
    return re.sub(r'[A-Za-z0-9_]+', lambda m: '****' if bad(m.group(0)) else m.group(0), s)[:400]
tb = text.rsplit('Traceback (most recent call last):', 1)
frames, exc = [], ''
if len(tb) == 2:
    lines = tb[1].strip().splitlines()
    for line in lines:
        m = re.match(r'\s*File "([^"]+)", line (\d+), in (\S+)', line)
        if m: frames.append('%s:%s:%s' % (m.group(1).split('/')[-1], m.group(2), m.group(3)))
    exc = next((l for l in reversed(lines) if l and not l.startswith(' ')), '')
errors = [red(l) for l in text.splitlines() if re.search(r'(Error|Exception|error:|refus|differ)', l)][-16:]
json.dump({'rc': int(rc), 'frames': [red(f) for f in frames[-14:]], 'exception': red(exc), 'errors': errors,
           'tail': [red(l) for l in text.strip().splitlines()[-8:]]}, open(out, 'w'), indent=1)
