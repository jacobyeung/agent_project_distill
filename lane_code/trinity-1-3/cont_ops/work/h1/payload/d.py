"""Derive a data-only kit (or a narrowly admitted code-tree kit) from sealed kit 07ca49df's own records: same trainer tree, b/ gate, job scripts and 7.json;
new row-store pins (VQA, routing), pool selection, dev scene exclusions, init artifact and run identity.
Serialization follows launch_s1/build.py (sorted compact JSON plus newline; config file name = sha256(config)[:8];
launch source_seal as b/g.py checks it).

Usage: derive_kit.py KIT_DIR OUT_DIR OVERRIDES.json
OVERRIDES keys (anything else is refused):
  run_key, kit_key, persistent_run_root   all three required, and new, whenever any input changes
  code_tree: {archive: {path, sha256}, pin: {path, sha256}, archive_record?: {path, sha256}}
           validates deterministic source archive, regenerates tree bindings, installs fixed stop bridge;
           archive_record is required for READY and must attest this archive off scratch.
  config: {h1?, milestones?, recipe: {milestones?, scheduled_sampling?}?, scheduled_sampling?, streams: {vqa?, routing?}, init_artifact?, s1_routing: {selection?, catalog?}?}
           (the dev withheld list and scene coverage stay sealed: s1_exclusions binds them to the pool manifest)
  deployment: {init?, tars?, extra?}       replacements of k/0.json entries
  add_k: {name: {path, sha256}}            new small records: review.json, staging.json, 4.json, and new-named
                                           pool_selection_<tag>.json
  status: BLOCKED (default) | PREPARATION_ONLY | READY   READY needs review.json, staging.json and 4.json in add_k, bound to
                                           the new identity; PREPARATION_ONLY (mode p only) needs 4.json bound, modes [p]
  content: {sha256: local path}           bytes of new JSON documents (receipts, artifact.json, full_weights.json, ...) so their
                                           pins can be walked
  accept_unstaged: {sha256: {field: source, reason}}  a stream receipt's provenance source the kit does not place; each is
                                           reported in the result for the reviewer
  tar_members: {first part path: [names]} member listing of every new tar (c.sh extracts all members, verifies listed ones)
  export_member_names: [names]             init export members when the full_weights.json bytes are not at hand; each is
                                           then verified at staging against the sha-pinned manifest (c.sh tk_stage_init)
  sealed_docs: [local paths]               bytes of sealed stream receipts (each must equal a pin of the sealed config): a pin
                                           they name was resolved by the sealed kit's own admission, so a new document may
                                           name it too (same producers, nothing sealed removed)
  e00_listing: local path                  member listing of the sealed small tar e00 ({name: sha256}); used only to protect
                                           its destinations from additions, never to close a pin (job-side vt.py rechecks e00)
  fixture: true                            allow source-kit files listed in SHA256SUMS to be absent (tests only; output is
                                           marked FIXTURE and can never be READY)
An empty OVERRIDES reproduces the kit's k/ records byte for byte; with {"fixture": true} (big tars absent) every record except
launch.json (status FIXTURE, unauthorized) is byte-identical. The source must be the sealed kit itself (its SHA256SUMS.txt
hash), so a READY kit is never promoted from an earlier derivation.
Additions land only in fresh directories: ap/<d>/, X/u/<d>/ or X/runs/469ddece/m544/, with no sealed path (placements,
records, sealed receipts, e00 listing) under them."""
import copy, hashlib, json, re, shutil, sys, tarfile
from pathlib import Path

def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
def digest(v): return hashlib.sha256(enc(v).encode()).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, v): Path(p).write_text(enc(v) + '\n')
"""Mode-preserving writes confined to one derived output tree."""
from contextlib import contextmanager
import stat
from pathlib import Path


def mode_inventory(root):
    root = Path(root)
    return {str(p.relative_to(root)): stat.S_IMODE(p.stat().st_mode)
            for p in [root, *sorted(root.rglob('*'))]}


class SealedOutput:
    def __init__(self, root, file_mode=0o400):
        root = Path(root).absolute()
        if root != root.resolve(strict=True): refuse('symlink in output root')
        self.root = root
        self.file_mode = file_mode

    def checked(self, path):
        path = Path(path).absolute()
        if (path != self.root and self.root not in path.parents) or '..' in path.parts:
            refuse('write outside output directory')
        for p in [path, *path.parents]:
            if p.is_symlink(): refuse('symlink in output write')
            if p == self.root: break
        if path.is_file() and path.stat().st_nlink != 1:
            refuse('linked output file')
        return path

    @contextmanager
    def writable(self, path, mode=None):
        path = self.checked(path)
        if path == self.root: refuse('write must name an output member')
        parent = path.parent
        parent_mode = stat.S_IMODE(parent.stat().st_mode)
        final_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else (
            self.file_mode if mode is None else mode)
        try:
            parent.chmod(parent_mode | stat.S_IWUSR)
            if path.exists(): path.chmod(final_mode | stat.S_IWUSR)
            yield path
        finally:
            try:
                if path.exists(): path.chmod(final_mode)
            finally:
                parent.chmod(parent_mode)

    def text(self, path, text, mode=None):
        with self.writable(path, mode) as p: p.write_text(text)

    def write(self, path, value, mode=None):
        self.text(path, enc(value) + '\n', mode)

    def copy(self, source, path, mode=None):
        with self.writable(path, mode) as p: shutil.copyfile(source, p)

    def mkdir(self, path, mode):
        with self.writable(path, mode) as p: p.mkdir(mode=mode | stat.S_IWUSR)


def identity(cfg):  # b/i.py identity, same logic
    value = {k: v for k, v in cfg.items() if k not in ('preparation', 'admission', 'authorization', 'milestone_gate')}
    if 'readout' in value:
        value['readout'] = {k: v for k, v in value['readout'].items() if k != 'contiguous_clips'}
    if value.get('frame_layout') == 'spread': value.pop('frame_layout')
    return digest(value)

