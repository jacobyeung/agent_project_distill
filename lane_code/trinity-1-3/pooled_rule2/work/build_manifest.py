"""Write the provenance manifest of one direct read of one set (schema pooled-rule-read-manifest-v1, PROVENANCE_SCHEMA.md).

Two receipt layouts exist:
  kit    a read-kit build directory (h1read kit, D0 read kit): SUBMISSION.json, fetched/x/SPEC.json,
         fetched/x/<family>/a0/request.json, fetched/x/COMPLETE.json, fetched/x/ITEMS.jsonl
  evalx  the evalx milestone read e193c2a3c (Orchard 169526) behind A544.jsonl: SPEC.json, PLAN.json,
         merged/main/results/budget_2048/request.json, plus the read kit's ACCEPTED.json that names job and sources
usage: build_manifest.py kit BUILD_DIR SET OUT.json
       build_manifest.py evalx E193_DIR ACCEPTED.json READ.jsonl OUT.json"""
import hashlib, json, sys

RULE_TYPES = {'dev-S1': ('object_counting', 'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',
                         'object_rel_distance', 'object_size_estimation', 'route_planning'),
              'R0-dev': ('object_counting', 'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',
                         'object_rel_distance', 'object_size_estimation', 'obj_appearance_order')}
FAMILY = {'dev-S1': 'main', 'R0-dev': 'a7'}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def population(read, fam, types):
    c = {}
    for l in open(read):
        if l.strip():
            r = json.loads(l)
            if r.get('family') == fam and r.get('task_type') in types:
                c[r['task_type']] = c.get(r['task_type'], 0) + 1
    return {t: c.get(t, 0) for t in types}


def receipt(path, binds):
    return dict(path=path, sha256=sha(path), binds=binds)


def config(req, item_file_sha256, pop):
    cell = req['cells'][0]
    return dict(arm='direct', reader_package=req['source_sha256'],
                decoding=dict(decoding=cell['decoding'], frames=cell['frames'], layout=cell['layout'], max_tokens=req['max_tokens'],
                              thinking=req['thinking'], temperature=req['temperature'], max_model_len=req['max_model_len'],
                              engine_version=req['engine_version'], budget=2048),
                selector_rule='none (direct arm: no call is served)', scale_rule='none (direct arm)', tower_weights='none (direct arm)',
                item_file_sha256=item_file_sha256, rule_population=pop)


def kit(build, set_name, out):
    fam = FAMILY[set_name]
    x = build + '/fetched/x/'
    sub, spec, comp = json.load(open(build + '/SUBMISSION.json')), json.load(open(x + 'SPEC.json')), json.load(open(x + 'COMPLETE.json'))
    req_path = x + fam + '/a0/request.json'
    req = json.load(open(req_path))
    item_sha = req['items_sha256'] if fam == 'a7' else req['datasets'][0]['rows']['sha256']
    item_bind = 'items_sha256' if fam == 'a7' else 'datasets.0.rows.sha256'
    read = x + 'ITEMS.jsonl'
    m = dict(schema='pooled-rule-read-manifest-v1', set=set_name, family=fam,
             run=dict(run_id=spec['artifact']['path'].split('/runs/')[1].split('/')[0], step=spec['step'],
                      artifact_sha256=spec['artifact']['sha256'], artifact_path=spec['artifact']['path'],
                      orchard_job=sub['job'], read_token=sub['token'], plan_sha256=sub['plan_sha256']),
             config=config(req, item_sha, population(read, fam, RULE_TYPES[set_name])),
             type_filter=req.get('types') or 'none',
             read_file=dict(path=read, sha256=sha(read),
                            archive=dict(path=build + '/fetched/result.tar.gz', sha256=sha(build + '/fetched/result.tar.gz'), member='ITEMS.jsonl',
                                         decode='a7 and r0dev ids through ID_MAP.json (sha256 in ROOM_CROSSWALK.json sources.id_map)')),
             receipts=[receipt(build + '/fetched/FETCH.json', [['job', 'run.orchard_job'], ['token', 'run.read_token'],
                                                               ['status', 'read_file.fetch_status'], ['archive.sha256', 'read_file.archive.sha256']]),
                       receipt(build + '/SUBMISSION.json', [['job', 'run.orchard_job'], ['token', 'run.read_token'], ['plan_sha256', 'run.plan_sha256']]),
                       receipt(x + 'SPEC.json', [['artifact.sha256', 'run.artifact_sha256'], ['artifact.path', 'run.artifact_path'],
                                                 ['step', 'run.step'], ['scope', 'config.arm']]),
                       receipt(x + 'COMPLETE.json', [['plan_sha256', 'run.plan_sha256'], ['step', 'run.step']]),
                       receipt(req_path, [['source_sha256', 'config.reader_package'], [item_bind, 'config.item_file_sha256'],
                                          ['max_tokens', 'config.decoding.max_tokens'], ['thinking', 'config.decoding.thinking'],
                                          ['temperature', 'config.decoding.temperature'], ['engine_version', 'config.decoding.engine_version'],
                                          ['cells.0.layout', 'config.decoding.layout'], ['cells.0.frames', 'config.decoding.frames']])])
    m['read_file']['fetch_status'] = 'COMPLETE'
    if spec.get('export_binding'):
        next(r for r in m['receipts'] if r['path'].endswith('/SPEC.json'))['binds'].append(['export_binding.run', 'run.run_id'])
    write(m, out)


