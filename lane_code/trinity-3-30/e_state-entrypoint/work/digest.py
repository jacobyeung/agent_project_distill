import os, re, sys
sys.path.insert(0, 'clone/tools/docs')
import indexfmt
rows, _ = indexfmt.parse(open('ref/INDEX.md').read())
legacy = {}
for r in rows:
    for f in r.files:
        legacy.setdefault(f, (r.topic or '', r.status or ''))
names = indexfmt.read_listing('ref/design_ls.txt')
out = []
for n in names:
    topic, st = legacy.get(n, ('', ''))
    h1 = ''; sl = ''
    p = os.path.join('ref/heads', n)
    if os.path.exists(p):
        lines = open(p, errors='replace').read().splitlines()
        for l in lines:
            if l.startswith('# '): h1 = l[2:]; break
        for l in lines:
            if re.search(r'\bstatus\b', l, re.I) and not l.startswith('#'):
                sl = l.strip(); break
    out.append('%s\n  T: %s\n  S: %s\n  H: %s\n  HS: %s' % (n, topic[:140], st[:170], h1[:140], sl[:200]))
open('work/digest.txt', 'w').write('\n'.join(out) + '\n')
