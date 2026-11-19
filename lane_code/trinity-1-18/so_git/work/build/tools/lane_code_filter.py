# lane_code_filter.py <label> [manifest_dir]: run with cwd = the tree to sync.
# Prints NUL-separated relative paths of whitelisted agent-written files, one copy per distinct content;
# later identical copies are listed in <manifest_dir>/DEDUP_<label>.tsv.gz ("dup_path<TAB>kept_path") and
# that manifest path is printed last. Stats go to stderr.
import gzip, hashlib, os, re, sys
EXT = ('.py', '.sh', '.md', '.json', '.jsonl', '.yaml', '.yml', '.toml', '.cfg', '.txt', '.patch', '.diff', '.tpl', '.ini', '.tsv')
# Explicit opt-in for reviewed shell-code snapshots; default selection is unchanged.
if os.environ.get('LCS_INCLUDE_SHELL_COPIES') == '1':
    EXT += ('.sh.copy',)
MAXB = 512 * 1024
DATA_MAXB = 256 * 1024  # .json/.jsonl above this are data rows or result dumps
MAXDIR = 2000
SUBSTR = ('out/devin_traces', '/dl/', '/root/', '/envs/', 'site-packages', '__pycache__', '.cache', 'node_modules')
# Scratch copies, test/mutation outputs, caches, vendored libraries, data rows and result dumps.
DIRRE = re.compile(r'^(tmp.*|retained_.*|rows_.*|slices_v\d+|.*proofs?|.*_proof|artifacts|r2_[a-z0-9_]{8}|rec_v\d.*'
                   r'|.*_stale|.*_prev|cmp_.*|test_products|results|clone|mutation.*|mut|mut_.*|.*_mut|round_.*'
                   r'|.*cache.*|scipy|numpy|torch|.*\.dist-info|.*\.egg-info|runs|evidence|transactions|env\d*|venv|\.venv)$')
label = sys.argv[1] if len(sys.argv) > 1 else '?'
mdir = sys.argv[2] if len(sys.argv) > 2 else None
n = 0; tot = 0; big = 0; bigdirs = []; dups = []; seen = {}; out = sys.stdout.buffer
for d, dirs, files in os.walk('.', followlinks=False):
    p = '/' + d[2:] + '/' if d != '.' else '/'
    keep = []
    for x in dirs:
        q = p + x + '/'
        if x == '.git' or 'frames' in x or DIRRE.match(x) or any(s in q for s in SUBSTR):
            continue
        try:
            if len(os.listdir(os.path.join(d, x))) > MAXDIR:
                bigdirs.append(q[1:]); continue
        except OSError:
            continue
        keep.append(x)
    dirs[:] = sorted(keep)
    for f in sorted(files):
        if not f.endswith(EXT) or f.endswith('.sqlite'):
            continue
        fp = os.path.join(d, f)
        if os.path.islink(fp) or any(s in p + f for s in SUBSTR):
            continue
        try:
            sz = os.path.getsize(fp)
            if sz > MAXB or (sz > DATA_MAXB and f.endswith(('.json', '.jsonl'))):
                big += 1; continue
            h = hashlib.sha1(open(fp, 'rb').read()).hexdigest()
        except OSError:
            continue
        rel = fp[2:]
        if h in seen:
            dups.append(rel + '\t' + seen[h]); continue
        seen[h] = rel; n += 1; tot += sz
        out.write(rel.encode('utf-8', 'surrogateescape') + b'\0')
if mdir:
    os.makedirs(mdir, exist_ok=True)
    mp = os.path.join(mdir, 'DEDUP_%s.tsv.gz' % label.replace('/', '_'))
    with gzip.open(mp, 'wt', encoding='utf-8', errors='surrogateescape') as g:
        g.write(''.join(x + '\n' for x in dups))
    out.write(os.path.relpath(mp).encode() + b'\0')
sys.stderr.write('STATS %s files=%d bytes=%d dups=%d skipped_oversize=%d skipped_bigdirs=%d %s\n'
                 % (label, n, tot, len(dups), big, len(bigdirs), ' '.join(bigdirs[:20])))
