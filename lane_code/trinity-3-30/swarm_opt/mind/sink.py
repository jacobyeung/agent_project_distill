"""Copy stdin to a new local file and to stdout, hashing as it goes; write <file>.sha256 at the end."""
import hashlib, sys
out = sys.argv[1]; h = hashlib.sha256(); n = 0
with open(out, 'xb') as f:
    while True:
        b = sys.stdin.buffer.read(65536)
        if not b: break
        f.write(b); sys.stdout.buffer.write(b); h.update(b); n += len(b)
sys.stdout.buffer.flush()
open(out + '.sha256', 'w').write('%s  %s\n' % (h.hexdigest(), out.rsplit('/', 1)[-1]))
print('sink bytes=%d sha256=%s' % (n, h.hexdigest()), file=sys.stderr)
