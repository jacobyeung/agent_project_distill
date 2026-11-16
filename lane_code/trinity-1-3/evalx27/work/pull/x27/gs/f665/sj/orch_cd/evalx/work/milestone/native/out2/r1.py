import math
from collections import Counter

FAMILIES = ('camera_displacement','camera_movement_direction','camera_rotation',
            'object_abs_distance','room_size_estimation')
ALIASES = {'absolute_distance_object':'object_abs_distance',
           'absolute_size_room':'room_size_estimation'}
NOT_MEASURABLE = 'NOT MEASURABLE: this checkpoint has no trained forced-path flags'


def family(typ):
    return ALIASES.get(typ,typ)


def accounting(decoded):
    calls=decoded.get('calls',[])
    if not isinstance(calls,list):
        raise ValueError('Malformed call journal')
    errors=decoded.get('errors',0)
    if type(errors) is not int or errors<0:
        raise ValueError('Malformed call-error count')
    version=sum(c.get('kind')=='error' and any(s in str(c.get('code','')) for s in
                ('version','requires_v3.','unsupported_program')) for c in calls)
    version=max(version,int(bool(decoded.get('version_error'))))
    errors=max(errors,sum(c.get('kind')=='error' or bool(c.get('verify_error')) for c in calls))
    return dict(called=bool(calls),call_errors=errors,version_errors=version)