HEX8 = re.compile('[0-9a-f]{8}')
TOP = {'run_key', 'kit_key', 'persistent_run_root', 'config', 'deployment', 'add_k', 'status', 'fixture', 'content', 'accept_unstaged', 'tar_members', 'sealed_docs',
       'export_member_names', 'e00_listing', 'code_tree'}
SEALED_MANIFEST = 'de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b'  # SHA256SUMS.txt of sealed kit 07ca49df
CONFIG = {'streams', 'init_artifact', 's1_routing', 'h1', 'milestones', 'recipe', 'scheduled_sampling'}
STREAMS = {'vqa', 'routing'}
S1_ROUTING = {'selection', 'catalog'}
DEPLOYMENT = {'init', 'tars', 'extra'}
ADD_K = {'review.json', 'staging.json', '4.json'}
ADD_K_DATA = re.compile('pool_selection_[a-z0-9]{1,16}\\.json')  # new names: the sealed catalog keeps the old files
AS = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
AL = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
KIT_LOGICAL = AS + 'ap/8865619b/k/'

def refuse(why): raise ValueError('derive_kit: ' + why)

def staged_files(cur):
    """Logical relative path -> sha256 for everything k/0.json stages from tars and extra."""
    out = {}
    def put(k, v):
        if k in out and out[k] != v: refuse('k/0.json stages two different files at ' + k)
        out[k] = v
    for e in cur.get('extra', []):
        put(rel(e['dest']), e['sha256'])
    for t in cur.get('tars', []):
        for k, v in t['files'].items(): put(k, v)
    return out

def rel(path):
    for prefix in (AS, AL):
        if path.startswith(prefix): return path[len(prefix):]
    refuse('pin outside the code-aws prefixes: ' + path)

HEX64 = re.compile('[0-9a-f]{64}')
PART = re.compile('/project/community/jjyeung/(distill/okit/in(/cr)?|okh7/[A-Za-z0-9._-]+)/[A-Za-z0-9._-]+')
KIT_REL = 'ap/8865619b/'

def rel_or_none(path):
    for prefix in (AS, AL):
        if isinstance(path, str) and path.startswith(prefix): return path[len(prefix):]
    return None

def safe_rel(k): return isinstance(k, str) and not k.startswith('/') and all(x not in ('', '.', '..') for x in k.split('/'))

X_REL = 'ap/8865619b/'              # c.sh X = AS/ap/8865619b: bwrap binds it to the per-job kit root NX
MOUNTED = ('runs/', 'models/', 'data2root/', 'u/')  # explicit bwrap mounts under X (u/ is U/ap/8865619b/u)
NX_KIT = ('k/', 'b/')               # what c.sh tk_nx copies into NX from the kit (plus ANON_OK.json, SHA256SUMS.txt)

def trainer_view(path):
    """Physical file the trainer opens for a code-aws pin, under c.sh tk_bwrap: AS and AL -> U; AS/X -> NX, with
    X/u -> U/X/u and X/runs, X/models, X/data2root on separate mounts that derive_kit never populates."""
    if isinstance(path, str) and path.startswith(AS + X_REL):
        sub = path[len(AS + X_REL):]
        if sub.startswith('u/'): return ('U', X_REL + sub)
        if sub.startswith(MOUNTED): return None
        return ('NX', sub)
    r = rel_or_none(path)
    return ('U', r) if r else None

def hp_view(path):
    """c.sh hp(): AS/X -> NX; AS, AL -> U (used for extra destinations and the init artifact copy)."""
    if isinstance(path, str) and path.startswith(AS + X_REL): return ('NX', path[len(AS + X_REL):])
    r = rel_or_none(path)
    return ('U', r) if r else None

def union_view(path):
    """tk_stage_init host(): AS, AL -> U (init heads, full_weights manifest and shards)."""
    r = rel_or_none(path)
    return ('U', r) if r else None

def check_parts(parts):
    if not isinstance(parts, list) or not parts or not all(
            isinstance(x, str) and PART.fullmatch(x) and all(s not in ('.', '..', '') for s in x[1:].split('/')) for x in parts):
        refuse('parts must be files under okit/in or okh7/<dir>: ' + str(parts)[:120])

def check_entries(cur):
    """Shape of every tars and extra entry: parts in the okit input directory, safe logical paths, sha256 digests."""
    for t in cur.get('tars', []):
        if not isinstance(t, dict) or set(t) - {'files', 'parts', 'sha256'} or not {'files', 'parts'} <= set(t): refuse('malformed k/0.json tars entry')
        check_parts(t['parts'])
        if not isinstance(t['files'], dict) or not t['files'] or not all(
                safe_rel(k) and k.startswith('ap/') and isinstance(v, str) and HEX64.fullmatch(v) for k, v in t['files'].items()):
            refuse('tars files must map safe ap/ paths to sha256 digests')
        if 'sha256' in t and not (isinstance(t['sha256'], str) and HEX64.fullmatch(t['sha256'])): refuse('tars sha256 malformed')
    for e in cur.get('extra', []):
        if not isinstance(e, dict) or set(e) != {'dest', 'parts', 'sha256'}: refuse('malformed k/0.json extra entry')
        if not safe_rel(rel(e['dest'])) or not HEX64.fullmatch(str(e['sha256'])): refuse('malformed extra entry ' + e['dest'])
        check_parts(e['parts'])

def placements(cur, kit_files, small):
    """Physical key -> (sha256, producer) for every file the staging of c.sh places, in its order (small, extra, a1rows,
    tars, staged_inputs, kit copy into NX). Two producers placing different bytes at one key are refused. `small` is the
    evidenced member listing of the small tar (rel -> sha); tk_stage_small copies its AS/AL subtrees into U."""
    out = {}
    def put(key, value, producer):
        if key is None: refuse(producer + ': destination outside the code-aws prefixes')
        if key in out and out[key][0] != value: refuse(f'{producer} and {out[key][1]} place different bytes at {key[0]}:{key[1]}')
        out[key] = (value, producer)
    for r, v in small.items(): put(('U', r), v, 'small')
    for src, dst in (('ap/244cdf20/k/932c0c4e.json', 'ap/f1a2c7e9/k/932c0c4e.json'), ('ap/244cdf20/k/99e6eed6.json', 'ap/f1a2c7e9/k/99e6eed6.json')):
        if src in small: put(('U', dst), small[src], 'small copy')
    for e in cur.get('extra', []) + ([cur['a1rows']] if 'a1rows' in cur else []):
        put(hp_view(e['dest']), e['sha256'], 'extra ' + e['dest'][-60:])
    for i, t in enumerate(cur.get('tars', [])):
        for k, v in t['files'].items(): put(('U', k), v, f'tars[{i}]')
    si = cur.get('staged_inputs', {})
    for f in si.get('files', []): put(('U', X_REL + f['destination']), f['sha256'], 'staged_inputs')
    for pkg in si.get('packages', []):
        for item in pkg.get('inventory', []): put(('U', X_REL + pkg['destination'] + '/' + item['name']), item['sha256'], 'staged_inputs')
    for name, v in kit_files.items():
        if name.startswith(NX_KIT): put(('NX', name), v, 'kit')
    return out

