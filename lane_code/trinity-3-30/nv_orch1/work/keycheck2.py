import os, glob
keys = [os.environ.pop(k) for k in ('NVK_A', 'NVK_B', 'NVK_C', 'NVK_D') if os.environ.get(k)]
home = os.path.expanduser('~'); J = '/project/community/jjyeung/4f5e45fe5d74c'
files = set()
for root, dirs, fs in os.walk(J):
    for f in fs: files.add(os.path.join(root, f))
files |= set(glob.glob('/tmp/nvk1*') + glob.glob('/tmp/nvk1/**/*', recursive=True) + glob.glob('/tmp/nvo*') + glob.glob('/tmp/nvo*/**/*', recursive=True))
files |= {home + '/' + h for h in ('.bash_history', '.python_history', '.lesshst', '.viminfo', '.wget-hsts', '.sh_history', '.zsh_history')}
hits = scanned = nbytes = 0
for f in sorted(files):
    if not os.path.isfile(f): continue
    try: b = open(f, 'rb').read()
    except OSError: continue
    scanned += 1; nbytes += len(b)
    for k in keys:
        if k.encode() in b or k[:16].encode() in b: hits += 1; print('KEY MATERIAL FOUND IN', f)
procs = 0
for p in glob.glob('/proc/[0-9]*/environ'):
    try:
        if any(k.encode() in open(p, 'rb').read() for k in keys): procs += 1
    except OSError: pass
print('host', os.uname()[1], 'keys checked', len(keys), 'files scanned', scanned, 'bytes', nbytes, 'files with key material', hits, 'processes holding a key besides this checker', max(0, procs - 1))
