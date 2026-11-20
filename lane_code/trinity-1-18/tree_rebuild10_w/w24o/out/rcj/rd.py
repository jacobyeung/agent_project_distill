"""Publish bounded field differences and observed rejection decisions."""
from contextlib import contextmanager
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3


def key(source, qid):
    return json.dumps([source, qid], ensure_ascii=True, separators=(',', ':'))


@contextmanager
def observe(state, phase):
    from student_pilot.s1_exclusions import Exclusions
    original_keep, original_report = Exclusions.keep, Exclusions.report

    def keep(rule, row, source):
        result = original_keep(rule, row, source)
        if not result:
            name = (row.get('s1_source') or {}).get('name') if source == 'r16' else source.removeprefix('pool/')
            reasons = [name for name, flag in rule.matches(row).items() if flag]
            state['drops'].setdefault(key(name, row.get('qid')), []).append(
                dict(phase=phase, filter='scene_exclusion', reasons=reasons, source=source))
        return result

    def report(rule, validate=True):
        # Snapshot before the native comparison can refuse. Its return and exception survive.
        value = original_report(rule, validate=False)
        state['census'].append(dict(phase=phase, files=value['files'], sources=value['sources'],
                                    expected=value['expected']))
        return original_report(rule, validate=validate)

    Exclusions.keep, Exclusions.report = keep, report
    try:
        yield
    finally:
        Exclusions.keep, Exclusions.report = original_keep, original_report


def save(path, state):
    Path(path).write_text(json.dumps(state, sort_keys=True, separators=(',', ':'))+'\n')


def differences(a, b, path='row'):
    if type(a) is not type(b):
        yield path, a, b, True, True
    elif isinstance(a, dict):
        for name in sorted(a.keys() | b.keys()):
            child = path+'/'+name.replace('~', '~0').replace('/', '~1')
            if name not in a or name not in b:
                yield child, a.get(name), b.get(name), name in a, name in b
            else:
                yield from differences(a[name], b[name], child)
    elif isinstance(a, list):
        for i in range(max(len(a), len(b))):
            child = path+'/'+str(i)
            if i >= len(a) or i >= len(b):
                yield child, a[i] if i < len(a) else None, b[i] if i < len(b) else None, i < len(a), i < len(b)
            else:
                yield from differences(a[i], b[i], child)
    elif a != b:
        yield path, a, b, True, True


def display(value, limit):
    text = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'))
    return dict(value=text[:limit], truncated=len(text)>limit, chars=len(text))


def open_db(path):
    db = sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True)
    db.execute('PRAGMA query_only=ON')
    db.execute('PRAGMA cache_size=-8192')
    return db


def row(db, i, expected):
    value = db.execute('SELECT i,row,target FROM rows WHERE i=?', (i,)).fetchone()
    if value is None:
        raise ValueError('E97')
    parsed = json.loads(value[1])
    actual = [parsed.get('dataset'), parsed.get('scene'), parsed.get('qid'),
              (parsed.get('s1_source') or {}).get('name')]
    if actual != expected:
        raise ValueError('E97')
    return value, parsed


def publish(n_db, p_db, diff_path, state_path, output):
    with gzip.open(diff_path, 'rt') as handle:
        diff = json.load(handle)
    state = json.loads(Path(state_path).read_text()) if Path(state_path).is_file() else dict(drops={}, census=[])
    matched = [v for v in diff['N'] if v.get('P')]
    count = min(200, len(matched))
    positions = [i*(len(matched)-1)//(count-1) for i in range(count)] if count > 1 else list(range(count))
    records = []
    n, p = open_db(n_db), open_db(p_db)
    try:
        for pos in positions:
            item = matched[pos]
            nv, nr = row(n, item['i'], item['key'])
            pv, pr = row(p, item['P']['i'], item['key'])
            fields = list(differences(pr, nr))
            if pv[1] != nv[1] and not fields:
                fields.append(('row/$text', pv[1], nv[1], True, True))
            if pv[0] != nv[0]:
                fields.append(('i', pv[0], nv[0], True, True))
            if pv[2] != nv[2]:
                fields.append(('target', pv[2], nv[2], True, True))
            records.append(dict(key=item['key'], p_i=pv[0], n_i=nv[0], fields=fields,
                                row_text_equal=pv[1]==nv[1], target_equal=pv[2]==nv[2]))
    finally:
        n.close(); p.close()
    absent = []
    for item in diff['P_absent']:
        if item['removal_list_sha256s']:
            continue
        decisions = state['drops'].get(key(item['key'][3], item['key'][2]), [])
        absent.append(dict(key=item['key'], p_i=item['i'], rule=decisions or 'unknown'))
    census = [dict(phase=v['phase'], files=v['files'], sources=v['sources'],
                   expected={k:{f:x.get(f) for f in ('counts','rows','method')} for k,x in v['expected'].items()})
              for v in state['census']]
    result = dict(schema='d0-v1', matched_count=count, matched_available=len(matched),
                  unlisted_absent_count=len(absent), unknown=sum(v['rule']=='unknown' for v in absent),
                  absent=absent, census=census, comparison_unchanged=True)
    for limit in (200, 100, 40, 0):
        result['value_limit'] = limit
        result['matched'] = [{**r, 'fields':[dict(path=path, p=display(a,limit), n=display(b,limit),
                                                p_present=ap, n_present=bp) for path,a,b,ap,bp in r['fields']]}
                             for r in records]
        raw = (json.dumps(result, ensure_ascii=True, separators=(',', ':'))+'\n').encode()
        if len(raw) < 5_000_000:
            Path(output).write_bytes(raw)
            return dict(status='PASS', bytes=len(raw), matched=count, absent=len(absent),
                        unknown=result['unknown'], sha256=hashlib.sha256(raw).hexdigest())
    raise ValueError('E98')
