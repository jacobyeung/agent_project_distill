import re
p = 'pooled_harm_rule_v3.py'
s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a))
    s = s.replace(a, b)
rep('"""Pooled harm rule of leg R1: reference implementation v2', '"""Pooled harm rule of leg R1: reference implementation v3')
rep('''Provenance: every read of a set comes with a manifest (PROVENANCE_SCHEMA.md).  The tool refuses a read whose manifest is
  missing, inconsistent with its receipts, its read file or its rows, or different from the registered step-544 manifest of
  the set anywhere in `config`; only the `run` block (run, artifact, step and the read job that carries them) may differ.
  Both manifests of a read name one export.  A decision read is logged in the read ledger; a second read of the same
  boundary and arm whose read file or manifest differs is refused.''',
'''Provenance: every read of a set comes with a manifest (PROVENANCE_SCHEMA.md).  The tool refuses a read whose manifest is
  missing, inconsistent with its receipts, its read file or its rows, or different from the registered step-544 manifest of
  the set anywhere in `config`; only the `run` block (run, artifact, step and the read job that carries them) may differ.
  A read other than a pinned baseline must name its fetched archive, and the read file must equal the archive's decoded
  ITEMS.jsonl.  Every receipt binds at least one field, and the receipts together bind the export artifact's sha256 and
  path (which names run and step), the step, the arm, the reader package, the read token, the plan hash and, for an
  archived read, the archive's sha256.  The export artifact must be the one the training run's own export receipt (its
  runs/<run>/m<step>/artifact.json, supplied with --export-receipt) registers for that step.  A read or export already
  recorded under another run or step, in the tool's prior reads or in the read ledger, is refused.  Both manifests of a
  read name one export.  A decision read is logged in the read ledger; a second read of the same boundary and arm whose
  read file or manifest differs is refused.''')
rep('''usage: pooled_harm_rule_v2.py --step STEP --read ITEMS.jsonl [ITEMS.jsonl] --manifest-s1 M.json --manifest-r0 M.json
                              --output OUT.json (--ledger READ_LEDGER.jsonl | --calibration)
`--calibration` reads an export of another run at any step and decides nothing; it checks manifests but writes no ledger."""''',
'''usage: pooled_harm_rule_v3.py --step STEP --read ITEMS.jsonl [ITEMS.jsonl] --manifest-s1 M.json --manifest-r0 M.json
                              --output OUT.json --ledger READ_LEDGER.jsonl --export-receipt runs/<run>/m<step>/artifact.json
       pooled_harm_rule_v3.py ... --calibration [--ledger READ_LEDGER.jsonl] [--export-receipt artifact.json]
`--calibration` reads an export of another run at any step and decides nothing; it checks the manifests, checks the export
receipt when one is given, and with --ledger records the read as a calibration read (it never fills a boundary)."""''')
rep('''META = ('task_type',''', '''RUN_BINDS = ('run.artifact_sha256', 'run.artifact_path', 'run.step', 'config.arm', 'config.reader_package', 'run.read_token',
             'run.plan_sha256')                                     # the receipts of every manifest must bind all of these
ARCHIVE_BIND = 'read_file.archive.sha256'                            # and, for an archived read, this one
PRIOR = (('469ddece', 544, BASE_ARTIFACT, ('8347cd843f47fe637e770e47544ad49b03e60909e5312260a305319150edb8be',
                                           'a05c2318e038d6e19c368c309d8cba2cd31047fc6fd7ef124a7b8ac943565233')),
         ('359fcc3c', 200, '877c720bf19a83dc5946330c75e004fd01a774d7caef87bf9756f8304c2cbbaa',
          ('c1c99e4d4f818fbc5d29a56c20fed28b9e08b08a4c3a8a2d64cf056af8abe313', 'cf78973dcd9b697feae2f28d67b634a74db2624907a0fa54ba853f1c05d16d24')),
         ('359fcc3c', 100, '1f3ca7c7178a8913cc866dd6820a07b2d73a841ad1e9980f7e10c8ae491f3763',
          ('577a13a5b6752007a9c3108d142b76126b1726bfd6b178b8a3fe4d140a0fd6af',)),
         ('17c4ffa4', 100, '2ab263f3a0b784af0bc9f11041917e17d919a535907077b7085ed2f9c0642d5f',
          ('8a78e876624fd38b4ab1e735f7b7c36bbebe164cad180c4ce4e4d3d1a55d7b81',)))  # exports and reads made before registration
PRIOR_ENTRIES = [dict(run_id=r, step=t, artifact_sha256=a, read_sha256=x, kind='prior') for r, t, a, xs in PRIOR for x in xs]
META = ('task_type',''')
rep('''def check_manifest(m, d, read_by_sha, base_m, id_map):
    """Internal consistency of one manifest; returns the read path it names."""''',
'''def check_manifest(m, d, read_by_sha, base_m, id_map, baseline=False):
    """Internal consistency of one manifest; returns the read path it names.  `baseline`: the pinned step-544 manifest."""''')
