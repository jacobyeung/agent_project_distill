"""Apply the frozen P0 rules; missing measurements can never become a pass."""
import argparse
import json
import math
from pathlib import Path
from probe_common import *


def value(obj,*keys):
    for key in keys:
        if not isinstance(obj,dict):return None
        obj=obj.get(key)
    if isinstance(obj,dict):obj=obj.get('value')
    return float(obj) if isinstance(obj,(int,float)) and math.isfinite(obj) else None


def verdict(checks):
    if any(x is False for x in checks):return 'FAIL'
    if any(x is None for x in checks):return 'PENDING'
    return 'PASS'


def ge(x,y):return None if x is None or y is None else x>=y


def threshold(metric,minimum,strict=False):
    if not isinstance(metric,dict) or any(metric.get(k) is None for k in ('value','lo','hi')):
        return 'PENDING'
    if metric['lo']>minimum if strict else metric['lo']>=minimum:return 'PASS'
    if metric['hi']<=minimum if strict else metric['hi']<minimum:return 'FAIL'
    return 'INCONCLUSIVE'


def combine(statuses):
    for status in ('FAIL','PENDING','INCONCLUSIVE'):
        if status in statuses:return status
    return 'PASS'


def parity_verdict(metric,boundary):
    if not metric or any(metric.get(k) is None for k in ('value','lo','hi')):return 'PENDING'
    if metric['lo']>boundary:return 'PASS'
    if metric['hi']<boundary:return 'FAIL'
    return 'INCONCLUSIVE'


def rules_for(tasks,reference):
    cfg=rules();t1=tasks.get('T1',{});t2=tasks.get('T2',{});t3=tasks.get('T3',{});t4=tasks.get('T4',{})
    features=t1.get('features',{});fused=t1.get('fused') or {};presence=t3.get('metrics',{});identity=t4.get('linear',{})
    ratios={}
    if t2.get('records') and reference.get('T2',{}).get('records'):
        ratios={k:paired_ratio(t2['records'],reference['T2']['records'],small) for k,small in [('all',False),('under_1pct',True)]}
    r4=[combine([threshold(identity.get('retrieval_gain'),cfg['R4']['retrieval_gain_min']),
                  threshold(identity.get('retrieval_gain'),0,True)]),
        combine([threshold(identity.get('member_auroc'),cfg['R4']['member_auroc_min']),
                 threshold(identity.get('member_auroc_gain'),0,True)])]
    parity=paired_difference(t1['predictions'],reference['T1']['predictions']) if t1.get('predictions') and reference.get('T1',{}).get('predictions') else None
    r1=[parity_verdict(parity,-cfg['R1']['reference_max_deficit'])]
    # The 90% bars reject only an interval wholly below the bar.
    for key in ('name_consistent','training_val_top1'):
        status=threshold(features.get(key),cfg['R1'][key+'_min'])
        r1.append('PASS' if status=='INCONCLUSIVE' else status)
    return {
      'R1':combine(r1), 'R1_paired_reference':parity,
      'R1+':combine([threshold(fused.get('gain'),cfg['R1+']['gain_min']),threshold(fused.get('gain'),cfg['R1+']['gain_lower_strict_min'],True)]),
      'R2':combine([threshold(ratios.get('all'),cfg['R2']['iou_ratio_min']),threshold(ratios.get('under_1pct'),cfg['R2']['small_iou_ratio_min'])]),
      'R3':combine([threshold(presence.get('auroc'),cfg['R3']['auroc_min']),threshold(presence.get('shortlist_delta'),-cfg['R3']['shortlist_recall_max_deficit'])]),
      'R4':'PASS' if 'PASS' in r4 else 'INCONCLUSIVE' if 'INCONCLUSIVE' in r4 else 'PENDING' if 'PENDING' in r4 else 'FAIL',
      'ratios':ratios}


def paired_difference(first,second):
    a={r['object_id']:r for r in first};b={r['object_id']:r for r in second}
    if not a or set(a)!=set(b) or len(a)!=len(first) or len(b)!=len(second):
        raise ValueError('Paired arm object cohorts differ')
    keys=sorted(a)
    if any(a[k]['scene']!=b[k]['scene'] for k in keys):raise ValueError('Paired rooms differ')
    return mean_ci([a[k]['on_target'] for k in keys],[b[k]['on_target'] for k in keys],
                   rooms=[gate.room(*a[k]['scene'].split('/')) for k in keys])


