"""Derive a data-only kit from sealed kit 07ca49df's own records: same trainer tree, b/ gate, job scripts and 7.json;
new row-store pins (VQA, routing), pool selection, dev scene exclusions, init artifact and run identity.
Serialization follows launch_s1/build.py (sorted compact JSON plus newline; config file name = sha256(config)[:8];
launch source_seal as b/g.py checks it).

Usage: derive_kit.py KIT_DIR OUT_DIR OVERRIDES.json
OVERRIDES keys (anything else is refused):
  run_key, kit_key, persistent_run_root   all three required, and new, whenever any input changes
  config: {streams: {vqa?, routing?}, init_artifact?, s1_routing: {selection?, catalog?}?, dev_scene_exclusions?,
           scene_coverage?}
  deployment: {init?, tars?, extra?}       replacements of k/0.json entries
  add_k: {name: {path, sha256}}            new small records: review.json, staging.json, 4.json, and new-named
                                           pool_selection_<tag>.json / dev_scene_exclusions_<tag>.json
  status: BLOCKED (default) | READY        READY needs review.json, staging.json and 4.json in add_k, bound to the new identity
  content: {sha256: local path}           bytes of new JSON documents (receipts, artifact.json, full_weights.json, ...) so their
                                           pins can be walked
  accept_unstaged: {sha256: reason}        pins a new document names that the kit does not place (provenance only); each is
                                           reported in the result for the reviewer
  fixture: true                            allow source-kit files listed in SHA256SUMS to be absent (tests only; output is
                                           marked FIXTURE and can never be READY)
An empty OVERRIDES reproduces the kit's k/ records byte for byte; with {"fixture": true} (big tars absent) every record except
launch.json (status FIXTURE, unauthorized) is byte-identical."""
import copy, hashlib, json, re, shutil, sys
from pathlib import Path

def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
def digest(v): return hashlib.sha256(enc(v).encode()).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, v): Path(p).write_text(enc(v) + '\n')
def identity(cfg):  # b/i.py identity, same logic
    value = {k: v for k, v in cfg.items() if k not in ('preparation', 'admission', 'authorization', 'milestone_gate')}
    if 'readout' in value:
        value['readout'] = {k: v for k, v in value['readout'].items() if k != 'contiguous_clips'}
    if value.get('frame_layout') == 'spread': value.pop('frame_layout')
    return digest(value)

HEX8 = re.compile('[0-9a-f]{8}')
TOP = {'run_key', 'kit_key', 'persistent_run_root', 'config', 'deployment', 'add_k', 'status', 'fixture', 'content', 'accept_unstaged'}
CONFIG = {'streams', 'init_artifact', 's1_routing', 'dev_scene_exclusions', 'scene_coverage'}
STREAMS = {'vqa', 'routing'}
S1_ROUTING = {'selection', 'catalog'}
DEPLOYMENT = {'init', 'tars', 'extra'}
ADD_K = {'review.json', 'staging.json', '4.json'}
ADD_K_DATA = re.compile('(pool_selection|dev_scene_exclusions|scene_reference)_[a-z0-9]{1,16}\\.json')  # new names: the sealed catalog keeps the old files
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

def check_entries(cur):
    """Shape of every tars and extra entry: parts in the okit input directory, safe logical paths, sha256 digests."""
    parts_ok = lambda v: isinstance(v, list) and v and all(isinstance(x, str) and PART.fullmatch(x) for x in v)
    for t in cur.get('tars', []):
        if not isinstance(t, dict) or set(t) - {'files', 'parts', 'sha256'} or not {'files', 'parts'} <= set(t): refuse('malformed k/0.json tars entry')
        if not parts_ok(t['parts']): refuse('tars parts must be files under okit/in or okh7/<dir>: ' + str(t['parts'])[:120])
        if not isinstance(t['files'], dict) or not t['files'] or not all(
                safe_rel(k) and k.startswith('ap/') and isinstance(v, str) and HEX64.fullmatch(v) for k, v in t['files'].items()):
            refuse('tars files must map safe ap/ paths to sha256 digests')
        if 'sha256' in t and not (isinstance(t['sha256'], str) and HEX64.fullmatch(t['sha256'])): refuse('tars sha256 malformed')
    for e in cur.get('extra', []):
        if not isinstance(e, dict) or set(e) != {'dest', 'parts', 'sha256'}: refuse('malformed k/0.json extra entry')
        if not safe_rel(rel(e['dest'])) or not parts_ok(e['parts']) or not HEX64.fullmatch(str(e['sha256'])): refuse('malformed extra entry ' + e['dest'])

