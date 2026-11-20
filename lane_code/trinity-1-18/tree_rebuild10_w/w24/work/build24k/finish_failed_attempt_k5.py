"""Report retained k5 evidence; execute no rehearsal stage."""
from pathlib import Path
import hashlib
import json
import sys
import tarfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rehearsal_paths_k5 import D, R
from rehearsal_inputs_k5a import usage

def read(path): return json.loads(Path(path).read_text())
def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''): digest.update(block)
    return digest.hexdigest()
def new(path, value):
    with Path(path).open('x') as handle: json.dump(value, handle, indent=2); handle.write('\n')

setup = read(R/'SETUP.json')
kit = Path(setup['kit_dir'])
assert sha(kit/'SHA256SUMS.txt') == setup['kit']
for line in (kit/'SHA256SUMS.txt').read_text().splitlines():
    digest, name = line.split('  ', 1)
    assert sha(kit/name) == digest, name
helpers = []
for path in (R/'kit_n_go/b').rglob('*'):
    if path.is_file():
        relative = path.relative_to(R/'kit_n_go')
        assert sha(path) == sha(kit/relative)
        helpers.append(str(relative))
archive = R/'kit_n_go'/setup['source']['path']
assert sha(archive) == setup['source']['sha256']
tree_files = 0
with tarfile.open(archive) as stream:
    for member in stream.getmembers():
        if member.isfile():
            assert sha(R/'source'/member.name) == hashlib.sha256(stream.extractfile(member).read()).hexdigest()
            tree_files += 1
layout = read(R/'INPUT_LAYOUT.json')
for digest, record in layout['stores'].items(): assert sha(record['path']) == digest
closure = read(R/'FIXTURE_CLOSURE.json')
assert not closure['missing'] and closure['native_closure_calls'] == 1
stages = read(R/'STAGES.json')
assert [(s['stage'], s['returncode']) for s in stages] == [('routing',0),('dbb2',0),('canary',1)]
scene = read(R/'p2/i/sc.json')
error = 'Local metadata slices must contain at most 2000 rows per family'
lines = (R/'canary.log').read_text().splitlines()
error_line = next(i+1 for i, line in enumerate(lines) if line == 'ValueError: '+error)
camera = scene['spec']['sources']['camera']
assert camera['count'] == 16000 and camera['rows']['sha256'].startswith('38e7f9c5')
assert not (R/'BOUNDED_POPULATION.json').exists()
validation = read(R/'harness_validation/RESULT.json')
assert validation['status'] == 'PASS'
reason = 'The executed builder omitted the bound_population call; the authenticated planner still received the original fixture stores.'
new(R/'HARNESS_REFUSAL.json', dict(classification='harness wiring error', reason=reason,
    native_error=error, canary_log_line=error_line, camera=camera,
    executed_builder=dict(path=str(D/'make_rehearsal_k5.py'),sha256=sha(D/'make_rehearsal_k5.py')),
    corrected_builder=dict(path=str(D/'make_rehearsal_k5a.py'),sha256=sha(D/'make_rehearsal_k5a.py')),
    corrected_launcher=str(D/'go_rehearsal_k5a.sh'), corrected_rehearsal_run=False,
    no_retry=True, kit_defect_proved=False,
    post_run_checks='Only fixture construction, native bounded reads and static harness wiring were checked.'))
capacity = dict(native_source='source/student_pilot/r1_mix.py', source_sha256=sha(R/'source/student_pilot/r1_mix.py'),
    required_steps=1000, maximum_draws_per_row=4,
    quota_per_step=dict(pose=64,vqa=128,routing=64,pointing=32),
    minimum_rows=dict(pose=16000,vqa=32000,routing=16000,pointing=8000),
    bounded_fixture_rows=dict(pose=4000,vqa=2000,routing=2000,pointing=2000),
    gate='R1_POST_FILTER_CAPACITY_SHORTFALL',
    finding='Complete bounded stream subsets cannot satisfy unchanged native full-recipe allocation.',
    source_lines='r1_mix.py:10,25-26,30-40; r1_population.py:154',
    observed_in_rehearsal=False, evidence_kind='source-code arithmetic, not a second run')
new(R/'CAPACITY_CONSTRAINT.json', capacity)
new(R/'RESOLVED_INPUT_INVENTORY.json', dict(supplied=closure['supplied'], native_stream_pins=closure['native_stream_pins']))
measure = usage(R)
overhead = sum(p.stat().st_blocks*512 for p in D.glob('*k5*') if p.is_file())
assert measure['allocated_bytes'] + overhead < 3_000_000_000
new(R/'VALIDATION.json', dict(source_kit_verified=True, kit_seal=setup['kit'],
    fixture_helpers_unchanged=helpers, tree_files_unchanged=tree_files,
    five_original_store_hashes_verified=True, usage=measure, harness_allocated_bytes=overhead,
    total_new_allocation=measure['allocated_bytes']+overhead,
    peak_rss_bytes=max(s['peak_rss_bytes'] for s in stages),
    attempts=1, retries=0, fixture_validation_is_not_a_rehearsal=True,
    no_native_gate_changes=True, no_source_kit_changes=True,
    corrected_launcher_rehearsal_verified=False))