def choose(arms):
    def preds(a):return arms.get(a,{}).get('tasks',{}).get('T1',{}).get('predictions',[])
    def allowed(a,provisional=False):
        return all(arms[a]['rules'].get(k,'PENDING')!='FAIL' for k in (('R1',) if provisional else ('R1','R3')))
    comparisons={}
    available=[a for a in ['A1','A2','A8','A3','A5','A6','A7','A4','D2'] if preds(a)]
    for i,a in enumerate(available):
        for b in available[i+1:]:comparisons[a+'-'+b]=paired_difference(preds(a),preds(b))
    def difference(a,b):
        if a+'-'+b in comparisons:return comparisons[a+'-'+b]
        d=comparisons[b+'-'+a]
        return dict(d,value=-d['value'],lo=-d['hi'],hi=-d['lo'])
    def select(provisional):
        own='A1' if preds('A1') else 'A2' if preds('A2') else None
        if preds('A1') and preds('A2'):
            delta=difference('A1','A2')
            if delta['hi']<0 and allowed('A2',provisional):own='A2'
        selected=own
        if own:
            for arm in rules()['choice_order']:
                if arm in ('A1','A2') or not preds(arm):continue
                delta=difference(arm,own)
                if allowed(arm,provisional) and delta['lo']>0:
                    if selected==own:selected=arm
                    elif difference(arm,selected)['lo']>0:selected=arm
        if selected and not allowed(selected,provisional):selected=None
        return own,selected
    own,selected=select(False);_,provisional=select(True)
    mask_keys=selected if selected and arms[selected]['rules'].get('R2')=='PASS' else 'A7'
    mask_comparisons={}
    if mask_keys=='A7' and own:
        own_records=arms[own].get('tasks',{}).get('T2',{}).get('records',[])
        if own_records:
            for arm in rules()['choice_order']:
                if arm in ('A1','A2'):continue
                records=arms.get(arm,{}).get('tasks',{}).get('T2',{}).get('records',[])
                if not records:continue
                delta=paired_mask_difference(records,own_records)
                mask_comparisons[arm+'-'+own]=delta
                if delta and delta['lo']>0:
                    if mask_keys=='A7':mask_keys=arm
                    else:
                        best=arms[mask_keys]['tasks']['T2']['records']
                        head_to_head=paired_mask_difference(records,best)
                        mask_comparisons[arm+'-'+mask_keys]=head_to_head
                        if head_to_head and head_to_head['lo']>0:mask_keys=arm
    pending=[k for k in ('R1','R2','R3') if selected and arms[selected]['rules'].get(k,'PENDING')=='PENDING']
    return dict(keys=selected,selection_keys=selected,presence_keys=selected,provisional_keys=provisional,
                provisional_choice=('T1 provisionally chooses '+provisional+' for selection keys; R3 awaits teacher labels when PENDING.' if provisional else 'T1 has no eligible own selection baseline yet.'),
                own_default=own,paired_differences=comparisons,mask_paired_differences=mask_comparisons,
                ready_for_downstream=bool(selected and all(arms[selected]['rules'].get(k) in ('PASS','INCONCLUSIVE') for k in ('R1','R3'))),
                pending_rules=pending,waiting_for_choice=[] if selected else ['eligible T1 selection evidence'],
                add_g3t=arms.get('A4',{}).get('rules',{}).get('R4')=='PASS',
                g3t_rule_status=arms.get('A4',{}).get('rules',{}).get('R4','PENDING'),
                branch_s_selectors=[a for a,v in arms.items() if v['rules'].get('R1+')=='PASS'],
                mask_keys=mask_keys,masks_stay_sam=mask_keys=='A7',
                mask_role='frozen dense tower for masks only' if mask_keys not in (selected,'A7') else 'selection encoder' if mask_keys==selected else 'SAM 3 tower',
                pilot_path='Selection and presence pilot; masks follow mask_keys. R1 INCONCLUSIVE permits the pilot.',
                clean_read='Not authorized by this probe; a separate rev_ctrl decision card is required')


def paired_mask_difference(first,second):
    # Check identical masks, slots and objects before the paired object-level mean IoU contrast.
    paired_ratio(first,second)
    def rows(records):
        output=[]
        for r in records:
            values=[f['sam_iou'] for f in r['frames'] if f['sam_valid']]
            if values:output.append(dict(object_id=r['object_id'],scene=r.get('scene',r['object_id'].split('::')[0]),on_target=float(np.mean(values))))
        return output
    a,b=rows(first),rows(second)
    return paired_difference(a,b) if a and b else None