def resolvable(cur, kman):
    """Logical relative path -> sha256 of every file the kit places at a pinnable path: tars, extra, a1rows and single-file
    entries of k/0.json, the staged_inputs files and packages (kit root u/...), and the kit's own k/ records."""
    out = dict(staged_files(cur))
    for v in cur.values():
        if isinstance(v, dict) and isinstance(v.get('sha256'), str):
            r = rel_or_none(v.get('file', v.get('dest')))
            if r: out.setdefault(r, v['sha256'])
    si = cur.get('staged_inputs', {})
    for f in si.get('files', []): out.setdefault(KIT_REL + f['destination'], f['sha256'])
    for pkg in si.get('packages', []):
        for item in pkg.get('inventory', []): out.setdefault(KIT_REL + pkg['destination'] + '/' + item['name'], item['sha256'])
    for name, digest_ in kman.items():
        if name.startswith('k/'): out[KIT_REL + name] = digest_
    return out

def pins_in(doc):
    if isinstance(doc, dict):
        target = doc.get('path', doc.get('file'))
        if isinstance(target, str) and isinstance(doc.get('sha256'), str) and HEX64.fullmatch(doc['sha256']): yield target, doc['sha256']
        for v in doc.values(): yield from pins_in(v)
    elif isinstance(doc, list):
        for v in doc: yield from pins_in(v)

