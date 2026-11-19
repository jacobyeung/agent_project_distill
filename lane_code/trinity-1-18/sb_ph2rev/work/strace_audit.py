"""Audit an strace -f -e trace=%file log: writes outside an allowed root, and any touch of /home or /data*."""
import collections, json, re, sys

log, allowed = sys.argv[1], sys.argv[2:]
pat = re.compile(r'^(\d+)\s+(?:[\d:.]+\s+)?(\w+)\((.*)\)\s+=\s+(-?\d+|\?)')
WRITE_FLAGS = ('O_WRONLY', 'O_RDWR', 'O_CREAT', 'O_TRUNC', 'O_APPEND')
MUTATE = {'mkdir', 'mkdirat', 'rename', 'renameat', 'renameat2', 'unlink', 'unlinkat', 'rmdir', 'link', 'linkat',
          'symlink', 'symlinkat', 'chmod', 'fchmodat', 'truncate', 'utimensat', 'creat'}
writes, nfs, calls = collections.Counter(), collections.Counter(), collections.Counter()
for line in open(log, errors='replace'):
    m = pat.match(line)
    if not m:
        continue
    pid, call, args, ret = m.groups()
    calls[call] += 1
    paths = re.findall(r'"([^"]*)"', args)
    for p in paths:
        if p.startswith(('/home', '/data')):
            nfs[(call, p, 'ok' if ret not in ('-1',) else 'ENOENT/err')] += 1
    is_write = (call in ('open', 'openat') and any(f in args for f in WRITE_FLAGS)) or call in MUTATE
    if is_write and ret != '-1' and paths:
        p = paths[-1] if call.startswith('rename') or call.startswith('link') or call.startswith('symlink') else paths[0]
        if p.startswith('/') and not p.startswith(('/dev/', '/proc/')) and not any(p.startswith(a) for a in allowed):
            writes[(call, p)] += 1
        elif not p.startswith('/'):
            writes[(call, 'RELATIVE:'+p)] += 1
out = dict(log=log, allowed=allowed, syscalls=sum(calls.values()),
           nfs_touches=[dict(call=c, path=p, result=r, n=n) for (c, p, r), n in sorted(nfs.items())][:60], nfs_count=sum(nfs.values()),
           writes_outside=[dict(call=c, path=p, n=n) for (c, p), n in sorted(writes.items())][:80], writes_outside_count=sum(writes.values()))
print(json.dumps(out, indent=1))
