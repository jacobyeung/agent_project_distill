"""Grade archived teacher answers offline and index distinct accepted questions."""
from __future__ import annotations
import argparse,hashlib,json,math,re,time
from pathlib import Path
from training_assets import DATA_ROOT,teacher_rows,sha,read_json,require_data_path

LABELS=DATA_ROOT/'offline_labels/v2/train50k_scene_reuse_labels.jsonl'
LABELS_SHA='50ef9cc160f1f6e22a64a0f922d22fb999df2c25809009b022ac0a62af55cd79'
NUMBER=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
UNITS={'m':'m','meter':'m','meters':'m','metre':'m','metres':'m',
    'cm':'cm','centimeter':'cm','centimeters':'cm','centimetre':'cm','centimetres':'cm',
    'ft':'ft','foot':'ft','feet':'ft','in':'in','inch':'in','inches':'in',
    'square meters':'m2','square meter':'m2','square metres':'m2','square metre':'m2','m²':'m2','m^2':'m2','m2':'m2',
    'square feet':'ft2','square foot':'ft2','ft²':'ft2','ft^2':'ft2','ft2':'ft2'}


def visible_content(content):
    if isinstance(content,str):return content
    if isinstance(content,list):
        return '\n'.join(str(p.get('text','')) for p in content if isinstance(p,dict) and not p.get('thought') and p.get('type') not in ('thinking','reasoning'))
    return ''


def final_answer(trace):
    for message in reversed(trace.get('trace',[])):
        if message.get('role') not in ('ai','assistant'):continue
        if message.get('tool_calls'):return None
        if message.get('provenance') in ('runner_synthetic_recovery','synthetic'):return None
        matches=re.findall(r'<ANSWER>\s*(.*?)\s*</ANSWER>',visible_content(message.get('content')),flags=re.I|re.S)
        return matches[-1].strip() if len(matches)==1 else None
    return None


def requested_unit(row):
    if row['question_type']=='object_counting':return None
    question=row['question'].lower()
    if row['question_type']=='room_size_estimation':
        choices=[canonical for label,canonical in UNITS.items() if canonical in ('m2','ft2') and re.search(r'(?<!\w)'+re.escape(label)+r'(?!\w)',question)]
    else:
        choices=[canonical for label,canonical in UNITS.items() if canonical not in ('m2','ft2') and label!='in' and re.search(r'(?<!\w)'+re.escape(label)+r'(?!\w)',question)]
    if len(set(choices))!=1:raise ValueError('ambiguous or missing requested unit')
    return choices[0]


def grade(row,gold,answer):
    if answer is None:return False,'missing_answer'
    if row.get('options'):
        pred=answer.strip().upper()
        return pred in row['option_letters'] and pred==gold,'exact_option'
    match=re.fullmatch(r'\s*('+NUMBER+r')\s*(.*?)\s*',answer)
    if not match:return False,'malformed_number'
    pred=float(match[1]);target=float(gold)
    if not math.isfinite(pred) or pred<0 or not math.isfinite(target) or target<0:return False,'invalid_number'
    suffix=match[2].strip().lower().rstrip('.')
    if row['question_type']=='object_counting':
        return not suffix and pred.is_integer() and target.is_integer() and pred==target,'exact_integer'
    unit=requested_unit(row)
    if suffix and UNITS.get(suffix)!=unit:return False,'incompatible_or_unknown_unit'
    # MRA at thresholds .50,.55,...,.95 awards full credit only through 5% error.
    correct=target>0 and abs(pred-target)/target <= .05+1e-12
    return correct,'numeric_mra_1.0'