def close(kit, out, cfg, base_cfg, cur, base_cur, over, missing):
    """Fix 1: walk the dependency graph of every changed input (stream receipts, init artifact and its full_weights manifest,
    pool selection through the catalog, dev exclusions, scene coverage, new catalog entries). Every pin a new document
    names must be placed by the derived kit at that sha256; a pin already placed by the sealed kit at the same sha256 is
    the sealed kit's closure. A new .json needs its bytes (override content, or add_k) so its own pins can be walked.
    Added staging entries must be reached from a changed input; removed ones must belong to a replaced input."""
    check_entries(cur)
    src_man = dict(reversed(l.split('  ', 1)) for l in (kit / 'SHA256SUMS.txt').read_text().splitlines())
    out_man = {str(p.relative_to(out)): sha(p) for p in (out / 'k').iterdir() if p.is_file()}
    out_man.update({n: src_man[n] for n in missing if n.startswith('k/')})
    R, base_R = resolvable(cur, out_man), resolvable(base_cur, src_man)
    accept = over.get('accept_unstaged', {})
    if not isinstance(accept, dict) or not all(HEX64.fullmatch(k) and isinstance(v, str) and v.strip() for k, v in accept.items()):
        refuse('accept_unstaged maps sha256 -> reason')
    docs = {}
    for digest_, path in over.get('content', {}).items():
        if sha(path) != digest_: refuse('content file differs from its sha256: ' + str(path))
        docs[digest_] = json.loads(Path(path).read_text())
    for p in (out / 'k').iterdir():
        if p.suffix == '.json' and p.is_file(): docs.setdefault(sha(p), json.loads(p.read_text()))
    reached, accepted, walked = set(), {}, set()
    def sealed_pins(pin):  # provenance pins of the sealed document a new one replaces (pool selection, dev list, scene reference)
        r = rel_or_none((pin or {}).get('path'))
        if not r or not r.startswith(KIT_REL + 'k/') or src_man.get(r[len(KIT_REL):]) != pin['sha256']: return frozenset()
        return frozenset(pins_in(json.loads((kit / r[len(KIT_REL):]).read_text())))
    catalog = cfg['s1_routing']['catalog']
    inherited_hits = []
    def visit(path, digest_, where, leaf=False, via_catalog=False, inherit=frozenset()):
        r = rel_or_none(path)
        if (r is None or R.get(r) != digest_) and via_catalog and catalog.get(digest_) and catalog[digest_] != path:
            return visit(catalog[digest_], digest_, where + ' (catalog)', leaf)
        if (r is None or R.get(r) != digest_) and (path, digest_) in inherit:  # same provenance pin as the sealed document
            inherited_hits.append(path); return
        if r is None or R.get(r) != digest_:
            if digest_ in accept: accepted[digest_] = dict(path=path, where=where, reason=accept[digest_]); return
            refuse(f'{where}: pin {path} sha {digest_[:12]} is not placed by the derived kit')
        reached.add(r)
        if base_R.get(r) == digest_ or leaf or (r, digest_) in walked: return
        walked.add((r, digest_))
        doc = docs.get(digest_)
        if doc is None:
            if r.endswith('.json'): refuse(f'{where}: new {r} needs its bytes in override content to close its dependencies')
            return
        sub = where + ' > ' + r
        for p, s in pins_in(doc): visit(p, s, sub, via_catalog=via_catalog, inherit=inherit)
        if isinstance(doc.get('index'), dict) and isinstance(doc.get('files'), list) and 'name' in doc['index']:  # full_weights.json
            d = path.rsplit('/', 1)[0]
            for item in [doc['index']] + doc['files']:
                if not safe_rel(item.get('name')) or '/' in item['name']: refuse(sub + ': export manifest names a nested path')
                visit(d + '/' + item['name'], item['sha256'], sub, leaf=True)
    for name in cfg['streams']:
        if cfg['streams'][name] != base_cfg['streams'][name]: visit(cfg['streams'][name]['path'], cfg['streams'][name]['sha256'], 'stream ' + name)
    if cfg['init_artifact'] != base_cfg['init_artifact']:
        a = cfg['init_artifact']['artifact']; visit(a['path'], a['sha256'], 'init_artifact')
    if cfg['s1_routing']['selection'] != base_cfg['s1_routing']['selection']:
        sel = cfg['s1_routing']['selection']
        visit(sel['path'], sel['sha256'], 'pool selection', via_catalog=True, inherit=sealed_pins(base_cfg['s1_routing']['selection']))
    for s, p in catalog.items():  # every entry: a sealed one must still resolve, a new one must be placed
        visit(p, s, 'catalog')
    for k in ('dev_scene_exclusions', 'scene_coverage'):
        if cfg[k] != base_cfg[k]:
            for p, s in ([(cfg[k]['path'], cfg[k]['sha256'])] if k == 'dev_scene_exclusions' else list(pins_in(cfg[k]))):
                visit(p, s, k, inherit=sealed_pins(base_cfg[k] if k == 'dev_scene_exclusions' else base_cfg[k].get('reference')))
    # Staging edits are restricted to the inputs that changed.
    new_s, old_s = staged_files(cur), staged_files(base_cur)
    added = sorted(r for r, v in new_s.items() if old_s.get(r) != v)
    if set(added) - reached: refuse('staging entries not reached from any changed input: ' + ', '.join(sorted(set(added) - reached))[:300])
    owners = [rel(base_cfg['streams'][n]['path']).rsplit('/', 1)[0] + '/' for n in cfg['streams'] if cfg['streams'][n] != base_cfg['streams'][n]]
    if cfg['init_artifact'] != base_cfg['init_artifact']: owners.append(rel(base_cfg['init_artifact']['artifact']['path']).rsplit('/', 1)[0] + '/')
    removed = sorted(r for r, v in old_s.items() if new_s.get(r) != v)
    stray = [r for r in removed if not any(r.startswith(o) for o in owners)]
    if stray: refuse('staging entries removed that belong to no replaced input: ' + ', '.join(stray)[:300])
    base_parts = {}
    for e in base_cur.get('tars', []) + base_cur.get('extra', []):
        for x in e['parts']: base_parts[x] = e
    for e in cur.get('tars', []) + cur.get('extra', []):
        for x in e['parts']:
            if x in base_parts and base_parts[x] != e: refuse('a changed staging entry reuses the sealed part name ' + x)
    return dict(reached_new=len(walked), added=len(added), removed=len(removed), accepted_unstaged=accepted,
                inherited_provenance_pins=len(inherited_hits))

