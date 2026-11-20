"""Publish bounded observations from two existing stores without changing admission."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from collections import Counter

GATE = '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'
READER = '6945292e167d9f602a5aa94f86e8070c28bca6770df5886c34b0d3ee66ac1eda'
# Reserve three 64 KiB tails and 64 KiB for their metadata and E95 detail.
LIMIT = 5_000_000 - (4 << 16)
MISSING = object()


def reader():
    path = Path(__file__).with_name('ps.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != READER:
        raise ValueError('E96:reader')
    spec = importlib.util.spec_from_file_location('ns_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.GATE = GATE  # An inherited PS_GATE cannot relax the production gate.
    return module


def raw(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def load(path):
    return json.loads(Path(path).read_bytes(), parse_constant=lambda _: (_ for _ in ()).throw(ValueError('E96:json')))


def key(row):
    src = row.get('s1_source') or {}
    if not isinstance(src, dict) or not isinstance(row.get('qid'), str) or not row['qid']:
        raise ValueError('E96:key')
    return (row.get('dataset'), row.get('scene'), row['qid'], src.get('name'))


def pointer(part):
    return str(part).replace('~', '~0').replace('/', '~1')


def changes(a, b, path):
    """Yield leaf JSON pointers; absence and JSON null remain distinct."""
    if isinstance(a, dict) and isinstance(b, dict):
        for name in sorted(a.keys() | b.keys()):
            yield from changes(a.get(name, MISSING), b.get(name, MISSING), path+'/'+pointer(name))
    elif isinstance(a, list) and isinstance(b, list):
        for i in range(max(len(a), len(b))):
            yield from changes(a[i] if i < len(a) else MISSING, b[i] if i < len(b) else MISSING, path+'/'+str(i))
    elif a is MISSING and isinstance(b, (dict, list)) and b:
        items = b.items() if isinstance(b, dict) else enumerate(b)
        for name, value in items:
            yield from changes(MISSING, value, path+'/'+pointer(name))
    elif b is MISSING and isinstance(a, (dict, list)) and a:
        items = a.items() if isinstance(a, dict) else enumerate(a)
        for name, value in items:
            yield from changes(value, MISSING, path+'/'+pointer(name))
    elif a is MISSING or b is MISSING or type(a) is not type(b) or a != b:
        yield path, a, b


def shown(value):
    if value is MISSING:
        return dict(present=False)
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    return dict(present=True, type=type(value).__name__, value=text[:200], characters=len(text), truncated=len(text)>200)


def target(value):
    # A TEXT target need not itself be JSON. Keep that string intact.
    try:
        return json.loads(value, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('E96:json')))
    except (ValueError, TypeError):
        return value


def fields(p, n):
    result = list(changes(json.loads(p[1]), json.loads(n[1]), '/row'))
    result += list(changes(target(p[2]), target(n[2]), '/target'))
    if p[0] != n[0]:
        result.append(('/i', p[0], n[0]))
    if p[1] != n[1] and not any(s.startswith('/row/') or s == '/row' for s, _, _ in result):
        result.append(('/row_text', p[1], n[1]))
    if p[2] != n[2] and not any(s.startswith('/target/') or s == '/target' for s, _, _ in result):
        result.append(('/target_text', p[2], n[2]))
    return result


def opened(path):
    c = sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True)
    c.execute('PRAGMA query_only=ON')
    c.execute('PRAGMA cache_size=-8192')
    return c


def state(database, ps):
    """Read recorded state only. Missing or aggregate-only evidence gives unknown."""
    records = {}
    pins = []
    material = {}
    p = database.parent/'materialization.json'
    if p.is_file():
        try:
            material = load(p)
            pins.append(dict(path='materialization.json', sha256=ps.sha(p)))
            for reason, entry in material.get('contract_deferred_qids', {}).items():
                for qid in entry.get('qids', []):
                    records.setdefault(str(qid), set()).add(reason)
        except (OSError, ValueError, TypeError, AttributeError):
            material = {}
    return material, records, pins


def scene_state(database, ps):
    """Read exclusion predicates from authenticated files in N's build state."""
    q = database.parent.parent
    config = q/'n.json'
    result, pins = {}, []
    if not config.is_file():
        return result, pins
    try:
        cfg = load(config)
        for label, field in (('dev', 'dev_scene_exclusions'), ('benchmark', 'benchmark_scene_exclusions')):
            pin = cfg.get(field)
            if not isinstance(pin, dict):
                continue
            if not isinstance(pin.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', pin['sha256']):
                continue
            path = q/'u'/pin['sha256']
            if not path.is_file() or ps.sha(path) != pin['sha256']:
                continue
            value = load(path)
            names = []
            if label == 'dev':
                if value.get('schema') != 'dev_s1_withhold_v1':
                    continue
                for field in ('natives', 'rooms', 'physical_groups'):
                    names.extend(value.get(field, []))
                for field in ('canonical', 'aliases'):
                    for name, aliases in value.get(field, {}).items():
                        names.extend([name, *aliases])
            else:
                if value.get('schema') != 'benchmark_scene_exclusions_v1':
                    continue
                names.extend(value.get('scenes', [])); names.extend(value.get('physical_groups', []))
                names.extend('/'.join(parts) for parts in value.get('rung1_tokens', []))
                for corpus, scenes in value.get('other_corpora', {}).items():
                    names.extend(corpus+'/'+scene for scene in scenes)
            result[label] = {scene_key(name) for name in names}
            pins.append(dict(path='u/'+pin['sha256'], sha256=pin['sha256'], role=label))
    except (OSError, KeyError, TypeError, AttributeError, ValueError):
        return {}, []
    if pins:
        pins.append(dict(path='n.json', sha256=ps.sha(config)))
    return result, pins


def scene_key(value):
    prefix, separator, scene = value.partition('/')
    if not separator or not scene:
        raise ValueError('E96:scene')
    aliases = dict(scannet='d1', scannetpp='d2', scannetppv2='d2', arkitscenes='d3', **{'scannet++':'d2'})
    return aliases.get(prefix.casefold(), prefix.casefold())+'/'+scene


def scene_matches(row, rules):
    names = []
    scene, dataset = row.get('scene'), row.get('dataset')
    if isinstance(scene, str):
        if '/' in scene:
            names.append(scene)
        elif dataset:
            names.append(dataset+'/'+scene)
    for part in (row, row.get('routing'), row.get('provenance')):
        if isinstance(part, dict):
            names.extend(part[k] for k in ('canonical','physical_group','room','alias')
                         if isinstance(part.get(k),str) and '/' in part[k])
    keys = {scene_key(name) for name in names}
    keys.update(m[1] for key in tuple(keys) if (m := re.fullmatch(r'(d1/scene\d+)_\d+', key)))
    return [label for label, names in rules.items() if keys & names]


def reason_for(row, c, material, records, tables, scenes):
    qid = row['qid']
    # A surviving legacy candidate excluded from membership has this exact
    # recorded cause in the native builder. Never infer a rule from its absence.
    if key(row)[3] is None and {'candidates', 'membership', 'pool_qids'} <= tables:
        found = c.execute("SELECT 1 FROM candidates c WHERE c.qid=? AND c.origin='legacy' "
                          "AND NOT EXISTS (SELECT 1 FROM membership m WHERE m.k=c.k) "
                          "AND EXISTS (SELECT 1 FROM pool_qids p WHERE p.qid=c.qid)", (qid,)).fetchone()
        if found:
            return 'pool_qid_wins', 'tables'
    reasons = records.get(qid, set())
    if len(reasons) == 1:
        return next(iter(reasons)), 'materialization.json/contract_deferred_qids'
    source = key(row)[3]
    if source is not None:
        deferred = material.get('source_deferrals', {}).get(source, {})
        if isinstance(deferred.get('reason'), str):
            return deferred['reason'], 'materialization.json/source_deferrals'
    else:
        kind = (row.get('routing') or {}).get('question_type')
        verdict = material.get('legacy_compatibility', {}).get(kind, {})
        if verdict.get('disposition') in ('DROPPED', 'DEFERRED') and isinstance(verdict.get('reason'), str):
            return verdict['reason'], 'materialization.json/legacy_compatibility'
    hits = scene_matches(row, scenes)
    if hits:
        # This is a sufficient exclusion read from the build's pinned rules.
        # Refused builds do not persist the first rejection of each row.
        return 'scene_exclusion/'+ '+'.join(hits), 'n.json/pinned_predicate;first_rejection_unknown'
    return 'unknown', None


def listings(rd0, psha, nsha, ps):
    summary, detail = Path(rd0)/'rdiff_summary.json', Path(rd0)/'rdiff.json.gz'
    if not summary.is_file() or not detail.is_file():
        return None, None
    v = load(summary)
    if v['inputs']['P']['sha256'] != psha or v['inputs']['N']['sha256'] != nsha or v['rdiff_sha256'] != ps.sha(detail):
        raise ValueError('E96:rd')
    with gzip.open(detail, 'rt') as f:
        rows = json.load(f)['P_absent']
    result = {}
    for row in rows:
        k = tuple(row['key'])
        if k in result:
            raise ValueError('E96:duplicate')
        result[k] = row['removal_list_sha256s']
    return result, ps.sha(detail)


def publish(pdb, ndb, request, rd0, output, scratch):
    pdb, ndb, request, output, scratch = map(Path, (pdb, ndb, request, output, scratch))
    ps = reader()
    # Reuse the reference reader's gate, request semantics, seeds and ordering.
    # Its temporary sample stays in the job's private scratch directory.
    sample_path = scratch/'ns0.json'
    ps.main(pdb, request, str(rd0), sample_path)
    reference = load(sample_path)
    psha, nsha = reference['database_sha256'], ps.sha(ndb)
    listed, rdsha = listings(rd0, psha, nsha, ps)
    selected = {key(json.loads(s['row'])) for s in reference['rows']}
    nmap, n_samples, sample_diffs = {}, {}, {}
    counts, causes = Counter(), Counter()
    absent, unknown_lists = [], 0
    matched, identical, pcount, nuf = 0, 0, 0, 0
    material, records, state_pins = state(ndb, ps)
    scenes, scene_pins = scene_state(ndb, ps)
    state_pins.extend(scene_pins)
    with opened(ndb) as n, opened(pdb) as p:
        tables = {r[0] for r in n.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for nr in n.execute('SELECT i,row,target FROM rows ORDER BY i'):
            row = json.loads(nr[1]); k = key(row)
            if k in nmap:
                raise ValueError('E96:duplicate')
            nmap[k] = nr[0]
            nuf += k[3] == 'U_Faithful'
            if k in selected:
                n_samples[k] = nr
        pkeys = set()
        for pr in p.execute('SELECT i,row,target FROM rows ORDER BY i'):
            row = json.loads(pr[1]); k = key(row)
            if k in pkeys:
                raise ValueError('E96:duplicate')
            pkeys.add(k); pcount += 1
            if k in nmap:
                nr = n.execute('SELECT i,row,target FROM rows WHERE i=?', (nmap[k],)).fetchone()
                diff = fields(pr, nr)
                counts.update({path for path, _, _ in diff})
                matched += 1; identical += pr == nr
                if k in selected:
                    sample_diffs[k] = [dict(path=path, P=shown(a), N=shown(b)) for path, a, b in diff]
            else:
                if listed is not None and k not in listed:
                    raise ValueError('E96:rd')
                removals = None if listed is None else listed[k]
                if removals:
                    continue
                unknown_lists += removals is None
                rule, evidence = reason_for(row, n, material, records, tables, scenes)
                causes[(k[3], rule)] += 1
                absent.append(dict(key=k, i=pr[0], source=k[3], rule=rule, evidence=evidence,
                                   removal_list_sha256s=removals, listing='unknown' if removals is None else 'unlisted'))
        if listed is not None and set(listed) != pkeys-set(nmap):
            raise ValueError('E96:rd')
    samples, missing, diffs = [], [], []
    for s in reference['rows']:
        k = key(json.loads(s['row']))
        identity = dict(**{'class':s['class']}, position=s['position'], P_i=s['i'], key=k)
        if k not in n_samples:
            missing.append(identity)
            diffs.append(dict(identity, status='ABSENT'))
        else:
            nr = n_samples[k]
            samples.append(dict(identity, i=nr[0], row=nr[1], target=nr[2]))
            diffs.append(dict(identity, N_i=nr[0], status='PRESENT', changes=sample_diffs[k]))
    common = dict(P_database_sha256=psha, database_sha256=nsha, request_sha256=reference['request_sha256'],
                  P_absent_source=reference['P_absent_source'])
    ns = dict(common, count=len(nmap), U_Faithful_count=nuf, P_absent_count=reference['P_absent_count'],
              requested=len(reference['rows']), rows=samples, absent=missing)
    nd = dict(common, schema='nd-v1', path_encoding='RFC6901; array indices; missing differs from null',
              value_limit=200, P_rows=pcount, N_rows=len(nmap), matched_rows=matched,
              identical_sql_rows=identical, N_without_P=len(set(nmap)-pkeys), paths=dict(sorted(counts.items())),
              samples=diffs, state=state_pins, rd_sha256=rdsha,
              absent_unlisted=None if listed is None else len(absent), absent_listing_unknown=unknown_lists,
              absent_counts=[dict(source=s,rule=r,rows=v) for (s,r),v in sorted(causes.items(),key=lambda x:str(x[0]))],
              absent_file='na.json.gz')
    payloads = {'n_sample.json':raw(ns), 'nd.json':raw(nd),
                'na.json.gz':gzip.compress(raw(dict(schema='na-v1', rows=absent)), mtime=0)}
    total = sum(map(len, payloads.values()))
    if total >= LIMIT:
        raise ValueError('E96:size')
    output.mkdir(parents=True, exist_ok=True)
    for name in payloads:
        if (output/name).exists() or (output/name).is_symlink():
            raise ValueError('E96:exists')
    for name, data in payloads.items():
        with (output/name).open('xb') as f:
            f.write(data)
    return dict(status='PASS', files=list(payloads), bytes=total, sampled=len(samples), absent=len(missing), matched=matched)


if __name__ == '__main__':
    try:
        print(json.dumps(publish(*sys.argv[1:7]), sort_keys=True))
    except (Exception, SystemExit) as error:
        print('E96:'+type(error).__name__)
        raise SystemExit(1)