def rules(bundle,raised=(),step=100):
    if bundle.get('schema')!='legs1-r1-nomdg-v1' or set(bundle.get('arms',{}))!={'unflagged','scripted'}:
        raise ValueError('R1 requires the no-MDG paired bundle')
    arms={}
    for arm,rows in bundle['arms'].items():
        idx={}
        for row in rows:
            if row['key'] in idx:
                raise ValueError('Duplicate R1 item')
            if row.get('arm')!=arm:
                raise ValueError('R1 row arm differs')
            idx[row['key']]=row
        arms[arm]=idx
    keys=set(arms['unflagged'])
    if not keys or keys!=set(arms['scripted']) or keys!=set(bundle['expected_keys']):
        raise ValueError('R1 membership differs from the bound cohort')
    identity=('room','question_type','stratum','checkpoint_sha256','perception_identity',
              'prefill_identity','binding')
    for key in keys:
        a,b=(arms[arm][key] for arm in ('unflagged','scripted'))
        if any(a.get(k)!=b.get(k) for k in identity):
            raise ValueError('R1 must share checkpoint, perception, prefill, label stratum and room')
        for row in (a,b):
            if family(row['question_type']) not in FAMILIES:
                raise ValueError('R1 row outside the five routed types')
            if not row.get('perception_identity') or row.get('mask_source')!=(
                    'svp_sam3' if family(row['question_type'])=='object_abs_distance' else None):
                raise ValueError('R1 perception source missing or inconsistent')
            if row['perception_identity']!=bundle['perception_by_key'][key]:
                raise ValueError('R1 perception differs from its bound item')
            if row['checkpoint_sha256']!=bundle['artifact_sha256'] or row['binding']!=bundle['binding']:
                raise ValueError('R1 checkpoint/request differs')
            if type(row.get('called')) is not bool or any(
                    type(row.get(k)) is not int or row[k]<0 for k in ('call_errors','version_errors')):
                raise ValueError('R1 requires explicit call/error accounting')
            if type(row.get('no_answer')) is not bool:
                raise ValueError('R1 requires explicit no-answer accounting')
            for value in row['scores'].values():
                if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1):
                    raise ValueError('Invalid R1 score')
            if 'decode' in row and any(row[k]!=v for k,v in accounting(row['decode']).items()):
                raise ValueError('R1 accounting differs from decode')
            if row['no_answer'] and any(v not in (None,0.) for v in row['scores'].values()):
                raise ValueError('R1 no-answer rows must score zero')
            if row['arm']=='scripted' and 'decode' in row and row['no_answer']!=row['decode'].get('strict_no_answer'):
                raise ValueError('R1 scripted no-answer accounting differs from decode')
    out={};missing=[];unmeasurable=[]
    for typ in FAMILIES:
        selected=sorted(k for k in keys if family(arms['unflagged'][k]['question_type'])==typ)
        if not selected:
            missing.append(typ)
            out[typ]=dict(items=0,R1='NOT MEASURABLE: no frozen dev-S1 items',
                          R1b=NOT_MEASURABLE,R2=NOT_MEASURABLE)
            continue
        rs={a:[idx[k] for k in selected] for a,idx in arms.items()}
        n=len(selected)
        labels={('released_answer' if r['stratum']=='primary' else 'answer') for r in rs['unflagged']}
        if len(labels)!=1:
            raise ValueError('R1 type mixes label authorities')
        label=labels.pop()
        if any(r['scores'].get(label) is None for rows in rs.values() for r in rows):
            raise ValueError('R1 score missing; refusals must score zero')
        score={a:100*sum(r['scores'][label] for r in rows)/n for a,rows in rs.items()}
        calls=sum(r['called'] for r in rs['unflagged'])
        errors=sum(r['call_errors'] for rows in rs.values() for r in rows)
        versions=sum(r['version_errors'] for rows in rs.values() for r in rows)
        gap=score['unflagged']-score['scripted']
        answered=[k for k in selected if not arms['scripted'][k]['no_answer']]
        conditional={a:100*sum(idx[k]['scores'][label] for k in answered)/len(answered)
                     if answered else None for a,idx in arms.items()}
        conditional_gap=conditional['unflagged']-conditional['scripted'] if answered else None
        stricter=max(abs(gap),abs(conditional_gap)) if answered else None
        fail=not answered or stricter>5+1e-10 or calls/n<.95 or errors>0 or versions>0
        if not answered:
            unmeasurable.append(typ)
        verdict=('NOT MEASURABLE: scripted arm answered zero items' if not answered else
                 'STOP at m200: this type still fails after rows were raised at m100'
                 if fail and step==200 and typ in {family(t) for t in raised} else
                 'FAIL: send this form more rows at the next boundary' if fail else 'PASS')
        if step not in (100,200):
            verdict='DIAGNOSTIC ONLY: '+('not measurable' if not answered else
                                       'frozen checks not met' if fail else 'frozen checks met')
        codes=Counter()
        for rows in rs.values():
            for row in rows:
                decoded=row.get('decode',{})
                codes.update(c.get('code','unnamed_call_error') for c in decoded.get('calls',[])
                             if c.get('kind')=='error')
                if decoded.get('refusal'):
                    codes[decoded['refusal']]+=1
        out[typ]=dict(items=n,label=label,routed_score_pct=score['unflagged'],
            scripted_score_pct=score['scripted'],routed_minus_scripted_pp=gap,
            scripted_no_answer_count=n-len(answered),
            both_failed_count=sum(arms['scripted'][k]['no_answer'] and arms['unflagged'][k]['no_answer']
                                  for k in selected),
            both_zero_score_count=sum(all(arms[a][k]['scores'][label]==0 for a in arms) for k in selected),
            script_answered_items=len(answered),
            script_answered_routed_score_pct=conditional['unflagged'],
            script_answered_scripted_score_pct=conditional['scripted'],
            routed_minus_scripted_on_script_answered_pp=conditional_gap,
            r1_gap_used_abs_pp=stricter,r1_gap_rule='stricter absolute gap: all items or script-answered items',
            call_rate_pct=100*calls/n,call_errors=errors,version_errors=versions,
            error_codes=dict(codes),
            R1=verdict,R1b=NOT_MEASURABLE,R2=NOT_MEASURABLE)
    return dict(per_type=out,missing_types=missing,unmeasurable_types=unmeasurable,
                report_scope='REGISTERED READOUT; decision remains with ORCH' if step in (100,200) else
                             'REHEARSAL DIAGNOSTIC ONLY' if step==50 else
                             'REPORTED MILESTONE; no registered stop rule; decisions remain with ORCH',
                training_decision_allowed=False,
                perception_disclosure="The routed camera scores measure programs over the frozen tower's poses and depth, with scale and gravity supplied by the checkpoint.",
                completeness='INCOMPLETE: missing or unmeasurable routed types' if missing or unmeasurable else 'COMPLETE',
                R1b=NOT_MEASURABLE,R2=NOT_MEASURABLE,
                qualification='Natural no-flag R1 only; strict scripts use the same bound runtime perception')