def paired_ratio(arm_records,ref_records,small=False):
    def collect(records):
        return {r['object_id']:[f['sam_iou'] for f in r['frames'] if f['sam_valid'] and (not small or f['area']<rules()['R2']['small_area_lt'])] for r in records}
    if {r['object_id']: [(f['slot'],f['area'],f['sam_valid']) for f in r['frames']] for r in arm_records}!={r['object_id']: [(f['slot'],f['area'],f['sam_valid']) for f in r['frames']] for r in ref_records}:
        raise ValueError('R2 paired frame identities differ')
    a,b=collect(arm_records),collect(ref_records)
    if set(a)!=set(b):raise ValueError('R2 object cohorts differ')
    pairs=[]
    for k in sorted(a):
        if len(a[k])!=len(b[k]):raise ValueError('R2 frame cohorts differ')
        if a[k]:pairs.append(dict(object_id=k,a=float(np.mean(a[k])),b=float(np.mean(b[k]))))
    if not pairs:return None
    def metric(rows):
        denom=np.mean([r['b'] for r in rows]);return float(np.mean([r['a'] for r in rows])/denom) if denom>0 else None
    return object_bootstrap(pairs,metric)


def format_interval(metric,scale=1):
    if not isinstance(metric,dict) or any(metric.get(k) is None for k in ('value','lo','hi')):return 'PENDING'
    return f"{scale*metric['value']:.4f} [{scale*metric['lo']:.4f}, {scale*metric['hi']:.4f}]"