def sealed_parts(cur):
    """Every project path the sealed k/0.json names (archives, parts, single files): never reused by a changed entry."""
    found = set()
    def walk(v):
        if isinstance(v, dict): [walk(x) for x in v.values()]
        elif isinstance(v, list): [walk(x) for x in v]
        elif isinstance(v, str) and v.startswith('/project/'): found.add(v)
    walk(cur)
    return found

def pins_in(doc, keypath=()):
    """(keypath, path, sha256) for every {path|file, sha256} dict and every companion pair (X, X_sha256) in a document."""
    if isinstance(doc, dict):
        target = doc.get('path', doc.get('file'))
        if isinstance(target, str) and isinstance(doc.get('sha256'), str) and HEX64.fullmatch(doc['sha256']): yield keypath, target, doc['sha256']
        for k, v in doc.items():
            c = doc.get(str(k) + '_sha256')
            if isinstance(v, str) and isinstance(c, str) and HEX64.fullmatch(c): yield keypath + (k,), v, c
            yield from pins_in(v, keypath + (k,))
    elif isinstance(doc, list):
        for i, v in enumerate(doc): yield from pins_in(v, keypath + (i,))

LEAF_KEYS = {'database', 'heads'}
EXPORT_NAME = re.compile(r'full_weights\.json|model\.safetensors\.index\.json|model-\d{5}-of-\d{5}\.safetensors')
CODE_DIRS = ('ap/7b30c1e4/',)       # the fla overlay directory c.sh tk_pythonpath puts on PYTHONPATH (U side)
CODE_SUFFIXES = ('.py', '.pyc', '.pth', '.so', '.sh', '.pyz', '.egg', '.whl')   # row stores and head weights: binary files read by the trainer, verified by sha256 there

def sealed_paths(values):
    """Every code-aws path (relative) that a sealed record names, recursively."""
    found = set()
    def walk(v):
        if isinstance(v, dict): [walk(x) for x in list(v.keys()) + list(v.values())]
        elif isinstance(v, list): [walk(x) for x in v]
        elif isinstance(v, str):
            r = rel_or_none(v)
            if r is None and v.startswith(('scratch/', 'lustre/')): r = rel_or_none('/' + v)
            if r: found.add(r.rstrip('/'))
    walk(values)
    return found

def allocation(k):
    """The fresh directory an addition must own: X/runs/469ddece/m544/, X/u/<d>/ or ap/<d>/."""
    if k.startswith(X_REL + 'runs/469ddece/m544/'): return X_REL + 'runs/469ddece/m544/'
    if k.startswith(X_REL + 'u/'): return '/'.join(k.split('/')[:4]) + '/'
    return '/'.join(k.split('/')[:2]) + '/'

