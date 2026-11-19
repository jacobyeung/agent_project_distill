"""Inventory camera metadata on local disk; never read RGB or change the tree."""
import collections, copy, gzip, hashlib, json, os, resource, sys, tarfile, time, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/scratch/jjyeung/orch_n30/sb_rowA/out')
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1')
CHECK = Path('/scratch/jjyeung/orch_n30/sb_auditfix2')
resource.setrlimit(resource.RLIMIT_AS, (36 * 1024**3, 36 * 1024**3))
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE))
from student_pilot.p3_provenance import digest
from student_pilot.r2_intake import intake
from student_pilot.r2_adapters import normalize
from student_pilot.extent_receipt import Extents, required
from student_pilot.r1_coverage import source_names

CMD = 'nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B work/camera_inventory.py'
start = time.monotonic()
inputs = {}
def pin(path):
    p = Path(path).absolute()
    assert str(p).startswith(str(ROOT)) or str(p).startswith('/scratch/')
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    inputs[str(p)] = dict(sha256=h.hexdigest(), bytes=p.stat().st_size)
    return dict(path=str(p), sha256=h.hexdigest())
def load(path):
    pin(path)
    return json.loads(Path(path).read_text())
def write(path, data):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    data['inputs'] = dict(inputs)
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    return pin(p)
def status(text): (ROOT/'STATUS.md').write_text(text+'\n')
def norm(s): return s.replace('scannetppv2/', 'scannetpp/')

baseline = ROOT/'work/inputs/full_inventory_five.json'
baseline.parent.mkdir(parents=True, exist_ok=True)
if not baseline.exists(): baseline.write_bytes((ROOT/'out/FULL_INVENTORY.json').read_bytes())
md_baseline = ROOT/'work/inputs/full_inventory_five.md'
if not md_baseline.exists(): md_baseline.write_bytes((ROOT/'out/FULL_INVENTORY.md').read_bytes())
d = load(baseline)
pin(md_baseline)
pin(__file__)
docs = {name: load(SOURCE/name) for name in ('DELIVERABLES.json', 'SOURCE_AUDIT.json', 'INDEPENDENT_TRAINING_CHECK.json', 'CHECKS.json')}
for name in ('REPORT.md', 'HANDOFF_cont_ops18.md'): pin(SOURCE/name)
archive_pin = pin(SOURCE/'sb_rowA.tar')
assert archive_pin['sha256'].startswith('6e0fb408')
source = pin(SOURCE/'CAMERA_ROWS.jsonl')
assert source['sha256'] == docs['DELIVERABLES.json']['files']['out/CAMERA_ROWS.jsonl']['sha256']
archive_members = {}
with tarfile.open(SOURCE/'sb_rowA.tar') as archive:
    for name in ('CAMERA_ROWS.jsonl', 'CAMERA_LINEAGE.jsonl', 'CAMERA_SOURCES.jsonl.gz', 'REPORT.md', 'HANDOFF_cont_ops18.md', 'DELIVERABLES.json'):
        member = 'out/'+name
        f = archive.extractfile(member)
        h = hashlib.sha256()
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
        assert h.hexdigest() == pin(SOURCE/name)['sha256'], member
        archive_members[member] = h.hexdigest()
audit_path = ROOT/'work/audits_native/camera_wording/audit.json'
audit = load(audit_path)
assert audit['rows'] == 6000 and audit['complete'] and not any(audit['hits'].values())
assert audit['inputs'][source['path']]['sha256'] == source['sha256']
for p in d['exclusion_pins'].values():
    assert pin(p['path']) == p
    assert audit['inputs'][p['path']]['sha256'] == p['sha256']