def run(args):
    root=Path(args.results);arms={};source_paths=[RULES_PATH]
    availability=json.loads(Path(args.availability).read_text()) if args.availability else {}
    for arm in rules()['execution_order']:
        tasks={}
        for task in ('T1','T2','T3','T4'):
            p=root/arm/(task+'.json')
            if p.exists():
                obj=json.loads(p.read_text())
                if obj.get('rules_sha256')!=sha256(RULES_PATH):raise ValueError(f'Metrics use different rules: {p}')
                if obj.get('arm')!=arm or obj.get('task')!=task:raise ValueError('Mislabeled metric file')
                for record in obj.get('records',obj.get('predictions',[])):
                    if 'scene' in record:gate.check_row(record,'tuning')
                    elif 'object_id' in record:gate.check_row(dict(scene=record['object_id'].split('::')[0]),'tuning')
                tasks[task]=obj;source_paths.append(p)
        arms[arm]=dict(tasks=tasks,availability=availability.get(arm,dict(status='unmeasured',reason='GPU job has not run')))
        for variant in ('features','fused'):
            p=root/arm/('routed_'+variant)/'ROUTED.json'
            if p.exists():
                routed=json.loads(p.read_text())
                if routed.get('rules_sha256')!=sha256(RULES_PATH):raise ValueError('Routed rules pin differs')
                arms[arm].setdefault('routed_gains',{})[variant]=routed
                source_paths.append(p)
    reference=arms['A7']['tasks']
    for arm,row in arms.items():
        for readout,key in [('final','final_control'),('unstandardized','unstandardized_control')]:
            controls={}
            for task in ('T1','T2','T3','T4'):
                p=root/arm/readout/(task+'.json')
                if p.exists():
                    obj=json.loads(p.read_text())
                    if obj.get('rules_sha256')!=sha256(RULES_PATH):raise ValueError('Control rules differ')
                    if obj.get('arm')!=arm or obj.get('task')!=task or obj.get('readout')!=readout:raise ValueError('Mislabeled control')
                    for record in obj.get('records',obj.get('predictions',[])):
                        gate.check_row(dict(scene=record.get('scene') or record['object_id'].split('::')[0]),'tuning')
                    controls[task]=obj;source_paths.append(p)
            row[key]=controls
        for filename,key in [('SMOKE.json','smoke'),('CHANNEL_ENERGY.json','channel_energy')]:
            p=root/arm/filename
            if p.exists():row[key]=json.loads(p.read_text());source_paths.append(p)
    for arm,row in arms.items():
        row['rules']=rules_for(row['tasks'],reference)
        if row['tasks'].get('T2',{}).get('status')=='complete' and reference.get('T2',{}).get('status')=='complete':
            row['R2_intervals']=dict(all=paired_ratio(row['tasks']['T2']['records'],reference['T2']['records']),
                                    small=paired_ratio(row['tasks']['T2']['records'],reference['T2']['records'],True))
    for row in arms.values():
        for key in ('final_control','unstandardized_control'):row[key+'_rules']=rules_for(row[key],arms['A7'][key])
    decision=choose(arms)
    decision['control_status']={a:'complete' if all(r[key].get(t,{}).get('status') in ('complete','feature_complete_fusion_pending') for key in ('final_control','unstandardized_control') for t in ('T1','T4')) else 'pending' for a,r in arms.items()}
    if decision['keys'] and decision['control_status'][decision['keys']]!='complete':decision['ready_for_downstream']=False
    participants=[row for row in arms.values() if row['availability'].get('status')=='available' or row['tasks']]
    measured=bool(participants) and all(all(row['tasks'].get(t,{}).get('status')=='complete' for t in ('T1','T2','T3','T4')) for row in participants)
    decision['status']='measured' if measured else 'PROVISIONAL_T1' if any(r['tasks'].get('T1',{}).get('predictions') for r in arms.values()) else 'PENDING_GPU_OR_INPUTS'
    card=dict(experiment='E-A',decision=decision,arms=arms,rules_sha256=sha256(RULES_PATH),
              provenance=receipt(source_paths,[Path(__file__),ROOT/'work/probe_common.py'],vars(args)))
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);write_json(out/'P0_CARD.json',card)
    lines=['# E-A frozen-feature probe decision','',f'Status: {decision["status"]}.',
           'Keys: '+str(decision['keys'])+'. Add G3T: '+str(decision['add_g3t'])+'.',
           decision['provisional_choice'],
           'Mask keys: '+decision['mask_keys']+' ('+decision['mask_role']+').',
           'Pending rules: '+', '.join(decision['pending_rules'])+'.','',
           '| Arm | R1 | R1+ | R2 | R3 | R4 | Input/status |','|---|---|---|---|---|---|---|']
    for arm,r in arms.items():
        lines.append('| '+arm+' | '+' | '.join(r['rules'][k] for k in ('R1','R1+','R2','R3','R4'))+' | '+r['availability'].get('reason',r['availability'].get('status',''))+' |')
    lines+=['','| Arm | Task | Metric | Standardized four taps [95% CI] | Standardized final layer [95% CI] | Unstandardized four taps [95% CI] |','|---|---|---|---|---|---|']
    paths=[('T1','features','on_target'),('T1','features','name_consistent'),('T1','features','training_val_top1'),
           ('T1','fused','gain'),('T2','metrics','sam_all'),('T2','metrics','sam_small'),('T2','metrics','gt_all'),
           ('T3','metrics','auroc'),('T3','metrics','shortlist_recall'),('T4','linear','top1'),('T4','linear','member_auroc')]
    for arm,r in arms.items():
        if not r['tasks']:
            lines.append(f'| {arm} | T1–T4 | All measurements | Pending | Pending | Pending |');continue
        for task,group,metric in paths:
            m=r['tasks'].get(task,{}).get(group) or {};m=m.get(metric)
            number=(f'{m["value"]:.4f} [{m["lo"]:.4f}, {m["hi"]:.4f}]'
                    if isinstance(m,dict) and all(m.get(k) is not None for k in ('value','lo','hi')) else 'Pending')
            control=r['final_control'].get(task,{}).get(group) or {};control=control.get(metric)
            control_number=(f'{control["value"]:.4f} [{control["lo"]:.4f}, {control["hi"]:.4f}]'
                            if isinstance(control,dict) and all(control.get(k) is not None for k in ('value','lo','hi')) else 'Pending')
            extra=r['unstandardized_control'].get(task,{}).get(group) or {};extra=extra.get(metric)
            extra_number=format_interval(extra)
            lines.append(f'| {arm} | {task} | {group}.{metric} | {number} | {control_number} | {extra_number} |')
    lines+=['','| Paired T1 difference | Points [95% CI] |','|---|---|']
    for pair,m in decision['paired_differences'].items():lines.append('| '+pair+' | '+format_interval(m,100)+' |')
    lines+=['','| Arm minus A7 (R1) | Points [95% CI] |','|---|---|']
    for arm,r in arms.items():lines.append('| '+arm+' | '+format_interval(r['rules']['R1_paired_reference'],100)+' |')
    lines+=['','Paired mask-only differences: `'+json.dumps(decision['mask_paired_differences'])+'`.','',
        '| Arm | Tap | Split | Native before | Native after | Head before | Head after |','|---|---|---|---|---|---|---|']
    for arm,r in arms.items():
        energy=r.get('channel_energy',{}).get('summary',[])
        if not energy:
            for tap in range(1,5):lines.append(f'| {arm} | {tap} | All | PENDING | PENDING | PENDING | PENDING |')
        else:
            for row in energy:lines.append(f"| {arm} | {row['tap']} | {row['split']} | {row['before']:.5f} | {row['after']:.5f} | {row['before_head']:.5f} | {row['after_head']:.5f} |")
    lines+=['','Energy shares are token-weighted means of the largest channel share after per-token LN, before/after training-only standardization.',
        'SAM 3 bf16 autocast: '+('PASS' if arms['A7'].get('smoke',{}).get('measurements') and all(m.get('bf16_autocast') for m in arms['A7']['smoke']['measurements']) else 'PENDING')+'.']
    lines+=['','All shares use [0,1] in JSON. Intervals use 4,000 paired room-cluster draws, preserving every object, seed 17.',
            'No clean-33 data enters this probe. Missing metrics leave their rules pending.',
            'Per-arm metrics, intervals, sample counts and routed diagnostics are stored in P0_CARD.json.']
    (out/'P0_CARD.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(decision))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',required=True)
    p.add_argument('--availability');p.add_argument('--out',default=str(ROOT/'out'));run(p.parse_args())
