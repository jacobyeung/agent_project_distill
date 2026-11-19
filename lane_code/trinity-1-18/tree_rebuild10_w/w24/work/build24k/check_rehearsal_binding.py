"""Replay the shipped localization and native donor check on authenticated metadata."""
import ast
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

K = Path(__file__).resolve().parent
L = K.parents[1]
KIT = L / 'out/kit_n_go'
TREE = L / 'work/tree_r1'
sys.path.insert(0, str(TREE))
from student_pilot import r1_handover as H, r1_persisted as P
from launch_r1.entry import temporary_paths


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    value = json.loads(Path(p).read_text())
    if isinstance(value, dict) and 'payload' in value:
        raw = base64.b64decode(value['payload'], validate=True)
        assert hashlib.sha256(raw).hexdigest() == value['sha256']
        return json.loads(raw)
    return value


uploads = {}
def inventory(value, origin):
    if isinstance(value, dict):
        if 'local_path' in value and 'sha256' in value:
            uploads.setdefault(value['sha256'], []).append((value['local_path'], str(origin)))
        for item in value.values():
            inventory(item, origin)
    elif isinstance(value, list):
        for item in value:
            inventory(item, origin)


for path in sorted((L / 'out').glob('UPLOADS_*.json')):
    inventory(read(path), path)

real = L.parent / 'ext/m400real'
def locate(pin, label, production):
    candidates = list(uploads.get(pin['sha256'], [])) if production else []
    if production:
        # The inventory names this metadata snapshot through its routing receipt.
        # Other donor members are in the same already-present snapshot, not uploads.
        candidates.append((str(real / 'e.json' if label == 'receipt' else
                               real / 'files' / pin['path'].lstrip('/')), 'real donor snapshot'))
    else:
        candidates.append((pin['path'], 'fixture donor'))
    for name, origin in candidates:
        path = Path(name)
        if path.is_file() and sha(path) == pin['sha256']:
            return path, origin
    raise AssertionError('Authenticated metadata unavailable: ' + label)


planner = ast.parse((KIT / 'b/pl.py').read_text())
plan = next(n for n in planner.body if isinstance(n, ast.FunctionDef) and n.name == 'plan_payload')
localizer = next(n for n in plan.body if isinstance(n, ast.FunctionDef) and n.name == 'localize')
def localize(value, hashes, q):
    def unexpected_read(*args):
        raise AssertionError('Unexpected metadata read: ' + repr(args))
    env = dict(Path=Path, hashlib=hashlib, q=q, sources=dict.fromkeys(hashes),
               paths={h: str(q / 'u' / h) for h in hashes}, extras={},
               spec=read(KIT / 'k/p.json'), remember=unexpected_read)
    exec(compile(ast.Module(body=[localizer], type_ignores=[]), str(KIT / 'b/pl.py'), 'exec'), env)
    return env['localize'](deepcopy(value))


def checks(source, bound, prep, cfg):
    pin = cfg['r1_training']['p_run']['preparation']
    identity = H.export_identity(source)
    pairs = [('source.preparation.path', source['preparation']['path'], pin['path']),
             ('source.preparation.sha256', source['preparation']['sha256'], pin['sha256']),
             ('binding.preparation.path', bound['preparation']['path'], pin['path']),
             ('binding.preparation.sha256', bound['preparation']['sha256'], pin['sha256']),
             ('binding.config_sha256', bound.get('config_sha256'), identity),
             ('preparation.config_sha256', prep.get('config_sha256'), identity),
             ('preparation.schema', prep.get('schema'), 'c1-preparation-v1')]
    return [dict(field=k, actual=a, expected=b, equal=a == b) for k, a, b in pairs]