inputs.update(audit['inputs'])
map_pin = pin(ROOT/'work/archived_alias_map.raw')
assert map_pin['sha256'] == '488480ab4b7f352eba9c81e99313c8bfcc247e9cc463a11620be087a42f579cf'
archived = load(map_pin['path'])
authority = load(CHECK/'inputs/lists/authority_aliases.raw')
tiered = load(CHECK/'inputs/lists/TIERED_ALIAS_MAP.raw')
base_env = load(ROOT/'work/envelopes/recovery.json')
extent = load(base_env['extent_receipt']['path'])
extents = Extents(base_env['extent_receipt'])
catalog_path = TREE.parent/'build21/inputs/source_membership.json'
catalog = load(catalog_path)
specs = load(TREE.parent/'build21/inputs/row_sources.json')
names = list(source_names(specs))
assert 'camera_wording' not in source_names({**specs, 'camera_wording': {'source': source}})
for name in ('r1_coverage', 'r1_routing', 'r2_intake', 'r2_exclusions', 'r2_adapters', 'r2_contract', 'extent_receipt', 'p3_provenance'):
    pin(TREE/'student_pilot'/f'{name}.py')

lineage_pin = pin(SOURCE/'CAMERA_LINEAGE.jsonl')
with (SOURCE/'CAMERA_LINEAGE.jsonl').open() as f: lineage = {r['qid']: r for r in map(json.loads, f)}
source_records_pin = pin(SOURCE/'CAMERA_SOURCES.jsonl.gz')
with gzip.open(SOURCE/'CAMERA_SOURCES.jsonl.gz', 'rt') as f: parents = {r['i']: r for r in map(json.loads, f)}
admission_pin = pin(SOURCE/'SOURCE_ADMISSION.jsonl')
with (SOURCE/'SOURCE_ADMISSION.jsonl').open() as f: admission = {r['i']: r for r in map(json.loads, f)}
binds, coverage, scenes, tokens, requests, unique_frames = {}, {}, collections.Counter(), collections.Counter(), [], {}
keys, missing, conflicts, cells, source_ids = set(), [], [], collections.Counter(), set()
extent_required, extent_entries, extent_checks = 0, 0, 0
map_rows, authority_rows, frame_refs = 0, 0, 0
with (SOURCE/'CAMERA_ROWS.jsonl').open() as f:
    for raw in map(json.loads, f):
        q = raw['qid']; assert q not in binds
        binds[q] = digest(raw)
        lin = lineage[q]; parent_record = parents[lin['source_i']]
        assert lin['source_i'] not in source_ids
        source_ids.add(lin['source_i'])
        assert hashlib.sha256(parent_record['row'].encode()).hexdigest() == lin['source_row_sha256']
        assert hashlib.sha256(parent_record['target'].encode()).hexdigest() == lin['source_target_sha256']
        adm = admission[lin['source_i']]
        assert adm['keep'] and not adm['reasons'] and adm['row_sha256'] == lin['source_row_sha256']
        parent = json.loads(parent_record['row'])
        assert parent['qid'] == lin['source_qid']
        child = copy.deepcopy(raw)
        child['qid'] = parent['qid']; child['routing']['qid'] = parent['routing']['qid']
        child['student_input']['question'] = parent['student_input']['question']
        child.pop('candidate_id'); child['routing'].pop('candidate_id')
        assert child == parent, q
        kind = raw['routing']['question_type']; cells[kind+'|'+lin['wording_id']] += 1
        token = raw['dataset']+'/'+raw['scene']; claim = norm(raw['routing']['canonical'])
        assert claim == norm(lin['canonical']) == norm(adm['canonical'])
        scenes[claim] += 1; tokens[token] += 1
        independent = archived.get(token); evidence = map_pin
        if independent: map_rows += 1
        elif token in authority:
            independent = authority[token]; evidence = pin(CHECK/'inputs/lists/authority_aliases.raw'); authority_rows += 1
        if independent and norm(independent) != claim:
            conflicts.append(q); independent = None
        if independent:
            coverage[q] = dict(status='known', names=sorted({token, independent}), evidence=evidence)
        else:
            missing.append(q)
            coverage[q] = dict(status='MISSING', names='MISSING', evidence='MISSING', scene_token=token,
                               reason='Absent from pinned archived map and authority aliases; tier C candidate does not establish independent provenance.')
        si = raw['student_input']; indices = si['frame_indices']; frames = si['frames']
        assert len(indices) == len(frames) == 32 and len(set(indices)) == 32
        frame_refs += len(indices)
        keys.update((token, i) for i in indices)
        for i, frame in zip(indices, frames):
            k = (token, i)
            if k in unique_frames: assert unique_frames[k] == frame
            unique_frames[k] = frame
        requests.append(dict(qid=q, scene_token=token, indices=indices, frames=frames))
        normalized = normalize(raw)
        extent_required += int(required(normalized, 'routing'))
        extent_entries += int(q in extent['rows'])
        extents.check(normalized, 'routing'); extent_checks += 1
