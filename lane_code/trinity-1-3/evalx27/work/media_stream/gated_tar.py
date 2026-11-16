"""Stop until the governor continues this process, then write one deterministic USTAR stream of the pinned media to stdout.
Same member rules as kit_revsi/media/make_archive.py; every source is checked by size and sha256 while it streams."""
import hashlib, json, os, signal, sys, tarfile
need = json.load(open(sys.argv[1]))
os.kill(os.getpid(), signal.SIGSTOP)
out = sys.stdout.buffer
class R:
    def __init__(s, f): s.f = f; s.h = hashlib.sha256(); s.n = 0
    def read(s, n=-1):
        b = s.f.read(n); s.h.update(b); s.n += len(b); return b
with tarfile.open(fileobj=out, mode='w|', format=tarfile.USTAR_FORMAT) as tar:
    for row in sorted(need, key=lambda r: r['relative_path']):
        p = row['source']
        if os.path.islink(p) or not os.path.isfile(p) or os.path.getsize(p) != row['bytes']:
            sys.exit('source size/type differs: ' + p)
        ti = tarfile.TarInfo(row['relative_path']); ti.size = row['bytes']; ti.mode = 0o644; ti.mtime = 0; ti.uid = ti.gid = 0; ti.uname = ti.gname = ''
        with open(p, 'rb') as f:
            r = R(f); tar.addfile(ti, r)
            if r.read(1) or r.n != row['bytes'] or r.h.hexdigest() != row['sha256']:
                sys.exit('source pin differs: ' + p)
