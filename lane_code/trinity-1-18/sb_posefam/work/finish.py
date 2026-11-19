"""Render the evidence, validate its scope, and package reproducible local inputs."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

result=json.loads((OUT/'POSEFAM.json').read_text())
assert result['inputs']['proof_script']['sha256']==sha(ROOT/'work/prove.py'), 'Proof output is stale'
mix=result['N_pose_receipt']['sha256']
a2,a3=[s['database']['sha256'] for s in result['sources']]
bench=result['filters']['benchmark']['sha256']
dev=result['filters']['dev']['sha256']
command=result['command']
python=command.split('nice -n 10 ',1)[1].split(' -B ',1)[0]
finish_command='OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 '+python+' -B work/finish.py'
record=f'''N's pose binding is `ap/8865619b/k/8957d119.json`, SHA256 `{mix}`.
Its source-index order is a2v3 (`{a2}`), then a3v2 (`{a3}`); source receipt hashes are recorded in POSEFAM.json.
Sealed build 20 (`780ca7b4`) applies BENCH v2 (`{bench}`) and dev (`{dev}`) through `carrier_c1_run.prepare` and `s1_exclusions.apply`.
N's unchanged scene-filter code rejects all 23 raw a2v3 qids on venue 381879: 12 on d3/41159526 and 11 on d3/41159521; every row matches BENCH v2, with zero survivors.
The proof uses the complete source scene projections and independently verifies each capture's BENCH token and venue membership; POSEFAM.json lists every qid and drop reason.
N's exact admitted-order SHA256 is **MISSING**: the full raw SQLite frame/target payloads and an N-bound production order were not recovered, so the complete preparation cannot be replayed.
The source-wide scene-filter order is an upper bound, and the available build-21 capacity order binds different stores; neither supplies the missing hash.
The BENCH room aliases and reserve checks cover pose, but the separate K1/R0 room-authority audit does not certify all raw pose rows.
P's receipt already omits these 23 before its final scene filter; P's order is not N's order. This paragraph proves their exclusion under N's mandatory filter and leaves the complete `data_rows_r2` record MISSING.
Reproduce the proof from this workspace with `{command}`; render, validate and package with `{finish_command}`.
'''
(OUT/'RECORD_TEXT_data_rows_r2.md').write_text(record)
report=f'''The 23 venue-381879 qids cannot pass N's mandatory BENCH filter. The exact N admitted-order hash remains MISSING.
This is a complete exclusion proof for those qids, but it does not close the entire data_rows_r2 record.

Evidence binds sealed build 20 `{result['tree_sha256']}` and config `{result['N_config_sha256']}`.
Build 21 carried the inherited build-20 seal when inspected; its discovered capacity fixture is a different population.
The copied code files match their entries in TREE_SEAL.json; execution imports only workspace copies.

Code path (paths are relative to `work/code/`, with original sealed line numbers):
- `student_pilot/carrier_c1_run.py`, `prepare`, 464–505: load filters and pose mix; `prepare_exclusions`, 481–483, defers scene matches to the final filter.
- `student_pilot/c1_pose_mix.py`, `_row_selected`, 66–73, and `prepare`, 123–238: dense/frame-prefix selection, division validation, legacy exclusions, then source-index order.
- `student_pilot/carrier_c1_run.py`, `prepare`, 619–624: apply BENCH/dev scene exclusions to every stream, including pose.
- `student_pilot/s1_exclusions.py`, `Exclusions`, 42–128, `selection`, 191–224, and `apply`, 334–345: filter pose sources and write `pose_scene_order.json` while preserving order.

The pose receipt is `{mix}`; its sources pin a2v3 `{a2}` and a3v2 `{a3}`.
Source receipt `30612832` agrees with P's rc3 SHA256SUMS.txt; the a3v2 receipt is `1e7b491b`.
BENCH v2 is `{bench}`; N's dev list is `{dev}`.

The CPU scan covers all 66,934 a2v3 and 203,520 a3v2 projected rows (270,454 total).
All 23 target qids reject on BENCH alone: 12 on d3/41159526 and 11 on d3/41159521; no target matches dev or the reserve rule on its projection.
Each target token is independently minted from its capture and checked against BENCH membership and EVAL_ROOMS venue381879.
The independent scene census matches N's filter counts for both sources.
On the full projected sources, BENCH drops 5,039 / 22,160 rows and dev drops 5,618 / 13,440 rows, with zero overlap.
The 224,197 survivors form only a scene-filter upper bound; its native-array SHA256 is `{result['raw_scene_only_upper_bound']['sha256']}`.
Its filename explicitly says `raw_scene_filter_upper_bound_order.txt`; no production preparation receipt is fabricated.

P's authenticated mix/admitted orders contain 229,924 / 194,987 rows and zero target qids in either order.
Thus the 23 were already absent before P's final scene filter; P's broad BENCH drop count is not their removal count.
Applying N's final scene rule to P's preselection gives 185,667 rows, SHA256 `{result['P_control']['replay']['sha256']}`.
That conditional replay differs from P's order and cannot establish N's initial selection.
The build-21 capacity fixture admits 16,000 rows and joins to zero target qids, but its pose receipt is `d548daf8` and its databases differ from a2v3/a3v2.

Room-rule scope: BENCH physical groups and explicit capture tokens apply to pose (`s1_exclusions.py:74–104`); ScanNet room prefixes are also inferred.
The scene filter does not infer arbitrary ARKit capture-to-venue links. These two captures have explicit BENCH tokens, so their rejection needs no inferred mapping.
`carrier_c1_run.excluded_row:340–348` invokes the reserve rule; `Rows.row:1104–1128` rechecks it for r1_training.
The separate `r1_rooms.Rooms.admit` call is in routing `compose:53–90`; `r1_rooms.verify_audit/census:86–175` covers routing slices and VQA, not all pose rows.

MISSING: full raw `ap/f02f16ad/s/a2v3/rows.sqlite` and `ap/f02f16ad/s/a3v2/rows.sqlite`; exact production/recovery paths and receipt hashes are in POSEFAM.json.
MISSING: N-bound `{result['missing'][-1]['expected_order']}` and its preparation receipt; the inherited output path alone is not authentication.
Scene projections omit the dense-row targets, frame-prefix paths, and full-row reserve fields. The first actual removal stage and exact N order therefore remain MISSING.
The copied preparation code proves a mandatory final rejection for every target even if an earlier stage would remove it.

Commands (run from `/scratch/jjyeung/orch_n30/sb_posefam`):
`python3 work/stage.py` snapshots the inputs and verifies each copied code hash against the seal.
`{command}` produces every row count, qid join, order hash, filter census and missing-input result above.
`{finish_command}` checks the result and line limits, writes VALIDATION.json, and packages/verifies every archived member.
`sha256sum -c out/sb_posefam.tar.sha256` checks the deliverable archive; FILES.sha256 covers its members.
The archive contains the report, record paragraph, per-qid proof, copied source, input snapshots, commands, and explicitly scoped derived orders.
No borderline chronology sentence was retained. No BLOCKER.md was required: no target survives the mandatory filter.
'''
(OUT/'REPORT.md').write_text(report)
assert len(record.splitlines())<=15
assert len(report.splitlines())<=50
assert result['counts']['target_rows']==23 and result['counts']['target_survivors']==0
targets=result['targets']
assert len({t['qid'] for t in targets})==23
assert all(t['final_filter_matches']=={'benchmark':True,'dev':False} for t in targets)
assert all(t['drop_reason']=='BENCH_v2_final_scene_filter' and not t['admitted'] for t in targets)
assert result['exact_N_admitted_order']['sha256']=='MISSING'
assert result['fixture_join']['target_qid_matches']==[]
for order in [result['raw_scene_only_upper_bound'],result['P_control']['replay']]:
    path=ROOT/order['path'];assert sha(path)==order['sha256']
    pairs=json.loads(path.read_text());assert len(pairs)==order['count']
    assert not set(map(tuple,pairs))&{(t['source'],t['raw_index']) for t in targets}
for pin in result['inputs'].values():
    if pin.get('snapshot'):assert sha(ROOT/pin['snapshot'])==pin['sha256']
validation_inputs=[OUT/'POSEFAM.json',OUT/'REPORT.md',OUT/'RECORD_TEXT_data_rows_r2.md',Path(__file__),
                   ROOT/'work/prove.py',ROOT/'work/stage.py',ROOT/'work/SNAPSHOT.json']
validation=dict(schema='sb-posefam-validation-v1',status='PASS_WITH_EXACT_N_ORDER_MISSING',
    command=finish_command,inputs={str(p.relative_to(ROOT)):sha(p) for p in validation_inputs},
    report_lines=len(report.splitlines()),record_lines=len(record.splitlines()),
    checks=['23 distinct qids; BENCH true and dev false for each',
            'No target survives either explicitly scoped derived order',
            'Copied evidence hashes match proof inputs',
            'Exact N order remains MISSING', 'Foreign fixture join is empty'],
    scope='Validation of the mandatory exclusion proof; not validation of a recovered N production order.')
(OUT/'VALIDATION.json').write_text(json.dumps(validation,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Stage 4 complete: The CPU proof rejects all 23 venue-381879 qids under N’s sealed BENCH rule. REPORT.md, RECORD_TEXT_data_rows_r2.md, POSEFAM.json, and validation preserve the exact N order as MISSING because the full raw SQLite payloads are unavailable. The source-only order and P replay are explicitly scoped; all input hashes and qid reasons are recorded. The package and its SHA256 sidecar are complete and archive-member validation passes.\n')
paths=[ROOT/'STATUS.md',ROOT/'work/stage.py',ROOT/'work/prove.py',ROOT/'work/finish.py',
       ROOT/'work/SNAPSHOT.json',ROOT/'work/build_files.txt',ROOT/'work/other_candidates.txt',ROOT/'work/prove.log']
paths+=sorted(p for p in (ROOT/'work/inputs').iterdir() if p.is_file())
paths+=sorted(p for p in (ROOT/'work/code/student_pilot').iterdir() if p.is_file())
paths += [OUT/name for name in ('REPORT.md','RECORD_TEXT_data_rows_r2.md','POSEFAM.json','VALIDATION.json',
                               'raw_scene_filter_upper_bound_order.txt','P_order_under_N_scene_filter.txt')]
paths=sorted(set(paths))
manifest={str(p.relative_to(ROOT)):sha(p) for p in paths}
(OUT/'FILES.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in manifest.items()))
archive=OUT/'sb_posefam.tar'
with tarfile.open(archive,'w') as tar:
    for p in paths+[OUT/'FILES.sha256']:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
with tarfile.open(archive,'r') as tar:
    assert len(tar.getmembers())==len(paths)+1
    for member in tar:
        assert member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts
        expected=manifest.get(member.name,sha(OUT/'FILES.sha256'))
        h=hashlib.sha256()
        f=tar.extractfile(member)
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
        assert h.hexdigest()==expected, member.name
digest=sha(archive)
(OUT/'sb_posefam.tar.sha256').write_text(digest+'  out/sb_posefam.tar\n')
print(json.dumps(dict(archive_sha256=digest,bytes=archive.stat().st_size,members=len(paths)+1,
                      report_lines=len(report.splitlines()),record_lines=len(record.splitlines()),
                      validation=validation['status']),indent=2))
