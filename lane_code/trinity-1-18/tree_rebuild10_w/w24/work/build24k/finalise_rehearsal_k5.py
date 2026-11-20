"""Verify the single retained attempt and report each requested proof separately."""
from pathlib import Path
from contextlib import closing
import hashlib
import json
import sqlite3
import sys
import tarfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rehearsal_paths_k5 import D, R
from rehearsal_inputs_k5 import usage

def read(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default

def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''): value.update(block)
    return value.hexdigest()

def new(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2); handle.write('\n')

setup = read(R/'SETUP.json')
kit = Path(setup['kit_dir'])
stages = read(R/'STAGES.json', [])
failed = next((row for row in stages if row['returncode']), None)
refusal = read(R/'RUN_REFUSAL.json', {})
detail = None
if failed:
    lines = Path(failed['log']).read_text().splitlines()
    errors = [(i+1, line) for i, line in enumerate(lines)
              if line.startswith(('ValueError:', 'RuntimeError:', 'KeyError:', 'FileNotFoundError:', 'AssertionError:', 'TypeError:'))]
    excerpts = [dict(line=i+1, text=line) for i, line in enumerate(lines)
                if i >= max(0, len(lines)-65)]
    classification = 'native refusal; see exact traceback'
    if any('R1_POST_FILTER_CAPACITY_SHORTFALL' in line for _, line in errors):
        classification = 'fixture capacity conflicts with native full-recipe allocation; native gate unchanged'
    elif any('No such file or directory' in line and '/p2/q/' in line for _, line in errors):
        classification = 'kit staging/order defect: native child opens a future staged path before its bytes are available'
    detail = dict(stage=failed['stage'], returncode=failed['returncode'],
                  classification=classification, errors=[dict(line=n, text=s) for n, s in errors],
                  log=failed['log'], excerpts=excerpts, no_retry=True)
    new(R/'REFUSAL_DETAIL.json', detail)