def evaluate(production):
    original = read(KIT / 'k/c.json') if production else read(K / 'rehearsal_k/seed.json')
    spec = read(KIT / 'k/p.json')
    q = Path(spec['namespace']) / ('p' if production else 'p2') / 'q'
    value = original['r1_training']
    if production:
        assert value['p_run'] == spec['p_run']
        assert value['donor_config_sha256'] == spec['p_runtime_identity']
    pins = dict(value['p_run'], artifact=original['init_artifact']['artifact'],
                receipt=value['handover_receipt'])
    paths, documents, files = {}, {}, {}
    for label, pin in pins.items():
        path, origin = locate(pin, label, production)
        paths[pin['sha256']] = str(path)
        documents[label] = read(path)
        files[label] = dict(pin=pin, local_path=str(path), sha256=sha(path), origin=origin)
    hand = documents['receipt']
    assert hand['schema'] == 'p-export-only-v1' and hand['step'] == 400
    for label in ('config', 'binding', 'preparation', 'artifact'):
        assert hand['pins'][label] == pins[label]
    identity = H.export_identity(documents['config'])
    assert identity == documents['artifact']['config_sha256'] == value['donor_config_sha256']
    before = checks(documents['config'], documents['binding'], documents['preparation'], original)
    assert all(row['equal'] for row in before)
    fields = dict(p_run=value['p_run'], handover_receipt=value['handover_receipt'],
                  init_artifact=original['init_artifact'])
    localized_fields = localize(fields, paths, q)
    cfg = deepcopy(original)
    cfg['r1_training'].update(p_run=localized_fields['p_run'],
                              handover_receipt=localized_fields['handover_receipt'])
    cfg['init_artifact'] = localized_fields['init_artifact']
    cfg['r1_training'].setdefault('persisted_files', {})
    after = checks(documents['config'], documents['binding'], documents['preparation'], cfg)
    if not production:
        observed = read(K / 'rehearsal_k/p2/i/m/n.json')
        assert observed['r1_training']['p_run'] == localized_fields['p_run']
        assert observed['r1_training']['handover_receipt'] == localized_fields['handover_receipt']
        assert observed['init_artifact'] == localized_fields['init_artifact']
    with P.scope(paths):
        try:
            H._donor(cfg, documents['artifact'])
        except ValueError as error:
            refusal = str(error)
        else:
            raise AssertionError('Expected native refusal')
    assert refusal == 'P_EXPORT_RUN_BINDING_MISMATCH'
    assert [row['field'] for row in after if not row['equal']] == [
        'source.preparation.path', 'binding.preparation.path']
    try:
        temporary_paths(fields['p_run'], q)
    except ValueError as error:
        preserved_refusal = str(error)
    else:
        raise AssertionError('Expected confinement refusal')
    assert preserved_refusal == 'R1_HOST_PATH_OUTSIDE_JOB_TMP'
    temporary_paths(localized_fields, q)
    return dict(files=files, original_fields=fields, localized_fields=localized_fields,
                identity=identity, original_checks=before, localized_checks=after,
                native_refusal=refusal, preserved_p_run_refusal=preserved_refusal,
                receipt_schema=hand['schema'], artifact_step=documents['artifact']['step'],
                job_tmp=str(q))


evidence = dict(verdict='LAUNCH BLOCKER', fix_scope='tree change required',
                production=evaluate(True), fixture=evaluate(False),
                method='Exact shipped localize AST; unmodified native _donor and temporary_paths; authenticated metadata only.',
                limits='No native full q, production stores, weights, or training executed.',
                code={str(p.relative_to(L)): sha(p) for p in [KIT / 'b/pl.py',
                      TREE / 'student_pilot/r1_handover.py', TREE / 'launch_r1/entry.py']})
(K / 'REHEARSAL_K_BINDING_EVIDENCE.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
lines = ['Production: LAUNCH BLOCKER; native localized donor refuses P_EXPORT_RUN_BINDING_MISMATCH.',
         'The native temporary-path gate also refuses the original p_run pins; a tree change is required.',
         'The JSON evidence records every full pin, authenticated local filename, and code hash.']
for name in ('production', 'fixture'):
    item = evidence[name]
    lines += ['', name.capitalize() + ':', '', '| Field | Donor bytes | Localized comparison value | Equal |',
              '| --- | --- | --- | --- |']
    for row in item['localized_checks']:
        lines.append('| ' + ' | '.join(str(row[k]) for k in ('field', 'actual', 'expected', 'equal')) + ' |')
    lines += ['', 'Unlocalized binding: all seven field comparisons pass.',
              'Native refusal: `' + item['native_refusal'] + '`.',
              'Preserving p_run unchanged: `' + item['preserved_p_run_refusal'] + '`.']
(K / 'REHEARSAL_K_BINDING_FIELDS.md').write_text('\n'.join(lines) + '\n')
print('PASS: production and fixture reproduce P_EXPORT_RUN_BINDING_MISMATCH; original p_run fails confinement.')
print('LAUNCH BLOCKER: tree change required; no repair applied.')
