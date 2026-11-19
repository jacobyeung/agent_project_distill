"""Price the frozen scale options without rescoring any evaluation inputs."""
import os
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'): os.environ[k]='8'
import sys
sys.dont_write_bytecode=True
import ast,json,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'out'
SCORER=Path('/scratch/jjyeung/orch_n30/trin_read/kit_src/reader/evaluator/evalpath/official.py')
COMMAND='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/finish_report.py'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def dump(p,v): Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def fmt(v): return f"{v['mra']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]"
def delta(v): return f"{v['points']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}]"
def scaled(v,weight): return dict(points=v['points']*weight,ci95=[x*weight for x in v['ci95']])
def zero(): return dict(points=0.,ci95=[0.,0.])
def main():
    if (OUT/'SCALE_DRIFT.json').exists() or (OUT/'SCALE_DRIFT_REPORT.md').exists(): raise RuntimeError('Refuse existing final report')
    r=read(OUT/'ITEMS12.json'); b=read(OUT/'BARS_FROZEN.json')
    groups={}
    for n in ast.parse(SCORER.read_text()).body:
        if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('VSI_PRIMARY_GROUPS','VSTI_PRIMARY_GROUPS'):
            groups[n.targets[0].id]=ast.literal_eval(n.value)
    assert len(groups['VSTI_PRIMARY_GROUPS'])==5 and groups['VSTI_PRIMARY_GROUPS']['camera_displacement']==['camera_displacement']
    assert len(groups['VSI_PRIMARY_GROUPS'])==8 and groups['VSI_PRIMARY_GROUPS']['object_abs_distance']==['object_abs_distance']
    weights={'displacement':1/5,'distance':1/8}
    prices={}
    for arm in ('A','G','D'):
        prices[arm]={}
        for kind,weight in weights.items():
            data=r[kind]
            rows=[]
            for name,v in [(x['name'],x['all']) for x in data['folds']]+[('combined',data['combined']['all'])]:
                d=zero() if arm=='A' else v['paired_differences'][arm+'-A']
                rows.append(dict(fold=name,mra=v['arms'][arm]['mra'],mra_ci95=v['arms'][arm]['ci95'],paired_vs_A=d,benchmark_contribution_delta=scaled(d,weight)))
            prices[arm][kind]=rows
    options=[
      dict(option='a: frozen donor544',status='PRICED',price_arm='A',reason='Same depth outputs and FoV inputs reproduce arm A exactly; this prevents later head drift but does not establish a gain over N init.',
        tree='Add an immutable scale donor with its own frozen private visual features and donor pose FoV conditioner; live point-depth training may continue for other callers.',
        export='Bundle or reference donor544 weights, private-visual and FoV dependencies, preprocessing, scale rule, and SHA-256 pins separately from live heads.',
        reader='Select the pinned donor only for tower-arm scale; use the same scalar once on tower pose translations and routed G3T depth. Re-read every tower baseline under this rule before any N export.'),
      dict(option='a: frozen donor400',status='MISSING',price_arm=None,reason='Step400 K1 own depth is absent. The donor reproduces N init scale, whose paired price is unknown.',
        tree='Same frozen-donor path as donor544, with step400 dependencies.',export='Pin the complete step400 donor dependency closure.',reader='Use the pinned donor400; re-read tower baselines if the rule changes.'),
      dict(option='b: freeze point-depth training and FoV inputs',status='MISSING',price_arm=None,reason='Serving equals N init = R1 step400 head only if depth weights, private visual inputs, FoV conditioner, preprocessing and query layout remain invariant. Freezing weights alone is insufficient.',
        tree='Exclude point-depth weights from optimizer updates and freeze its FoV-producing path; use fixed private visual features. Set modules to deterministic evaluation behavior where required.',
        export='Record frozen head and FoV dependency hashes at N init and boundary; include an identical-output check.',
        reader='Keep existing OwnDepthScale arithmetic. If the contract and dependency sources are unchanged, a training freeze alone does not change the serving rule; any new FoV/donor source requires baseline re-reading.'),
      dict(option='c: global calibration alone',status='PRICED_AT_544_ONLY',price_arm='G',reason='One fit-half room-balanced factor applied to live own scale; does not prevent subsequent head drift.',
        tree='Multiply OwnDepthScale output by pinned global c; preserve confidence mask and validity filter.',export='Pin c, fit-room identities, donor/live head identity, and scale-rule version.',reader='Apply c once to shared pose/depth scalar; re-read all tower baselines.'),
      dict(option='c: dataset calibration alone',status='PRICED_AT_544_ONLY',price_arm='D',reason='One factor per known dataset; deployment needs a legitimate dataset identity and an explicit unknown-dataset policy.',
        tree='Lookup a pinned c by receipt-backed dataset identity; refuse unknown identities until a policy is priced.',export='Pin factors, fit-room identities, dataset mapping and rule version.',reader='Apply dataset c once to shared scale and re-read all tower baselines; K1 dataset codes are not pose-stream source mappings.'),
      dict(option='c: global calibration on donor544',status='PRICED',price_arm='G',reason='Exactly the G price while donor544 supplies identical depth and FoV inputs.',tree='Compose donor544 with one fixed c.',export='Pin both donor closure and c.',reader='Re-read every tower baseline under the composed rule.'),
      dict(option='c: dataset calibration on donor544',status='PRICED',price_arm='D',reason='Exactly the D price with the same identity requirements.',tree='Compose donor544 and dataset lookup.',export='Pin donor closure, factors and mapping.',reader='Re-read every tower baseline under the composed rule.'),
      dict(option='c: calibration on donor400 or frozen N init',status='MISSING',price_arm=None,reason='Factors and gains at step544 cannot be transferred as measured step400 prices.',tree='Fit factors using step400 train predictions on these folds.',export='Pin step400 donor, factors and fit provenance.',reader='Re-read baselines if the scale rule changes.'),
      dict(option='d: remove or reweight a biased depth source',status='MISSING',price_arm=None,reason='All four source target-depth comparisons and dataset mappings are missing. K1 depth/pose inconsistency cannot identify a training source or price causal retraining.',
        tree='After source identification, change its depth-loss sampling/weight only in a controlled training comparison.',export='Pin training-source receipts, weights, training recipe and resulting head.',reader='Compare exported candidates under one serving pin; if a new scale rule is introduced, re-read baselines first.'),
      dict(option='e: pinned learned scale head',status='REJECTED',price_arm=None,reason='The user supplies a 9.3-point loss; no local K1 training prediction here supports reversal. That loss is not re-scored or represented as a K1 measurement.',
        tree='No change recommended.',export='Keep its existing pin out of the recommended scale path.',reader='Do not substitute it; require K1 training predictions and paired intervals before reconsideration.')]
    missing_tests=[
      dict(input='step400 K1 own depth',settles=['donor400','freeze-training level','step400 calibration'],gpu_hours=1.04,gpu_hours_status='Planning estimate from sb_scale1; plus staging and model load, device unverified.',
       test='Use NEEDS_INPUTS.json capture and RGB pins: 242 train captures, 32 anchors each, frozen private visual depth path conditioned on matching pose FoV. Save 32x51x51 metre depth and checkpoint/capture/code receipts. No G3T or SAM forward. Score both frozen folds in a fresh output directory.',
       expected_output='Paths are specified per capture in /scratch/jjyeung/orch_n30/sb_scale1/out/NEEDS_INPUTS.json; no existing local step400 weights path is claimed.'),
      dict(input='three missing K1 GT archives',settles=['complete 242-capture coverage'],gpu_hours=0.,test='Supply the exact GT archives and hashes listed in ITEMS12.json missing; rerun in a fresh frozen experiment.',expected_output=[x['expected'] for x in r['missing']]),
      dict(input='pose-stream targets and source identities',settles=['four source depth ratios','dataset mapping','candidate biased source'],gpu_hours=0.,gpu_hours_status='CPU if matching G3T and pose labels are supplied; otherwise G3T forward cost MISSING, requires measured pilot and row count.',
       test='Stage receipt-pinned rows.sqlite for a2v3 and a3v2, an explicit dataset mapping receipt, and matched frame/intrinsic/pose/G3T pins. Use legal training rows only. Compare target-depth-implied G3T scale against pose-length scale on the same frames.',
       expected_output={k:v['expected_target_database'] for k,v in r['pose_stream']['sources'].items()}),
      dict(input='frozen donor or training-freeze implementation invariance',settles=['serving equals donor/init across N boundaries'],gpu_hours='MISSING',gpu_hours_status='No new forward for CPU cached-grid identity test; model output invariance needs the implemented tree and measured pilot. A full cached-grid pass can use the 1.04 GPU-h planning estimate per checkpoint.',
       test='Compare depth/FoV/output hashes on fixed train captures before and after optimizer updates; verify optimizer exclusion and immutable donor inputs. Assert exactly one scale multiplication on translations and routed depth.'),
      dict(input='source-removal causal price',settles=['option d MRA gain'],gpu_hours='MISSING',gpu_hours_status='Requires source evidence, training recipe and measured training throughput; 1.04 GPU-h own forward per resulting checkpoint is an additional estimate.',
       test='Run matched-control retraining with identical initial checkpoint, schedule and seeds, altering only identified depth-source weight; evaluate with the same room folds and paired bootstrap.'),
      dict(input='learned-head K1 train predictions',settles=['possible rejection reversal'],gpu_hours='MISSING',gpu_hours_status='CPU scoring costs 0 GPU-h if predictions exist; a new model forward needs a pilot because no matching runner timing is established.',
       test='Supply pinned per-capture scale outputs and valid export/input receipts for K1 train. Require CI-positive paired gain over A in both halves and combined, plus no supported distance harm.')]
    final=dict(schema='sb-scale2-final-v1',input_sha256={**r['input_sha256'],str(OUT/'ITEMS12.json'):sha(OUT/'ITEMS12.json'),str(OUT/'ITEMS12.md'):sha(OUT/'ITEMS12.md'),str(Path(__file__)):sha(__file__),str(SCORER):sha(SCORER),str(OUT/'IMPLEMENTATION_FIX.json'):sha(OUT/'IMPLEMENTATION_FIX.json'),str(OUT/'BARS_FROZEN_pre_refusal_fix.json'):sha(OUT/'BARS_FROZEN_pre_refusal_fix.json')},
      command=COMMAND,scoring_command=r['command'],prices=prices,options=options,missing_tests=missing_tests,
      conversion=dict(source=str(SCORER),source_sha256=sha(SCORER),groups=groups,weights=weights,
       interpretation='Mechanical contribution projection: displacement delta/5 for VSTI; object absolute-distance delta/8 for VSI, all other tasks fixed. These are separate benchmark projections, not measured benchmark gains; K1 room-balanced all-pairs/GT-mask populations differ from official benchmark question populations.'),
      recommendation='Keep N first-boundary comparisons on the existing serving pin. Complete the 1.04 GPU-h step400 K1 own forward before claiming a donor/freezing benefit. Do not use dataset calibration or remove a source without its required evidence. Prefer a frozen donor400 dependency closure for prospective drift control because it preserves N init; its MRA price must await that forward. Donor544 is an immediately priceable alternative, but it has no measured advantage over N init. Do not present a live-scale N read as drift-controlled.',
      serving_pin='Any changed scale rule, coefficient or donor input means every tower-arm baseline is read again before any N export is read under it.',
      results=r)
    # The measured decisions determine calibration advice without overriding frozen bars.
    pose=r['displacement']['decisions']; dist=r['distance']['decisions']
    preferred='D' if pose['D-G']=='SUPPORTED' and pose['D-A']=='SUPPORTED' else ('G' if pose['G-A']=='SUPPORTED' else 'A')
    harms={}
    for arm in ('G','D'):
        name=arm+'-A'
        harms[arm]=any(v['all']['paired_differences'][name]['ci95'][1]<0 for v in r['distance']['folds']) or r['distance']['combined']['all']['paired_differences'][name]['ci95'][1]<0
    eligible={arm:pose[arm+'-A']=='SUPPORTED' and not harms[arm] for arm in ('G','D')}
    choice='D' if eligible['D'] and pose['D-G']=='SUPPORTED' else ('G' if eligible['G'] else 'A')
    final['calibration_advice']=dict(displacement_preference=preferred,distance_supported_harm=harms.get(preferred,False),distance_harm_by_arm=harms,
       deployment_choice=choice,scope='Step544 K1 train only; no step400 pricing')
    write_report(final)
    dump(OUT/'SCALE_DRIFT.json',final)
    (ROOT/'STATUS.md').write_text('ITEMS12 and SCALE_DRIFT reports and JSON files are complete. The reports price donor544 and calibration, mark step400 and causal source-removal prices MISSING, and state the benchmark projection and serving-pin consequence. Final validation checks output provenance, exact room folds, fit-room isolation, score refusal and distance arithmetic.\n')
    print('FINAL REPORT COMPLETE')
