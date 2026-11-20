DEV = 'a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5'
TREE = 'de202f58b31793608f886360a9fdfb5f58c24932e35976efcf74acead62e3cfe'
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
    # Same precedence as the native family reader, including its units test.
    raw = row.get('routing', row)
    kind = raw.get('question_type', row.get('question_type'))
    record = raw.get('ground_record', {})
    qid = str(row.get('qid', raw.get('qid', '')))
    if record.get('not_seen') or qid.startswith('a0_recovery_'): return 'recovery'
    if record.get('unit') or qid.startswith('a0_units_'): return 'units'
    if kind in ('object_abs_distance', 'absolute_distance_object'): return 'absolute_distance'
    return str(kind)


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
            sample_status = 'REFUSE:'+type(error).__name__
    selected = {key(json.loads(s['row'])) for s in reference['rows']}
    nmap, n_samples, sample_diffs = {}, {}, {}
    paths, classes, content_counts, class_rows, content_class_rows = (Counter() for _ in range(5))
    unclassified, examples, absent, types = {}, {}, [], Counter()
    causes = Counter(); matched = identical = pcount = nuf = puf = uf_expected = 0
    violations = retained_excluded = content_bad = 0
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
                absent.append(dict(key=k, i=pr[0], source=k[3], **why))
                labels = ['list:'+h for h in why['removal_list_sha256s']] if why['attribution']=='list' else [why['attribution']]
                for label in labels: causes[(k[3], label)] += 1
                continue
            nr = n.execute('SELECT i,row,target FROM rows WHERE i=?', (nmap[k],)).fetchone()
            matched += 1; identical += pr == nr
            diff = fields(pr, nr)
            # Raw differences include escaped strings and 1 versus 1.0, even if parsed values agree.
            rawp, rawn = tokens(pr[1]), tokens(nr[1])
            known = {v[0] for v in diff}
            for path in sorted(rawp.keys() | rawn.keys()):
                if path == '/row' or path in known: continue
                a, b = rawp.get(path, MISSING), rawn.get(path, MISSING)
                if a != b and not any(in_path(v, path) and v != path for v in rawp.keys() | rawn.keys()):
                    diff.append((path, a, b)); known.add(path)
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
    task_i = 'FAIL' if extras or content_bad or unclassified else 'PASS'
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
        rd0='informational; includes ordinal',comparison='exact raw field text and typed SQL target')
    rt = type_table(types,nsha)
    mandatory = {'nd.json':raw(nd),'na.json.gz':gzip.compress(raw(na),mtime=0),'routing_types.json':raw(rt)}
    existing = sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) if output.exists() else 0
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
    return dict(status=status,task_i=task_i,task_ii=task_ii,task_iii=task_iii,routing_types=rt['status'],
                files=list(payloads),bytes=total,sampled=len(ns['rows']),absent=len(absent),matched=matched)
