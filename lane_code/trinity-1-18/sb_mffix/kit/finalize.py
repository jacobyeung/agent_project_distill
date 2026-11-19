"""Render verified audit artifacts; run bash run.sh finalize.py."""
import collections, hashlib, json, tarfile
from pathlib import Path
import numpy as np
import analyze as A

O=A.OUT
LABELS={'omitted_selection':'selected track absent', 'wrong_instance':'wrong_instance (structurally empty)'}
def load(p):return json.loads(p.read_text())
def pc(v,n):return f'{100*v/n:.1f}' if n else 'NA'
def failure_table(groups):
    lines=['| Group | Rows | Visible frames | No proposal % | Selected track absent % | Wrong instance % | Wrong class % | Partial % | Merged % | Other % | Correct % |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,g in groups.items():
        n=g['visible_valid'];ct=g['failure']['0.5']
        lines.append('| '+str(name)+' | '+str(g.get('rows','—'))+' | '+str(n)+' | '+' | '.join(pc(ct.get(k,0),n) for k in A.KINDS)+' |')
    return lines

def main():
    s=load(O/'SPLITS.json');a=load(O/'ATTRIBUTION.json');m=load(O/'MASKFAIL.json')
    fixes=load(O/'RECOMPUTED.json')
    parity=load(O/'FRESH_ENDPOINT_PARITY.json')
    assert len(parity['rows'])==2074 and all(x['passed'] and x['prediction']==x['expected_prediction'] for x in parity['rows'])
    cf=load(O/'COUNTERFACTUAL_ROWS.json');arms=collections.defaultdict(list)
    for x in cf['rows']:arms[x['arm']].append(x)
    assert len(arms)==48 and all(len(x)==1037 and len({r['row_id'] for r in x})==1037 for x in arms.values())
    r=m['records'];g=s['overall'];v=g['visible_valid'];avail=g['availability']['0.5']
    for field,key in [('dataset','by_dataset'),('share_bin','by_share'),('class','by_class')]:
        for name,group in s[key].items():
            group['rows']=len({x['row'] for x in r if x[field]==name})
    endpoints={(x['arm'],x['row_id']):x for x in parity['rows']}
    published={}
    per=A.BOX/'out/box_ladder/PER_ITEM.jsonl'
    with per.open() as f:
        for line in f:
            x=json.loads(line)
            if (x['arm'],x['row_id']) in endpoints:published[(x['arm'],x['row_id'])]=x
    assert len(published)==2074
    for key,x in endpoints.items():
        assert x['prediction']==published[key]['prediction'] and x['label']==published[key]['label']
    for t in A.THRESH:
        for x in arms[f'{t}/cumulative/correct']:
            assert x['prediction']==endpoints[('A2_gt_masks',x['row_id'])]['prediction']
    refused={rid for (arm,rid),x in endpoints.items() if arm=='A0_deployed' and x['prediction'] is None}
    no=arms['0.5/independent/no_proposal'];wcrows=arms['0.5/independent/wrong_class']
    newref=[x for x in wcrows if x['prediction'] is None and x['row_id'] not in refused]
    no_points=100*sum(A.T.M.mra(x['prediction'],x['label']) for x in no if x['row_id'] in refused)/1037
    lost_points=100*sum(A.T.M.mra(endpoints[('A0_deployed',x['row_id'])]['prediction'],x['label']) for x in newref)/1037
    effects=dict(A0_refusals=len(refused),A2_refusals=sum(x['prediction'] is None for (arm,_),x in endpoints.items() if arm=='A2_gt_masks'),no_proposal_points_from_A0_refusals=no_points,wrong_class_new_refusals=len(newref),wrong_class_points_lost=lost_points,wrong_class_absent_frames=sum(x['valid'] and not x['visible'] and x['failure_kind']=='wrong_class' for x in r),input_sha256={str(p):A.sha(p) for p in [O/'FRESH_ENDPOINT_PARITY.json',O/'COUNTERFACTUAL_ROWS.json',O/'MASKFAIL.json',per,Path(__file__)]})
    A.write(O/'REFUSAL_EFFECTS.json',effects)
    assert all(x['exact_label_instances']==1 for x in fixes['objects'])
    omitted=fixes['by_kind']['0.5']['omitted_selection']
    q5=fixes['layers']['0.5']
    assert sum(q5.values())==avail['wrong']
    assert q5['in_accepted_track']+q5['passes_floor_no_accepted_track']+q5['below_floor']==avail['deployed_correct']
    assert all(x['matches'] for t in fixes['reviewer_comparison'].values() for x in t.values()), 'Report both counts if reviewer comparison differs'
    assert [omitted.get(k,0) for k in ['none','in_accepted_track']]==[963,1155]
    assert omitted.get('passes_floor_no_accepted_track',0)+omitted.get('below_floor',0)==275
    track_comparison=dict(reviewer=dict(wrong_object_tracks=140,omitted_frames=803,source='review/REVIEW_VERDICT.md, F1',counting_recipe='MISSING from supplied compare.py and rerun.py'),kit=dict(wrong_object_tracks=fixes['wrong_object_tracks'],omitted_frames=fixes['omitted_frames_on_wrong_object_tracks'],definition='train_pricing.majority: pool all selected proposal pixels, count nonnegative GT instance IDs, choose the largest count with smallest-ID tie break, compare with the target instance'),interpretation='Different track-level summaries cannot be equated without the reviewer counting recipe; both results are reported. The exact-label structural-empty result and all candidate availability layers are independently verified.',input_sha256={str(p):A.sha(p) for p in [O/'RECOMPUTED.json',A.HERE/'review/REVIEW_VERDICT.md',A.HERE/'review/compare.py',A.HERE/'review/rerun.py',Path(__file__),Path(A.T.__file__)]})
    A.write(O/'F1_COMPARISON.json',track_comparison)


    # Area bins partition frames, so omit the pricing-frame statistic from them.
    for group in s['by_share'].values():group.pop('pricing_best_frame_iou',None)
    s['input_sha256'][str(Path(__file__).resolve())]=A.sha(__file__)
    s['input_sha256'][str(O/'MASKFAIL.json')]=A.sha(O/'MASKFAIL.json')
    s['input_sha256'][str(O/'RECOMPUTED.json')]=A.sha(O/'RECOMPUTED.json')
    s['overall']['availability_layers']=fixes['layers']
    s['availability_layers_by_kind']=fixes['by_kind']
    A.write(O/'SPLITS.json',s)
    missing=load(O/'MISSING_INPUTS.json')
    for p in [A.MAN,A.IDS,A.BOX/'pinned_train.json',Path(__file__).resolve()]:
        missing['input_sha256'][str(p)]=A.sha(p)
    A.write(O/'MISSING_INPUTS.json',missing)
    assert len(r)==66368 and len({x['row'] for x in r})==1037
    assert sum(g['failure']['0.5'].values())==v
    assert a['gap']['n']==1037 and a['gap']['rooms']==192
    assert abs(a['gap']['estimate']-17.20347155255545)<1e-8
    assert all(abs(a['thresholds'][str(t)]['cumulative']['correct']['estimate']-a['gap']['estimate'])<1e-10 for t in A.THRESH)
    A.first_table(s,a)
    table=(O/'FIRST_TABLE.md').read_text().splitlines()
    for i,line in enumerate(table):
        if not line.startswith('|'):continue
        parts=line.split('|')
        if i==0:cell=' Ordered increment (% of gap) '
        elif i==1:cell='---:'
        else:
            kind=parts[1].strip();inc=a['thresholds']['0.5']['cumulative'][kind]['increment']['estimate']
            cell=f' {inc:+.4f} ({100*inc/a["gap"]["estimate"]:+.1f}%) '
        parts.insert(6,cell)
        if i==0: parts.insert(-1,' Refusals independent / cumulative ')
        elif i==1: parts.insert(-1,'---:')
        else:
            parts[1]=' '+LABELS.get(kind,kind)+' '
            parts.insert(-1,f' {a["thresholds"]["0.5"]["independent"][kind]["refusals"]} / {a["thresholds"]["0.5"]["cumulative"][kind]["refusals"]} ')
        table[i]='|'.join(parts)
    table[-1]=table[-1].replace('Rules: RULES.md.','Rules: [RULES.md](../RULES.md).')
    table += [
        f'wrong_instance is structurally empty: all {len(fixes["objects"])} targets have unique exact labels in their captures. The review reports 140 wrong-object selected tracks and 803 selected-track-absent frames on those tracks.',
        f'A0 refuses {len(refused)} rows; A2 refuses {effects["A2_refusals"]}. Independent no_proposal recovers {no_points:+.4f} points from the {len(refused)} A0-refused rows. Independent wrong_class adds {len(newref)} refusals, costing {lost_points:.4f} points, when {effects["wrong_class_absent_frames"]} GT-absent wrong-class frames are emptied.',
        'Selected track absent is the display label for omitted_selection; the rule and intervention remain unchanged. At IoU 0.5, 963/2,393 frames have no correct raw candidate, 275 have one only outside accepted tracks, and 1,155 are selectable (48.3%). Its +3.7801 independent / +2.9412 ordered gain is an upper bound for a selector or track-coverage fix.'
    ]
    table.append(f'The kit’s pooled-pixel track-majority helper returns {fixes["wrong_object_tracks"]} wrong-object tracks and {fixes["omitted_frames_on_wrong_object_tracks"]} selected-track-absent frames. The reviewer’s track-count recipe is MISSING from the supplied compare.py and rerun.py, so the 140/803 versus {fixes["wrong_object_tracks"]}/{fixes["omitted_frames_on_wrong_object_tracks"]} discrepancy is unresolved; see F1_COMPARISON.json. This does not affect the structurally empty exact-label class or item 5.')
    table.insert(-4,'')
    table.insert(-3,'')
    table.insert(-2,'')
    table.insert(-1,'')
    (O/'FIRST_TABLE.md').write_text('\n'.join(table)+'\n')
    split=['Primary threshold 0.5; visible valid operand-frames; percentages sum to 100 within rounding. Rows count distinct row IDs among records assigned to each group, including GT-absent records; area groups can overlap in rows. Full threshold sensitivity, IoU distributions, and candidate availability appear in SPLITS.json.','']
    for title,key in [('Datasets','by_dataset'),('Native GT frame share','by_share'),('Top 30 GT classes by distinct training rows','by_class')]:
        split.extend([title,'']+failure_table(s[key])+[''])
    (O/'SPLITS.md').write_text('\n'.join(split)+'\n')
    lines=[f'# Training mask failure analysis',f'A0 scores {a["baseline"]:.4f}; raster masks score {a["raster"]:.4f}: +{a["gap"]["estimate"]:.4f} distance MRA points on 1,037 rows (192 rooms).','']
    lines+= (O/'FIRST_TABLE.md').read_text().splitlines()
    strongest=max((k for k in A.KINDS if k!='correct'),key=lambda k:a['thresholds']['0.5']['independent'][k]['estimate'])
    gain=a['thresholds']['0.5']['independent'][strongest]['estimate']
    lines+=['',f'The largest independent repair is {strongest}: +{gain:.4f} points ({100*gain/a["gap"]["estimate"]:.1f}% of the full gap). This is an intervention effect, not an additive allocation.']
    miss=a['thresholds']['0.5']['cumulative']['omitted_selection']['estimate']
    wc=a['thresholds']['0.5']['cumulative']['wrong_class']['increment']['estimate']
    alone=a['thresholds']['0.5']['independent']['wrong_class']['estimate']
    lines+=[f'No-proposal and omitted-frame repairs together recover {miss:.4f} points ({100*miss/a["gap"]["estimate"]:.1f}% of the gap). Wrong-class repair contributes {wc:+.4f} points after those repairs, versus {alone:+.4f} alone; attribution depends on the intervention order.']
    lines+=['', 'Counts use visible, valid row-operand frames; interventions also remove false-positive masks in GT-absent frames. Gains use unchanged serving geometry, best-frame selection, box pricing, and refusal-as-zero scoring. Brackets are paired 95% room-bootstrap intervals.',
        'Independent gains overlap. Cumulative gains follow table order; each incremental gain and its interval are in ATTRIBUTION.json. Repairs use native A2 rasters, so the correct category retains boundary and sampling-resolution differences above the IoU cutoff.', '',
        'Rules (fixed before counting; precedence shown; full definitions in ../RULES.md):', '',
        '1. Correct: IoU ≥ threshold. No proposal: visible target and no retained raw-name deployed proposal touches it.',
        '2. Selected track absent (omitted_selection): an overlapping proposal exists but the selected track supplies no mask in that frame.',
        '3. Merged: ≥2 annotated instances each occupy ≥10% of the mask and each has ≥10% of its visible area covered.',
        '4. Wrong instance/class: a different instance occupies ≥50% of the mask; exact GT class labels distinguish the two.',
        '5. Partial: IoU below threshold and ≥80% of served pixels lie inside the target. Remaining masks are other errors.',
        '6. Both-empty frames are absent_both; invalid GT frames are MISSING. These are excluded from visible-frame counts.', '',
        f'Coverage: {len(r):,} operand-frame records; {v:,} visible/valid, {g["absent"]:,} GT-absent, {g["invalid"]:,} invalid. Compare masks on the 240×320 serving canvas; frame share uses native GT raster area. Repeated operands retain row weight; unique-instance statistics are in SPLITS.json.', '',
        '| Dataset | Visible frames | IoU mean / median / p90 | Object best IoU mean / median |',
        '|---|---:|---|---|']
    for ds,d in [('all',g)]+list(s['by_dataset'].items()):
        f=d['object_frame'];b=d['object_best_frame'];lines.append(f'| {ds} | {f["n"]} | {f["mean"]:.3f} / {f["quantiles"]["p50"]:.3f} / {f["quantiles"]["p90"]:.3f} | {b["mean"]:.3f} / {b["quantiles"]["p50"]:.3f} |')
    lines+=['', f'Best-frame IoU is the maximum over visible anchors for each row operand. The actual pricing-selected frame has mean IoU {g["pricing_best_frame_iou"]["mean"]:.3f}. Across all {g["all_evaluable_object_frame"]["n"]:,} nonempty-union frames, mean IoU is {g["all_evaluable_object_frame"]["mean"]:.3f}; both-empty frames are undefined. Full quantiles and unique-instance distributions: SPLITS.json.',
        f'Frame area matters: objects below 0.5% of the frame have mean IoU {s["by_share"]["<0.5%"]["object_frame"]["mean"]:.3f}; objects above 20% have mean IoU {s["by_share"][">20%"]["object_frame"]["mean"]:.3f}.', '',
        '| IoU threshold | Correct % | Wrong frames | Correct in accepted track | Passes 0.3 floor, no accepted track | Below 0.3 floor | Teacher-only correct |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for t in A.THRESH:
        q=g['availability'][str(t)];ct=g['failure'][str(t)];layer=fixes['layers'][str(t)]
        lines.append(f'| {t} | {pc(ct.get("correct",0),v)} | {q["wrong"]} | {layer["in_accepted_track"]} ({pc(layer["in_accepted_track"],q["wrong"])}%) | {layer["passes_floor_no_accepted_track"]} | {layer["below_floor"]} | {q["teacher_only_correct"]} |')
    lines+=['', 'The teacher pool is a subset of the deployed pool, not independent evidence: the review found deployed matches at IoU ≥0.8 for all 594 teacher instances in 12 sampled captures. Teacher-only correct is 0 at 0.5; four threshold-0.7 discrepancies in the stored masks do not establish independent proposals.', '',
        'Item 5: among 7,699 wrong frames at IoU 0.5, 1,487 (19.3%) have a correct candidate inside an accepted track and count as selection failures. Another 156 pass the 0.3 track floor but enter no accepted track, and 458 fall below it: 614 proposal-filter failures. The raw total is 2,101 (27.3%); 5,598 lack a correct raw candidate.',
        'The three layers use Objects.load and routed_candidates.lift at the unchanged score floor 0.3. Passing the score floor alone does not guarantee valid lifted pixels or an accepted track. All three thresholds match the reviewer exactly (RECOMPUTED.json).',
        'The deployed raw-name pool has joint floor 0.05 and cap 30; the teacher has floor 0.2 and cap 10. No proposal means none recorded at joint score ≥0.05 touches the target. Item 5 rests on the deployed pool alone; discarded logits and other-name prompts provide no evidence here.',
        f'Teacher status is MISSING for {avail["teacher_missing"]} wrong frames; {avail["unknown_teacher_without_deployed"]} also lack a correct deployed proposal, so joint absence is unknown. Exact missing paths: [MISSING_INPUTS.json](MISSING_INPUTS.json). Exact GT labels supply class identity; no synonym mapping is invented.', '',
        'Dataset, area-bin, and top-30 class failure tables: [SPLITS.md](SPLITS.md). All three thresholds and candidate availability by group: [SPLITS.json](SPLITS.json). All independent/cumulative scores, refusal counts, gap fractions, and incremental intervals: [ATTRIBUTION.json](ATTRIBUTION.json).', '',
        'Commands (run from kit/ or the extracted archive root; run.sh enforces CPU-only, nice 10, eight-thread limits):',
        '`bash run.sh analyze.py measure` measures overlaps and verifies exact A0/A2 parity; `bash run.sh classify.py` applies RULES.md and produces MASKFAIL.json, all distributions/splits, and FIRST_TABLE.md.',
        '`bash run.sh analyze.py price` produces 48 interventions (three thresholds × independent/cumulative × eight kinds), each on all 1,037 rows; 10,000 room-bootstrap draws, seed 20261119.',
        '`bash run.sh recompute.py` produces the availability layers, exact-label and wrong-object-track checks, reviewer comparisons, and repriced A0/A2 endpoints. The reviewer’s 140/803 track counts and teacher subset evidence are in review/REVIEW_VERDICT.md; compare.py produces REVIEW_NUMBERS.json.',
        '`bash run.sh finalize.py` rechecks all 2,074 endpoint predictions against PER_ITEM and all three cumulative closures, computes refusal effects and distinct-row counts, and renders the report and sb_mffix.tar with SHA256.',
        'Input SHA256 values are recorded in every output JSON; each frame record references its capture provenance JSON by SHA256. No held-out capture is evaluated.']
    assert len(lines)<=80,len(lines)
    (O/'MASKFAIL_REPORT.md').write_text('\n'.join(lines)+'\n')
    def at(file, text):
        return next(i for i,line in enumerate((A.HERE/file).read_text().splitlines(),1) if text in line)
    notes=['# Review corrections', '', 'All six reporting corrections are applied. Candidate availability matches the reviewer at all three IoU thresholds. The additional track-majority diagnostic differs from F1; both counts and the missing reviewer recipe are disclosed below. No rule, threshold, pricing function, or endpoint changed.', '']
    changes=[
        ('F1',f'Marked wrong_instance structurally empty and reported the reviewer’s 140 wrong-object tracks / 803 selected-track-absent frames. The kit pooled-pixel majority helper yields {fixes["wrong_object_tracks"]} / {fixes["omitted_frames_on_wrong_object_tracks"]}. It pools nonnegative GT IDs across selected proposal pixels; the reviewer’s counting recipe is MISSING from the supplied compare.py and rerun.py, so this discrepancy remains unresolved (F1_COMPARISON.json).','out/FIRST_TABLE.md','wrong_instance is structurally empty'),
        ('F2','Recomputed candidate availability through Objects.load and routed_candidates.lift at floor 0.3: 1,487 accepted-track frames, 156 passing the floor outside accepted tracks, and 458 below the floor. Only 1,487 count as selection failures; 614 need proposal-filter changes.','out/MASKFAIL_REPORT.md','Item 5:'),
        ('F3','Stated beside the teacher column that its pool is a subset of the deployed pool. Item 5 uses deployed candidates alone; retained threshold-0.7 mask discrepancies are not independent proposal evidence.','out/MASKFAIL_REPORT.md','The teacher pool is a subset'),
        ('F4','Renamed the displayed category selected track absent and reported candidate availability: 963 absent, 275 outside accepted tracks, and 1,155 selectable. The intervention remains an upper bound.','out/FIRST_TABLE.md','Selected track absent is the display'),
        ('F5',f'Added independent/cumulative refusal counts and point effects: 36 A0 refusals contribute +{no_points:.4f} no_proposal points; 119 new wrong_class refusals cost {lost_points:.4f} points after 588 GT-absent masks are emptied.','out/FIRST_TABLE.md','A0 refuses'),
        ('F6','Filled every Rows cell with distinct row IDs; the caption states that group membership includes GT-absent records and area groups can overlap in rows.','out/SPLITS.md','| arkitscenes |')]
    for finding,change,file,needle in changes: notes.append(f'- {finding}: {change} `{file}:{at(file,needle)}`.')
    notes += ['', f'Implementation: `recompute.py:{at("recompute.py","def main")}` computes availability and reprices endpoints; `finalize.py:{at("finalize.py","endpoints=")}` verifies all 2,074 predictions against PER_ITEM and all cumulative closures. `run.sh:3` sets the working directory to this copy.', '', 'Commands: `bash run.sh recompute.py` and `bash run.sh finalize.py`, from kit/ (or the extracted archive root). Original overlap, classification, and intervention commands are recorded in MASKFAIL_REPORT.md.', '', 'The source kit remains read-only. Copied measurement JSON retains its original input hashes; RECOMPUTED.json, FRESH_ENDPOINT_PARITY.json, REFUSAL_EFFECTS.json, and VALIDATION.json record hashes for the new computations.', '', 'No reader-facing revision-history passages were retained; this requested correction log records the changes.']
    (O/'FIX_NOTES.md').write_text('\n'.join(notes)+'\n')
    # Validate the record provenance chain and generated artifacts before packaging.
    prov={}
    for x in r:
        for path,h in x['input_sha256'].items():
            if path not in prov:prov[path]=A.sha(path)
            assert prov[path]==h
    checks=dict(records=len(r),rows=1037,captures=len({x['capture'] for x in r}),physical_rooms=192,report_lines=len(lines),
        prediction_parity='A0 and A2 repriced by recompute.py and verified against PER_ITEM in finalize.py: 2074 exact predictions',cumulative_closure='Exact A2 predictions at all thresholds; rechecked in finalize.py',
        input_sha256={str(O/f):A.sha(O/f) for f in ['MASKFAIL.json','SPLITS.json','ATTRIBUTION.json','COUNTERFACTUAL_ROWS.json','FRESH_ENDPOINT_PARITY.json','RECOMPUTED.json','REFUSAL_EFFECTS.json','F1_COMPARISON.json']})
    checks['input_sha256'][str(Path(__file__).resolve())]=A.sha(__file__)
    checks['input_sha256'][str(per)]=A.sha(per)
    A.write(O/'VALIDATION.json',checks)
    A.status(f'Complete: 1,037 training rows, 66,368 operand-frame records, 209 captures, 192 rooms. A0 and A2 reproduce exactly; all cumulative interventions close to A2. MASKFAIL_REPORT.md has {len(lines)} lines. FIRST_TABLE.md, split tables, provenance, counterfactual scores, and sb_mffix.tar with SHA256 are ready.')
    files=[O/f for f in ['MASKFAIL_REPORT.md','MASKFAIL.json','FIRST_TABLE.md','SPLITS.md','SPLITS.json','ATTRIBUTION.json','COUNTERFACTUAL_ROWS.json','ENDPOINT_PARITY.json','MISSING_INPUTS.json','VALIDATION.json','FRESH_ENDPOINT_PARITY.json','RECOMPUTED.json','REFUSAL_EFFECTS.json','F1_COMPARISON.json','FIX_NOTES.md']]
    files+=sorted(A.PROV.glob('*.json'))+sorted((O/'executed_sources').glob('*.py'))+[A.HERE/f for f in ['RULES.md','run.sh','analyze.py','classify.py','finalize.py','recompute.py','STATUS.md']]
    files+=sorted((A.HERE/'review').glob('*'))
    with tarfile.open(O/'sb_mffix.tar','w') as tar:
        for p in files:tar.add(p,arcname=str(p.relative_to(A.HERE)),recursive=False)
    h=A.sha(O/'sb_mffix.tar');(O/'sb_mffix.tar.sha256').write_text(h+'  sb_mffix.tar\n')
    print(json.dumps(dict(report_lines=len(lines),archive_sha256=h,validation=checks)),flush=True)

if __name__=='__main__':main()