def write_report(f):
    r=f['results']; p=f['prices']; ad=f['calibration_advice']
    cg=r['displacement']['combined']['all']['paired_differences']['G-A']; cd=r['displacement']['combined']['all']['paired_differences']['D-G']
    lines=['# Price of stopping tower-arm scale drift','',
     'The question is whether freezing or calibrating the depth-derived tower scale gives vehicle N a defensible gain at its first boundary. The available K1 own-depth cache prices step 544 only. It cannot price N’s step-400 initialization or prove that a particular training source caused the drift.','',
     f"Global calibration changes displacement by **{delta(cg)} MRA points**. Dataset calibration minus global calibration is **{delta(cd)}**. The frozen displacement preference is **{ad['displacement_preference']}**; the choice after the distance-harm guard is **{ad['deployment_choice']}**. A means unchanged step544 scale, G global calibration, and D calibration per dataset.",'',
     f['recommendation'],'',f"**Serving consequence:** {f['serving_pin']}",'',
     '## Test-half prices','',
     'Each interval is a paired room bootstrap with 10,000 draws, seed 17 and 95% coverage. Both swapped folds use exactly the sb_scale1 rooms. The combined table scores each available room once. Fit factors use fit-half displacement only; distance uses those same factors with exact relifting. The distance guard rejects a calibration if either test half or the combined interval shows harm (upper bound below zero).','']
    for kind in ('displacement','distance'):
        lines += [f'### {kind.title()}', '', '| Arm | Fold 1 MRA [95% CI] | Fold 2 MRA [95% CI] | Combined MRA [95% CI] |','|---|---:|---:|---:|']
        for arm in ('A','G','D'):
            vals=[x['all']['arms'][arm] for x in r[kind]['folds']]+[r[kind]['combined']['all']['arms'][arm]]
            lines.append('| '+arm+' | '+' | '.join(fmt(v) for v in vals)+' |')
        lines += ['', '| Arm minus A | Fold 1 MRA points [95% CI] | Fold 2 MRA points [95% CI] | Combined MRA points [95% CI] |','|---|---:|---:|---:|']
        for arm in ('A','G','D'): lines.append('| '+arm+' | '+' | '.join(delta(x['paired_vs_A']) for x in p[arm][kind])+' |')
        lines += ['', '| Arm minus A, benchmark contribution | Fold 1 points [95% CI] | Fold 2 points [95% CI] | Combined points [95% CI] |','|---|---:|---:|---:|']
        for arm in ('A','G','D'): lines.append('| '+arm+' | '+' | '.join(delta(x['benchmark_contribution_delta']) for x in p[arm][kind])+' |')
        lines.append('')
    lines += ['## Calibration decision','', f"Displacement decisions are global versus A: {r['displacement']['decisions']['G-A']}; dataset versus A: {r['displacement']['decisions']['D-A']}; dataset versus global: {r['displacement']['decisions']['D-G']}. The distance guard reports supported harm for the preferred calibration: {ad['distance_supported_harm']}. The fit-half factors price a fixed rule; they are not a single production coefficient. A production factor and dataset identity policy still need explicit export pins.", '', '## Benchmark conversion','',
      'Camera displacement is one of five equally weighted VSTI task groups, so a displacement change of Δ MRA points contributes Δ/5 benchmark points if the other groups remain fixed. Object absolute distance is one of eight VSI groups, so its contribution is Δ/8. These projections refer to different benchmarks and must not be added. The official code defines the groups at lines 109–139 and averages group scores at lines 544–564.','',
      f"Source: `{f['conversion']['source']}`, SHA-256 `{f['conversion']['source_sha256']}`. Only source code was read; no benchmark row was opened.",'',
      'The arithmetic converts type points; it does not establish benchmark improvement. This experiment averages rooms and uses all eligible anchor pairs or GT-mask distance rows. Official benchmark questions have different distributions and include grounding and routing errors. Geometrically, scaling all translations uniformly leaves move direction and turn rotation unchanged, but other scale-dependent tasks can change and were not priced here.','',
      '## Bias and origin','',
      'ITEMS12.md reports pooled and per-dataset served/GT ratios, capture distributions, paired global-versus-dataset tests, own/GT depth, pose-scaled G3T/GT depth, and depth-implied/pose-length scale. The JSON includes every fit-room identity and capture diagnostic.','',
      'A depth-implied/pose-length discrepancy is measured through G3T. It can reflect G3T shape, FoV, registration or GT errors. It is not an independent proof that dataset metric depth disagrees with metric poses. A decisive label audit needs matched depth reprojections across metric poses and trustworthy camera intrinsics, followed by the actual training-target audit.','',
      'All four pose-stream source comparisons are MISSING: a2v3 d1, a2v3 d2, a3v2 d1 and a3v2 d3. The local scene lists contain identifiers, not depths. The receipts name opaque dataset codes only. No source can be named for removal, and no retraining gain can be priced.','',
      '## Options and implementation needs','']
    bias_lines=['### Step-544 bias by dataset','', '| Dataset | Displacement pooled ratio; capture p10 / p50 / p90 | Distance pooled ratio; capture p10 / p50 / p90 |', '|---|---:|---:|']
    triple=lambda v: ' / '.join(f'{x:.4f}' for x in v) if v else 'MISSING'
    for ds in ('all','arkitscenes','scannet','scannetpp'):
        values=[r[k]['combined'][ds]['arms']['A'] for k in ('displacement','distance')]
        bias_lines.append('| '+ds+' | '+' | '.join(f"{v['pooled_median_ratio']:.4f}; {triple(v['capture_median_ratio_p10_p50_p90'])}" for v in values)+' |')
    bias_lines += ['', '| Distance dataset | Refusals A / G / D | Captures with a finite A ratio |', '|---|---:|---:|']
    for ds,v in r['distance']['combined'].items():
        bias_lines.append('| '+ds+' | '+' / '.join(str(v['arms'][arm]['refusals']) for arm in ('A','G','D'))+' | '+str(v['arms']['A']['captures_with_ratio'])+' |')
    bias_lines += ['', '| Dataset | Own / GT depth, pooled | Pose-scaled G3T / GT depth, pooled | Depth-scale / pose-scale capture p10 / p50 / p90 |', '|---|---:|---:|---:|']
    for ds,v in r['depth'].items():
        bias_lines.append(f"| {ds} | {v['own_over_GT']['pooled_median_ratio']:.4f} | {v['pose_scaled_G3T_over_GT']['pooled_median_ratio']:.4f} | {triple(v['depth_scale_over_pose_scale_p10_p50_p90'])} |")
    bias_lines += ['', 'Depth ratios use the matched confidence/valid-depth grid mask specified in ITEMS12 and the frozen bars. Capture quantiles are descriptive distributions, not confidence intervals. The JSON also reports room-bootstrap intervals for the means of room median depth ratios.', '']
    insertion=lines.index('## Options and implementation needs')
    lines[insertion:insertion]=bias_lines
    for o in f['options']:
        lines += [f"### {o['option']}: {o['status']}",'',o['reason']]
        if o['price_arm']:
            a=o['price_arm']; lines.append(f"Use arm {a} in both fold tables and benchmark-contribution tables above. Its combined displacement change is {delta(p[a]['displacement'][-1]['paired_vs_A'])}; its projected VSTI contribution is {delta(p[a]['displacement'][-1]['benchmark_contribution_delta'])}.")
        else: lines.append('Both fold prices, the combined price, and benchmark-point conversions are MISSING; rejection is a decision, not an invented measured price.')
        lines += ['', 'Tree: '+o['tree'], '', 'Export: '+o['export'], '', 'Reader: '+o['reader'], '']
    lines += ['## What could fail, and how to detect it','',
      '| Failure | Observable test |','|---|---|',
      '| The frozen head still receives moving FoV inputs. | Compare depth, FoV and scale on fixed training RGB before and after an optimizer update; freeze the full input dependency closure. |',
      '| Freezing the live depth head harms other depth callers. | Compare those callers on permitted training inputs; a separate scale donor allows the live head to keep learning. |',
      '| A donor export silently mixes live and frozen dependencies. | Verify donor weight, private-feature, FoV, preprocessing and scale-rule hashes; reproduce its cached 51×51 grids. |',
      '| Dataset calibration overfits or uses the wrong identity. | Require D−G to pass both folds and combined; validate dataset lookup from receipts and refuse an unknown identity. |',
      '| A camera calibration harms routed distance. | Relift with the changed scale and compare paired GT-mask distance scores; monitor refusals and per-dataset losses. |',
      '| GT depth/pose discrepancy is caused by geometry rather than labels. | Audit frame registration, optical-axis depth, intrinsics, multi-view reprojection and G3T shape before blaming a source. |',
      '| GT-mask improvement does not survive predicted masks or routing. | Run a separately authorized complete reader comparison under the same serving pin; no such claim is made here. |',
      '| A scale is applied twice. | Check geometry scale counts and linearity of camera translations and lifted depths; preserve a single shared scalar. |',
      '| The first N comparison mixes serving rules. | Check baseline and N serving-pin hashes; reject a mixed comparison and re-read all tower baselines first. |','',
      '## Tests that settle missing prices','']
    for m in f['missing_tests']:
        lines += [f"- **{m['input']}**: {m['test']} GPU-hours: **{m['gpu_hours']}**. {m.get('gpu_hours_status','CPU analysis only.')} "]
    lines += ['', 'The step-400 forward is exactly the one specified in sb_scale1/out/NEEDS.md and NEEDS_INPUTS.json: 242 training captures and 7,744 RGB anchor slots, matched checkpoint context, no token generation, and one finite [32,51,51] own-depth grid per capture. Its 1.04 GPU-hour estimate excludes staging/model load. This CPU-only task ran no forward.','',
      '## Reproduction and validation','',
      'All measured tables originate from the frozen scoring command; benchmark conversions and option tables originate from the report command.','', '```sh',
      'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/test_scale_drift.py',
      'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/scale_drift.py freeze',
      r['command'],COMMAND,'```','',
      'IMPLEMENTATION_FIX.json documents exception handling for E3 geometry refusals and pins both code versions and the original bars. Metrics, folds, fitting and decisions are identical. The scorer refuses existing score files and verifies the frozen code and input hashes. The tests check exact room folds, dataset-fit isolation, refusal behavior, zero credit for program refusals and strict MRA parity. Final validation is recorded in VALIDATION.json. These commands describe the original run; a fresh scoring run requires a new experiment directory rather than overwriting these outputs.','',
      f"Scoring elapsed time: {r['elapsed_seconds']:.2f} seconds. Resource usage is in resources.log. All jobs used nice 10 and at most eight numerical-library threads. Inputs and imported scoring dependencies are SHA-256 pinned in the JSON outputs.",'',
      'This internal diagnostic retains checkpoint names, split details and the supplied learned-head loss because the task requires reproducible option pricing. It does not claim an evaluated step400 result or a discovered biased training source.']
    (OUT/'SCALE_DRIFT_REPORT.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__': main()
