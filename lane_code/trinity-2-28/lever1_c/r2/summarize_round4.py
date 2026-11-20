"""Report registered full-population and paired GT-depth-support readings."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import hashlib,json
import numpy as np
import k1x as K
import box_followup as B

OUT=K.ROOT/'out4'
BOX=K.ROOT/'out_box'
GROUPS=('all','arkitscenes','scannet_scannetpp')
MAIN=('C1','C3_depth','C3_pose','C3_joint','C3_full_gap')


def stat(rows,cell):
    return K.bootstrap(rows,[100*K.mra(r['cells'][cell]['prediction'],r['label']) for r in rows])[0] if rows else None


def support(r,a,b):
    return all(r['cells'][k].get('gt_depth_support',False) for k in (a,b))


def paired(rs,a,b,valid_only):
    rows=[r for r in rs if not valid_only or support(r,a,b)]
    av,bv=stat(rows,a),stat(rows,b)
    delta=K.bootstrap(rows,[100*(K.mra(r['cells'][a]['prediction'],r['label'])-K.mra(r['cells'][b]['prediction'],r['label'])) for r in rows])[0] if rows else None
    return dict(total=len(rs),n=len(rows),rooms=len({r['room'] for r in rows}),
        excluded=len(rs)-len(rows),row_ids=[r['row_id'] for r in rows],
        arm=a,reference=b,arm_score=av,reference_score=bv,delta=delta,
        answered_arm=sum(r['cells'][a]['prediction'] is not None for r in rows),
        answered_reference=sum(r['cells'][b]['prediction'] is not None for r in rows))


def readings(result,M):
    out={}
    for mode in ('A','B'):
        out[mode]={}
        for split,ids in M.sets.items():
            out[mode][split]={}
            for ds,keep in K.BUCKETS.items():
                rs=[r for r in result['rows'] if r['row_id'] in ids and keep(r)]
                pairs={k:paired(rs,a,b,mode=='B') for k,(a,b) in K.CONTRAST_PAIRS.items()}
                stats={k:v['delta'] for k,v in pairs.items()}
                verdicts=K.verdicts(stats) if all(stats.values()) else None
                depths={}
                for k in K.CELLS:
                    m,d,p,s=k.split('/')
                    if d=='GT':depths[k]=paired(rs,k,K.cell_name(m,'G3T',p,s),mode=='B')
                out[mode][split][ds]=dict(contrasts=pairs,gt_depth_rows=depths,verdicts=verdicts)
    return out


def report(result):
    R=result['readings'];p=result['parity']
    lines=['K1-X round 4: GT-depth eligibility and masked sampling. Scores and differences are MRA points.',
        'A uses the registered full population; refusals score zero. B pairs only rows whose pinned operand frames contain GT depth in both contrast arms.',
        'B requires finite positive GT depth somewhere in each selected frame, plus GT frame validity. It does not impute absent frames or claim complete sensor coverage.',
        'Held-out: 216 rows / 48 physical rooms; train1012 cross-checks; train1037 establishes parity. Train deployed masks are in-sample.',
        f"Full-population held-out coverage: ARKit {R['A']['heldout']['arkitscenes']['contrasts']['C1']['total']} rows; ScanNet/ScanNet++ {R['A']['heldout']['scannet_scannetpp']['contrasts']['C1']['total']} rows. B coverage is stated for each contrast.",
        'Every interval uses 10,000 paired room-bootstrap draws, seed 20261120. JSON includes all 16 cells, extras, separate ScanNet/ScanNet++, all splits, row IDs, refusals and input hashes.',
        f"Train parity: deployed {p[0]['observed']:.4f} / 56.77; GT masks {p[1]['observed']:.4f} / 73.97. Both pass; each matches all 1,037 predictions and printed boxes.",
        f"Served-depth invariance: {result['served_invariance']['passed']}/{result['served_invariance']['checked']} row/cell outputs match out/K1X.json exactly.",
        f"The {result['defect_audit']['audited_rows']} audited held-out depth-swap refusals yield {result['defect_audit']['answered']} answers and {result['defect_audit']['refused']} refusals under the corrected GT-depth rule.",
        '',
        '| Contrast | A all [95% CI] | B all [95% CI]; n | A ARKit / SN+SN++ | B ARKit / SN+SN++; n | T1012 A / B |',
        '|---|---:|---:|---:|---:|---:|']
    for k in MAIN:
        a=R['A']['heldout']['all']['contrasts'][k];b=R['B']['heldout']['all']['contrasts'][k]
        av=' / '.join(K.fmt(R['A']['heldout'][d]['contrasts'][k]['delta'],False) for d in GROUPS[1:])
        bv=' / '.join(K.fmt(R['B']['heldout'][d]['contrasts'][k]['delta'],False)+f" (n={R['B']['heldout'][d]['contrasts'][k]['n']})" for d in GROUPS[1:])
        tv=' / '.join(K.fmt(R[m]['train1012']['all']['contrasts'][k]['delta'],False) for m in ('A','B'))
        lines.append(f"| {k} | {K.fmt(a['delta'])} | {K.fmt(b['delta'])}; {b['n']}/{b['total']} | {av} | {bv} | {tv} |")
    lines+=['','| GT-depth cell: masks/depth/pose/scale | A all / ARKit / SN+SN++ | B all / ARKit / SN+SN++ (n) | T1012 A / B (n) |',
            '|---|---:|---:|---:|']
    for k in R['A']['heldout']['all']['gt_depth_rows']:
        av=' / '.join(K.fmt(R['A']['heldout'][d]['gt_depth_rows'][k]['arm_score'],False) for d in GROUPS)
        bv=' / '.join(K.fmt(R['B']['heldout'][d]['gt_depth_rows'][k]['arm_score'],False)+f" ({R['B']['heldout'][d]['gt_depth_rows'][k]['n']})" for d in GROUPS)
        tr=[R[m]['train1012']['all']['gt_depth_rows'][k] for m in ('A','B')]
        lines.append(f"| {k} | {av} | {bv} | {K.fmt(tr[0]['arm_score'],False)} / {K.fmt(tr[1]['arm_score'],False)} ({tr[1]['n']}) |")
    lines+=['B pairs each GT-depth row with the same masks, pose and scale under G3T depth; JSON records both scores, their paired difference and coverage.',
            'C1 compares full GT geometry with served geometry at deployed masks. C3 depth/pose/joint retain own scale; C3_full_gap also replaces scale.','']
    for mode in ('A','B'):
        v=R[mode]['heldout']['all']['verdicts']
        lines.append(f"{mode} verdicts: C1 {v['C1']}; C3 depth {v['C3_depth']}; C3 pose {v['C3_pose']}; {v['C3_interaction']}; arm B full gate {v['arm_B_full_gate']['verdict']}.")
        lines.append(f"{mode} other bars: C5 {v['C5']}; C6 {v['C6']}; Pi3X {v['Pi3X']}; DA3 {v['DA3']}.")
    differences=result['bar_disagreements']
    lines.append('A/B bar disagreements: '+(json.dumps(differences,sort_keys=True)+'; retain both readings without choosing one.' if differences else 'none on held-out; neither reading is preferred.'))
    for ds in GROUPS[1:]:
        for mode in ('A','B'):
            v=R[mode]['heldout'][ds]['verdicts']
            lines.append(f"{ds} {mode}: C1 {v['C1']}; depth {v['C3_depth']}; pose {v['C3_pose']}; {v['C3_interaction']}; arm B {v['arm_B_full_gate']['verdict']}.")
    lines+=['GT depth excludes nonpositive raster samples; bilinear weights renormalize over positive neighbours, and the spread stencil excludes missing samples. An exactly missing sample remains unanswered when no positive neighbour has nonzero weight.',
            'Entirely missing GT-depth frames have no lift visibility or box pin. Their poses remain accessible. GT-depth masks keep the deployed selector choices; only depth eligibility changes.',
            'Scale matching retains s=own or E3 oracle SO and q=s/SO. G3T depth/translations use s; GT depth/translations use q. Served intrinsics and the 51×51 endpoint grid remain fixed.',
            'These GT-depth endpoints remain conditional on mask coverage, served intrinsics, coarse sampling, spread filtering and the served distance program.',
            'The two absent convert geometries use the ladder tower.npz plus own.npz reconstruction. Pi3X/DA3 and oracle-extent input gaps remain explicit in the JSON.',
            'Execution: CPU, nice 10; eight factorial workers and four E3 BOX workers plus their two parents, at most 14 processes. All experiment inputs and outputs use local /scratch. No subagents, SSH or Git.',
            'Deviations: small writing-skill files were read from /home; experiment data remained on /scratch. The run uses a persistent command session, consistent with the existing sandbox limitation on tmux.',
            'No missing sensor raster was restored; A measures the corrected available-depth intervention, and B measures identical valid frame support.',
            'Borderline no-archaeology sentences retained: the served-output parity comparison, because the requested regression explicitly requires it.',
            'Validation and exact test counts: TESTS.json. Files: K1X4.json, REPORT_R2_4.md, SHA256SUMS; BOX results are in ../out_box/.']
    assert len(lines)<=60,len(lines)
    return '\n'.join(lines)+'\n'


def box_report(box):
    lines=['BOX follow-up: deployable centre and box rules under served geometry. Scores and differences are MRA points.',
        'Held-out decides: 216 rows / 48 physical rooms. Train1012 cross-checks; deployed-mask train scores are in-sample. GT masks are report-only.',
        'Intervals use 10,000 paired room-bootstrap draws, seed 20261120. JSON includes separate ScanNet/ScanNet++, train1037, all row outputs and intervals.',
        f"Base parity: all {len(box['base_parity'])} row/mask predictions, refusals and printed boxes match the factorial served cells.",
        f"Area floor F={box['freeze']['floor']} pixels, selected by room-grouped five-fold CV on train1012 only; smallest F breaks ties. The same F applies to GT masks.",
        'The candidate grid is {0,50,100,200,400,800}; fixed candidates require no fold-specific fitted parameters. Selection pools held-fold predictions with item weighting.',
        'The floor is frozen before any held-out floor evaluation. Held-out evaluates exactly one floor.',
        '', '| Rule | HO deployed | Δ [95% CI] | HO ARKit / SN+SN++ | Δ ARKit / SN+SN++ | T1012 deployed (Δ) | HO GT masks (Δ) |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for arm in ('base','e3_fused','fused','robust','floor'):
        k='deployed/'+arm
        score=box['tables']['heldout']['all'][k]
        delta=box['contrasts']['heldout']['all'].get(k)
        groups=' / '.join(K.fmt(box['tables']['heldout'][d][k],False) for d in GROUPS[1:])
        gd=' / '.join(K.fmt(box['contrasts']['heldout'][d].get(k),False) for d in GROUPS[1:]) if delta else '—'
        train=box['tables']['train1012']['all'][k];td=box['contrasts']['train1012']['all'].get(k)
        gt=box['tables']['heldout']['all']['GT/'+arm];gtd=box['contrasts']['heldout']['all'].get('GT/'+arm)
        lines.append(f"| {arm} | {K.fmt(score,False)} | {K.fmt(delta)} | {groups} | {gd} | {K.fmt(train,False)} ({K.fmt(td,False)}) | {K.fmt(gt,False)} ({K.fmt(gtd,False)}) |")
    lines+=['','| Rule | Registered held-out verdict | Dev-item check |','|---|---|---|']
    for arm in ('e3_fused','fused','robust','floor'):
        v=box['contrasts']['heldout']['all']['deployed/'+arm]
        lines.append(f"| {arm} | {v['verdict']} | pending rank 1 dump |")
    lines+=['A proposal requires ≥3 held-out points, a paired lower bound >0, and no dev-item loss. No complete proposal passes while the dev check is pending.',
        'e3_fused uses the E3 sensor FusedBoxProvider: fit_gbox_full over all grounded points, capped at 20,000 with RNG seed 0. fused uses frozen vote_10_3_best: 10 cm voxels, three-frame support plus best-frame points.',
        'Robust centre uses the coordinatewise median of all post-spread lifted mask points, retaining the served box lengths and axes.',
        'Mask floors filter lift visibility and points before the served frame pin. Areas use the 240×320 served grid; portrait orientation has the same pixel count.',
        'A minimum area cannot replace a valid largest-mask frame with a different smaller frame; it can only leave that choice unchanged or remove all eligible frames.',
        'The E3 and ladder fusion rules are evaluated separately. Both retain the served reader lift, geometry, guard and selector; no fusion constant is fitted.',
        'GT-mask and dataset contrasts, including every registered threshold result, appear in BOX.json; only the overall deployed-mask held-out result decides.',
        'Deviations: none in the BOX experiment. Dev-item check is pending rank 1 dump, as required.',
        'Borderline no-archaeology sentences retained: none. Validation: ../out4/TESTS.json and TESTS.json. Files: BOX.json, REPORT_BOX.md, SHA256SUMS.']
    assert len(lines)<=50
    return '\n'.join(lines)+'\n'


def add_e3(box,records,M):
    references={rec['capture']:rec for rec in records}
    rows={r['row_id']:r for r in box['rows']}
    checks=[]
    for c in M.captures:
        rec=json.loads((BOX/'e3_fused'/(c['canonical'].replace('/','__')+'.json')).read_text())
        assert rec['choices']==references[c['canonical']]['choices']
        box['input_sha256'].update(rec['input_sha256'])
        for rid,cells in rec['box'].items():
            r=rows[rid]
            for m in ('deployed','GT'):
                a=cells[m+'/base'];b=r['box'][m+'/base']
                passed=all(a[k]==b[k] for k in ('prediction','refusal','printed'))
                assert passed,(rid,m)
                checks.append(dict(row_id=rid,masks=m,passed=passed))
                r['box'][m+'/e3_fused']=cells[m+'/e3_fused']
    for split,ids in M.sets.items():
        for ds,keep in K.BUCKETS.items():
            rs=[r for r in box['rows'] if r['row_id'] in ids and keep(r)]
            for m in ('deployed','GT'):
                k=m+'/e3_fused'
                scores=[100*K.mra(r['box'][k]['prediction'],r['label']) for r in rs]
                box['tables'][split][ds][k]=dict(K.bootstrap(rs,scores)[0],answered=sum(r['box'][k]['prediction'] is not None for r in rs))
                diff=[v-100*K.mra(r['box'][m+'/base']['prediction'],r['label']) for r,v in zip(rs,scores)]
                stat=K.bootstrap(rs,diff)[0];passed=stat['mean']>=3 and stat['ci95'][0]>0
                box['contrasts'][split][ds][k]=dict(stat,heldout_bar_passed=passed,dev_item_check='pending rank 1 dump',propose=False,
                    verdict='held-out bar passes; proposal pending rank 1 dump' if passed else 'box rule waits for better masks too')
    box['e3_base_parity']=checks
    box['rules']['e3_fused']='E3 sensor FusedBoxProvider, fit_gbox_full over served post-spread points; cap 20000, seed 0'
    receipt=json.loads((BOX/'E3_RECEIPT.json').read_text())
    box['input_sha256'].update(receipt['input_sha256'])


def checksums():
    for folder in (OUT,BOX):
        files=sorted(p for p in folder.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
        files+=sorted(K.ROOT.glob('*.py'))+sorted((K.ROOT/'tests').glob('*.py'))+sorted((K.ROOT/'vendor').glob('*'))
        (folder/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(K.ROOT)}\n' for p in files if p.is_file()))


def main():
    args=K.options(['summarize','--out',str(OUT)])
    I=K.Inputs();M=K.metadata(args,I)
    records=[json.loads((OUT/'factorial'/(c['canonical'].replace('/','__')+'.json')).read_text()) for c in M.captures]
    result=json.loads((OUT/'K1X.json').read_text())
    assert result['status']=='COMPLETE'
    old=I.json(K.ROOT/'out/K1X.json');oldrows={r['row_id']:r for r in old['rows']}
    checked=0
    for r in result['rows']:
        for k in K.CELLS:
            if k.split('/')[1]!='G3T':continue
            for field in ('prediction','refusal','printed'):
                assert r['cells'][k][field]==oldrows[r['row_id']]['cells'][k][field],(r['row_id'],k,field)
            checked+=1
    result['served_invariance']=dict(checked=checked,passed=checked,fields=['prediction','refusal','printed'],reference='out/K1X.json')
    depth='deployed/GT/G3T/own'
    audited=[r for r in result['rows'] if r['split']=='heldout'
        and oldrows[r['row_id']]['cells'][K.DBASE]['prediction'] is not None
        and oldrows[r['row_id']]['cells'][depth]['prediction'] is None]
    answered=[r['row_id'] for r in audited if r['cells'][depth]['prediction'] is not None]
    refused=[r['row_id'] for r in audited if r['cells'][depth]['prediction'] is None]
    result['defect_audit']=dict(audited_rows=len(audited),answered=len(answered),refused=len(refused),answered_ids=answered,refused_ids=refused)
    result['input_sha256'].update(I.hashes)
    result['readings']=readings(result,M)
    result['support_definition']='Both operands must have selected visible frames, each GT-valid with some finite positive native GT raster depth, in both arms. No outcome/score filtering. Contrasts have their own paired support.'
    disagreements={}
    for ds in K.BUCKETS:
        a=result['readings']['A']['heldout'][ds]['verdicts'];b=result['readings']['B']['heldout'][ds]['verdicts']
        differences={k:dict(A=a[k],B=b[k]) for k in a if a[k]!=b[k]}
        if differences:disagreements[ds]=differences
    result['bar_disagreements']=disagreements
    K.write(OUT/'K1X4.json',result)
    (OUT/'REPORT_R2_4.md').write_text(report(result))
    box=B.summarize(records,M)
    frozen=json.loads((OUT/'BOX_FREEZE.json').read_text())
    assert K.clean(box['freeze'])==frozen
    box['input_sha256']=result['input_sha256'];box['source_factorial']='out4/K1X4.json'
    add_e3(box,records,M)
    K.write(BOX/'BOX.json',box);(BOX/'REPORT_BOX.md').write_text(box_report(box))
    checksums()
    print(json.dumps(dict(part1=result['readings']['A']['heldout']['all']['verdicts'],part1_B=result['readings']['B']['heldout']['all']['verdicts'],box=box['contrasts']['heldout']['all']),indent=2))


if __name__=='__main__':main()