raw_path = R/'CHECK_RAW.json' if (R/'CHECK_RAW.json').exists() else R/'CHECK.json'
rows = read(raw_path)
new(R/'CHECK_EXECUTED.json', rows)
for row in rows:
    row['expected_evidence'] = row['evidence']
    if row['passed']:
        row['evidence'] = ['DBB_STEP.json','dbb/db_bytes.json','dbb2.log']
    else:
        row['evidence'] = ['STAGES.json','HARNESS_REFUSAL.json','canary.log:'+str(error_line)]
        row['reason'] = 'Not reached: '+reason
    if row['path'] == 'mode r production database reconstruction':
        row['evidence'] = ['routing_retained/plan.json','FIXTURE_INPUTS.json']
        row['reason'] = 'Synthetic routing_base does not exercise production P reconstruction.'
def emit(name, passed, evidence, explanation):
    rows.append(dict(path=name, status='PROVED' if passed else 'NOT PROVED', passed=passed,
                     evidence=evidence, reason=explanation))
emit('authenticated fixture pin closure', True, ['FIXTURE_CLOSURE.json','RESOLVED_INPUT_INVENTORY.json'], 'The executed fixture closure supplied every required pin.')
emit('native fixture routing regeneration', True, ['routing_retained/routing_selection.json','STAGES.json'], 'The single routing stage exited zero.')
emit('scene populations within native host limit in rehearsal', False, ['p2/i/sc.json','HARNESS_REFUSAL.json'], 'The executed builder did not invoke the new population helper.')
emit('corrected fixture native bounded-reader validation', True, ['harness_validation/RESULT.json','harness_validation/BOUNDED_POPULATION.json'], 'All five new 2,000-row subsets passed unchanged native rows() on Trinity; no scene stage or planner closure was rerun.')
emit('dbb2 header mismatch search', False, ['DBB_STEP.json','dbb/db_bytes.json'], 'DBB_TARGET equalled the fixture database digest; no mismatching header was searched.')
# CHECK.json belongs to this fresh attempt; retain its raw bytes separately above.
(R/'CHECK.json').write_text(json.dumps(rows,indent=2)+'\n')
report = [
    'NOT PROVED end-to-end; kit n_go '+setup['kit']+'; tree C '+setup['source']['tree_sha256']+'.',
    'Harness error: make_rehearsal_k5.py omitted the bounded-population call, so the run supplied the original stores (rehearsal_k5/HARNESS_REFUSAL.json).',
    'Fixture closure PROVED: one native closure call, 13 stream pins and '+str(len(closure['supplied']))+' authenticated inputs, none missing (rehearsal_k5/FIXTURE_CLOSURE.json).',
    'Native fixture routing PROVED; production P reconstruction NOT PROVED (rehearsal_k5/routing_retained/plan.json; STAGES.json).',
    'dbb2 PROVED on the fixture database digest; header mismatch search NOT PROVED (rehearsal_k5/DBB_STEP.json; dbb/db_bytes.json).',
    'Scene-rebuild pins NOT PROVED: camera count 16,000 exceeds the unchanged 2,000-row limit; canary.log:'+str(error_line)+' records the native refusal (rehearsal_k5/p2/i/sc.json).',
    'Native host receipt NOT PROVED: admission was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'Handover with localised pins NOT PROVED: admission was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'Clock inheritance NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'Fresh optimizer / counter zero NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'Finite losses on four ranks NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'Step-1 checkpoint through milestone NOT PROVED; timed checkpoint NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'Milestone export / local receipt / kit copier NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'TK_JOB_START budget self-stop NOT PROVED; resume_pin latest / one further step NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'Census receipt bound in h.py NOT PROVED; review wait / published v.json / fixture review NOT PROVED: publication was not reached (rehearsal_k5/CHECK.json; STAGES.json).',
    'Corrected fixture-reader check PROVED: five complete 2,000-row subsets preserve row/target bytes and pass native rows() on Trinity; no rehearsal stage was rerun (rehearsal_k5/harness_validation/RESULT.json).',
    'Rerun artifact: go_rehearsal_k5a.sh KIT_PATH FRESH_ROOT takes a fresh build24k/rehearsal_k5* root; its wiring is checked, its rehearsal is NOT PROVED. go_rehearsal_k5.sh preserves the failed launcher.',
    'Full admission remains constrained: the unchanged sampler needs 32,000 VQA rows, exceeding a complete 2,000-row fixture; this is source-derived, not a measured second refusal (rehearsal_k5/CAPACITY_CONSTRAINT.json).',
    'One attempt, no retry; no kit defect established. Source kit, helpers, tree and original stores verify unchanged; peak RSS '+str(max(s['peak_rss_bytes'] for s in stages))+' B; new allocation '+str(measure['allocated_bytes']+overhead)+' B (rehearsal_k5/VALIDATION.json).'
]
assert len(report) < 20
with (D/'REHEARSAL_K5_REPORT.md').open('x') as handle: handle.write('\n'.join(report)+'\n')
print(json.dumps(dict(report=str(D/'REHEARSAL_K5_REPORT.md'), rows=len(rows), proved=sum(r['passed'] for r in rows), allocated_bytes=measure['allocated_bytes']+overhead)))