assert len(binds) == len(lineage) == len(parents) == len(source_ids) == 6000
assert len(cells) == 120 and set(cells.values()) == {50}
other_keys = set(); other_frames = {}
for name, item in d['slices'].items():
    if name == 'camera_wording': continue
    fp = item['frames']['request_inventory']; frame_doc = load(fp['path']); assert pin(fp['path']) == fp
    ks = {(r['scene_token'], i) for r in frame_doc['rows'] for i in r['indices']}
    other_keys.update(ks); other_frames[name] = len(keys & ks)
assert len(other_keys) == 56640
status(f'The camera metadata binds 6,000 rows and 120 cells. The checker resolves all rows with zero five-pin hits. The archived map covers {map_rows} rows; {len(missing)} lack independent scene evidence. Frame requests and extent applicability are computed; the draft envelope and native dry checks remain.')

bp = write('work/bindings/camera_wording.json', dict(source=source, count=len(binds), row_bindings=binds, command=CMD))
cp = write('work/coverage/camera_wording.json', dict(rows_sha256=source['sha256'], exclusions=base_env['exclusions'], rows=coverage,
    complete=not missing, missing_qids=missing, conflicting_qids=conflicts, command=CMD,
    scope='Independent archived map membership; unproven tier C claims remain MISSING. No raster verification.'))
fp = write('work/frames/camera_wording.json', dict(source=source, rows=requests, frame_references=frame_refs,
    unique_scene_ordinal_requests=len(keys), unique_claimed_png_paths=len({p['path'] for p in unique_frames.values()}),
    unique_claimed_png_hashes=len({p['sha256'] for p in unique_frames.values()}), overlap_with_other_five=len(keys & other_keys),
    additional_requests=len(keys-other_keys), union_all_six=len(keys|other_keys), overlap_by_slice=other_frames,
    physical_verified_count='MISSING', total_rgb_bytes='MISSING', frame_host_stage_receipt='MISSING', command=CMD,
    scope='Paths/hashes are carried by source rows under /data2/kr9c. Logical overlap does not prove equality to the other five slices PNGs; their map/plan are missing.'))
lineage_result = write('work/camera_lineage_check.json', dict(command=CMD, source=source, lineage=lineage_pin,
    source_records=source_records_pin, admission=admission_pin, rows=6000, distinct_sources=len(source_ids),
    cells=dict(sorted(cells.items())), exact_wording_and_identifier_only_changes=6000,
    raw_source_text_hash_matches=6000, admitted_source_decisions=6000,
    archive=archive_pin, verified_archive_members=archive_members,
    scope='Rechecked delivered parent TEXT, lineage and keep decisions; did not rerun upstream geometry or original-store extraction.'))
