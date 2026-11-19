"""Write an honest blocked-stage report, provenance, and a small review archive."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import tarfile
from adapters import ROOT
from box_math import CONSTANTS, paired_bootstrap, mra
from decisions import judge

OUT=ROOT/'out';LADDER=OUT/'box_ladder'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    dry=json.loads((OUT/'DRYRUN.json').read_text())
    pins=dict(dry['input_sha256'])
    code=sorted(ROOT.glob('*.py'))+sorted((ROOT/'vendor').glob('*.py'))+[ROOT/'run.sh']
    pins.update({str(p):sha(p) for p in code})
    pins.update({str(p):sha(p) for p in [OUT/'DRYRUN.json',LADDER/'PER_ITEM.jsonl',LADDER/'unit_tests.log']})
    rows=[json.loads(line) for line in (LADDER/'PER_ITEM.jsonl').read_text().splitlines()]
    arms=defaultdict(list)
    for row in rows:arms[row['arm']].append(row)
    summary={a:dict(n=len(rs),rooms=len({r['room'] for r in rs}),
                    mra=100*sum(mra(r['prediction'],r['label']) for r in rs)/len(rs),
                    versus_A2=paired_bootstrap(rs,arms['A2_gt_masks'])) for a,rs in arms.items()}
    def output(name,obj):
        (LADDER/name).write_text(json.dumps(dict(obj,input_sha256=pins),indent=2,allow_nan=False)+'\n')
    output('DRYRUN_SUMMARY.json',dict(stage='dry_run_only_not_for_selection',arms=summary))
    bars=judge({})
    for bar in bars.values():
        bar.update(train_estimate=None,paired_ci95=None,heldout_estimate=None,
                   reason='All-arm dry run blocked; no full train decision or held-out evaluation.')
    text='{\n'+',\n'.join(json.dumps(name)+': '+json.dumps(dict(value,input_sha256=pins)) for name,value in bars.items())+'\n}\n'
    (LADDER/'DECISION.json').write_text(text)
    output('CONFIG.json',dict(constants=CONSTANTS,train_shards=4,maximum_cpu_cores=16,
        process_cpu_threads=1,memory_limit_kib=40000000,cuda_visible_devices='',
        selector=dict(seed=20261116,folds=5,epochs=15,hidden=32,name_mode='none',lr=.003,wd=.001,
                      target='uniform mass on positive candidates; no null; exclude no-positive objects from fit'),
        arms=dict(A0='raw SAM3, run_iso candidates_argmax, bestspread, GD',
                  A1='positive candidate; most frames on tie; A0 if none, GD',
                  A2='GT masks, bestspread, GD',A3='GT masks, five fusion rules, GD',
                  A4='A0 seed + gather; bestspread and train-winning fusion, GD',
                  A5='A1 seed + gather; train-winning fusion, GD',
                  A6='GT masks; bestspread and lift_plain; GT depth/pose',
                  A7='GT masks; bestspread and train-winning fusion; DA3/Pi3X',
                  A8='nonull OOF selector; bestspread and gathered train-winning fusion; GD'),
        heldout_gate='train decision fixed, code reviewed, then one evaluation; not authorized by passing time'))
    output('MISSING_ARMS.json',dict(status='MISSING',arms=['A0','A1','A4','A5','A8'],
        missing_python_modules=dry['missing_python_modules'],reason='Required environment lacks torch and safetensors',
        uncompleted=['full train coordinator','all-arm dry replay','nonull training execution',
                     'GT size-label join','full diagnostics aggregation','reviewed held-out pass']))
    (LADDER/'LADDER_TRAIN.txt').write_text('MISSING: full pricing was not started because the all-arm dry-run gate did not pass.\nNo fusion winner or train decision has been selected. See DRYRUN_SUMMARY.json for dry-run-only results.\n')
    (LADDER/'LADDER_HELDOUT_once.NOT_RUN.txt').write_text('MISSING: no fixed train decision and no reviewer code read.\nLADDER_HELDOUT_once.txt is deliberately absent; it is reserved for the single reviewed evaluation.\n')
    (LADDER/'CODE_SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in code))
    # Every vendor source remains exactly as copied, including hardcoded paths.
    src=json.loads((LADDER/'SOURCE_INPUTS.json').read_text())
    equal={name:sha(ROOT/'vendor'/name)==src['input_sha256'][path] for name,path in src['copied_sources'].items()}
    assert all(equal.values())
    output('SOURCE_VERIFICATION.json',dict(copied_files_byte_equal=equal,edited_lines=[],
        reader_reference_status='MISSING: R1 files on trinity-3-30 unavailable locally; no SSH permitted',
        expected_tree='/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449',
        resolved_tree='/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449'))
    lines=[
        'The kit is BLOCKED. The required Python lacks torch and safetensors, so the all-arm dry run did not pass.',
        'The package contains a tested GT dry-run runner and fixed-math kernels; full all-arm orchestration remains incomplete.',
        'No full train pass, selector fitting, train rule selection, or held-out evaluation ran.',
        '',
        'Commands: `bash run.sh dryrun.py > out/box_ladder/dryrun.log 2>&1`; `bash run.sh -m unittest -v test_box_math`.',
        'Command for all MRA/paired bounds below: `bash run.sh finalize.py` (reads dry-run PER_ITEM.jsonl).',
        f'Dry run: {dry["seconds"]:.3f} seconds; peak process RSS {dry["peak_rss_mib"]:.3f} MiB; CUDA disabled; one numerical thread.',
        'Six numerical unit tests passed. The dry run produced 68 records: 17 arms/variants on four rows in two physical rooms.',
        'Captures: arkitscenes/41048124 and scannetpp/036bce3393; all four stored S4+G1+bestspread rows match exactly.',
        'All five rules equal best1 on synthetic single-member data and eight real-object single-frame restrictions.',
        'GT fused geometry ran and answered all four rows. A0 parity and the >=95% StageOne choice test are MISSING.',
        '',
        'These dry-run numbers cannot select a rule. Bootstrap: paired shared rows, item weights, 10,000 room draws, seed 20261119.',
        '| Dry-run arm | MRA | Delta vs A2 | Paired 95% bounds |',
        '|---|---:|---:|---|',
    ]
    for a in ['A2_gt_masks','A3_gt_fused_vote2_best','A3_gt_fused_vote2','A3_gt_fused_allspread','A3_gt_fused_trim','A6_gtgeo_single','A6_gtgeo_fused']:
        s=summary[a];d=s['versus_A2'];lo,hi=d['ci95']
        lines.append(f'| {a} | {s["mra"]:.2f} | {d["estimate"]:+.2f} | [{lo:+.2f}, {hi:+.2f}] |')
    lines += ['', '| Decision bar | Verdict | Train estimate / paired bounds / held-out estimate |',
              '|---|---|---|']
    lines += [f'| {name} | MISSING | MISSING / MISSING / MISSING |' for name in bars]
    lines += [
        '',
        'Every deviation and limitation:',
        '- A0/A1/A4/A5/A8 were not executed; StageOne replay and selector training code are unvalidated because dependencies are absent.',
        '- A2/A3/A6 and all five DA3/Pi3X fusion variants ran only on the two dry captures. No A3 winner was chosen for A4/A5/A7/A8.',
        '- The full four-shard train coordinator is not implemented. The task forbids starting full pricing before the dry gate passes.',
        '- Size ratios/MRA are MISSING: the per-instance GT full-box join is unfinished; no dimension or half/full convention was guessed.',
        '- First-seen records use the specified 0.002 threshold, but the referenced B12 document was outside the allowed NFS reads.',
        '- Predicted member precision, gap-band/member-frame aggregation, and full-train diagnostics are unfinished.',
        '- The required early five-held-out replay conflicts with the task’s train-first discipline; it was deferred, not counted as passed.',
        '- Mixed manifest/label container bytes were read and hashed for filtering; only train records were decoded. No held-out record was decoded or priced.',
        '- The expected top-level tree is missing; the existing b04host3 mirror is the path resolved by lift_price.py and was used read-only.',
        '- R1 grounding.py/stage1.py byte equality cannot be checked: the remote trinity-3-30 source is unavailable locally and SSH is prohibited.',
        '- The NFS replay2.py archive and LANE_RULES.md were not opened; only the two prompt-named NFS documents were copied.',
        '- Replay uses the local StageOne producer and raw-name cache adapter; the archived replay was not substituted or claimed identical.',
        '- Source harness declarations are AST-loaded with workspace globals; inventory/startup audit/main are not executed. Tree files are unchanged.',
        '- GTGeometry receives C=c2w for the reader’s frame_count interface. Its lift arithmetic is unchanged.',
        '- Dry reference parity uses the stored S4 scale. Corrected labels score every reported MRA; stored labels appear only in exact parity evidence.',
        '- Fusion keeps original points in voted voxels; trim uses allspread box axes and 2nd/98th percentile extents. Equal gather overlaps use proposal index.',
        '- Nonull uses the fixed run_iso config and trainer seed 20261116; multiple positives get uniform CE mass. This choice was not fit to results.',
        '- No copied source line was edited: edited-line list is empty; SOURCE_VERIFICATION.json checks every copied source byte.',
        '- No GPU, SSH, network, Git, tmux, process termination, or external write was requested. The tar remains local as the task requires.',
        '- LADDER_HELDOUT_once.txt is reserved for the reviewed pass; its NOT_RUN companion records the missing stage.',
        '',
        'Exact missing GT inputs (33 manifest train rows; excluding them leaves the specified 1,037 rows / 192 rooms):',
    ]
    lines += ['- '+p for p in dry['missing_inputs']]
    lines += [
        'Expected tree: /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449 (MISSING).',
        'R1 reference: trinity-3-30:/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src (not locally available).',
        'Dependency location: /scratch/jjyeung/envs/planner_local_v1/bin/python cannot import torch or safetensors.',
        'All inputs for each JSON are SHA256-pinned; source hashes, per-item provenance, exact parity rows, and logs are in out/box_ladder/.',
        'Archive: out/sb_kbox.tar; checksum: out/sb_kbox.tar.sha256. It contains code, configs and reports, without rasters or tower caches.',
    ]
    assert len(lines)<=80,len(lines)
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'STATUS.md').write_text('Final stage: Packaged a BLOCKED partial kit in out/sb_kbox.tar. Available CPU dry checks matched 4/4 stored GT-reference rows, answered 4/4 GT-fused rows, and passed six numerical tests. The required environment lacks torch and safetensors, so A0/selector validation and the full all-arm driver remain incomplete; every decision bar is MISSING. No full train or held-out pass ran. See out/REPORT.md and out/DRYRUN.json.\n')
    paths=code+[ROOT/'STATUS.md',ROOT/'KIT_SPEC_box_ladder_k1.md',ROOT/'HEAD_ACCURACY_DESIGN_20261119.md',OUT/'REPORT.md',OUT/'DRYRUN.json']
    paths+=sorted(p for p in LADDER.iterdir() if p.is_file())
    with tarfile.open(OUT/'sb_kbox.tar','w') as tar:
        for p in sorted(set(paths)):
            tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    digest=sha(OUT/'sb_kbox.tar')
    (OUT/'sb_kbox.tar.sha256').write_text(digest+'  sb_kbox.tar\n')
    print(json.dumps(dict(report_lines=len(lines),archive_bytes=(OUT/'sb_kbox.tar').stat().st_size,sha256=digest)))


if __name__=='__main__':main()
