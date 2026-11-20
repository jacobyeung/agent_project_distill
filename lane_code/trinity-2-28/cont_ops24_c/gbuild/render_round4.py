"""Render the T2 stage evidence and short workspace report."""
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'cap/score_t2'
data=json.loads((OUT/'STAGES_T2.json').read_text())
lines=[]
def add(s=''): lines.append(s)
def num(v,d=2): return 'undefined' if v is None else f'{v:.{d}f}'
def ci(v):
    if v['mean'] is None: return 'undefined'
    return f"{v['mean']:+.2f} [{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}]"
def marked(n,u,a): return f'{n} ({u} U; {a} E)'
def compact(o):
    e=o['evidence']
    if not e: return f"{o['name']}: U ({o['reason']})"
    text=(f"{o['name']}: {o['stage']}; visible {len(o['visible_frames'])}/32; "
          f"raw matches {o['matching_proposal_count']}/{o['raw_proposal_count']}; "
          f"selected matches {e['selected_correct_frames']}/{o['nonempty_selected_frames']}")
    if e['outside_box_m'] is not None: text+=f"; outside {e['outside_box_m']:.3f} m"
    if o['stage']=='U': text+=f" ({o['reason']})"
    if o['extent_ambiguous']: text+=' [E: ScanNet extents]'
    return text

add('# T2 point and restricted-arm loss stages')
add()
add('T2 contains 150 items in each arm and ten text-repeat records. The authenticated capture SHA256 is '
    '`2406c812f4d7c615a49d151f9038fdd1575f61479e8cdca60c3154fbeb5a8b08`. '
    'The recorded baseline scores 58.60, the point arm 63.53, and the restricted arm 52.53. '
    'All 300 arm scores and all paired baseline scores reproduce SCORE_T2.json.')
add()
add('On the 76 items with available GT (including U/E rows), the baseline mean is 69.21, the point mean is 67.63, '
    'and the restricted mean is 57.63. On the other 74 items, whose stages are U because GT is missing '
    '(or no call was recorded), the point mean rises from 47.70 to 59.32. The full-population point gain '
    'therefore cannot be explained by treating the available-GT subset as representative.')
add()
p=data['tables']['points']['gt_available'];l=data['tables']['points']['landscape_gt']
accepted=[a for a in data['alignments'] if a['accepted']]
add(f"GT exists for {p['captures']} captures, {p['items']} items, and {p['objects']} called-object occurrences per arm. "
    f"The landscape subset has {l['captures']} captures, {l['items']} items, and {l['objects']} occurrences. "
    f"Nine portrait captures have unknown orientation. Only {len(accepted)}/38 camera alignments pass; "
    f"{sum(a['orientation']['status']=='identity' for a in accepted)} passing captures are landscape. "
    'Failed alignment leaves S4/S5 unknown while preserving resolved S0–S3 evidence.')
add()
add('The capture contains retained raw proposals for all 298 called objects in each arm: '
    '44,125 point-arm proposals and 26,286 restricted-arm proposals. No field needed for the mask join is missing. '
    '“Raw” means after the detector joint-score floor and cap; pre-filter logits and rejected masks are absent. '
    'The restricted records omit `frame_decisions`, which the GT join does not need. '
    'One item has no recorded calls, no objects, and no geometry; it remains U.')
add()
add('**Stage and uncertainty rules.** Raw and selected predictions use the pinned reader resize at the GT 240×320 grid. '
    'A mask matches only at IoU >0.5. The selected identity is correct when at least half its nonempty masks match. '
    'S0 means no GT visibility; S1 means no retained raw proposal matches; S2 means no correct identity selected '
    '(including no selection); S3 means a correct identity in fewer than three matching frames; '
    'S4 means the fitted centroid lies >0.25 m outside the GT box; S5 passes these checks. '
    'S2 is an operational mask-based identity failure; the capture alone does not distinguish wrong-instance selection '
    'from a mask whose segmentation misses the IoU threshold. S5 does not prove the full box is correct or isolate a bug in the gap program. Its remaining error includes box extent, '
    'permitted centroid error, the gap calculation, and disagreement with the task distance label.')
add()
add('Items take the worse stage across called objects using the existing `funnel.worse`: S0 dominates; otherwise '
    'any U operand makes the item U; otherwise the earliest stage wins. Counts are occurrences, not unique physical objects. '
    '`U` marks unresolved evidence. `E` marks ScanNet extent ambiguity, including rows whose stage agrees under both readings. '
    'ScanNet++ half extents are doubled; ARKit uses full extents; ScanNet carries both readings and becomes U if they disagree. '
    'Every count below lists its U/E subset; these flags can overlap.')