def close(kit, out, cfg, base_cfg, cur, base_cur, over, missing):
    """Walk the dependency graph of every changed input (stream receipts, init artifact and its full_weights manifest,
    pool selection through the catalog, every catalog entry) against the physical placements of c.sh. A pin is closed
    when the file its consumer opens (trainer_view, union_view for init weights, hp_view for the init artifact) holds that
    sha256. A placement identical in the sealed kit closes a sealed document's own dependencies, since the sealed kit
    staged and ran with them and no sealed placement may be removed except the replaced init. A new document needs its
    bytes (override content) unless it is a leaf (row database, heads, export members). Staging additions must be
    reached; removals must belong to the replaced init; sealed part names are never reused."""
    check_entries(cur)
    src_man = dict(reversed(l.split('  ', 1)) for l in (kit / 'SHA256SUMS.txt').read_text().splitlines())
    out_man = {str(p.relative_to(out)): sha(p) for part in NX_KIT for p in (out / part).rglob('*') if p.is_file()}
    out_man.update({n: src_man[n] for n in missing})
    regen = {'k/0.json', 'k/1.json', 'k/launch.json', 'k/' + json.loads((kit / 'k/1.json').read_text())['0'] + '.json'}
    if 'code_tree' in over:
        regen |= code_records(json.loads((out / 'k/7.json').read_text()))
    out_man = {n: v for n, v in out_man.items() if n not in regen}  # regenerated records, written after the closure
    src_man = {n: v for n, v in src_man.items() if n not in regen}
    small = {}  # the sealed small tar's members are not enumerated in k/0.json: nothing new may rely on them
    P, base_P = placements(cur, out_man, small), placements(base_cur, src_man, small)
    accept = over.get('accept_unstaged', {})
    if not isinstance(accept, dict) or not all(HEX64.fullmatch(k) and isinstance(v, dict) and v.get('field') == 'source'
                                               and isinstance(v.get('reason'), str) and v['reason'].strip() for k, v in accept.items()):
        refuse('accept_unstaged maps sha256 -> {field: source, reason}; only a stream receipt\'s provenance source may be waived')
    docs = {}
    for digest_, path in over.get('content', {}).items():
        if sha(path) != digest_: refuse('content file differs from its sha256: ' + str(path))
        docs[digest_] = json.loads(Path(path).read_text())
    for p in (out / 'k').iterdir():
        if p.suffix == '.json' and p.is_file(): docs.setdefault(sha(p), json.loads(p.read_text()))
    tar_members = over.get('tar_members', {})
    if not isinstance(tar_members, dict): refuse('tar_members maps a first part path to the archive member names')
    for e in cur.get('tars', []):  # members a new archive holds without a listed sha256: placed, bytes unverified here
        for n in tar_members.get(e['parts'][0], []):
            if not safe_rel(n): refuse('unsafe tar member name ' + str(n))
            P.setdefault(('U', n), ('<unlisted>', 'tar member ' + e['parts'][0][-40:]))
    reached, accepted, walked, chained = set(), {}, set(), set()
    sealed_pins = {(base_cfg['streams'][n]['path'], base_cfg['streams'][n]['sha256']): n for n in base_cfg['streams']}
    sealed_closed = {}
    for path in over.get('sealed_docs', []):
        d = sha(path); owner = [n for (p_, s_), n in sealed_pins.items() if s_ == d]
        if not owner: refuse('sealed_docs entry is not a sealed stream receipt: ' + str(path))
        for kp, p_, s_ in pins_in(json.loads(Path(path).read_text())): sealed_closed[(p_, s_)] = owner[0]
    catalog = cfg['s1_routing']['catalog']
    lost = [d for d, pth in base_cfg['s1_routing']['catalog'].items() if catalog.get(d) != pth]
    if lost: refuse('the catalog must keep every sealed mapping: ' + ', '.join(x[:12] for x in lost[:5]))
    def visit(path, digest_, where, view=trainer_view, leaf=False, via_catalog=False, field=None, doc_schema=None):
        key = view(path)
        if (key is None or P.get(key, (None,))[0] != digest_) and via_catalog and catalog.get(digest_) and catalog[digest_] != path:
            return visit(catalog[digest_], digest_, where + ' (catalog)', view, leaf)
        if (key is None or key not in P) and (path, digest_) in sealed_closed:  # unplaced here: the sealed admission resolved it
            accepted[digest_] = dict(path=path, where=where, reason='named by the sealed ' + sealed_closed[(path, digest_)] + ' receipt')
            return
        if key is None or P.get(key, (None,))[0] != digest_:
            if digest_ in accept and field == ('source',) and doc_schema == 'c1-stream-v1':
                accepted[digest_] = dict(path=path, where=where, reason=accept[digest_]['reason']); return
            refuse(f'{where}: pin {path} sha {digest_[:12]} is not placed where its consumer reads it')
        reached.add(key)
        if base_P.get(key, (None,))[0] == digest_ or leaf or (key, digest_) in walked: return
        walked.add((key, digest_))
        doc = docs.get(digest_)
        sub = where + ' > ' + key[1]
        if doc is None:
            if key in chained: return  # export member named by a sha-pinned manifest; tk_stage_init verifies it
            refuse(f'{where}: new {key[1]} needs its bytes in override content to close its dependencies')
        schema = doc.get('schema') if isinstance(doc, dict) else None
        is_export = isinstance(doc, dict) and isinstance(doc.get('index'), dict) and isinstance(doc.get('files'), list)
        for kp, p, s in pins_in(doc):
            if is_export and kp and kp[0] in ('index', 'files'): continue
            init_weights = schema == 'carrier-c1-artifact-v1' and kp[:1] in (('heads',), ('full_weights',))
            visit(p, s, sub, union_view if init_weights or view is union_view else trainer_view,
                  leaf=bool(kp) and kp[-1] in LEAF_KEYS, via_catalog=via_catalog, field=kp, doc_schema=schema)
        if is_export:
            d = path.rsplit('/', 1)[0]
            for item in [doc['index']] + doc['files']:
                if not safe_rel(item.get('name')) or '/' in item['name']: refuse(sub + ': export manifest names a nested path')
                visit(d + '/' + item['name'], item['sha256'], sub, union_view, leaf=True)
    def visit_export_by_name(manifest_path, names, where):
        d = manifest_path.rsplit('/', 1)[0]
        for n in names:
            k = union_view(d + '/' + n)
            if k not in P: refuse(f'{where}: export member {n} is not placed')
            reached.add(k); chained.add(k)
    for name in cfg['streams']:
        if cfg['streams'][name] != base_cfg['streams'][name]:
            visit(cfg['streams'][name]['path'], cfg['streams'][name]['sha256'], 'stream ' + name)
    if cfg['init_artifact'] != base_cfg['init_artifact']:
        a = cfg['init_artifact']['artifact']
        art = docs.get(a['sha256'])
        if art is None: refuse('init_artifact needs the artifact bytes in override content')
        fw = art['full_weights']
        if fw['sha256'] not in docs:  # manifest bytes absent: its members must be placed by name (tar_members evidence)
            names = over.get('export_member_names', [])
            if not names or not isinstance(names, list): refuse('init export: give its full_weights.json bytes or export_member_names')
            if over.get('status', 'BLOCKED') == 'READY': refuse('READY needs the full_weights.json bytes (names alone admit only preparation)')
            if any(not isinstance(n, str) or not EXPORT_NAME.fullmatch(n) for n in names) or 'full_weights.json' not in names:
                refuse('export_member_names must be the manifest, its index and model shards only')
            visit_export_by_name(fw['path'], names, 'init_artifact')
            chained.add(union_view(fw['path']))
        visit(a['path'], a['sha256'], 'init_artifact', hp_view)
        if fw['sha256'] in docs:  # the init archive must hold exactly the artifact, heads, manifest and the manifest's files
            d = rel(fw['path']).rsplit('/', 1)[0]; man = docs[fw['sha256']]
            exact = {rel(a['path']), rel(art['heads']['path']), rel(fw['path'])} | {d + '/' + i['name'] for i in [man['index']] + man['files']}
            holders = [e for e in cur.get('tars', []) if rel(fw['path']) in e['files']]
            if len(holders) != 1 or set(tar_members.get(holders[0]['parts'][0], [])) != exact:
                refuse('the init archive listing must equal the artifact, heads, manifest and manifest files')
    if cfg['s1_routing']['selection'] != base_cfg['s1_routing']['selection']:
        sel = cfg['s1_routing']['selection']
        visit(sel['path'], sel['sha256'], 'pool selection', via_catalog=True)
    for s, p in catalog.items():
        visit(p, s, 'catalog')
    # Staging edits are restricted to the inputs that changed.
    added = sorted(k for k, v in P.items() if base_P.get(k, (None,))[0] != v[0])
    records = {('NX', 'k/' + n) for n in over.get('add_k', {})}  # new kit records named by add_k (checked above)
    added = [k for k in added if k not in records]
    removed_records = {k for k in records if k in base_P}
    for k in added:
        if k[0] != 'U' or (k[1].startswith(X_REL) and not k[1].startswith((X_REL + 'runs/469ddece/m544/', X_REL + 'u/'))):
            refuse(f'staging adds {k[0]}:{k[1]}: additions may only reach the union outside the kit root')
        if k[1].startswith(CODE_DIRS) or k[1].endswith(CODE_SUFFIXES) or '/site-packages/' in k[1]:
            refuse(f'staging adds {k[1]}: no addition may land in an import or executable location')
    prot = {k[1] for k in base_P if k[0] == 'U'} | sealed_paths([base_cfg, base_cur]) | sealed_paths(
        [json.loads(p.read_text()) for p in sorted((kit / 'k').iterdir()) if p.suffix == '.json' and p.is_file()])
    prot |= sealed_paths([json.loads(Path(p).read_text()) for p in over.get('sealed_docs', [])])
    if 'e00_listing' in over: prot |= sealed_paths(json.loads(Path(over['e00_listing']).read_text()))
    for k in added:
        a = allocation(k[1])
        if len(a.split('/')) < 3 or any(p == a.rstrip('/') or p.startswith(a) for p in prot):
            refuse(f'staging adds {k[1]}: its directory {a} is not fresh (a sealed path lies under it)')
    if set(added) - reached: refuse('staging entries not reached from any changed input: ' + ', '.join(sorted(k[1] for k in set(added) - reached))[:300])
    owners = []
    if cfg['init_artifact'] != base_cfg['init_artifact']:
        owners.append(rel(base_cfg['init_artifact']['artifact']['path']).rsplit('/', 1)[0] + '/')
    removed = sorted(k for k, v in base_P.items() if P.get(k, (None,))[0] != v[0] and k not in removed_records)
    stray = [k[1] for k in removed if not (k[0] == 'U' and any(k[1].startswith(o) for o in owners))]
    if stray: refuse('staging entries removed that belong to no replaced input: ' + ', '.join(stray)[:300])
    reserved = sealed_parts(base_cur)
    base_entries = [enc(e) for e in base_cur.get('tars', []) + base_cur.get('extra', [])]
    for e in cur.get('tars', []) + cur.get('extra', []):
        if enc(e) in base_entries: continue
        if set(e['parts']) & reserved: refuse('a changed staging entry reuses the sealed part ' + sorted(set(e['parts']) & reserved)[0])
        if 'files' in e:  # c.sh extracts every member and verifies only listed ones: the archive listing must be supplied
            listing = tar_members.get(e['parts'][0])
            if not isinstance(listing, list): refuse('new tar entry needs its member listing in tar_members: ' + e['parts'][0])
            extra_members = set(listing) - set(e['files']) - {k[1] for k in chained}
            if extra_members: refuse('new tar holds members that are neither listed nor chained: ' + ', '.join(sorted(extra_members))[:200])
    return dict(reached_new=len(walked), added=len(added), removed=len(removed), accepted_unstaged=accepted,
                chained_export_members=len(chained))