env = {k: base_env[k] for k in ('schema','stream','trace_contract','validator_sha256','exclusions','dev_scene_exclusions','withheld_rooms','extent_receipt','required_exclusion_pins')}
env.update(family='camera_wording', count=6000, rows=source, row_bindings=binds, scene_coverage=cp,
    prefiltered=True, upstream_receipts='MISSING', draft_status='NOT_ADMISSIBLE', exclusion_audit=pin(audit_path),
    missing_notes={'upstream_receipts':'MISSING: tree owner must supply an r2_exclusions.upstream-compatible authenticated receipt list at the final manifest upstream_receipts pins. SOURCE_AUDIT.json has different accounting fields and no exact seven-role exclusions binding.',
    'scene_coverage':f'MISSING for {len(missing)} QIDs; see the pinned coverage artifact.',
    'family':'Proposed camera_wording integration key; absent from source_names and source catalog. Tree owner must add and reseal.',
    'frame_host_stage_receipt':'MISSING: expected in final frame-host preparation evidence; producer has not specified its path.'},
    frame_metadata_mode='Embedded student_input frames, indices, timestamps, fps and total_num_frames; optional external frame_map/frame_plan/fps_authority omitted.',
    mix_cells={q: lineage[q]['type']+'|'+lineage[q]['wording_id'] for q in binds})
ep = write('work/envelopes/camera_wording.json', env)
dry = []
for limit in (None, 2000):
    try:
        items, report = intake(ep['path'], limit=limit)
        dry.append(dict(limit=limit, status='RETURNED', admitted=len(items), report=report))
    except Exception as error:
        tb = traceback.extract_tb(error.__traceback__)
        dry.append(dict(limit=limit, status='REFUSED', exception=type(error).__name__, message=str(error),
            location=dict(file=tb[-1].filename,line=tb[-1].lineno),
            stack=[dict(file=x.filename, line=x.lineno, function=x.name) for x in tb]))
dp = write('work/camera_dry_validation.json', dict(command=CMD, envelope=ep, results=dry,
    scope='Unmodified intake on Trinity; no bypasses, synthetic upstream receipts or frame reads. Local first failure does not validate per-row coverage.'))
missing_tokens = sorted({coverage[q]['scene_token'] for q in missing})
integration = dict(owner='tree_rebuild / tree owner', source_names=names,
    adding_camera_key_alone_is_ignored=True,
    required='Explicitly admit camera_wording in r1_coverage.source_names; authenticate camera source/wording/lineage pins without weakening the paired V2H rules. Bind matching row_sources, staged row_slice_inputs, routing_inputs and an exact six-family source_membership catalog. Resolve independent scene coverage and genuine upstream receipts, preserve cfg.extent_receipt equality, bind request/config and reseal the tree. Stage /data2/kr9c pins and audit retained frames. Camera-specific held-out wording authority must be integrated; the eight-template V2H authority is not the 24-template camera authority.',
    source_names_evidence=pin(TREE/'student_pilot/r1_coverage.py'), composition_evidence=pin(TREE/'student_pilot/r1_routing.py'))
