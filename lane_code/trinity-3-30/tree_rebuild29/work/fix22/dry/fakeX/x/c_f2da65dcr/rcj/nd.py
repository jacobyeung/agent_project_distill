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
import traceback
from collections import Counter

GATE = '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'
READER = '6945292e167d9f602a5aa94f86e8070c28bca6770df5886c34b0d3ee66ac1eda'
LIMIT = 5_000_000
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


FIELDS = '8be6cc6338406fa1cff328b1821955537d5176156dc1e9c33e5505a08ef2e238'

DEV = 'a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5'
TREE = '6fa18a6e1d7d8306d7317688447da24b0aef7e202b45171ad5765440d7d61226'
QUOTAS = dict(camera_displacement=18.25, camera_movement_direction=15.88,
              camera_rotation=12.53, absolute_distance=16.34, units=1.00)


def tokens(text):
    """Map every JSON pointer to its exact lexical value, without reserialization."""
    decoder = json.JSONDecoder(parse_constant=lambda _: (_ for _ in ()).throw(ValueError('E96:json')))
    result = {}
    def ws(i):
        while i < len(text) and text[i] in ' \t\r\n': i += 1
        return i
    def value(i, path):
        i = ws(i); start = i
        if text[i] == '{':
            i = ws(i+1); names = set()
            if text[i] != '}':
                while True:
                    name, i = decoder.raw_decode(text, i)
                    if not isinstance(name, str) or name in names: raise ValueError('E96:duplicate')
                    names.add(name); i = ws(i)
                    if text[i] != ':': raise ValueError('E96:json')
                    i = ws(value(i+1, path+'/'+pointer(name)))
                    if text[i] == '}': break
                    if text[i] != ',': raise ValueError('E96:json')
                    i = ws(i+1)
            i += 1
        elif text[i] == '[':
            i = ws(i+1); index = 0
            if text[i] != ']':
                while True:
                    i = ws(value(i, path+'/'+str(index))); index += 1
                    if text[i] == ']': break
                    if text[i] != ',': raise ValueError('E96:json')
                    i = ws(i+1)
            i += 1
        else:
            _, i = decoder.raw_decode(text, i)
        result[path] = text[start:i]
        return i
    end = ws(value(0, '/row'))
    if end != len(text): raise ValueError('E96:json')
    return result


def in_path(path, parent):
    return path == parent or path.startswith(parent+'/')


def category(path, contract):
    for name, value in contract['allowed_metadata_classes'].items():
        if any(in_path(path, p) for p in value['paths']): return name
    return None


def exact_fields(pr, nr, contract):
    p, n = tokens(pr[1]), tokens(nr[1])
    p.update({'/i': pr[0], '/target': pr[2]})
    n.update({'/i': nr[0], '/target': nr[2]})
    return [(path, p.get(path, MISSING), n.get(path, MISSING))
            for path in contract['content_field_paths']
            if type(p.get(path, MISSING)) is not type(n.get(path, MISSING))
            or p.get(path, MISSING) != n.get(path, MISSING)]


def native_rules(database):
    """Authenticate C and use its exact removal and scene predicates outside the sandbox."""
    q = Path(database).parent.parent; tree = q.parent/'s'
    sys.path.insert(0, str(tree))
    from student_pilot.source_seal import inventory
    from student_pilot.p3_provenance import digest, pinned
    from student_pilot.r1_persisted import scope
    from student_pilot.row_removals import Removals
    from student_pilot.s1_exclusions import Exclusions
    from student_pilot.r1_launch22 import validate_removals
    if digest(inventory(tree)) != TREE: raise ValueError('E96:tree')
    cfg = load(q/'n.json')
    if cfg['dev_scene_exclusions']['sha256'] != DEV: raise ValueError('E96:scene')
    paths = {p.name: str(p) for p in (q/'u').iterdir() if p.is_file()}
    with scope(paths):
        validate_removals(cfg)
        removals = Removals(cfg['remove_files'])
        scenes = Exclusions(cfg['dev_scene_exclusions'])
        pinned(cfg['dev_scene_exclusions'])
    return removals, scenes, dict(config_sha256=reader().sha(q/'n.json'), tree_sha256=TREE,
        dev_sha256=DEV, removal_files=[{k:v for k,v in p.items() if k!='path'} for p in removals.files])