# Code changes have a separate validator; data staging never gains executable destinations.
H1 = dict(faithful_own_camera_rows=True, routing_pose_targets=True,
          camera_types=['camera_displacement', 'camera_movement_direction', 'camera_rotation'],
          stop_after_step=200, metrics=True,
          r0_rooms=dict(path='auth/R0_ROOMS.txt', sha256='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'))
SAMPLING = dict(force_from_step=1, max_own_probability=0.5)

def validate_h1(over):
    oc = over.get('config', {})
    new = set(oc) & {'h1', 'milestones', 'recipe', 'scheduled_sampling'}
    if new and 'code_tree' not in over: refuse('new training settings require code_tree')
    if 'h1' in oc and enc(oc['h1']) != enc(H1): refuse('only the registered settings are admitted')
    if 'milestones' in oc and enc(oc['milestones']) != enc([100, 200]): refuse('only milestones [100, 200] admitted')
    for value in [oc.get('scheduled_sampling', {}), oc.get('recipe', {}).get('scheduled_sampling', {})]:
        if not isinstance(value, dict) or set(value)-set(SAMPLING) or any(enc(value[k]) != enc(SAMPLING[k]) for k in value):
            refuse('scheduled_sampling permits only force_from_step=1 and max_own_probability=0.5')
    if set(oc.get('recipe', {}))-{'milestones', 'scheduled_sampling'}: refuse('unknown recipe keys')
    if 'milestones' in oc.get('recipe', {}) and oc['recipe']['milestones'] != [100, 200]: refuse('recipe milestones differ')
    if 'code_tree' in over:
        if '4.json' not in over.get('add_k', {}): refuse('code_tree requires add_k 4.json')
        if new != {'h1', 'milestones', 'recipe', 'scheduled_sampling'} or oc['recipe'] != dict(milestones=[100, 200], scheduled_sampling=SAMPLING) or oc['scheduled_sampling'] != SAMPLING:
            refuse('code_tree requires the complete registered settings')

def code_records(code):
    return {'k/7.json', 'k/s1_record.json', 'k/archive.json', 'k/' + Path(code['archive']['path']).name,
            'b/c.sh', 'b/p0.sh', 'b/r.sh', 'b/h.py', 'b/i.py', 'job.sh'}

