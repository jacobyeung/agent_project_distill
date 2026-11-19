from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parent
BUILD = Path('/scratch/jjyeung/orch_n30/sb_cachefix')
pins = {}
def read(p):
    b = p.read_bytes()
    pins[str(p)] = hashlib.sha256(b).hexdigest()
    return b
read(Path(__file__))
read(ROOT/'run.sh')
prep = json.loads(read(ROOT/'evidence/preparation.json'))
audit = json.loads(read(ROOT/'evidence/input_audit.json'))
mutations = json.loads(read(ROOT/'evidence/mutations.json'))
contracts = json.loads(read(ROOT/'evidence/contracts.json'))
parity = json.loads(read(ROOT/'evidence/parity.json'))
tests = read(ROOT/'logs/tests.log').decode()
assert '29 passed' in tests and 'skipped' not in tests
assert len(mutations['results']) == 4 and all(r['killed'] for r in mutations['results'].values())
assert parity['passed']
assert audit['step400']['status'] == 'MISSING'
for rel in ('out/cachefix.patch', 'out/sb_cachefix.tar'):
    path = BUILD/rel
    assert hashlib.sha256(read(path)).hexdigest() == prep['input_sha256'][str(path)]
modules = {}
for name in ('routed_features.py','routed_candidates.py'):
    source = ROOT/'work/orig/src/tree/student_pilot'/name
    patched = ROOT/'work/patched/src/tree/student_pilot'/name
    modules[name] = dict(original=hashlib.sha256(read(source)).hexdigest(),patched=hashlib.sha256(read(patched)).hexdigest())
reader_a = ROOT/'work/orig/src/b/e2e_reader/stage1.py'
reader_b = Path('/scratch/jjyeung/orch_n30/sb_kbox4/reader_src/e2e_reader/stage1.py')
assert read(reader_a) == read(reader_b)
config = json.loads(read(ROOT/'work/orig/src/9.json'))
for name, hashes in modules.items():
    assert config['payload_pins']['tree/student_pilot/'+name]['sha256'] == hashes['original']
    assert hashes['patched'] != hashes['original']
read(ROOT/'work/orig/src/orchard_h10/job.py')
for arm in ('today','fixed'):
    for p in (ROOT/'work/k1diag'/arm).glob('*.json'):
        c = json.loads(read(p))
        for name, hashes in modules.items():
            assert c['module_sha256'][name[:-3]] == hashes['patched' if arm=='fixed' else 'original']
result = dict(input_sha256=pins,modules=modules,tests_passed=29,mutations_killed=4,
              parity_passed=parity['passed'],reader_stage1_identity=True,
              sealed_pins_match_original=True,patched_modules_require_reseal=True,
              scope='CPU-only independent review; no serving or external workspace edits')
(ROOT/'evidence/final_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
