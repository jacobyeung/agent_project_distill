"""Write the concise current report, validate pins and package the inventory."""
import hashlib, json, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def pin(path): return dict(path=str(path),sha256=sha(path))

report = ROOT/'out/FULL_INVENTORY.json'
d = json.loads(report.read_text()); s = d['slices']['camera_wording']; f = s['frames']
lines = (ROOT/'work/inputs/full_inventory_five.md').read_text().splitlines()
for i, line in enumerate(lines):
    if line.startswith('FULL native routing inventory:'):
        lines[i] = 'FULL native routing inventory: NOT READY. All six slices are inventoried; camera has zero five-pin hits, but 21 rows lack independent scene evidence. Recovery/units contain K1 hits; upstream and frame-host dependencies remain incomplete.'
    elif line.startswith('Counts come from'):
        lines[i] = 'Commands: run `work/inventory.py` and `work/run_audits.py` for the five slices; `work/camera_inventory.py` computes every camera count, SHA256, raw binding, scene/frame set, overlap, lineage/extent check and native dry result. Use `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B`. The exact camera checker command is in `work/audits_native/camera_wording/audit.json`.'
    elif line.startswith('| `/scratch/jjyeung/orch_n30/sb_rowA2'):
        lines[i] = f"| `{s['source']['path']}`; SHA `{s['source']['sha256']}`; 6,000 rows/bindings; {s['source_bytes']:,} bytes; 120 cells × 50; 6,000 distinct admitted parents; wording/ID-only changes verified | {s['scene_count']} scenes; archived map covers 5,979 rows. 21 rows at `d2/vfc2c241f2978` lack independent evidence; tier C is insufficient. Checker resolves 6,000, zero hits on all five pins | {f['references']:,} references / {f['unique_scene_ordinals']:,} requests; {f['overlap_with_other_five']:,} overlap, {f['additional_requests']:,} additional. {f['unique_claimed_png_paths']:,} explicit `/data2/kr9c` PNG pins; physical count/bytes/stage=MISSING. Extent pin `c072905b`: 0 QID entries, 0 required rows; current camera predicate is exempt. `work/envelopes/camera_wording.json` is NOT_ADMISSIBLE. |"
    elif line.startswith('| Coverage |'):
        lines[i] = line.replace('All five coverage files are produced', 'The five complete coverage files and 5,979 camera entries are produced').replace('not row canonical claims. |', 'not row canonical claims. Camera missing entries fail closed. |')
    elif line.startswith('| RGB metadata |'):
        lines[i] = line.replace('Map/plan missing;', 'Five slices need missing map/plan; camera already carries RGB metadata;')
    elif line.startswith('| Full host / first failures |'):
        lines[i] = '| Full host / first failures | Every draft with limit=None fails `r2_intake.py:42`: Local slices must contain at most 2000 rows per family. With 2000, all six fail upstream MISSING at `r2_intake.py:58`→`p3_provenance.py:46`. Camera coverage is incomplete despite passing the global coverage-file binding; row checks are not reached. No hostname or function substitution. |'
    elif line.startswith('The five slices share'):
        lines[i] = f"The five slices share 56,640 distinct scene/ordinal requests; camera adds {f['additional_requests']:,}, making {f['union_all_six']:,} across six. Camera provides {f['unique_claimed_png_paths']:,} path/hash pins under `/data2/kr9c`; they are source claims, not current byte verification. The other five need map `17aa3e9e` and plan `7cc01f36` at the exact `/scratch/fsw/.../8865619b/k/` paths in JSON. Physical cross-root overlap and total bytes=MISSING."
    elif line.startswith('The frame host must hold'):
        lines[i] = line.replace('under mapped `/data2/k6tk`', 'under mapped `/data2/k6tk` and `/data2/kr9c`')
    elif line.startswith('| 2 this lane'):
        lines[i] = f'| 2 this lane — done | 29,886 digest(raw) bindings; six five-pin audits and envelope dry checks; five complete coverage files and one partial camera file. Camera metadata/lineage/dry work: {s["seconds"]:.2f}s measured; the five-slice timings remain in JSON. |'
    elif line.startswith('| 3 main |'):
        lines[i] = '| 3 main | Supply independently authenticated evidence for `d2/vfc2c241f2978` at camera scene_coverage entries, plus pinned map/plan for the other five and current RGB byte/staging receipts. No map-extension or stage-receipt source path was supplied. Metadata join estimate: 1–3 min once inputs exist; availability wait MISSING. |'
    elif line.startswith('| 4 tree_rebuild + main |'):
        lines[i] = '| 4 tree_rebuild + main | Add `camera_wording` explicitly to `r1_coverage.source_names`; adding a source key alone is ignored. Bind six-family row_sources/staging/catalog/routing_inputs, camera wording/lineage authorities, compatible upstream receipts and exact extent pin; bind request/config and reseal. Metadata checks 1–5 min; engineering estimate 15–30 min. |'
    elif line.startswith('Estimates assume'):
        lines[i] = 'Estimates assume ≤8 CPU threads and local inputs. No transfers, RGB reads, GPU, network, launcher, tmux, Git, foreign writes or deletions occurred. No borderline revision-history sentence is retained.'
lines += ['', f"Camera delivery archive `{s['source_archive']['path']}` verifies as `{s['source_archive']['sha256']}`; six relevant members match loose files. `SOURCE_AUDIT.json` supports admitted-source lineage but lacks the exact seven-role exclusions/counts schema required by `r2_exclusions.upstream`; compatible receipt pins remain MISSING. Camera omits optional external frame-map/plan/FPS fields because every row embeds those values.",
    'Packaging command: run the same CPU prefix with `work/package_fullinv2.py`. It checks all current workspace pins, six envelopes, coverage/cardinality, frame overlap arithmetic and archive member hashes, then writes `out/sb_fullinv2.tar.sha256`.']