def recorded_cap(trace):
    from training_policy import normalize_finish
    calls=((trace.get('llm_usage') or {}).get('planner') or {}).get('calls_detail',[])
    capped=False
    for call in calls:
        if call.get('status')!='ok':
            evidence=call.get('native_output_cap_evidence')
            if evidence:
                path=Path(evidence['event_path'])
                if sha(path)!=evidence['event_sha256']:raise ValueError('native cap event drift')
                payload=read_json(path)['payload']
                if payload.get('call_id')!=evidence['call_id'] or payload.get('response')!=evidence['response']:raise ValueError('native cap response mismatch')
                response=evidence['response'];usage=response.get('usage_metadata') or {}
                if not all(type(usage.get(k)) is int and usage[k]>=0 for k in ('prompt_token_count','candidates_token_count','total_token_count')):raise ValueError('missing native cap usage')
                if not any(normalize_finish(c.get('finish_reason'))=='max_tokens' for c in response.get('candidates') or []):raise ValueError('native response did not cap')
                if normalize_finish(call.get('finish_reason'))!='max_tokens':raise ValueError('error cap metadata disagrees')
                capped=True
            continue
        raw=call.get('raw_response')
        if not isinstance(raw,dict):raise ValueError('successful planner call lacks native response')
        finish=normalize_finish(call.get('finish_reason'))
        raw_finish=normalize_finish((raw.get('response_metadata') or {}).get('finish_reason'))
        if not finish or finish=='none' or finish!=raw_finish:raise ValueError('planner finish reason disagrees with native response')
        capped |= finish=='max_tokens'
    if bool(trace.get('budget_terminal'))!=capped:raise ValueError('cap flag disagrees with planner telemetry')
    return capped


def mechanically_complete(trace):
    try:
        from provider_history import native_ai_evidence
        from reference_native_tool_telemetry import validate_native_tools
        if trace.get('error') or trace.get('orphan_tool_drop') or trace.get('pred_source') not in ('answer_tag','salvage_commit'):return False
        calls=((trace.get('llm_usage') or {}).get('planner') or {}).get('calls_detail',[])
        successful=[c for c in calls if c.get('status')=='ok']
        if not successful:return False
        for call in successful:
            usage=call.get('usage',{})
            if not all(type(usage.get(k)) is int and usage[k]>=0 for k in ('input_tokens','output_tokens','total_tokens')):return False
            if not call.get('served_model') or not call.get('request_controls'):return False
        recorded_cap(trace)
        native_ai_evidence(trace,calls)
        validate_native_tools(trace)
        pending=set()
        for message in trace.get('trace',[]):
            if message.get('role') in ('ai','assistant'):
                if pending:return False
                for call in message.get('tool_calls') or []:
                    identity=call.get('id')
                    if not identity or identity in pending:return False
                    pending.add(identity)
            elif message.get('role')=='tool':
                identity=message.get('tool_call_id')
                if identity not in pending:return False
                pending.remove(identity)
        return not pending
    except (ValueError,RuntimeError,TypeError,KeyError):return False