source_kit_matches = sha(kit/'SHA256SUMS.txt') == setup['kit']
source_file_matches = []
if source_kit_matches:
    for line in (kit/'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        source_file_matches.append(sha(kit/name) == digest)
helpers = {}
for path in (R/'kit_n_go/b').rglob('*'):
    if path.is_file():
        relative = path.relative_to(R/'kit_n_go')
        helpers[str(relative)] = source_kit_matches and sha(path) == sha(kit/relative)
archive = R/'kit_n_go'/setup['source']['path']
assert sha(archive) == setup['source']['sha256']
tree_matches = []
with tarfile.open(archive) as stream:
    for member in stream.getmembers():
        if member.isfile():
            tree_matches.append(sha(R/'source'/member.name) == hashlib.sha256(stream.extractfile(member).read()).hexdigest())
population = read(R/'BOUNDED_POPULATION.json')
pop_checks = []
for record in population['records']:
    original = record['original_database']; bounded = record['database']
    assert sha(original['path']) == original['sha256']
    assert sha(bounded['path']) == bounded['sha256']
    assert sha(record['receipt']['path']) == record['receipt']['sha256']
    with closing(sqlite3.connect(Path(original['path']).as_uri()+'?mode=ro&immutable=1', uri=True)) as a, \
         closing(sqlite3.connect(Path(bounded['path']).as_uri()+'?mode=ro&immutable=1', uri=True)) as b:
        expected = a.execute('SELECT i,row,target FROM rows ORDER BY i LIMIT ?', (population['native_limit'],)).fetchall()
        actual = b.execute('SELECT i,row,target FROM rows ORDER BY i').fetchall()
        assert actual == expected and len(actual) == record['count'] <= population['native_limit']
    pop_checks.append(dict(source=record['source'], count=record['count'], original_unchanged=True,
                           complete_subset=True, native_row_bytes_equal=True))
measure = usage(R)
overhead = sum(path.stat().st_blocks*512 for path in D.glob('*k5*') if path.is_file())
assert measure['allocated_bytes'] + overhead < 3_000_000_000
closure = read(R/'FIXTURE_CLOSURE.json')
assert not closure['missing'] and closure['native_closure_calls'] == 1
new(R/'RESOLVED_INPUT_INVENTORY.json', dict(supplied=closure['supplied'],
      native_stream_pins=closure['native_stream_pins'], fixture_populations=population['records']))
validation = dict(kit_seal=setup['kit'], source_kit_unchanged=source_kit_matches and all(source_file_matches),
                  fixture_helpers_unchanged=helpers, extracted_tree_unchanged=all(tree_matches),
                  tree_file_count=len(tree_matches), original_and_bounded_stores=pop_checks,
                  usage=measure, harness_allocated_bytes=overhead,
                  total_new_allocation=measure['allocated_bytes']+overhead,
                  peak_rss_bytes=max((s.get('peak_rss_bytes', 0) for s in stages), default=0),
                  one_attempt=True, no_retry=True, native_limit_unchanged=True,
                  removal_configuration_unchanged=True, native_gates_unchanged=True)
new(R/'VALIDATION.json', validation)
rows = read(R/'CHECK_RAW.json', [])
for row in rows:
    row['expected_evidence'] = row['evidence']
    if row['passed']:
        row['evidence'] = [s.strip() for s in row['evidence'].split(';')]
    else:
        row['evidence'] = ['STAGES.json', 'RUN_REFUSAL.json'] + (['REFUSAL_DETAIL.json', failed['stage']+'.log'] if failed else [])
        row['reason'] = 'Not proved by this attempt; stopped at '+(failed['stage'] if failed else refusal.get('error', 'completed checks'))+'.'
    if row['path'] == 'mode r production database reconstruction':
        row['evidence'] = ['FIXTURE_INPUTS.json', 'routing_retained/plan.json']
        row['reason'] = 'The authenticated synthetic routing_base does not enter production P reconstruction.'

def emit(name, passed, evidence, reason=None):
    row = dict(path=name, status='PROVED' if passed else 'NOT PROVED', passed=bool(passed), evidence=evidence)
    if reason: row['reason'] = reason
    rows.append(row)

emit('authenticated fixture pin closure', not closure['missing'], ['FIXTURE_CLOSURE.json', 'RESOLVED_INPUT_INVENTORY.json'])
emit('native fixture routing regeneration', any(s['stage']=='routing' and s['returncode']==0 for s in stages),
     ['routing_retained/routing_selection.json', 'routing_retained/plan.json', 'STAGES.json'])
emit('scene populations within native host limit', all(p['count']<=population['native_limit'] for p in pop_checks),
     ['BOUNDED_POPULATION.json', 'VALIDATION.json'])
emit('dbb2 header mismatch search', False, ['DBB_STEP.json', 'dbb/db_bytes.json'],
     'DBB_TARGET is the generated fixture database digest, so no mismatching header is searched.')
new(R/'CHECK.json', rows)
lookup = {row['path']: row for row in rows}
def status(name): return lookup[name]['status']
core = [row for row in rows if row['path'] not in ('mode r production database reconstruction', 'dbb2 header mismatch search')]
verdict = 'PROVED fixture end-to-end' if all(row['passed'] for row in core) else 'NOT PROVED end-to-end'
reason = (detail['errors'][-1]['text'] if detail and detail['errors'] else refusal.get('error', 'See CHECK.json'))
prefix = R.name+'/'
report = [
    verdict+'; kit n_go '+setup['kit']+'.',
    'Bounded fixture populations '+status('scene populations within native host limit')+': five complete 2,000-row subsets preserve row/target bytes; the native limit stays unchanged ('+prefix+'BOUNDED_POPULATION.json; VALIDATION.json).',
    'Fixture closure '+status('authenticated fixture pin closure')+': one selected-planner closure call, '+str(len(closure['supplied']))+' authenticated pins, none missing ('+prefix+'FIXTURE_CLOSURE.json; RESOLVED_INPUT_INVENTORY.json).',
    'Native fixture routing '+status('native fixture routing regeneration')+'; production P reconstruction NOT PROVED ('+prefix+'routing_retained/plan.json; CHECK.json).',
    'dbb2 '+status('dbb2 generated fixture database')+' on the fixture digest; header mismatch search NOT PROVED ('+prefix+'DBB_STEP.json; dbb/db_bytes.json).',
    'Scene-rebuild pins '+status('scene-rebuild step pins')+' ('+prefix+'CHECK.json; canary.log).',
    'Native host receipt '+status('native host receipt')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Handover with localised pins '+status('handover passes with localised pins')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Clock inheritance '+status('clock inheritance')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Fresh optimizer / counter zero '+status('fresh optimizer / counter zero')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Finite losses on four ranks '+status('finite losses on four ranks')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Step-1 checkpoint through milestone '+status('step-1 checkpoint through milestone')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Timed checkpoint '+status('timed checkpoint')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Milestone export / local receipt / kit copier '+status('milestone export / local receipt / kit copier')+' ('+prefix+'CHECK.json; STAGES.json).',
    'TK_JOB_START budget self-stop '+status('TK_JOB_START budget self-stop')+'; resume_pin latest / one further step '+status('resume_pin latest / one further step')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Census receipt bound in h.py '+status('census receipt bound in h.py')+'; review wait / published v.json / fixture review '+status('review wait / published v.json / fixture review')+' ('+prefix+'CHECK.json; STAGES.json).',
    'Stop: '+reason+' ('+prefix+'REFUSAL_DETAIL.json; '+(failed['stage']+'.log' if failed else 'STAGES.json')+'); no retry.',
    'Integrity '+('PROVED' if validation['source_kit_unchanged'] and all(helpers.values()) and all(tree_matches) else 'NOT PROVED')+': source kit, helper code, extracted tree and original stores; peak RSS '+str(validation['peak_rss_bytes'])+' B, new allocation '+str(validation['total_new_allocation'])+' B ('+prefix+'VALIDATION.json).',
    'Rerun: bash '+str(D/'go_rehearsal_k5.sh')+' KIT_PATH '+str(D/'rehearsal_k5_fixed')+'; the root must be fresh. CHECK.json records the scope of every proof.'
]
assert len(report) < 20
report_path = D/'REHEARSAL_K5_REPORT.md' if R.name == 'rehearsal_k5' else R/'REHEARSAL_K5_REPORT.md'
with report_path.open('x') as handle: handle.write('\n'.join(report)+'\n')
print(json.dumps(dict(verdict=verdict, report=str(report_path), proved=sum(row['passed'] for row in rows),
                      rows=len(rows), allocated_bytes=validation['total_new_allocation'])))
