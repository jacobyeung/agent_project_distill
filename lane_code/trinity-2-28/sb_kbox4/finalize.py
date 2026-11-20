"""Summarize verified dry-run results and blocked gates; package exact local artifacts."""
from collections import defaultdict
import difflib,hashlib,json,resource,tarfile,time
from pathlib import Path
import numpy as np
from adapters import ROOT,source_hashes
from box_math import CONSTANTS,mra,paired_bootstrap
from decisions import judge
OUT=ROOT/'out';L=OUT/'box_ladder'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    start=time.monotonic();dry=json.loads((OUT/'DRYRUN.json').read_text());pins=dict(dry['input_sha256'])
    names=['REPLAY_CHECK.json','REPLAY_DIAGNOSIS.json','DRYRUN_PARITY.json','PER_ITEM.jsonl','unit_tests.log','dryrun.log','replay_check.log','replay_diagnosis.log']
    pins.update({str(p):sha(p) for p in [OUT/'DRYRUN.json',ROOT/'pinned_train.json',ROOT/'train_boxes.json']+[L/n for n in names]})
    pins.update(source_hashes())
    for p in sorted(ROOT.glob('*.py'))+sorted((ROOT/'vendor').glob('*.py'))+[ROOT/'run.sh']:
        original=Path('/scratch/jjyeung/orch_n30/sb_kbox')/p.relative_to(ROOT)
        if original.is_file():pins[str(original)]=sha(original)
    def write(name,obj):
        (L/name).write_text(json.dumps(dict(obj,input_sha256=pins),indent=2,allow_nan=False)+'\n')
    items=[json.loads(line) for line in (L/'PER_ITEM.jsonl').read_text().splitlines()]
    by=defaultdict(list)
    for r in items:by[r['arm']].append(r)
    summary={a:dict(n=len(rs),rooms=len({r['room'] for r in rs}),mra=100*np.mean([mra(r['prediction'],r['label']) for r in rs]),versus_A0=paired_bootstrap(rs,by['A0_deployed']),versus_A2=paired_bootstrap(rs,by['A2_gt_masks'])) for a,rs in sorted(by.items())}
    geometry_increment=paired_bootstrap(by['A6_gtgeo_fused'],by['A6_gtgeo_single'])
    write('DRYRUN_SUMMARY.json',dict(scope='dry_run_only; no selection',arms=summary,gt_geometry_fusion_increment=geometry_increment,external_F32_aliases='MISSING: aliases not defined by available v1 specification'))
    diagnostics={}
    for arm,rs in by.items():
        objects={}
        for r in rs:
            for name,d in r['diagnostics'].items():objects[(r['capture'],name)]=d
        sizes=[d['size_mra'] for d in objects.values() if d['size_mra'] is not None]
        ratios=[d['size_ratio'] for d in objects.values() if d['size_ratio'] is not None]
        def group(fn):
            groups=defaultdict(list)
            for r in rs:groups[str(fn(r))].append(r)
            return {k:dict(n=len(v),mra=100*np.mean([mra(r['prediction'],r['label']) for r in v])) for k,v in groups.items()}
        diagnostics[arm]=dict(objects=len(objects),size_available=len(sizes),size_missing=len(objects)-len(sizes),size_mra=100*np.mean(sizes) if sizes else None,size_ratio_median=float(np.median(ratios)) if ratios else None,first_exact=np.mean([d['exact'] for d in objects.values()]),first_within_one=np.mean([d['within_one'] for d in objects.values()]),by_dataset=group(lambda r:r['dataset']),by_gap_band=group(lambda r:'under_1m' if r['label']<1 else '1_to_2m' if r['label']<2 else '2_to_4m' if r['label']<=4 else 'above_4m'),by_minimum_member_frames=group(lambda r:min(map(len,r['member_frames'].values()))))
    gathers={}
    for r in by['DRY_A4_gathered_best1']:
        for name,d in r['gather'].items():gathers[(r['capture'],name)]=d
    scored=[d for d in gathers.values() if d['correct'] is not None]
    gather=dict(objects=len(gathers),unmatched_seed_objects=sum(d['correct'] is None for d in gathers.values()),members_scored=sum(d['members'] for d in scored),correct=sum(d['correct'] for d in scored))
    gather['precision']=gather['correct']/gather['members_scored'] if gather['members_scored'] else None
    write('DIAGNOSTICS_DRY.json',dict(scope='dry_run_only',arms=diagnostics,gather=gather,objects=[dict(capture=c,name=n,**v) for (c,n),v in gathers.items()]))
    decisions=judge({})
    for name,d in decisions.items():d.update(train_estimate='MISSING',paired_ci95='MISSING',heldout_estimate='MISSING',reason='StageOne deployed-geometry replay gate failed: 4/5, below .95. No complete training pass.')
    write('DECISION.json',dict(bars=decisions,heldout_role='report-only; cannot affect any decision',choices_frozen=False))
    membership=json.loads((ROOT/'pinned_train.json').read_text())
    write('CONFIG.json',dict(constants=CONSTANTS,maximum_cpu_cores=8,nice=10,thread_environment=8,torch_threads=8,address_space_limit_kib=40000000,cuda_visible_devices='',interpreter='/scratch/jjyeung/envs/p1cpu/bin/python',counts=membership['counts'],spec='KIT_SPEC_box_ladder_k1.md plus SPEC_APPLIED.md',heldout='unopened; no evaluation',selector_training='NOT_RUN; blocked parity'))
    write('ROW_SETS.json',dict(train=membership['rows'],predicted_train=membership['predicted_rows'],counts=membership['counts'],heldout='NOT_READ; no row IDs inferred'))
    write('MISSING_ARMS.json',dict(status='MISSING',dry_arms=['A1_oracle_select','A5_gathered_oracle_seed','A8_selector_nonull'],full_train='MISSING',heldout='MISSING',reason='Deployed geometry changes linked candidate identity; the table labels cannot safely transfer by candidate ID alone. Required parity is 4/5, below .95.',missing_inputs=dry['missing_inputs'],missing_python_modules=[]))
    (L/'LADDER_TRAIN.txt').write_text('MISSING: all-arm dry-run gate failed (StageOne deployed/table choices 4/5 = 80%, required >=95%).\nPinned rows: 1037 / 192 rooms; predicted-mask subset 883 / 173 rooms. No complete pricing, rule selection, or five-fold selector fit.\n')
    (L/'LADDER_HELDOUT_once.txt').write_text('MISSING: held-out was not opened or evaluated. Training choices are not frozen because the required dry-run gate failed.\nThis file is a status artifact, not a held-out report or consumed held-out look.\n')
    code=sorted(ROOT.glob('*.py'))+sorted((ROOT/'vendor').glob('*.py'))+[ROOT/'run.sh']
    changes={}
    baseline=Path('/scratch/jjyeung/orch_n30/sb_kbox')
    for p in code:
        old=baseline/p.relative_to(ROOT);new=p.read_text().splitlines()
        spans=[]
        if old.exists():
            before=old.read_text().splitlines()
            for tag,i,j,k,l in difflib.SequenceMatcher(None,before,new).get_opcodes():
                if tag!='equal':spans.append(dict(operation=tag,old_lines=[i+1,j],new_lines=[k+1,l]))
        else:spans=[dict(operation='new_file',new_lines=[1,len(new)])]
        if spans:changes[str(p.relative_to(ROOT))]=spans
    write('EDITED_LINES.json',dict(files=changes,method='difflib against read-only copied sb_kbox source'))
    copied={str(p.relative_to(ROOT)):dict(sha256=sha(p),original_sha256=sha(baseline/p.relative_to(ROOT)),equal=sha(p)==sha(baseline/p.relative_to(ROOT))) for p in (ROOT/'vendor').glob('*.py')}
    write('SOURCE_VERIFICATION.json',dict(vendor=copied,remote_R1='MISSING: SSH prohibited; remote R1 bytes not available locally'))
    (L/'CODE_SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in code))
    rep=json.loads((L/'REPLAY_DIAGNOSIS.json').read_text())
    replay=json.loads((L/'REPLAY_CHECK.json').read_text())
    rows=[
      'The kit is BLOCKED: deployed StageOne matches 4/5 labelled-table choices (80%; required >=95%).',
      'No full training pricing, rule selection, selector fitting, or held-out evaluation ran. Every decision bar is MISSING.',
      'The ARKitScenes TV changes from table candidate tv:002 (four frames) to deployed tv:000 (five frames).',
      f'The deployed scale is {rep["gd_metadata"]["scale"]:.10f}; the table scale is {rep["table_scale"]:.10f}. The adapter reproduces both ARKitScenes table feature vectors exactly under the table geometry.',
      '',
      'Commands: `bash run.sh prepare.py`; `bash run.sh prepare_pinned.py`; `bash run.sh replay_check.py`; `bash run.sh diagnose_replay.py`.',
      'Pricing/checks: `bash run.sh dryrun.py > out/box_ladder/dryrun.log 2>&1`; `bash run.sh -m unittest -v test_box_math`.',
      'All means, paired bounds, denominators, diagnostics, and archive: `bash run.sh finalize.py`.',
      f'Dry run: {dry["seconds"]:.3f} seconds; peak RSS {dry["peak_rss_mib"]:.3f} MiB; CPU-only, nice 10, eight numerical threads.',
      f'Replay check: {replay["seconds"]:.3f} seconds / {replay["peak_rss_mib"]:.3f} MiB; diagnosis: {rep["seconds"]:.3f} seconds / {rep["peak_rss_mib"]:.3f} MiB.',
      'PRIMARY_296 pins 1,037 train distance rows / 192 rooms; raw-name tables cover 883 / 173 rooms. All primary train rasters exist.',
      f'The dry run prices {len(items)} records on four distance rows in two training rooms. It cannot choose a rule.',
      'Checks: stored-label S4 parity 4/4; copied-reader A0 row parity 4/4; single-frame fusion checks pass; GT fused answers 4/4; eight numerical and decision-boundary tests pass.',
      'Every MRA below uses corrected labels. Paired bootstrap: item-weighted, physical rooms, 10,000 draws, seed 20261119.',
      '',
      '| Dry arm | MRA | Delta vs A0 [paired 95%] | Delta vs A2 [paired 95%] |',
      '|---|---:|---|---|']
    for arm,s in summary.items():
        def fmt(d):return f'{d["estimate"]:+.2f} [{d["ci95"][0]:+.2f}, {d["ci95"][1]:+.2f}]'
        rows.append(f'| {arm} | {s["mra"]:.2f} | {fmt(s["versus_A0"])} | {fmt(s["versus_A2"])} |')
    rows += [f'GT-geometry fusion increment (A6 fused minus A6 single): {fmt(geometry_increment)}; this is distinct from either arm minus A2.',
             f'Dry gather precision: {gather["correct"]}/{gather["members_scored"]}; unmatched seed objects: {gather["unmatched_seed_objects"]}/{gather["objects"]}. Full diagnostics: DIAGNOSTICS_DRY.json.',
             '', '| Decision bar | Verdict | Train / paired bounds / held-out |','|---|---|---|']
    rows += [f'| {n} | MISSING | MISSING / MISSING / MISSING |' for n in decisions]
    rows += ['',
      'Deviations and limits:',
      '- V2 was absent when checked; SPEC_APPLIED.md lists all five required corrections. F32/F32_fused aliases are MISSING from v1; no alias mapping was invented.',
      '- Held-out is report-only. No early five-capture replay, held-out score gate, size gate, or external split was used.',
      '- A1/A5 labels are MISSING because candidate IDs can denote changed members under GD; A8 fitting is deferred behind the parity gate.',
      '- A4 and A7 dry outputs enumerate all fusion rules; no winner exists. The full coordinator remains unfinished behind the failed prerequisite.',
      '- Size uses the exact capture/instance audit join and full extents; unknown conventions remain MISSING. Basket is unknown in the ScanNet++ dry capture.',
      '- Gather seeds match only manifest-listed same-name GT instances; IoU ties use count, summed IoU, then instance ID. Unmatched seeds remain MISSING.',
      '- The expected top-level tree is MISSING; the harness-resolved b04host3 tree is used read-only. Remote R1 source equality is MISSING because SSH is prohibited.',
      '- Harness declarations are AST-loaded with workspace bindings; GTGeometry receives C=c2w for frame_count. Vendor bytes remain unchanged.',
      '- Mixed input containers were hashed and train records filtered. No held-out capture, cached output, raster, or table was evaluated.',
      '- No GPU, network, SSH, Git, tmux, process termination, external write, install, or deletion ran. Local tar transfer was omitted as required.',
      'Edited files and exact line spans: box_ladder/EDITED_LINES.json; executable/source hashes: box_ladder/CODE_SHA256SUMS.',
      'Input hashes accompany every output JSON and per-item record. Historical copied outputs are isolated in out/inherited and excluded from the archive.',
      'Archive: out/sb_kbox2.tar; SHA256: out/sb_kbox2.tar.sha256. No rasters, tower caches, or inherited archive is included.',
      'No borderline revision-history prose was kept.']
    assert len(rows)<=80,len(rows)
    (OUT/'REPORT.md').write_text('\n'.join(rows)+'\n')
    (ROOT/'STATUS.md').write_text(f'Final stage: BLOCKED by deployed StageOne/table parity of 4/5 (80%, required 95%). The CPU dry run priced {len(items)} records on four training rows; stored parity and A0 reader parity both pass 4/4. PRIMARY_296 fixes 1037 train rows / 192 rooms and a predicted subset of 883 / 173. No full training pricing, selector fit, rule selection, or held-out evaluation ran. out/REPORT.md, out/DRYRUN.json, and out/sb_kbox2.tar with SHA256 contain the evidence and exact missing stages.\n')
    write('FINALIZE_METRICS.json',dict(seconds=time.monotonic()-start,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,report_lines=len(rows)))
    files=code+[ROOT/n for n in ['KIT_SPEC_box_ladder_k1.md','SPEC_APPLIED.md','HEAD_ACCURACY_DESIGN_20261119.md','train_manifest.json','train_labels.json','pinned_train.json','train_boxes.json','STATUS.md']]+[OUT/'REPORT.md',OUT/'DRYRUN.json']+sorted(L.iterdir())
    with tarfile.open(OUT/'sb_kbox2.tar','w') as tar:
        for p in files:
            if p.is_file():tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    digest=sha(OUT/'sb_kbox2.tar');(OUT/'sb_kbox2.tar.sha256').write_text(digest+'  sb_kbox2.tar\n')
    print(json.dumps(dict(status='BLOCKED',records=len(items),report_lines=len(rows),sha256=digest)))
if __name__=='__main__':main()