assert len(lines) <= 75
(ROOT/'out/FULL_INVENTORY.md').write_text('\n'.join(lines)+'\n')

checked = {}
def check_pins(v):
    if isinstance(v,dict):
        if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str) and v['sha256']!='MISSING':
            p = Path(v['path'])
            if p.is_relative_to(ROOT):
                if str(p) not in checked: checked[str(p)] = sha(p)
                assert checked[str(p)] == v['sha256'], str(p)
        for item in v.values(): check_pins(item)
    elif isinstance(v,list):
        for item in v: check_pins(item)
check_pins(d)
count = 0
for name, item in d['slices'].items():
    env = json.loads(Path(item['draft_envelope']['path']).read_text())
    assert env['required_exclusion_pins'] == d['exclusion_pins']
    assert env['extent_receipt']['sha256'].startswith('c072905b')
    assert len(env['row_bindings']) == item['rows'] == env['count']; count += item['rows']
    cov = json.loads(Path(env['scene_coverage']['path']).read_text())
    assert set(cov['rows']) == set(env['row_bindings'])
    assert cov['rows_sha256'] == env['rows']['sha256'] and cov['exclusions'] == env['exclusions']
    audit = json.loads(Path(item['exclusions']['audit']['path']).read_text())
    assert audit['tree'] == '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1'
    assert audit['complete'] and audit['rows'] == item['rows']
    assert item['dry_validation'][0]['location']['line'] == 42
    assert any(t['function']=='intake' and t['line']==58 for t in item['dry_validation'][1]['stack'])
    if name == 'camera_wording':
        assert not cov['complete'] and len(cov['missing_qids']) == 21
        assert sum(v['status']=='known' for v in cov['rows'].values()) == 5979
        assert not any(audit['hits'].values())
        assert item['extent']['required_rows']==item['extent']['qid_entries']==0
        assert item['extent']['check_returns']==6000
        assert env['upstream_receipts']=='MISSING' and env['prefiltered'] is True
        assert not any(k in env for k in ('frame_map','frame_plan','fps_authority'))
    else:
        assert cov['complete'] and not item['catalog_missing_qids'] and not item['extent']['missing_qids']
        assert not item['existing_removal_coverage']['unremoved_K1_qids']
assert count == 29886
assert f['unique_scene_ordinals']-f['overlap_with_other_five']==f['additional_requests']
assert f['union_all_six']==56640+f['additional_requests']
validation = dict(schema='fullinv2-package-validation-v1',status='PASS',inventory_admissible=False,
    checked_workspace_pins=len(checked), rows=count, envelopes=6,report_lines=len(lines),
    checks=['Current workspace pin consistency','Six row/binding/source cardinalities','Five complete independent map coverages and honest 21-row camera gap',
        'Real selected-tree checker and five pins','Six actual intake first failures','Camera extent exemption is not a geometry proof',
        'Frame overlap set arithmetic','Existing K1 removal coverage'],
    command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= /scratch/jjyeung/envs/p1cpu/bin/python -B work/package_fullinv2.py',
    inputs={str(p):dict(sha256=sha(p)) for p in [report,ROOT/'out/FULL_INVENTORY.md',Path(__file__)]})
vp=ROOT/'out/PACKAGE_VALIDATION.json';vp.write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n')
(ROOT/'STATUS.md').write_text(f'The six-slice FULL inventory is packaged as out/sb_fullinv2.tar with a SHA256 sidecar. Camera contributes 6,000 rows with zero five-pin hits, {s["scene_count"]} scenes and {f["unique_scene_ordinals"]:,} scene/ordinal requests; {f["additional_requests"]:,} are additional to the other five. Independent scene evidence remains MISSING for 21 rows; upstream receipts, physical staging and tree-owner sixth-family integration remain required. The {len(lines)}-line report, JSON ledger, native dry results and package validation state these limits.\n')
members=[ROOT/'STATUS.md',ROOT/'out/FULL_INVENTORY.md',report,vp]
members += [p for p in (ROOT/'work').rglob('*') if p.is_file() and 'audits' not in p.relative_to(ROOT/'work').parts and '__pycache__' not in p.parts and p.suffix!='.log']
members=sorted(set(members))
manifest=dict(schema='fullinv2-package-manifest-v1',members={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in members},
    inputs={str(p):dict(sha256=sha(p)) for p in [report,Path(__file__)]})
mp=ROOT/'out/PACKAGE_MANIFEST.json';mp.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');members.append(mp)
archive=ROOT/'out/sb_fullinv2.tar'
with tarfile.open(archive,'w') as t:
    for p in members:t.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
with tarfile.open(archive,'r') as t:
    for member in t:
        h=hashlib.sha256();handle=t.extractfile(member)
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
        expected=sha(mp) if member.name=='out/PACKAGE_MANIFEST.json' else manifest['members'][member.name]['sha256']
        assert h.hexdigest()==expected,member.name
archive_sha=sha(archive)
(ROOT/'out/sb_fullinv2.tar.sha256').write_text(archive_sha+'  out/sb_fullinv2.tar\n')
print(json.dumps(dict(status='PASS',archive=str(archive),sha256=archive_sha,bytes=archive.stat().st_size,members=len(members),report_lines=len(lines))))