add()
add('**Score-loss intervals.** Loss is the paired recorded-baseline score minus arm score: positive is worse, negative is a gain. '
    'The conditional loss uses only items assigned to that stage. The contribution sums their paired losses and divides by '
    'all items in that table’s population, so stage contributions sum to the population’s paired loss. '
    'These are descriptive score partitions, not causal effects of fixing a stage. U receives a measured score partition '
    'but no stage attribution. Intervals are percentile 95% intervals from 10,000 shared draws of all 46 physical rooms '
    'with seed 20261120, weighted by items. Empty subgroup draws are excluded and counted, never replaced. '
    'The JSON also supplies each stage’s contribution to the full 150-item score.')
add();add('An empty stage has an undefined conditional score/loss and a zero arithmetic contribution to the observed '
    'population total. That zero is not an estimate of the loss recoverable by fixing the stage. Single-room '
    'conditional intervals can collapse to one value; their undefined-draw counts expose the limited support.')
add();add('No item reaches S5 in either arm, so an item-level gap-program/extent score loss is undefined. '
    'Each arm has five resolved S5 object occurrences, two with ambiguous ScanNet extents that pass both readings; '
    'all five centroids lie inside the GT box. There are no resolved S4 objects. These small resolved counts do '
    'not establish that placement errors are rare: alignment rejection censors the placement test.')

for scope,title in [('gt_available','Available GT, including U portrait/binding/alignment rows'),
                    ('landscape_gt','Landscape GT'),('all_150','All 150 items, including missing GT')]:
    add();add(f'**{title}.**')
    for arm in ('points','restricted_selector'):
        t=data['tables'][arm][scope]
        add();add(f"{arm}: {t['items']} items; {t['objects']} called objects; {t['captures']} captures; {t['rooms']} rooms.")
        add();add('| Stage | Objects (U; E) | Items (U operand; E) | Arm mean | Baseline mean | Paired loss [95% CI] | Population contribution [95% CI] | Undefined conditional draws |')
        add('|---|---:|---:|---:|---:|---|---|---:|')
        for r in t['table']:
            add(f"| {r['stage']} | {marked(r['objects'],r['objects_with_U'],r['objects_ambiguous_extents'])} | "
                f"{marked(r['items'],r['items_with_U_operand'],r['items_ambiguous_extents'])} | "
                f"{num(r['score']['mean'])} | {num(r['baseline']['mean'])} | {ci(r['paired_loss'])} | "
                f"{ci(r['population_loss_contribution'])} | {r['paired_loss']['undefined_draws']} |")

add();add('**Unknown evidence in the available-GT objects.**')
add();add('| Arm | Reason | Objects (all U) | Ambiguous extents (E subset) |')
add('|---|---|---:|---:|')
for arm in ('points','restricted_selector'):
    for reason,n in data['tables'][arm]['gt_available']['table'][-1]['unknown_reason_counts'].items():
        e=sum(o['extent_ambiguous'] for o in data['objects'][arm] if o['gt_available'] and o['stage']=='U' and o['reason']==reason)
        add(f'| {arm} | {reason} | {n} | {e} |')

add();add('**Alignment residuals.** One center-only rigid SE(3) fit uses the exact captured cameras across the two arms '
    'for each capture, without scale. All camera arrays within a capture are identical; repeated observations therefore '
    'leave the 32-anchor fit unchanged. Acceptance requires center rank ≥2, translation RMS ≤0.10 m, and every '
    'rotation residual ≤5°. `P` marks portrait orientation U for the mask join. `E` marks ambiguous ScanNet box extents. '
    'An alignment can pass for a portrait capture while its masks remain unusable.')
add();add('| Capture | Flags | Translation RMS (m) | Rotation RMS (°) | Rotation max (°) | Rank | Accepted |')
add('|---|---|---:|---:|---:|---:|---|')
for a in data['alignments']:
    flags=[]
    if a['orientation']['status']=='U': flags.append('P/U masks')
    if a['capture'].startswith('scannet/'): flags.append('E')
    add(f"| {a['capture']} | {', '.join(flags) or '—'} | {num(a.get('translation_rms_m'),4)} | "
        f"{num(a.get('rotation_rms_deg'),3)} | {num(a.get('rotation_max_deg'),3)} | {a.get('center_rank')} | {'yes' if a['accepted'] else 'no; S4/S5 U'} |")