def archive_complete(trace_path):
    archive=Path(trace_path).parents[2]/'archive'
    journal=archive/'journal.jsonl'
    if not journal.exists():return False
    try:
        starts={};terminals={};responses={};tool_starts=set();tool_terminals=set();terminal_episode=False;last_response=None
        for line in journal.open():
            row=json.loads(line);event=read_json(archive/row['path'])
            if row['id']!=event['id'] or row['kind']!=event['kind']:return False
            payload=event['payload'];kind=event['kind']
            if kind=='provider_request':
                call=payload.get('call_id')
                if not call or call in starts:return False
                starts[call]=payload
            elif kind in ('provider_response','provider_chunk'):
                call=payload.get('call_id')
                if call not in starts or call in terminals:return False
                response=payload.get('response')
                if not isinstance(response,dict):return False
                responses.setdefault(call,[]).append(response);last_response=response
            elif kind=='provider_terminal':
                call=payload.get('call_id')
                if not call or call in terminals:return False
                terminals[call]=payload
            elif kind=='tool_start':
                if payload['call_id'] in tool_starts:return False
                tool_starts.add(payload['call_id'])
            elif kind=='tool_terminal':
                if payload['call_id'] in tool_terminals:return False
                tool_terminals.add(payload['call_id'])
            elif kind=='episode_terminal':terminal_episode=payload.get('status')=='completed'
        if not starts or starts.keys()!=terminals.keys() or tool_starts!=tool_terminals or not terminal_episode:return False
        for call, terminal in terminals.items():
            if terminal.get('status')=='ok' and not responses.get(call):return False
            if terminal.get('status') not in ('ok','error'):return False
        # The last returned provider answer must agree with the archived final AI answer.
        trace=read_json(trace_path)
        expected_calls=len(((trace.get('llm_usage') or {}).get('planner') or {}).get('calls_detail',[]))+len(trace.get('native_google_provider_calls',[]))
        if len(starts)!=expected_calls:return False
        parts=(((last_response or {}).get('candidates') or [{}])[0].get('content') or {}).get('parts') or []
        native_text=''.join(part.get('text','') for part in parts if not part.get('thought'))
        matches=re.findall(r'<ANSWER>\s*(.*?)\s*</ANSWER>',native_text,flags=re.I|re.S)
        if len(matches)!=1 or matches[-1].strip()!=final_answer(trace):return False
        refs=archive/'artifact_refs.jsonl'
        if not refs.exists():return False
        checked=set()
        for line in refs.open():
            ref=json.loads(line)
            if ref['path'] in checked:continue
            path=Path(ref['path'])
            if path.stat().st_size!=ref['bytes'] or sha(path)!=ref['sha256']:return False
            checked.add(ref['path'])
        return True
    except (OSError,ValueError,KeyError,TypeError):return False


# These tools return model-derived visual or geometry observations to the planner.
# Path-only frame lookup, arbitrary Python, verifiers and pure arithmetic do not qualify.
PERCEPTION_TOOLS=frozenset({'find_frames_with_object','predict_2d_bounding_box',
    'predict_2d_points','get_world_3d_point_from_2d','get_3d_points_in_bbox',
    'get_3d_points_in_mask','predict_2d_segmentation_masks',
    'predict_2d_segmentation_masks_video','get_camera_pose','render_topdown_bev','render_novel_view'})


def perceptual_evidence(trace):
    """Return successful observations that precede a later provider AI turn."""
    import ast
    def usable(value):
        if isinstance(value,str):
            text=value.strip()
            if not text or re.search(r'\b(error|exception|refused|failed|not found|unavailable)\b',text,re.I):return False
            if text.startswith(('[','{')):
                try:return usable(json.loads(text))
                except (ValueError,TypeError):
                    try:return usable(ast.literal_eval(text))
                    except (ValueError,SyntaxError):return False
            return not text.startswith('/')
        if isinstance(value,dict):
            if value.get('error') or value.get('valid') is False or value.get('success') is False:return False
            return bool(value) and any(usable(v) for k,v in value.items() if k not in ('type','status'))
        if isinstance(value,list):return bool(value) and all(usable(v) for v in value)
        return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    requests={};pending=[];observed=[]
    for message in trace.get('trace',[]):
        if message.get('role') in ('ai','assistant'):
            if message.get('provenance')=='provider':observed.extend(pending);pending=[]
            for call in message.get('tool_calls') or []:requests[call.get('id')]=call.get('name')
        elif message.get('role')=='tool':
            call=message.get('tool_call_id');name=requests.get(call)
            if name in PERCEPTION_TOOLS and message.get('status')!='error' and usable(message.get('content')):
                pending.append({'tool_call_id':call,'tool':name})
    return observed