def attribution(row, removals, scenes):
    listed = [removals.files[i]['sha256'] for i in removals.match(row)]
    identifiers = set(scenes.identifiers(row))
    identifiers.update(m[1] for key in tuple(identifiers) if (m := re.fullmatch(r'(d1/scene\d+)_\d+', key)))
    matches = sorted(identifiers & scenes.names['dev'])
    label = 'list' if listed else 'scene' if matches else 'unattributed'
    return dict(attribution=label, removal_list_sha256s=listed,
                scene_sha256=DEV if matches else None, scene_ids=matches,
                normalized_scene_ids=sorted(identifiers))


def row_type(row):
    from student_pilot.r1_population import family
    return family(row, 'routing')


def type_table(counts, database_sha256=None):
    total = sum(counts.values()); table = []
    for kind, quota in QUOTAS.items():
        count = counts.get(kind, 0)
        rate = 64*count/total if total else 0
        off = 100*(rate-quota)/quota
        table.append(dict(type=kind, rows=count, expected_rows_per_step=rate,
                          P_quota=quota, percent_off=off, absolute_percent_off=abs(off),
                          status='PASS' if abs(off) <= 10+1e-12 else 'FAIL'))
    extra = {k:v for k,v in sorted(counts.items()) if k not in QUOTAS and v}
    units = 64*counts.get('units', 0)/total if total else 0
    return dict(schema='rt-v1', database_sha256=database_sha256, total_rows=total, rows_by_type=dict(counts),
        rows_per_step=64, types=table, units_type='units', units_rows_per_step=units,
        unknown_types=extra, status='PASS' if total and not extra and units>=0.90
        and all(t['status']=='PASS' for t in table) else 'FAIL')