add();add('| Population | Residual | N | Min | Median | P95 | Max |')
add('|---|---|---:|---:|---:|---:|---:|')
for scope,metrics in data['alignment_distribution'].items():
    for metric,d in metrics.items():
        add(f"| {scope} | {metric} | {d['n']} | {num(d['min'],4)} | {num(d['median'],4)} | {num(d['p95'],4)} | {num(d['max'],4)} |")
add();add('Per-anchor residuals, every paired observation, fitted transforms, and record membership are in `STAGES_T2.json`. '
    'These distribution counts include rejected alignments; they measure camera agreement, not established placement accuracy.')

add();add('**Centroid errors for resolved S4/S5 objects.** Outside-box distance defines the stage. '
    'Distance to the annotated box center is also shown; a correct fitted centroid need not equal that center. '
    'Objects with failed alignment, portrait orientation, or unresolved binding do not enter either distribution.')
add();add('| Arm | Stage | Objects (U; E) | Distance | Mean (m) | Min | Median | P95 | Max |')
add('|---|---|---:|---|---:|---:|---:|---:|---:|')
for arm,stages in data['centroid_error'].items():
    for s,v in stages.items():
        for metric in ('outside_gt_box_m','centroid_to_gt_center_m'):
            d=v[metric]
            add(f"| {arm} | {s} | {marked(v['objects'],0,v['ambiguous_extents'])} | {metric} | "
                f"{num(d['mean'],4)} | {num(d['min'],4)} | {num(d['median'],4)} | {num(d['p95'],4)} | {num(d['max'],4)} |")

add();add('**The seven point-arm items without a numeric gap.** Six have an operand with all 32 points null; '
    'none of those six has a retained proposal or selected mask for that operand. The seventh has no recorded '
    'calls in either the deployed response or T2. Thus only six are observed operand-mask failures. '
    'There are zero “no retained mask despite a nonnull point” and zero “mask without the point” causes among these failures. '
    'Six have item stage U. Item `vsi590k_163796` is S0 because its bound slippers instance has zero GT-visible '
    'frames; its heater operand is U for alignment. The point-input diagnosis is directly observed even where GT stage attribution is unavailable.')
add();add('| Item | Capture | Missing operand / cause | Baseline | Point score | GT stage |')
add('|---|---|---|---:|---:|---|')
for item in data['no_numeric_gap_items']:
    missing=[o for o in item['operands'] if o['diagnostics']['no_mask_cause']]
    cause='no recorded calls (no operand diagnosis)' if item['no_recorded_object_call'] else '; '.join(f"{o['name']}: {o['diagnostics']['no_mask_cause']}" for o in missing)
    source_item=next(i for i in data['items']['points'] if i['item_id']==item['item_id'])
    flags=('; E' if source_item['extent_ambiguous'] else '')+('; U operand' if source_item['has_U_operand'] and item['stage']!='U' else '')
    add(f"| {item['item_id']} | {item['capture']} | {cause} | {item['baseline']:.0f} | {item['score']:.0f} | {item['stage']}{flags} |")
pd=[o['point_diagnostics'] for o in data['objects']['points']]
add();add(f"Across all point-arm called objects, {sum(p['chosen_without_point'] for p in pd)} chosen frame masks "
    f"do not contain their point, affecting {sum(p['chosen_without_point']>0 for p in pd)} object occurrences. "
    'These fallback selections are recorded explicitly and are not, by themselves, a no-mask failure.')

obj={o['key']:o for o in data['objects']['points']}
for key,title in [('worst_point_items','Ten worst point-arm items across all 150'),
                  ('worst_landscape_gt_point_items','Ten worst point-arm items with landscape GT')]:
    add();add(f'**{title}.** Rank by lowest point score, then greatest paired loss, then item ID. '
        'The landscape list provides GT evidence where the full-population list is unresolvable.')
    add();add('| Item / capture | Point / baseline | Item stage | Object evidence |')
    add('|---|---:|---|---|')
    for i in data[key]:
        evidence='; '.join(compact(obj[k]) for k in i['object_keys']) or 'No recorded object call; U.'
        add(f"| {i['item_id']} / {i['capture']} | {i['score']:.0f} / {i['baseline']:.0f} | {i['stage']} | {evidence} |")

