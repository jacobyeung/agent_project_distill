"""Render verified audit artifacts; run bash run.sh finalize.py."""
import collections, hashlib, json, tarfile
from pathlib import Path
import numpy as np
import analyze as A

O=A.OUT
def load(p):return json.loads(p.read_text())
def pc(v,n):return f'{100*v/n:.1f}' if n else 'NA'
def failure_table(groups):
    lines=['| Group | Rows | Visible frames | No proposal % | Omitted % | Wrong instance % | Wrong class % | Partial % | Merged % | Other % | Correct % |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,g in groups.items():
        n=g['visible_valid'];ct=g['failure']['0.5']
        lines.append('| '+str(name)+' | '+str(g.get('rows','—'))+' | '+str(n)+' | '+' | '.join(pc(ct.get(k,0),n) for k in A.KINDS)+' |')
    return lines

def main():
    s=load(O/'SPLITS.json');a=load(O/'ATTRIBUTION.json');m=load(O/'MASKFAIL.json')
    parity=load(O/'ENDPOINT_PARITY.json')
    assert len(parity['rows'])==2074 and all(x['passed'] and x['prediction']==x['expected_prediction'] for x in parity['rows'])
    cf=load(O/'COUNTERFACTUAL_ROWS.json');arms=collections.defaultdict(list)
    for x in cf['rows']:arms[x['arm']].append(x)
    assert len(arms)==48 and all(len(x)==1037 and len({r['row_id'] for r in x})==1037 for x in arms.values())
    r=m['records'];g=s['overall'];v=g['visible_valid'];avail=g['availability']['0.5']
    # Area bins partition frames, so omit the pricing-frame statistic from them.
    for group in s['by_share'].values():group.pop('pricing_best_frame_iou',None)
    s['input_sha256'][str(Path(__file__).resolve())]=A.sha(__file__)
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
        parts.insert(6,cell);table[i]='|'.join(parts)
    table[-1]=table[-1].replace('Rules: RULES.md.','Rules: [RULES.md](../RULES.md).')
    (O/'FIRST_TABLE.md').write_text('\n'.join(table)+'\n')
    split=['Primary threshold 0.5; visible valid operand-frames; percentages sum to 100 within rounding. Full threshold sensitivity, IoU distributions, and candidate availability appear in SPLITS.json.','']
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
        '2. Omitted: an overlapping proposal exists but the selected track supplies no mask in that frame.',
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
        '| IoU threshold | Correct % | Wrong frames | Correct deployed candidate % of wrong | Teacher-only correct % of wrong |',
        '|---|---:|---:|---:|---:|']
    for t in A.THRESH:
        q=g['availability'][str(t)];ct=g['failure'][str(t)];lines.append(f'| {t} | {pc(ct.get("correct",0),v)} | {q["wrong"]} | {pc(q["deployed_correct"],q["wrong"])} | {100*q["teacher_only_correct"]/q["wrong"]:.2f} ({q["teacher_only_correct"]} frames) |')
    lines+=['',f'At 0.5, {avail["deployed_correct"]:,}/{avail["wrong"]:,} wrong frames have a correct deployed proposal: a selection/track-retention failure. Another {avail["teacher_only_correct"]:,} have a correct same-name teacher proposal only; {avail["neither_correct"]:,} have none in either recorded pool.',
        'The deployed pool uses its raw-name retention (joint floor 0.05, cap 30); the teacher uses floor 0.2, cap 10. Teacher-only matches establish potential proposal availability, not availability to the deployed selector. Discarded SAM logits and other-name teacher prompts are outside this claim.',
        f'Teacher status is MISSING for {avail["teacher_missing"]} wrong frames; {avail["unknown_teacher_without_deployed"]} also lack a correct deployed proposal, so joint absence is unknown. Exact missing paths: [MISSING_INPUTS.json](MISSING_INPUTS.json). Exact GT labels supply class identity; no synonym mapping is invented.', '',
        'Dataset, area-bin, and top-30 class failure tables: [SPLITS.md](SPLITS.md). All three thresholds and candidate availability by group: [SPLITS.json](SPLITS.json). All independent/cumulative scores, refusal counts, gap fractions, and incremental intervals: [ATTRIBUTION.json](ATTRIBUTION.json).', '',
        'Commands (run from the workspace; run.sh enforces CPU-only, nice 10, eight-thread limits):',
        '`bash run.sh analyze.py measure` measures overlaps and verifies exact A0/A2 parity; `bash run.sh classify.py` applies RULES.md and produces MASKFAIL.json, all distributions/splits, and FIRST_TABLE.md.',
        '`bash run.sh analyze.py price` produces 48 interventions (three thresholds × independent/cumulative × eight kinds), each on all 1,037 rows; 10,000 room-bootstrap draws, seed 20261119.',
        '`bash run.sh finalize.py` validates counts and endpoint closure, renders this report and SPLITS.md, and creates sb_maskfail.tar plus its SHA256 file.',
        'Input SHA256 values are recorded in every output JSON; each frame record references its capture provenance JSON by SHA256. No held-out capture is evaluated.']
    assert len(lines)<=80,len(lines)
    (O/'MASKFAIL_REPORT.md').write_text('\n'.join(lines)+'\n')
    # Validate the record provenance chain and generated artifacts before packaging.
    prov={}
    for x in r:
        for path,h in x['input_sha256'].items():
            if path not in prov:prov[path]=A.sha(path)
            assert prov[path]==h
    checks=dict(records=len(r),rows=1037,captures=len({x['capture'] for x in r}),physical_rooms=192,report_lines=len(lines),
        prediction_parity='A0 and A2 exact for every row; checked during measure',cumulative_closure='Exact A2 predictions at all thresholds; checked during price',
        input_sha256={str(O/f):A.sha(O/f) for f in ['MASKFAIL.json','SPLITS.json','ATTRIBUTION.json','COUNTERFACTUAL_ROWS.json','ENDPOINT_PARITY.json']})
    checks['input_sha256'][str(Path(__file__).resolve())]=A.sha(__file__)
    A.write(O/'VALIDATION.json',checks)
    A.status(f'Complete: 1,037 training rows, 66,368 operand-frame records, 209 captures, 192 rooms. A0 and A2 reproduce exactly; all cumulative interventions close to A2. MASKFAIL_REPORT.md has {len(lines)} lines. FIRST_TABLE.md, split tables, provenance, counterfactual scores, and sb_maskfail.tar with SHA256 are ready.')
    files=[O/f for f in ['MASKFAIL_REPORT.md','MASKFAIL.json','FIRST_TABLE.md','SPLITS.md','SPLITS.json','ATTRIBUTION.json','COUNTERFACTUAL_ROWS.json','ENDPOINT_PARITY.json','MISSING_INPUTS.json','VALIDATION.json']]
    files+=sorted(A.PROV.glob('*.json'))+sorted((O/'executed_sources').glob('*.py'))+[A.HERE/f for f in ['RULES.md','run.sh','analyze.py','classify.py','finalize.py','STATUS.md']]
    with tarfile.open(O/'sb_maskfail.tar','w') as tar:
        for p in files:tar.add(p,arcname=str(p.relative_to(A.HERE)),recursive=False)
    h=A.sha(O/'sb_maskfail.tar');(O/'sb_maskfail.tar.sha256').write_text(h+'  sb_maskfail.tar\n')
    print(json.dumps(dict(report_lines=len(lines),archive_sha256=h,validation=checks)),flush=True)

if __name__=='__main__':main()