def publish_types(database, output):
    database, output = Path(database), Path(output)
    native_rules(database)
    counts = Counter()
    with opened(database) as c:
        for (text,) in c.execute('SELECT row FROM rows ORDER BY i'):
            counts[row_type(json.loads(text))] += 1
    result = type_table(counts, reader().sha(database))
    data = raw(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    used = sum((output.parent/n).stat().st_size for n in ('nd.json','na.json.gz','n_sample.json') if (output.parent/n).is_file())
    if used+len(data)+65536 >= LIMIT: raise ValueError('E96:size')
    with output.open('xb') as f: f.write(data)
    return dict(status=result['status'], bytes=len(data))


def decision(nrows, matched, extras, bad, counts, unclassified, classes, class_rows, contract, chain, nsha):
    """Evaluate ANSWER 1226Z (a)-(d); preparation is outside mode r."""
    routing = chain.get('streams', {}).get('routing', {})
    pins = routing.get('databases', [])
    complete = (routing.get('complete') is True and routing.get('database_rows') == nrows
        and routing.get('rows_checked') == nrows and nrows > 0
        and routing.get('database_key_set_sha256') == routing.get('checked_key_set_sha256')
        and bool(routing.get('database_key_set_sha256'))
        and len(pins) == 1 and pins[0].get('sha256') == nsha)
    cpass = (complete and chain.get('status') == 'PASS' and routing.get('status') == 'PASS'
             and routing.get('refused_rows') == 0)
    return dict(
        a=dict(status='PASS' if nrows and matched == nrows and not extras and not bad else 'FAIL',
            rows=nrows, compared_rows=matched, differing_rows=bad, extra_rows=extras,
            field_counts=dict(counts), fields=contract['content_field_paths'], derivation=contract['derivation']),
        b=dict(status='PASS' if matched == nrows and not extras and not unclassified else 'FAIL',
            rows=matched, classes={name:dict(rows=class_rows[name],path_differences=classes[name])
                for name in contract['allowed_metadata_classes']}, unclassified_paths=unclassified),
        c=dict(status='PASS' if cpass else 'FAIL', rows=routing.get('rows_checked'),
            refused_rows=routing.get('refused_rows'), complete=complete,
            database_sha256=nsha, config_sha256=chain.get('config_sha256'),
            extent_receipt=chain.get('extent_receipt'), key_set_sha256=routing.get('checked_key_set_sha256')),
        d=dict(status='DEFERRED_TO_DISCOVERY', rows=None, key_set_sha256=None,
            required_rows=nrows, required_key_set_sha256=routing.get('database_key_set_sha256'),
            reason='Mode r does not reach preparation.'))


def publish(pdb, ndb, request, rd0, output, scratch):
    pdb, ndb, request, output, scratch = map(Path, (pdb, ndb, request, output, scratch))
    ps = reader(); psha, nsha = ps.sha(pdb), ps.sha(ndb)
    if psha != GATE: raise ValueError('E96:gate')
    contract_path = Path(__file__).with_name('f.json'); contract = load(contract_path)
    if ps.sha(contract_path) != FIELDS: raise ValueError('E96:fields')
    removals, scenes, state_pins = native_rules(ndb)
    # Samples are optional; a bad or missing sample request cannot skip the population.
    reference = dict(rows=[], request_sha256=None, P_absent_source=None, P_absent_count=None)
    sample_status = 'SKIPPED'
    if request.is_file():
        try:
            ps.main(pdb, request, str(rd0), scratch/'ns0.json')
            reference = load(scratch/'ns0.json'); sample_status = 'PASS'
        except (Exception, SystemExit) as error:
            sample_status = 'REFUSE:'+type(error).__name__+': '+str(error)
    selected = {key(json.loads(s['row'])) for s in reference['rows']}
    nmap, n_samples, sample_diffs = {}, {}, {}
    paths, classes, content_counts, class_rows, content_class_rows = (Counter() for _ in range(5))
    unclassified, examples, absent, types = {}, {}, [], Counter()
    causes = Counter(); matched = identical = pcount = nuf = puf = uf_expected = 0
    violations = retained_excluded = content_bad = 0
    literal_counts = Counter()
    with opened(ndb) as n, opened(pdb) as p:
        for nr in n.execute('SELECT i,row,target FROM rows ORDER BY i'):
            row = json.loads(nr[1]); k = key(row)
            if k in nmap: raise ValueError('E96:duplicate')
            nmap[k] = nr[0]; nuf += k[3] == 'U_Faithful'; types[row_type(row)] += 1
            if k in selected: n_samples[k] = nr
            retained_excluded += attribution(row, removals, scenes)['attribution'] != 'unattributed'
        pkeys = set()
        for pr in p.execute('SELECT i,row,target FROM rows ORDER BY i'):
            row = json.loads(pr[1]); k = key(row)
            if k in pkeys: raise ValueError('E96:duplicate')
            pkeys.add(k); pcount += 1; puf += k[3] == 'U_Faithful'
            why = attribution(row, removals, scenes)
            uf_expected += k[3] == 'U_Faithful' and why['attribution'] == 'unattributed'
            if k not in nmap:
                record = dict(why); record.update(key=k, i=pr[0], source=k[3])
                absent.append(record)
                labels = ['list:'+h for h in why['removal_list_sha256s']] if why['attribution']=='list' else [why['attribution']]
                for label in labels: causes[(k[3], label)] += 1
                continue
            nr = n.execute('SELECT i,row,target FROM rows WHERE i=?', (nmap[k],)).fetchone()
            matched += 1; identical += pr == nr
            for path, a, b in (('/i', pr[0], nr[0]), ('/row', pr[1], nr[1]), ('/target', pr[2], nr[2])):
                literal_counts[path] += int(type(a) is not type(b) or a != b)
            diff = fields(pr, nr)
            # Raw differences include escaped strings and 1 versus 1.0, even if parsed values agree.
            rawp, rawn = tokens(pr[1]), tokens(nr[1])
            known = {v[0] for v in diff}
            all_paths = rawp.keys() | rawn.keys()
            ancestors = set()
            def cover(path):
                while '/' in path:
                    path = path.rsplit('/',1)[0]; ancestors.add(path)
            for path in known: cover(path)
            for path in sorted(all_paths, key=lambda p: (-p.count('/'),p)):
                if path == '/row' or path in known or path in ancestors: continue
                a, b = rawp.get(path, MISSING), rawn.get(path, MISSING)
                if a != b:
                    diff.append((path, a, b)); known.add(path); cover(path)
            touched, failed_classes = set(), set()
            for path, a, b in diff:
                paths[path] += 1; label = category(path, contract)
                if label:
                    classes[label] += 1; touched.add(label)
                    if any(in_path(path, v) for v in contract['content_field_paths']): failed_classes.add(label)
                elif not any(in_path(path, v) for v in contract['content_field_paths']) and path not in ('/row_text','/target_text'):
                    entry = unclassified.setdefault(path, dict(count=0, examples=[])); entry['count'] += 1
                    if len(entry['examples']) < 3: entry['examples'].append(dict(key=k, P=shown(a), N=shown(b)))
            class_rows.update(touched); content_class_rows.update(failed_classes)
            exact = exact_fields(pr, nr, contract)
            content_bad += bool(exact)
            for path, a, b in exact:
                content_counts[path] += 1
                values = examples.setdefault(path, [])
                if len(values) < 3: values.append(dict(key=k, P=shown(a), N=shown(b)))
            if k in selected:
                sample_diffs[k] = [dict(path=path, P=shown(a), N=shown(b)) for path,a,b in diff]
    extras = sorted(set(nmap)-pkeys, key=str)
    unattributed = sum(v['attribution']=='unattributed' for v in absent)
    chain_path = next((p for p in (output/'chain.json', scratch.parent/'chain.json') if p.is_file()), None)
    chain = load(chain_path) if chain_path else {}
    criteria = decision(len(nmap), matched, len(extras), content_bad, content_counts,
                        unclassified, classes, class_rows, contract, chain, nsha)
    task_i = 'PASS' if all(criteria[k]['status'] == 'PASS' for k in ('a','b','c')) else 'FAIL' 
    task_ii = 'FAIL' if unattributed else 'PASS'
    task_iii = 'PASS' if nuf == uf_expected and not any(v['source']=='U_Faithful' and v['attribution']=='unattributed' for v in absent) else 'FAIL'
    status = 'PASS' if task_i == task_ii == task_iii == 'PASS' and not retained_excluded else 'FAIL'
    common = dict(P_database_sha256=psha, database_sha256=nsha, request_sha256=reference['request_sha256'],
                  P_absent_source=reference['P_absent_source'])
    samples, missing, diffs = [], [], []
    for s in reference['rows']:
        k = key(json.loads(s['row'])); identity = dict(**{'class':s['class']},position=s['position'],P_i=s['i'],key=k)
        if k not in n_samples:
            missing.append(identity); diffs.append(dict(identity,status='ABSENT'))
        else:
            nr = n_samples[k]; samples.append(dict(identity,i=nr[0],row=nr[1],target=nr[2]))
            diffs.append(dict(identity,N_i=nr[0],status='PRESENT',changes=sample_diffs[k]))
    faithful = dict(P=puf, kept=nuf, expected_kept=uf_expected, status=task_iii)
    by_source = [dict(source=s, attribution=a, rows=v) for (s,a),v in sorted(causes.items(),key=lambda x:str(x[0]))]
    na = dict(schema='na-v2', status=task_ii, rows=absent, count=len(absent), unattributed=unattributed,
              counts_by_source_attribution=by_source, U_Faithful=faithful, state=state_pins)
    ns = dict(common,count=len(nmap),U_Faithful_count=nuf,P_absent_count=len(absent),requested=len(reference['rows']),
              rows=samples,absent=missing,sample_status=sample_status)
    nd = dict(common,schema='nd-v2',status=status,task_i=task_i,task_ii=task_ii,task_iii=task_iii,
        P_rows=pcount,N_rows=len(nmap),matched_rows=matched,identical_sql_rows=identical,
        N_without_P=len(extras),N_without_P_examples=extras[:3],content_differing_rows=content_bad,
        content_fields_sha256=ps.sha(contract_path),content_field_counts=dict(content_counts),content_examples=examples,
        metadata_classes={name:dict(path_differences=classes[name],rows=class_rows[name],
            content_rows=content_class_rows[name]) for name in contract['allowed_metadata_classes']},
        unclassified_paths=unclassified,paths=dict(sorted(paths.items())),samples=diffs,state=state_pins,
        absent_file='na.json.gz',absent_count=len(absent),absent_unattributed=unattributed,
        absent_counts=by_source,U_Faithful=faithful,retained_excluded=retained_excluded,
        rd0='informational; includes ordinal; superseded by ANSWER 1226Z',
        comparison='exact raw encode field text and typed SQL target', criteria=criteria,
        content_field_paths=contract['content_field_paths'], field_derivation=contract['derivation'],
        literal_file='nl.json.gz')
    literal = dict(schema='nl-v1', role='information; superseded by ANSWER 1226Z',
        P_rows=pcount, N_rows=len(nmap), matched_rows=matched, identical_sql_rows=identical,
        differing_sql_rows=matched-identical, field_counts=dict(literal_counts), paths=dict(sorted(paths.items())),
        metadata_classes=nd['metadata_classes'], unclassified_paths=unclassified)
    rt = type_table(types,nsha)
    mandatory = {'nd.json':raw(nd),'na.json.gz':gzip.compress(raw(na),mtime=0),
                 'nl.json.gz':gzip.compress(raw(literal),mtime=0)}
    if (output/'routing_types.json').is_file():
        if (output/'routing_types.json').read_bytes() != raw(rt): raise ValueError('E96:types')
    else: mandatory['routing_types.json'] = raw(rt)
    existing = sum((output/n).stat().st_size for n in ('routing_types.json',) if (output/n).is_file())
    budget = LIMIT-existing-300_000
    payloads = dict(mandatory, **{'n_sample.json':raw(ns)})
    # Only optional sample details can shrink. Complete population counts and absences never do.
    while sum(map(len,payloads.values())) >= budget and (ns['rows'] or nd['samples']):
        if nd['samples']: nd['samples'].pop()
        if ns['rows']: ns['rows'].pop()
        ns['budget_limited']=True; nd['sample_budget_limited']=True
        payloads['n_sample.json']=raw(ns); payloads['nd.json']=raw(nd)
    total = sum(map(len,payloads.values()))
    if total >= budget: raise ValueError('E96:size')
    output.mkdir(parents=True,exist_ok=True)
    for name in payloads:
        if (output/name).exists() or (output/name).is_symlink(): raise ValueError('E96:exists')
    for name,data in payloads.items():
        with (output/name).open('xb') as f: f.write(data)
    return dict(status=status,task_i=task_i,task_ii=task_ii,task_iii=task_iii,criteria=criteria,routing_types=rt['status'],
                files=list(payloads),bytes=total,sampled=len(ns['rows']),absent=len(absent),matched=matched)


if __name__ == '__main__':
    try:
        result = publish_types(*sys.argv[2:4]) if sys.argv[1:2] == ['types'] else publish(*sys.argv[1:7])
        print(json.dumps(result,sort_keys=True))
    except (Exception,SystemExit) as error:
        print(json.dumps(dict(status='REFUSE', reason=type(error).__name__+': '+str(error),
            exception_line=traceback.format_exception_only(type(error),error)[-1].strip(),
            traceback=traceback.format_exc()), sort_keys=True))
        raise SystemExit(1)