rep('''    arch = m['read_file'].get('archive')
    if arch:
        if not os.path.exists(arch['path']) or sha(arch['path']) != arch['sha256']:''',
'''    arch = m['read_file'].get('archive')
    if not arch and not baseline:
        refuse('%s manifest names no fetched archive; only a pinned baseline may omit it' % b['name'])
    if arch:
        if not isinstance(arch, dict) or arch.get('member') != 'ITEMS.jsonl' or not arch.get('path') or not arch.get('sha256'):
            refuse('%s manifest: the archive entry lacks path, sha256 or member ITEMS.jsonl' % b['name'])
        if not os.path.exists(arch['path']) or sha(arch['path']) != arch['sha256']:''')
rep('''    if not m['receipts']:
        refuse('%s manifest has no receipt' % b['name'])
    for rc in m['receipts']:
        if not os.path.exists(rc['path']) or sha(rc['path']) != rc['sha256']:
            refuse('%s manifest: receipt missing or changed: %s' % (b['name'], rc['path']))
        doc = json.load(open(rc['path']))
        for src, dst in rc['binds']:''',
'''    if not m['receipts']:
        refuse('%s manifest has no receipt' % b['name'])
    bound = set()
    for rc in m['receipts']:
        if not os.path.exists(rc['path']) or sha(rc['path']) != rc['sha256']:
            refuse('%s manifest: receipt missing or changed: %s' % (b['name'], rc['path']))
        binds = rc.get('binds')
        if not binds or not all(isinstance(x, list) and len(x) == 2 and all(isinstance(y, str) and y for y in x) for x in binds):
            refuse('%s manifest: receipt %s binds no field' % (b['name'], os.path.basename(rc['path'])))
        doc = json.load(open(rc['path']))
        for src, dst in binds:
            bound.add(dst)''')
rep('''                refuse('%s manifest: %s of %s does not match %s' % (b['name'], src, os.path.basename(rc['path']), dst))
    return path''',
'''                refuse('%s manifest: %s of %s does not match %s' % (b['name'], src, os.path.basename(rc['path']), dst))
    unbound = [f for f in RUN_BINDS + ((ARCHIVE_BIND,) if arch else ()) if f not in bound]
    if unbound:
        refuse('%s manifest: no receipt binds %s' % (b['name'], ', '.join(unbound)))
    return path


def check_export_receipt(run, path):
    """The training run's own export receipt: the artifact.json the run wrote at runs/<run_id>/m<step>/, fetched unchanged
    into a directory of the same layout.  The manifest's export must be the file's sha256, at the step the file records."""
    if not path or not os.path.isfile(path):
        refuse('no export receipt of the training run (runs/<run>/m<step>/artifact.json) was supplied')
    mm = re.search(r'/runs/([0-9a-f]+)/m(\\d+)/artifact\\.json$', os.path.abspath(path))
    if not mm or (mm.group(1), int(mm.group(2))) != (run['run_id'], run['step']):
        refuse('the export receipt %s is not the receipt of run %s at step %s' % (path, run['run_id'], run['step']))
    if sha(path) != run['artifact_sha256']:
        refuse('the export artifact %s is not the one the training run registers for step %s (%s)'
               % (run['artifact_sha256'][:12], run['step'], sha(path)[:12]))
    if json.load(open(path)).get('step') != run['step']:
        refuse('the export receipt records another step than %s' % run['step'])''')
