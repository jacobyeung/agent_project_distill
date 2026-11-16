import json, collections, sys
src, out, title = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src))
def short(p):
    for k, tag in (('/tree_b01ce449/', 'tree:'), ('/tree_r1/', 'b5:'), ('/native/out2/', 'c8r:'), ('/orchard_native/', 'c8r:orchard_native/')):
        if k in p:
            return tag+p.split(k)[1]
    return p
lines = [f'# {title}', '', f'Source: `{src}` (eat1.scan, eat1/allowlist.json PROPOSED). Static-only mode: every finding in scope counts. '
         '`tree:` = sealed tree b01ce449 audit copy; `b5:` = next-leg tree build 5 (ba346bd9); `c8r:` = code_c8r.tar out2 reader.', '']
by = collections.defaultdict(list)
for f in d['findings']:
    by[f['clause']].append(f)
for c in sorted(by):
    lines += [f'## {c} ({len(by[c])})', '']
    for f in sorted(by[c], key=lambda f: (short(f['file']), f['line'])):
        lines.append(f"- `{f['rule']}` {short(f['file'])}:{f['line']} ({f['function']}): {f['detail'][:70]} — `{f['text'][:110]}`")
    lines.append('')
open(out, 'w').write('\n'.join(lines)+'\n')