def derive(kit, out, over):
    kit, out = Path(kit), Path(out)
    if set(over) - TOP: refuse('unknown override keys ' + str(sorted(set(over) - TOP)))
    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the data-only set ' + str(sorted(set(over['config']) - CONFIG)))
    if set(over.get('config', {}).get('streams', {})) - STREAMS: refuse('only the vqa and routing streams may change')
    if set(over.get('config', {}).get('s1_routing', {})) - S1_ROUTING: refuse('only s1_routing.selection and .catalog may change')
    if set(over.get('deployment', {})) - DEPLOYMENT: refuse('deployment keys outside init/tars/extra')
    for name in over.get('add_k', {}):
        if name not in ADD_K and not ADD_K_DATA.fullmatch(name): refuse('add_k name not allowed: ' + name)
    if sum(n.startswith('pool_selection_') for n in over.get('add_k', {})) > 1 or sum(
            n.startswith('dev_scene_exclusions_') for n in over.get('add_k', {})) > 1: refuse('one pool selection and one dev exclusion file at most')
    fixture = over.get('fixture') is True
    status = over.get('status', 'BLOCKED')
    if status not in ('BLOCKED', 'READY'): refuse('status must be BLOCKED or READY')
    if fixture and status == 'READY': refuse('a fixture derivation can never be READY')
    # Source kit must match its own sealed manifest (absent big files allowed only for fixtures).
    missing = []
    for line in (kit / 'SHA256SUMS.txt').read_text().splitlines():
        want, name = line.split('  ', 1)
        p = kit / name
        if not p.is_file(): missing.append(name); continue
        if sha(p) != want: refuse('source kit file differs from its manifest: ' + name)
    if missing and not fixture: refuse('source kit files absent: ' + ', '.join(missing))
    launch = json.loads((kit / 'k/launch.json').read_text())
    old_key = json.loads((kit / 'k/1.json').read_text())['0']
    base_cfg = json.loads((kit / 'k' / (old_key + '.json')).read_text())
    base_cur = json.loads((kit / 'k/0.json').read_text())
    old_run, old_kit, old_root = launch['run_key'], launch['kit_key'], launch['persistent_run_root']
    run, kit_key, root = (over.get(k, d) for k, d in (('run_key', old_run), ('kit_key', old_kit), ('persistent_run_root', old_root)))
    norm = lambda p: '/' + '/'.join(x for x in str(p).split('/') if x not in ('', '.'))
    changing = bool(over.get('config') or over.get('deployment') or over.get('add_k')
                    or run != old_run or kit_key != old_kit or norm(root) != norm(old_root))
    root = norm(root) if changing else root
    if changing and (run == old_run or kit_key == old_kit or root == norm(old_root)):
        refuse('changed inputs need a new run_key, kit_key and persistent_run_root')
    for key in (run, kit_key):
        if not HEX8.fullmatch(key): refuse('keys must be eight hex digits')
    if not isinstance(root, str) or not root.startswith('/') or '..' in root.split('/'): refuse('persistent_run_root must be absolute')
    if changing and '/home/' in root: refuse('persistent_run_root must not be under /home')

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
    for k in ('dev_scene_exclusions', 'scene_coverage'):
        if k in oc: cfg[k] = oc[k]
    for k, v in over.get('deployment', {}).items(): cur[k] = v

    out.mkdir()
    shutil.copytree(kit / 'b', out / 'b')
    for name in ('job.sh', 'job8.sh'): shutil.copy2(kit / name, out / name)
    (out / 'k').mkdir(); (out / 'o').mkdir(); (out / 'runs').mkdir()
    for p in sorted((kit / 'k').iterdir()):
        if p.name in ('launch.json', '1.json', '0.json', old_key + '.json'): continue
        shutil.copy2(p, out / 'k' / p.name)
    for name, pin in over.get('add_k', {}).items():
        if sha(pin['path']) != pin['sha256']: refuse('add_k pin differs: ' + name)
        shutil.copyfile(pin['path'], out / 'k' / name)
    if 'review.json' in over.get('add_k', {}):
        cfg['admission'] = dict(path=KIT_LOGICAL + 'review.json', sha256=sha(out / 'k/review.json'))

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
        got = (cfg['s1_routing']['selection'] if name.startswith('pool_selection_') else cfg['dev_scene_exclusions']
               if name.startswith('dev_scene_exclusions_') else cfg['scene_coverage'].get('reference'))
        if got != want: refuse(f'{name} added but the config does not pin it')
        if name.startswith('pool_selection_') and cfg['s1_routing']['catalog'].get(want['sha256']) != want['path']:
            refuse('pool selection missing from the catalog')
    if 'selection' in oc.get('s1_routing', {}) and not any(n.startswith('pool_selection_') for n in over.get('add_k', {})):
        refuse('selection pin changed without a new k/pool_selection_<tag>.json')
    if 'dev_scene_exclusions' in oc and not any(n.startswith('dev_scene_exclusions_') for n in over.get('add_k', {})):
        refuse('dev_scene_exclusions changed without a new k/dev_scene_exclusions_<tag>.json')
    if (cfg['scene_coverage'].get('reference') != base_cfg['scene_coverage'].get('reference')
            and not any(n.startswith('scene_reference_') for n in over.get('add_k', {}))):
        refuse('scene_coverage.reference changed without a new k/scene_reference_<tag>.json')
    closure = close(kit, out, cfg, base_cfg, cur, base_cur, over, missing)
    if cfg['dev_scene_exclusions'] != base_cfg['dev_scene_exclusions']:  # s1_exclusions.totals/coverage_report bind the list
        dev = cfg['dev_scene_exclusions']['sha256']
        load_k = lambda pin: json.loads((out / 'k' / rel(pin['path'])[len(KIT_REL + 'k/'):]).read_text()) if rel(pin['path']).startswith(KIT_REL + 'k/') else None
        ref, sel = load_k(cfg['scene_coverage']['reference']), load_k(cfg['s1_routing']['selection'])
        if not ref or ref.get('withhold_file', {}).get('sha256') != dev: refuse('scene_coverage.reference does not name the new dev list')
        bound = [sel.get('scene_exclusions', {}).get('dev'), sel['source_scene_exclusions']['files'].get('dev')] + [
            v['files'].get('dev') for v in sel['source_scene_exclusions']['expected'].values()] if sel else [None]
        if any((b or {}).get('sha256') != dev for b in bound): refuse('the pool selection is bound to another dev list')

    key = digest(cfg)[:8]
    write(out / 'k' / (key + '.json'), cfg)
    write(out / 'k/1.json', {'0': key})
    write(out / 'k/0.json', cur)
    code = json.loads((kit / 'k/7.json').read_text())
    seal = dict(schema='s1-run-seal-v1', tree_sha256=code['tree_sha256'], config_sha256=identity(cfg), archive=code['archive'])
    launch = copy.deepcopy(launch)
    launch.update(config=dict(file='k/' + key + '.json', sha256=sha(out / 'k' / (key + '.json'))), run_key=run, kit_key=kit_key,
                  run_directory=f'/tmp/jjyeung/okit_8865619b/runs/{run}', source_seal={**seal, 'sha256': digest(seal)},
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
        launch.update(status=status, production_authorized=status == 'READY')
    if fixture:  # incomplete source: never launchable, whatever changed
        launch.update(status='FIXTURE', production_authorized=False)
    write(out / 'k/launch.json', launch)
    inventory = {str(p.relative_to(out)): sha(p) for part in ('b', 'k') for p in sorted((out / part).rglob('*')) if p.is_file()}
    inventory.update({n: sha(out / n) for n in ('job.sh', 'job8.sh')})
    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())))
    if changing:  # explicit placeholder: a.py refuses until an independent content scan replaces it
        write(out / 'ANON_OK.json', dict(status='UNREVIEWED', hits=None, manifest_sha256=sha(out / 'SHA256SUMS.txt'), external=[],
                                         scope='integrity-manifest-only; independent-content-scan-not-supplied'))
    return dict(config_key=key, config_identity=identity(cfg), run_key=run, kit_key=kit_key, persistent_run_root=root,
                manifest_sha256=sha(out / 'SHA256SUMS.txt'), launch_status=launch.get('status'), absent_source_files=missing,
                closure=closure)

if __name__ == '__main__':
    print(json.dumps(derive(sys.argv[1], sys.argv[2], json.loads(Path(sys.argv[3]).read_text())), indent=1))
