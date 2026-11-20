def scope_tests(cfg, rows):
    """Use native stored rows and a sealed reference for the absent source class."""
    from student_pilot.extent_receipt import Extents, required
    from student_pilot.p3_provenance import digest
    gate = Extents(cfg.get('extent_receipt'), cfg.get('extent_pool_sources'))
    examples = {}
    for row in rows:
        if gate.exempt(row, 'routing'):
            examples.setdefault('pool', row)
        elif required(row, 'routing'):
            name = 'slice' if str(row.get('qid', '')).startswith('a0_') else 'other'
            examples.setdefault(name, row)
        if len(examples) == 3:
            break
    origins = {name: 'database' for name in examples}
    if 'other' not in examples:
        import base64
        value = json.loads(base64.b64decode(REFERENCE))
        if digest(value) != REFERENCE_SHA:
            raise ValueError('E99:reference')
        examples['other'] = value
        origins['other'] = 'sealed_reference'
    results = {}
    for name in ('slice', 'pool', 'other'):
        if name not in examples:
            results[name] = dict(status='UNAVAILABLE', reason='E99:row')
            continue
        row = examples[name]
        test = Extents(cfg.get('extent_receipt'), cfg.get('extent_pool_sources'))
        if name != 'pool':
            # Negative control: remove only this entry in memory, never on disk.
            test.receipt = dict(test.receipt, rows={q:e for q,e in test.receipt['rows'].items()
                                                  if q != row['qid']})
        expected = None if name == 'pool' else 'EXTENT_ROW_UNAUDITED'
        error = None
        try:
            test.check(row, 'routing')
        except Exception as caught:
            error = str(caught)
        results[name] = dict(status='PASS' if error == expected else 'FAIL',
            qid=row['qid'], row_sha256=digest(row), origin=origins[name],
            expected=expected, observed=error, exempted=test.exempted)
    return dict(status='PASS' if all(v['status']=='PASS' for v in results.values()) else 'FAIL',
                cases=results)


def card_rows(cfg, n_rows, p_rows):
    from student_pilot.extent_receipt import Extents
    import re
    gate = Extents(cfg.get('extent_receipt'), cfg.get('extent_pool_sources'))
    def norm(qid):
        match = re.search(r'vsi590k_[0-9]+', qid)
        return match.group() if match else qid
    p_qids = {r['qid'] for r in p_rows if r.get('s1_source', {}).get('name') in gate.pool_sources}
    entries = gate.receipt['rows']
    exact = p_qids & entries.keys()
    normalized = {}; repaired = set(); flagged = set()
    for qid, entry in entries.items():
        key = norm(qid)
        normalized[key] = True
        if entry.get('repair_sha256'):
            repaired.add(key)
        if any(s != 'full' for s in entry.get('box_statuses', [])):
            flagged.add(key)
    counts = Counter(); by_source = Counter()
    for row in n_rows:
        value = {**row, **row['routing']} if isinstance(row.get('routing'), dict) else row
        kind = value.get('question_type', value.get('type'))
        if kind in ('object_abs_distance', 'absolute_distance_object', 'camera_object_abs_distance'):
            counts['distance_rows'] += 1
        if not gate.exempt(row, 'routing'):
            continue
        counts['exempted_rows'] += 1
        source = row['s1_source']; by_source[source['name']] += 1
        canonical = source.get('provenance', {}).get('canonical', '')
        if canonical.startswith(bytes.fromhex('7363616e6e657470702f').decode()):
            counts['v1_rows'] += 1
    return dict(counts=counts, by_source=by_source,
        v1_fraction=counts['v1_rows']/counts['distance_rows'] if counts['distance_rows'] else None,
        p_pool_qids=len(p_qids), exact_matches=len(exact),
        exact_repaired=sum(bool(entries[q].get('repair_sha256')) for q in exact),
        exact_flagged=sum(any(s != 'full' for s in entries[q].get('box_statuses', [])) for q in exact),
        normalized_qid_matches=sum(norm(q) in normalized for q in p_qids),
        normalized_distinct_matches=len({norm(q) for q in p_qids} & normalized.keys()),
        normalized_repaired=sum(norm(q) in repaired for q in p_qids),
        normalized_flagged=sum(norm(q) in flagged for q in p_qids),
        normalization='base numeric identifier; all receipt variants; diagnostic only')


def scope_report(cfg, directory):
    from student_pilot.p3_provenance import sha256
    directory = Path(directory)
    def rows(c):
        for (text,) in c.execute('SELECT row FROM rows ORDER BY i'):
            yield json.loads(text)
    with sqlite3.connect((directory/'selection/rows.sqlite').as_uri()+'?mode=ro', uri=True) as n:
        tests = scope_tests(cfg, rows(n))
        if sha256(directory/'base/rows.sqlite') != DB:
            raise ValueError('E99:base')
        with sqlite3.connect((directory/'base/rows.sqlite').as_uri()+'?mode=ro', uri=True) as p:
            card = card_rows(cfg, rows(n), rows(p))
    return dict(status=tests['status'], tests=tests, card=card)