add();add('**Validation and reproduction.** The capture digest and byte count match both receipts. '
    'All 310 records are complete, both arms cover all 150 manifest items, frame identities and served-call sequences match, '
    f"and all arm/baseline scores agree with the supplied scorer. {data['validation']['reference_join_records']} real landscape records independently match "
    'the existing GT join’s stages and evidence, covering every observed stage in both arms. '
    'The complete-population bootstrap intervals also reproduce SCORE_T2.json. The JSON retains every object and item assignment, U reason, '
    'extent flag, frame IoU, proposal-match count, score, and bootstrap interval. '
    '`PARITY.json` has `trusted=false` and `parity_gate_applies=false` by design for the changed point mode; '
    'this is not a baseline-parity claim. All ten separate text-repeat responses match the recorded baseline.')
add();add('Run from gbuild with the required CPU interpreter:')
add();add('```bash\nOPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= \\\n/scratch/jjyeung/envs/p1cpu/bin/python -B analyze_round4.py\n/scratch/jjyeung/envs/p1cpu/bin/python -B render_round4.py\n```')
add();add(f"The analysis used one numerical thread, a 15 GiB address-space cap, and "
    f"{data['validation']['max_rss_KiB']/1024:.1f} MiB peak RSS. No delivery or build output was changed.")
(OUT/'STAGES_T2.md').write_text('\n'.join(lines)+'\n')

report=['# Round 4: T2 GT loss stages','',
    'Failure of the mask-based identity rule is the largest resolved point-arm stage: 36 of 152 called-object occurrences on available-GT '
    'captures are S2 (one has ambiguous ScanNet extents). Another 84 are unknown, including 54 censored by alignment. '
    'Only 6 of 38 camera alignments pass the rigid no-scale ruling; five passing captures are landscape.','',
    'Counts below mark U for unresolved evidence and E for ambiguous ScanNet extents; flags can overlap.','']
for arm in ('points','restricted_selector'):
    t=data['tables'][arm]['gt_available'];counts=', '.join(f"{r['stage']}={marked(r['objects'],r['objects_with_U'],r['objects_ambiguous_extents'])}" for r in t['table'])
    report.append(f"For {arm}, the {t['objects']} called-object occurrences on available-GT captures split as {counts}.")
    report.append('')
report+=['No item reaches S5 in either arm, so gap-program/extent score loss cannot be estimated from an S5 item group. '
    'Each arm has five S5 objects (two E), all with centroids inside the GT box, and zero resolved S4 objects. '
    'Failed alignment prevents interpreting zero S4 as evidence of accurate placement.','',
    'The 11 point-arm S2 items (one E) lose only 0.91 points versus their recorded baseline '
    '(95% interval −12.86 to +12.50). The 13 restricted-arm S1 items (no U/E) lose 20.00 points '
    '[+1.25, +41.25], contributing 1.73 [+0.07, +3.95] points of loss across all 150 items. '
    'The resolved stage counts therefore do not establish which repair would recover the most score.','',
    'The point arm scores 67.63 versus a 69.21 baseline on the 76 available-GT items (U/E included). '
    'Its overall gain comes from the 74 items without GT stage assignments, where scores rise from 47.70 to 59.32.','',
    'Six point-arm zero-score items lose an operand because all 32 input points are null. '
    'The seventh item without a numeric gap has no recorded calls in either baseline or T2. '
    'None of these cases is a nonnull-point detector rejection or a mask-without-point failure.','',
    'The stage tables report object and item counts, item means, and paired score-loss intervals from 10,000 draws '
    'over the same 46 rooms (seed 20261120). Every count flags unknown evidence and ambiguous ScanNet extents. '
    'The report also gives all 38 capture alignments, resolved S4/S5 centroid distributions, '
    'and the ten worst point-arm items with object evidence. Stage score partitions are descriptive, not causal estimates.','',
    f"[Read the stage report]({OUT/'STAGES_T2.md'}). "
    f"[Inspect the full JSON evidence]({OUT/'STAGES_T2.json'}).",'',
    'The capture SHA256 matches the supplied value and both receipts. All 300 arm scores and paired baseline scores '
    f"reproduce SCORE_T2.json; {data['validation']['reference_join_records']} real records independently agree with the existing join. "
    'The analysis used one CPU thread and stayed below 16 GB. No delivery or build output was changed.','',
    'Reproduction scripts: [analyze_round4.py](analyze_round4.py) and [render_round4.py](render_round4.py).']
(ROOT/'REPORT4.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(markdown=str(OUT/'STAGES_T2.md'),report=str(ROOT/'REPORT4.md'))))