def metadata_projection_receipt(trace, trace_sha256):
    """Bind an offline interpretation to unchanged source bytes and validator code."""
    from reference_native_tool_telemetry import summary_representation, legacy_summary
    def digest(value):
        return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    try:
        mode=summary_representation(trace)
    except (ValueError,TypeError):
        mode='invalid_summary_representation'
    rows=trace.get('tool_telemetry')
    canonical=legacy_summary(rows) if isinstance(rows,list) and all(isinstance(r,dict) for r in rows) else None
    return {'schema':'r1313-native-summary-interpretation-v1','mode':mode,
        'original_trace_sha256':trace_sha256,'raw_trace_unchanged':True,
        'original_field_structural_sha256':digest(trace.get('tool_vlm_responses')),
        'canonical_summary_structural_sha256':digest(canonical),
        'validator_sha256':sha(Path(__file__).with_name('reference_native_tool_telemetry.py')),
        'donor_r1308_validator_sha256':'dad8d8c27e2f7b23f706fddff6054ef09c824db7141f13c3770c55e9d9a47ca1'}


def select_attempt(row,gold,attempts):
    by_budget={}
    for attempt in attempts:
        budget=attempt['budget']
        if budget in by_budget:raise ValueError('duplicate finalized question/budget; adjudicate before acceptance')
        by_budget[budget]=attempt
    initial=by_budget.get(16384)
    if initial is None:return {'accepted':False,'needs_topup':False,'reason':'no_initial_attempt'}
    first=initial['trace'];correct,rule=grade(row,gold,final_answer(first))
    try: capped=recorded_cap(first)
    except ValueError: return {'accepted':False,'needs_topup':False,'reason':'inconsistent_cap_telemetry'}
    eligible=(not correct and capped)
    if 32768 in by_budget and not eligible:raise ValueError('unauthorized32k attempt for this question')
    chosen=by_budget.get(32768) if eligible and 32768 in by_budget else initial
    if chosen is not initial:correct,rule=grade(row,gold,final_answer(chosen['trace']))
    complete=mechanically_complete(chosen['trace']) and chosen.get('archive_complete',False)
    evidence=perceptual_evidence(chosen['trace'])
    return {'accepted':bool(correct and complete and evidence),'answer_correct':bool(correct),'mechanically_complete':complete,
        'perceptual_evidence':evidence,'has_perceptual_evidence':bool(evidence),
        'needs_topup':eligible and 32768 not in by_budget,'reason':rule,'chosen_budget':chosen['budget'],
        'trace_path':chosen['trace_path'],'trace_sha256':chosen['trace_sha256'],
        'metadata_projection':metadata_projection_receipt(chosen['trace'],chosen['trace_sha256']),
        'final_cap_failure':not correct and bool(chosen['trace'].get('budget_terminal')) and chosen['budget']==32768}


def baseline_annotations(manifest_path,by_id,gold):
    """Join optional baseline outputs offline; baseline correctness never filters keepers."""
    if manifest_path is None:return {}
    manifest=read_json(manifest_path)
    if manifest.get('schema')!='r1308-baseline-annotations-v1':raise ValueError('baseline annotation schema mismatch')
    result={}
    for item in manifest['records']:
        qid=item['id'];row=by_id[qid]
        if item['question_video_sha256']!=row['question_video_sha256']:raise ValueError('baseline input identity mismatch')
        if not item.get('model_id') or sha(item['trace_path'])!=item['trace_sha256']:raise ValueError('baseline model/trace provenance mismatch')
        trace=read_json(item['trace_path'])
        if trace.get('question_id')!=qid:raise ValueError('baseline trace question mismatch')
        answer=final_answer(trace);correct,rule=grade(row,gold[qid],answer)
        annotation={**item,'status':'scored','answer':answer,'correct':correct,'scoring_rule':rule}
        result.setdefault(qid,[]).append(annotation)
    return result