def read_override_pin(value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'} or not HEX64.fullmatch(str(value['sha256'])):
        refuse('malformed code override pin')
    if sha(value['path']) != value['sha256']: refuse('code override pin differs')
    return Path(value['path'])

def replace_once(fs, path, before, after):
    text = path.read_text()
    if text.count(before) != 1: refuse('fixed runtime patch does not match ' + path.name)
    fs.text(path, text.replace(before, after))

def install_code(kit, out, over, cfg, cur, launch, fs):
    if over['run_key'] != '17c4ffa4': refuse('unregistered run')
    value = over['code_tree']
    if not isinstance(value, dict) or set(value)-{'archive', 'pin', 'archive_record'} or not {'archive', 'pin'} <= set(value):
        refuse('unknown or incomplete code_tree keys')
    archive = read_override_pin(value['archive']); pin = read_override_pin(value['pin'])
    code = json.loads(pin.read_text())
    if set(code) != {'schema', 'commit', 'tree_sha256', 'files', 'sources', 'operation_sources', 'archive'} or code['schema'] != 'c1-sealed-source-v1':
        refuse('code pin schema differs')
    tree = digest(code['files']); name = 't_' + tree[:16] + '.tar'
    if code['tree_sha256'] != tree or code['commit'] != 'sha256:' + tree or code['archive'] != dict(path=KIT_LOGICAL + name, sha256=sha(archive)):
        refuse('code tree/archive identity differs')
    members = {}; order = []
    with tarfile.open(archive) as tf:
        for m in tf:
            if not m.isfile() or not safe_rel(m.name) or m.name in members or m.size > 16_000_000 or (m.uid,m.gid,m.uname,m.gname,m.mtime) != (0,0,'','',0) or m.mode not in (0o644,0o755):
                refuse('unsafe or nondeterministic source member')
            order.append(m.name); members[m.name] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()
    if order != sorted(order) or members != code['files']: refuse('archive members differ from code pin')
    for key in ('sources', 'operation_sources'):
        if not code[key] or any(members.get(n) != h for n,h in code[key].items()): refuse('source closure differs')
    if members.get('auth/R0_ROOMS.txt') != H1['r0_rooms']['sha256']: refuse('required member is not sealed in tree')
    fs.copy(archive, out / 'k' / name); fs.copy(pin, out / 'k/7.json')
    record = json.loads((kit / 'k/s1_record.json').read_text())
    record['trees']['trainer'] = dict(commit=code['commit'], file_count=len(members), files=members)
    fs.write(out / 'k/s1_record.json', record)
    cur['record'] = dict(file=KIT_LOGICAL + 's1_record.json', sha256=sha(out / 'k/s1_record.json'))
    cur['trainer'] = dict(file=code['archive']['path'], sha256=code['archive']['sha256'])
    cur['commit'] = code['commit']; cfg['code'] = dict(path=KIT_LOGICAL + '7.json', sha256=sha(out / 'k/7.json'))
    launch['source_revision'] = code['commit']; launch['slot']['wall_seconds'] = 46800
    if 'archive_record' in value:
        rec = json.loads(read_override_pin(value['archive_record']).read_text())
        location = str(archive)
        if not PART.fullmatch(location): refuse('archive attestation must name the uploaded project archive')
        if rec.get('status') != 'ARCHIVED' or rec.get('durable') is not True or rec.get('location') != location or rec.get('sha256') != sha(archive) or rec.get('tree_sha256') != tree or rec.get('bytes') != archive.stat().st_size:
            refuse('archive attestation differs')
    else:
        if over.get('status') == 'READY': refuse('READY needs an off-scratch archive attestation')
        rec = dict(schema='s1-source-archive-v1', status='PENDING', durable=False,
                   sha256=sha(archive), tree_sha256=tree, bytes=archive.stat().st_size)
    fs.write(out / 'k/archive.json', rec)
    if '4.json' in over.get('add_k', {}):
        auth = json.loads((out / 'k/4.json').read_text())
        if auth.get('source_revision') != code['commit'] or auth.get('config_sha256') != identity(cfg) or auth.get('production_go_granted') is not False or auth.get('wall_seconds') != 46800:
            refuse('new source needs its own conditional authorization')
    # Both paths refer to the same inode through c.sh's NR -> X/runs writable bind.
    replace_once(fs, out / 'b/r.sh', '    printf \'USR1\\n\' >> "$stop_file"',
        '    printf \'USR1\\n\' >> "$stop_file"\n'
        '    run_dir=$(/usr/bin/python3 -I -c \'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])\' "$HX/k/launch.json")\n'
        '    mkdir -p "$run_dir"\n'
        '    printf \'USR1\\n\' >> "$run_dir/stop.${SLURM_JOB_ID:-local}.request"')
    replace_once(fs, out / 'b/h.py', 'except (FileNotFoundError, ProcessLookupError):',
                 'except (FileNotFoundError, ProcessLookupError, PermissionError):')
    replace_once(fs, out / 'b/i.py', '        except FileNotFoundError: pass',
                 '        except (FileNotFoundError, PermissionError): pass')
    replace_once(fs, out / 'job.sh', '#SBATCH --time=24:00:00', '#SBATCH --time=13:00:00')
    for before, after in [
        ('S=/tmp/jjyeung/okit_$K/root', 'S=/tmp/jjyeung/a_17c4ffa4/root'),
        ('NX=/tmp/jjyeung/okit_$K/x_${SLURM_JOB_ID:-local}', 'NX=/tmp/jjyeung/a_17c4ffa4/x_${SLURM_JOB_ID:-local}'),
        ('NR=${TK_RUNS_DIR:-/tmp/jjyeung/okit_$K/runs}', 'NR=/tmp/jjyeung/a_17c4ffa4/runs')]:
        replace_once(fs, out / 'b/c.sh', before, after)
    replace_once(fs, out / 'b/p0.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.preflight',
                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.preflight')
    replace_once(fs, out / 'b/r.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.${1:-x}',
                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.${1:-x}')


def derive(kit, out, over):
    kit, out = Path(kit), Path(out)
    if set(over) - TOP: refuse('unknown override keys ' + str(sorted(set(over) - TOP)))
    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the admitted set ' + str(sorted(set(over['config']) - CONFIG)))
    if set(over.get('config', {}).get('streams', {})) - STREAMS: refuse('only the vqa and routing streams may change')
    if set(over.get('config', {}).get('s1_routing', {})) - S1_ROUTING: refuse('only s1_routing.selection and .catalog may change')
    if set(over.get('deployment', {})) - DEPLOYMENT: refuse('deployment keys outside init/tars/extra')
    for name in over.get('add_k', {}):
        if name not in ADD_K and not ADD_K_DATA.fullmatch(name): refuse('add_k name not allowed: ' + name)
    if sum(n.startswith('pool_selection_') for n in over.get('add_k', {})) > 1: refuse('one pool selection file at most')
    validate_h1(over)
    fixture = over.get('fixture') is True
    status = over.get('status', 'BLOCKED')
    if status not in ('BLOCKED', 'PREPARATION_ONLY', 'READY'): refuse('status must be BLOCKED, PREPARATION_ONLY or READY')
    if fixture and status != 'BLOCKED': refuse('a fixture derivation can never be READY or PREPARATION_ONLY')
    # Source kit must match its own sealed manifest (absent big files allowed only for fixtures).
    missing, src_inventory = [], {}
    for line in (kit / 'SHA256SUMS.txt').read_text().splitlines():
        want, name = line.split('  ', 1); src_inventory[name] = want
        p = kit / name
        if not p.is_file(): missing.append(name); continue
        if sha(p) != want: refuse('source kit file differs from its manifest: ' + name)
    if sha(kit / 'SHA256SUMS.txt') != SEALED_MANIFEST: refuse('the source is not the sealed kit 07ca49df (derive from the sealed kit only)')
    if missing and not fixture: refuse('source kit files absent: ' + ', '.join(missing))
    launch = json.loads((kit / 'k/launch.json').read_text())
    if launch.get('status') == 'FIXTURE' and not fixture: refuse('the source kit is a fixture derivation')
    old_key = json.loads((kit / 'k/1.json').read_text())['0']
    base_cfg = json.loads((kit / 'k' / (old_key + '.json')).read_text())
    base_cur = json.loads((kit / 'k/0.json').read_text())
    old_run, old_kit, old_root = launch['run_key'], launch['kit_key'], launch['persistent_run_root']
    run, kit_key, root = (over.get(k, d) for k, d in (('run_key', old_run), ('kit_key', old_kit), ('persistent_run_root', old_root)))
    norm = lambda p: '/' + '/'.join(x for x in str(p).split('/') if x not in ('', '.'))
    changing = bool(over.get('code_tree') or over.get('config') or over.get('deployment') or over.get('add_k')
                    or run != old_run or kit_key != old_kit or norm(root) != norm(old_root))
    root = norm(root) if changing else root
    if changing and (run == old_run or kit_key == old_kit or root == norm(old_root)):
        refuse('changed inputs need a new run_key, kit_key and persistent_run_root')
    for key in (run, kit_key):
        if not HEX8.fullmatch(key): refuse('keys must be eight hex digits')
    if not isinstance(root, str) or not root.startswith('/') or '..' in root.split('/'): refuse('persistent_run_root must be absolute')
    if changing and '/home/' in root: refuse('persistent_run_root must not be under /home')
    if changing and Path(root).exists():  # b/r8.py binds a root to the first job that runs any mode on it (mode p included)
        refuse('persistent_run_root exists: an earlier job claimed it; every derived kit needs a root no job has used')

    cfg, cur = copy.deepcopy(base_cfg), copy.deepcopy(base_cur)
    if run != old_run:
        for field in ('output', 'preparation_output'):
            cfg[field] = re.sub('/' + old_run + '$', '/' + run, cfg[field])
            if not cfg[field].endswith('/' + run): refuse(field + ' does not end in the run key')
    oc = over.get('config', {})
    if 'streams' in oc: cfg['streams'] = {**cfg['streams'], **oc['streams']}
    if 's1_routing' in oc: cfg['s1_routing'] = {**cfg['s1_routing'], **oc['s1_routing']}
    if 'init_artifact' in oc:
        ia = oc['init_artifact']
        if set(ia) != {'artifact'} and any(ia.get(k) != base_cfg['init_artifact'][k] for k in ('lm', 'heads')):
            refuse('init_artifact may change only its artifact pin (lm and heads are training settings)')
        cfg['init_artifact'] = {**base_cfg['init_artifact'], 'artifact': ia['artifact']}
    for name in ('h1', 'milestones'):
        if name in oc: cfg[name] = copy.deepcopy(oc[name])
    for name in ('scheduled_sampling', 'recipe'):
        if name in oc:
            cfg[name] = copy.deepcopy(cfg[name])
            for k, v in oc[name].items():
                if name == 'recipe' and k == 'scheduled_sampling':
                    cfg[name][k] = {**cfg[name][k], **v}
                else: cfg[name][k] = copy.deepcopy(v)
    for k, v in over.get('deployment', {}).items(): cur[k] = v

    # Copy only regular files/directories; never follow a sealed link into another tree.
    for p in kit.rglob('*'):
        if p.is_symlink() or not (p.is_file() or p.is_dir()): refuse('unsupported source member')
    out.mkdir(mode=0o700)
    fs = SealedOutput(out, stat.S_IMODE((kit / 'k/1.json').stat().st_mode))
    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')
    shutil.copytree(kit / 'b', out / 'b')
    for name in ('job.sh', 'job8.sh'): shutil.copy2(kit / name, out / name)
    for name in ('k', 'o', 'runs'):
        if not changing and not (kit / name).exists(): continue
        mode = stat.S_IMODE((kit / name).stat().st_mode) if (kit / name).exists() else 0o700
        fs.mkdir(out / name, mode)
    for p in sorted((kit / 'k').iterdir()):
        if p.name == old_key + '.json' and changing: continue
        fs.copy(p, out / 'k' / p.name, stat.S_IMODE(p.stat().st_mode))
    for name, pin in over.get('add_k', {}).items():
        if sha(pin['path']) != pin['sha256']: refuse('add_k pin differs: ' + name)
        fs.copy(pin['path'], out / 'k' / name)
    if 'review.json' in over.get('add_k', {}):
        cfg['admission'] = dict(path=KIT_LOGICAL + 'review.json', sha256=sha(out / 'k/review.json'))

    if 'code_tree' in over:
        install_code(kit, out, over, cfg, cur, launch, fs)

    # Dependency chain: every changed config pin must be staged, and config and deployment must agree.
    staged = staged_files(cur)
    if 'init_artifact' in oc or 'init' in over.get('deployment', {}):
        if 'init' in over.get('deployment', {}) and 'init_artifact' not in oc: refuse('k/0.json init changed without config init_artifact')
        a = cfg['init_artifact']['artifact']
        if cur.get('init') != dict(file=a['path'], sha256=a['sha256']): refuse('config init_artifact and k/0.json init differ')
        if any(k.startswith('ap/f2ad01ad/runs/49becb79/m200/') for k in staged) and base_cfg['init_artifact'] != cfg['init_artifact']:
            refuse('the old init (CP1 m200) is still staged')
    for name in over.get('add_k', {}):
        if not ADD_K_DATA.fullmatch(name): continue
        if (kit / 'k' / name).exists(): refuse('add_k may not overwrite the sealed k/' + name)
        want = dict(path=KIT_LOGICAL + name, sha256=sha(out / 'k' / name))
        if cfg['s1_routing']['selection'] != want: refuse(f'{name} added but the config does not pin it')
        if cfg['s1_routing']['catalog'].get(want['sha256']) != want['path']:
            refuse('pool selection missing from the catalog')
    if 'selection' in oc.get('s1_routing', {}) and not any(n.startswith('pool_selection_') for n in over.get('add_k', {})):
        refuse('selection pin changed without a new k/pool_selection_<tag>.json')
    closure = close(kit, out, cfg, base_cfg, cur, base_cur, over, missing)

    key = digest(cfg)[:8]
    fs.write(out / 'k' / (key + '.json'), cfg, stat.S_IMODE((kit / 'k' / (old_key + '.json')).stat().st_mode))
    fs.write(out / 'k/1.json', {'0': key})
    fs.write(out / 'k/0.json', cur)
    code = json.loads((out / 'k/7.json').read_text())
    seal = dict(schema='s1-run-seal-v1', tree_sha256=code['tree_sha256'], config_sha256=identity(cfg), archive=code['archive'])
    launch = copy.deepcopy(launch)
    launch.update(config=dict(file='k/' + key + '.json', sha256=sha(out / 'k' / (key + '.json'))), run_key=run, kit_key=kit_key,
                  run_directory=(f'/tmp/jjyeung/a_{run}/runs/{run}' if 'code_tree' in over else f'/tmp/jjyeung/okit_8865619b/runs/{run}'), source_seal={**seal, 'sha256': digest(seal)},
                  persistent_run_root=root, inherited_streams=copy.deepcopy(cfg['streams']),
                  source_selection=copy.deepcopy(cfg['s1_routing']['selection']))
    if 'in_job_admission' in launch:
        launch['in_job_admission']['directory'] = cfg['output'] + '/inputs'
    for k in ('review', 'staging', 'archive', 'first_batch'):
        if k in launch and (out / 'k' / (k + '.json')).is_file():
            launch[k] = dict(file=f'k/{k}.json', sha256=sha(out / 'k' / (k + '.json')))
    if changing:
        if status == 'READY':
            ident = identity(cfg)
            for name in ('review.json', 'staging.json', '4.json'):
                if name not in over.get('add_k', {}): refuse('READY needs a new ' + name)
            if json.loads((out / 'k/review.json').read_text()).get('config_sha256') != ident: refuse('review does not bind the new identity')
            if json.loads((out / 'k/staging.json').read_text()).get('config_sha256') != ident: refuse('staging does not bind the new identity')
            if json.loads((out / 'k/4.json').read_text()).get('config_sha256') != ident: refuse('authorization does not bind the new identity')
        if status == 'PREPARATION_ONLY':  # b/g.py lets mode p alone run; 4.json must bind the identity and allow only p
            if '4.json' not in over.get('add_k', {}): refuse('PREPARATION_ONLY needs a new 4.json')
            auth = json.loads((out / 'k/4.json').read_text())
            if auth.get('config_sha256') != identity(cfg) or auth.get('modes') != ['p']:
                refuse('PREPARATION_ONLY needs 4.json bound to the new identity with modes [p]')
        launch.update(status=status, production_authorized=status == 'READY')
    elif 'status' in over:  # an explicit status binds even when nothing changed
        if status != 'BLOCKED': refuse(status + ' needs changed inputs with their own records')
        launch.update(status=status, production_authorized=False)
    if fixture:  # incomplete source: never launchable, whatever changed
        launch.update(status='FIXTURE', production_authorized=False)
    fs.write(out / 'k/launch.json', launch)
    inventory = {str(p.relative_to(out)): sha(p) for part in ('b', 'k') for p in sorted((out / part).rglob('*')) if p.is_file()}
    inventory.update({n: sha(out / n) for n in ('job.sh', 'job8.sh')})
    inventory.update({n: v for n, v in src_inventory.items() if n in missing})  # absent payloads stay listed; a later derivation sees them absent
    fs.text(out / 'SHA256SUMS.txt', ''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())), stat.S_IMODE((kit / 'SHA256SUMS.txt').stat().st_mode))
    if (kit / 'ANON_OK.json').is_file():
        fs.copy(kit / 'ANON_OK.json', out / 'ANON_OK.json', stat.S_IMODE((kit / 'ANON_OK.json').stat().st_mode))
    if changing:  # explicit placeholder: a.py refuses until an independent content scan replaces it
        fs.write(out / 'ANON_OK.json', dict(status='UNREVIEWED', hits=None, manifest_sha256=sha(out / 'SHA256SUMS.txt'), external=[],
                                         scope='integrity-manifest-only; independent-content-scan-not-supplied'))
    if not changing: out.chmod(stat.S_IMODE(kit.stat().st_mode))
    return dict(config_key=key, config_identity=identity(cfg), run_key=run, kit_key=kit_key, persistent_run_root=root,
                manifest_sha256=sha(out / 'SHA256SUMS.txt'), launch_status=launch.get('status'), absent_source_files=missing,
                closure=closure)

if __name__ == '__main__':
    print(json.dumps(derive(sys.argv[1], sys.argv[2], json.loads(Path(sys.argv[3]).read_text())), indent=1))
