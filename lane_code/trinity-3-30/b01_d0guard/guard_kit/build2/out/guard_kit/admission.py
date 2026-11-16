"""Native-only merge and in-job admission against the authenticated C8r request."""
import math
from pathlib import Path
from guard_core import digest, read, sha, write, rows_in_order, zero_nonanswers

def merge(session, rows, keys, destination, fixture=False):
    N=session.N;request=N.validate_request(N.load(session.destination/'paired/request.json'),live=True)
    rows=zero_nonanswers(rows_in_order(rows,keys))
    journal=session.destination/'paired/results/items.jsonl'
    recorded=N.rows(journal)
    if len(recorded)!=len(keys) or len({r['key'] for r in recorded})!=len(keys):
        raise ValueError('Native journal cardinality differs')
    by_key={r['key']:r for r in recorded}
    # The journal is JSON: compare canonical JSON, so tuples and lists of equal content agree.
    if set(by_key)!=set(keys):
        raise ValueError('Merged rows differ from the authenticated native journal')
    journaled=zero_nonanswers([by_key[k] for k in keys])
    differences={}
    for key,recorded_row,memory_row in zip(keys,journaled,rows):
        if digest(recorded_row)!=digest(memory_row):
            differences[key]=sorted(field for field in set(recorded_row)|set(memory_row)
                if field not in recorded_row or field not in memory_row
                or digest(recorded_row[field])!=digest(memory_row[field]))
    if differences:
        write(Path(destination)/'MERGE_DIFF.json',dict(keys=list(differences),fields=differences))
        raise ValueError('Merged rows differ from the authenticated native journal')
    rows=journaled
    if not set(keys)<=set(request['keys']):raise ValueError('Read membership is outside the bound request')
    if not fixture and keys!=request['keys']:raise ValueError('Production read must retain the full denominator')
    parity=N.load(session.destination/'paired/results/GPU_PARITY.json')
    if parity.get('pass') is not True:raise ValueError('GPU parity failed')
    tasks,_=N.tasks_and_captures(request['inputs']);tasks={'devrows:'+t['id']:t for t in tasks}
    from r1 import accounting
    for row in rows:
        key=row['key'];task=tasks[key];typ=N.family(row['question_type'])
        if typ not in N.FAMILIES or row['question_type']!=task['question_type']:
            raise ValueError('Item family differs from the bound task')
        if (row.get('room'),row.get('stratum'))!=(task['room'],task['stratum']):
            raise ValueError('Item room or label authority differs')
        if row.get('checkpoint_sha256')!=request['artifact']['sha256'] or row.get('binding')!=request['binding']:
            raise ValueError('Item checkpoint or request binding differs')
        if row.get('perception_identity')!=digest(request['perceptions'][task['id']]):raise ValueError('Item perception differs')
        if row.get('mask_source')!=N.mask_source(task['question_type']):raise ValueError('Item mask source differs')
        if type(row.get('called')) is not bool or type(row.get('no_answer')) is not bool:
            raise ValueError('Missing boolean call/answer accounting')
        if any(type(row.get(k)) is not int or row[k]<0 for k in ('call_errors','version_errors')):
            raise ValueError('Invalid call errors')
        if 'decode' in row and any(row[k]!=v for k,v in accounting(row['decode']).items()):raise ValueError('Decode accounting differs')
        if not row.get('scores') or any(v is not None and (type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1) for v in row['scores'].values()):
            raise ValueError('Invalid item score')
        label='released_answer' if row['stratum']=='primary' else 'answer'
        if row['scores'].get(label) is None:raise ValueError('Missing score removes an item from the denominator')
        if row['no_answer'] and any(v not in (None,0.) for v in row['scores'].values()):raise ValueError('Non-answer has a positive score')
        if task['id'] in request['geometry_refusals']:
            if row!=N.geometry_refusal_pair(task,request)[0]:raise ValueError('Geometry-refused item differs')
        elif row.get('geometry_refusal'):raise ValueError('Unbound geometry refusal')
    import gravity_guard
    import native_metrics
    geom=N.load(N.checked(request['grounding']['geometry_manifest']))
    guard=gravity_guard.report();native_metrics.validate_gravity_guard(guard,{'dev-S1':geom['records']})
    destination=Path(destination)
    bundle=dict(schema='legs1-r1-nomdg-v1',synthetic=fixture,arms={'unflagged':rows},expected_keys=keys,
        artifact_sha256=request['artifact']['sha256'],binding=request['binding'],
        perception_by_key={k:digest(request['perceptions'][tasks[k]['id']]) for k in keys},
        adapter_sources=request['adapter_sources'],reader_semantics=dict(N.Q.REPORT_SEMANTICS),
        report_scope='Internal instrument; never a claimed result',training_decision_allowed=False,
        receipts=dict(request=N.pin(session.destination/'paired/request.json'),journal=N.pin(journal)))
    write(destination/'R1.json',bundle)
    report=dict(schema='g2-admission-v1',status='PASS',fixture=fixture,items=len(rows),
        artifact=request['artifact'],bundle=dict(path=str(destination/'R1.json'),sha256=sha(destination/'R1.json')),
        gravity_guard=gravity_guard.identity(),gravity_guard_report=guard,
        geometry_manifest=request['grounding']['geometry_manifest'],request=bundle['receipts']['request'],
        parity=N.pin(session.destination/'paired/results/GPU_PARITY.json'),
        single_arm=True,all_calls_served=True,program_refusals=native_metrics.program_refusals(rows))
    write(destination/'IN_JOB_ADMISSION.json',report)
    return bundle
