import os, glob, json, collections
keys = [os.environ.pop(k) for k in ('NVK_A', 'NVK_B', 'NVK_C', 'NVK_D') if os.environ.get(k)]
home = os.path.expanduser('~')
files = sorted(set(glob.glob('/tmp/nvk1/*') + glob.glob('/tmp/nvk1_*') + glob.glob('/tmp/nvk1/**/*', recursive=True) +
                   [home + '/.bash_history', home + '/.python_history', home + '/.lesshst', home + '/.viminfo', home + '/.wget-hsts']))
hits = 0; scanned = 0
for f in files:
    if not os.path.isfile(f): continue
    try: b = open(f, 'rb').read()
    except OSError: continue
    scanned += 1
    for k in keys:
        if k.encode() in b or k[:16].encode() in b: hits += 1; print('KEY MATERIAL FOUND IN', f)
procs = 0
for p in glob.glob('/proc/[0-9]*/environ'):
    try:
        b = open(p, 'rb').read()
        if any(k.encode() in b for k in keys): procs += 1; print('KEY IN ENVIRON OF PID', p.split('/')[2], open(p.replace('environ', 'cmdline'), 'rb').read()[:60])
    except OSError: pass
print('keys checked', len(keys), 'files scanned', scanned, 'files with key material', hits, 'processes with keys in environ (besides this one)', procs - 1 if procs else 0)
print('files', [os.path.basename(f) for f in files if os.path.isfile(f)])