rep('''def prepare(read_paths, manifests, step, calibration, crosswalk=CROSSWALK, size_units=SIZE_UNITS, base_paths=None):''',
'''def prepare(read_paths, manifests, step, calibration, crosswalk=CROSSWALK, size_units=SIZE_UNITS, base_paths=None, export_receipt=None):''')
rep('''        check_manifest(base_m, d, {b['sha256']: bpath}, base_m, id_map)''',
'''        check_manifest(base_m, d, {b['sha256']: bpath}, base_m, id_map, baseline=True)''')
rep('''    if mS['artifact_sha256'] == BASE_ARTIFACT:
        refuse('the read is of the baseline artifact itself')
    return data''',
'''    if mS['artifact_sha256'] == BASE_ARTIFACT:
        refuse('the read is of the baseline artifact itself')
    if not calibration or export_receipt:
        check_export_receipt(mS, export_receipt)
    return data''')
rep('''def ledger_check(path, entry):
    old = [json.loads(l) for l in open(path) if l.strip()] if os.path.exists(path) else []
    for e in old:
        if all(e[k] == entry[k] for k in ('step', 'arm', 'set')):''',
'''def ledger_check(path, entry):
    """True when the entry is new.  Refuses a read or export recorded under another run or step (prior reads and ledger),
    and a second, different decision read of one boundary, arm and set."""
    old = [json.loads(l) for l in open(path) if l.strip()] if path and os.path.exists(path) else []
    for e in PRIOR_ENTRIES + old:
        for k, what in (('read_sha256', 'read'), ('artifact_sha256', 'export artifact')):
            if e.get(k) == entry[k] and (e.get('run_id'), e.get('step')) != (entry['run_id'], entry['step']):
                refuse('%s %s is already recorded under run %s step %s' % (what, entry[k][:12], e.get('run_id'), e.get('step')))
    if entry['kind'] != 'decision':
        return not any(all(e.get(k) == entry[k] for k in ('kind', 'step', 'set', 'run_id', 'read_sha256', 'manifest_sha256')) for e in old)
    for e in old:
        if e.get('kind', 'decision') == 'decision' and all(e[k] == entry[k] for k in ('step', 'arm', 'set')):''')
rep('''    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--ledger')
    g.add_argument('--calibration', action='store_true')
    a = ap.parse_args()''',
'''    ap.add_argument('--ledger')
    ap.add_argument('--export-receipt')
    ap.add_argument('--calibration', action='store_true')
    a = ap.parse_args()
    if not a.calibration and not (a.ledger and a.export_receipt):
        ap.error('a decision read needs --ledger and --export-receipt')''')
rep('''        data = prepare(a.read, man, a.step, a.calibration)
        entries = [dict(step=a.step, arm='direct', set=BASE[d]['name'], run_id=man[d]['run']['run_id'],''',
'''        data = prepare(a.read, man, a.step, a.calibration, export_receipt=a.export_receipt)
        entries = [dict(kind='calibration' if a.calibration else 'decision', step=a.step if not a.calibration else man[d]['run']['step'],
                        arm='direct', set=BASE[d]['name'], run_id=man[d]['run']['run_id'],''')
rep('''        new = [e for e in entries if ledger_check(a.ledger, e)] if a.ledger else []''',
'''        new = [e for e in entries if ledger_check(a.ledger, e)]
        new = new if a.ledger else []''')
rep("rule='R1 pooled harm rule v2'", "rule='R1 pooled harm rule v3'")
rep("run=man['S']['run'], script_sha256", "run=man['S']['run'], export_receipt_sha256=sha(a.export_receipt) if a.export_receipt else None, script_sha256")
open(p, 'w').write(s)