def census(run_root,output_root,baseline_manifest=None):
    run_root=require_data_path(run_root);output_root=require_data_path(output_root)
    rows=teacher_rows();by_id={r['id']:r for r in rows}
    if sha(LABELS)!=LABELS_SHA:raise ValueError('offline label digest mismatch')
    gold={r['id']:r['ground_truth'] for r in map(json.loads,LABELS.open())}
    baselines=baseline_annotations(baseline_manifest,by_id,gold)
    attempts={};started=set();failures=[]
    # Layout is run/attempts/<qid>/b16384 or b32768; list only the fixed attempt root.
    root=Path(run_root)/'attempts'
    for qdir in sorted(root.iterdir()) if root.exists() else []:
        if qdir.name not in by_id:raise ValueError('unknown question directory')
        for adir in sorted(qdir.iterdir()):
            if adir.name not in ('b16384','b32768'):raise ValueError('unknown attempt budget')
            started.add(qdir.name)
            path=adir/'finalized'/qdir.name/f'trace_{qdir.name}.json'
            if not path.exists():failures.append({'id':qdir.name,'budget':int(adir.name[1:]),'reason':'partial_or_missing_final'});continue
            trace=read_json(path)
            if (trace.get('run_receipt') or {}).get('fixture_only'):raise ValueError('synthetic transport fixtures cannot enter a production census')
            if (trace.get('run_receipt') or {}).get('round')!=1313:raise ValueError('census requires an r1313 GT-training attempt')
            if trace.get('question_id')!=qdir.name:raise ValueError('trace question identity mismatch')
            attempts.setdefault(qdir.name,[]).append({'budget':int(adir.name[1:]),'trace':trace,'trace_path':str(path),'trace_sha256':sha(path),'archive_complete':archive_complete(path)})
    decisions=[];topups=[]
    for qid,items in sorted(attempts.items()):
        decision={'id':qid,**select_attempt(by_id[qid],gold[qid],items),
            'baseline':{'status':'scored' if qid in baselines else 'pending','records':baselines.get(qid,[])}}
        decisions.append(decision)
        if decision['needs_topup']:
            topups.append({'row':by_id[qid],'original_trace_path':decision['trace_path'],'original_trace_sha256':decision['trace_sha256'],'output_budget_tokens':32768})
    accepted=[d for d in decisions if d['accepted']]
    output=Path(output_root)/str(time.time_ns());output.mkdir(parents=True,exist_ok=False)
    values={'DECISIONS.json':decisions,'ACCEPTED.json':accepted,'TOPUPS.json':topups,'PARTIAL_ATTEMPTS.json':failures}
    summary={'schema':'r1313-collection-census-v1','candidate_questions':len(rows),'distinct_attempted':len(started),
        'distinct_finalized':len(attempts),'distinct_answer_correct':sum(d.get('answer_correct',False) for d in decisions),'distinct_correct_without_perception':sum(d.get('answer_correct',False) and not d.get('has_perceptual_evidence',False) for d in decisions),'distinct_accepted':len(accepted),'target':20000,'target_reached':len(accepted)>=20000,
        'yield_over_all_attempted':len(accepted)/len(started) if started else 0,'rerun_32k_questions':sum(any(a['budget']==32768 for a in v) for v in attempts.values()),
        'final_cap_failures':sum(d.get('final_cap_failure',False) for d in decisions),'pending_topups':len(topups),
        'remaining_candidates':len(rows)-len(started),'all_traces_preserved':True,'label_sha256':LABELS_SHA,
        'acceptance_scope':'answer-correct, mechanically complete and successful perceptual evidence received by a later teacher turn; rationale faithfulness is not certified',
        'baseline_manifest_sha256':sha(baseline_manifest) if baseline_manifest else None,'baseline_is_eligibility_filter':False,
        'expansion_required':len(started)==len(rows) and len(accepted)<20000,'snapshot':str(output)}
    values['SUMMARY.json']=summary
    for name,value in values.items():(output/name).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(summary,indent=2));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);p.add_argument('--baseline-manifest',type=Path);a=p.parse_args();census(a.run_root,a.output_root,a.baseline_manifest)