def evalx(e193, accepted, read, out):
    spec, plan, acc = json.load(open(e193 + '/SPEC.json')), json.load(open(e193 + '/PLAN.json')), json.load(open(accepted))
    req_path = e193 + '/merged/main/results/budget_2048/request.json'
    req = json.load(open(req_path))
    m = dict(schema='pooled-rule-read-manifest-v1', set='dev-S1', family='main',
             run=dict(run_id=spec['artifact']['path'].split('/runs/')[1].split('/')[0], step=spec['step'],
                      artifact_sha256=spec['artifact']['sha256'], artifact_path=spec['artifact']['path'],
                      orchard_job=acc['job'], read_token=acc['packet'], plan_sha256=plan['plan_sha256']),
             config=config(req, req['datasets'][0]['rows']['sha256'], population(read, 'main', RULE_TYPES['dev-S1'])),
             type_filter=req.get('types') or 'none',
             read_file=dict(path=read, sha256=sha(read)),
             receipts=[receipt(accepted, [['job', 'run.orchard_job'], ['packet', 'run.read_token']]),
                       receipt(e193 + '/SPEC.json', [['artifact.sha256', 'run.artifact_sha256'], ['artifact.path', 'run.artifact_path'],
                                                     ['step', 'run.step'], ['scope', 'config.arm']]),
                       receipt(e193 + '/PLAN.json', [['plan_sha256', 'run.plan_sha256'], ['step', 'run.step'], ['scope', 'config.arm']]),
                       receipt(req_path, [['source_sha256', 'config.reader_package'], ['datasets.0.rows.sha256', 'config.item_file_sha256'],
                                          ['max_tokens', 'config.decoding.max_tokens'], ['thinking', 'config.decoding.thinking'],
                                          ['temperature', 'config.decoding.temperature'], ['engine_version', 'config.decoding.engine_version'],
                                          ['cells.0.layout', 'config.decoding.layout'], ['cells.0.frames', 'config.decoding.frames'],
                                          ['legs1.artifact.sha256', 'run.artifact_sha256']])])
    write(m, out)


def write(m, out):
    s = json.dumps(m, indent=1, sort_keys=True) + '\n'
    open(out, 'w').write(s)
    print(out, hashlib.sha256(s.encode()).hexdigest())


if __name__ == '__main__':
    if sys.argv[1] == 'kit':
        kit(*sys.argv[2:5])
    else:
        evalx(*sys.argv[2:6])