s = dict(status='INVENTORIED_NOT_ADMISSIBLE', source=source, source_bytes=inputs[source['path']]['bytes'],
    source_archive=archive_pin, rows=6000, row_bindings_count=6000, row_bindings=bp, duplicate_qids=0,
    scene_count=len(scenes), scenes_claimed=dict(sorted(scenes.items())), scene_tokens=dict(sorted(tokens.items())),
    lineage_check=lineage_result, cells=120, rows_per_cell=50, distinct_sources=6000,
    catalog_status='MISSING: camera_wording is absent from '+str(catalog_path),
    catalog_missing_qids=sorted(binds),
    independent_coverage=dict(receipt=cp, complete=not missing, missing_qids=missing, conflicting_qids=conflicts,
        missing_tokens=missing_tokens, counts=dict(archived_original_alias_map_rows=map_rows,authority_aliases_rows=authority_rows),
        tiered_candidates={t:tiered['aliases'].get(t,'MISSING') for t in missing_tokens},
        missing_input='Independent provenance binding for '+', '.join(missing_tokens)+'; expected as witnessed entries in scene_coverage.rows in '+cp['path']+'. No independently authenticated map extension path was supplied.'),
    frames=dict(request_inventory=fp, references=frame_refs, unique_scene_ordinals=len(keys),
        overlap_with_other_five=len(keys&other_keys), additional_requests=len(keys-other_keys), union_all_six=len(keys|other_keys),
        unique_claimed_png_paths=len({p['path'] for p in unique_frames.values()}), unique_claimed_png_hashes=len({p['sha256'] for p in unique_frames.values()}),
        physical_count='MISSING', bytes='MISSING', remote_staged_count='MISSING', remote_stage_receipt='MISSING', logical_store='/data2/kr9c',
        external_metadata_required=False, metadata_scope='Embedded source pins; exact overlap of physical PNGs with other slices remains MISSING.'),
    exclusions=dict(audit=pin(audit_path), status=audit['status'], complete=audit['complete'], hits=audit['hits'], all_five_zero=True,
                    checker_tiers=audit['coverage_by_tier'], independent_scene_proof_is_separate=True),
    extent=dict(pin=base_env['extent_receipt'], qid_entries=extent_entries, required_rows=extent_required,
        check_returns=extent_checks, binding_status='Exact configured receipt pin; no camera QID entries. Native required() exempts these camera types and no not_seen flag is present.',
        normalized_content_validation='NOT_APPLICABLE under current extent predicate; successful no-op checks are not geometry evidence.'),
    draft_envelope=ep, dry_validation=dry, dry_validation_artifact=dp, integration=integration,
    seconds=time.monotonic()-start, command=CMD)
sp = write('work/CAMERA_INVENTORY.json', s)
d['slices']['camera_wording'] = s
d['frame_host'].update(unique_scene_ordinals_all_six=len(keys|other_keys), camera_additional_requests=len(keys-other_keys),
    camera_overlap_with_other_five=len(keys&other_keys), camera_frame_root='/data2/kr9c', camera_requests=fp)
d['production_ranked'][1].update(produce='29,886 digest(raw) bindings, five complete and one partial independent coverage files, six drafts, native dry checks and six five-pin exclusion audits.', basis=d['production_ranked'][1]['basis']+[sp])
d['production_ranked'][2].update(produce='Supply independent scene evidence for the camera missing token, pinned map/plan for the other five slices, and current frame-store byte/staging receipts for /data2/k6tk and /data2/kr9c.', cpu_estimate='Metadata join estimate 1-3 minutes once inputs exist; availability wait MISSING.', basis=[sp])
d['production_ranked'][3]['produce'] = integration['required']+' Authenticate compatible upstream accounting for all families.'
d['production_ranked'][5]['produce'] = f'Stage and audit {len(keys|other_keys):,} distinct scene/ordinal requests across six slices. Camera provides explicit /data2/kr9c pins; the other five need map/plan joins. Physical union count/bytes remain MISSING.'
d['timing']['camera_inventory_seconds_measured'] = s['seconds']
d['timing']['command_camera'] = CMD
d['command_camera'] = CMD
d['camera_inventory_artifact'] = sp
d['inputs'].update(inputs)
(ROOT/'out/FULL_INVENTORY.json').write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
status(f'The camera inventory and envelope are complete as drafts. All 6,000 rows pass the five-pin checker; independent coverage is missing for {len(missing)} rows. Native dry validation preserves the full-host veto and fails locally on MISSING upstream receipts. The camera requests {len(keys):,} scene/ordinals, overlaps {len(keys&other_keys):,} of the five-slice union and adds {len(keys-other_keys):,}. Packaging and report validation remain.')
print(json.dumps({k:s[k] for k in ('rows','source','scene_count','seconds')}))
print(json.dumps(dict(map_rows=map_rows,missing=len(missing),missing_tokens=missing_tokens,frames=s['frames'],extent=s['extent'],dry=dry)))
