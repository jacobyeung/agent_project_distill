"""CPU integration fixtures use real cell tasks and deterministic synthetic token IDs."""
import argparse
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adapter as A
import report as R
from dev_scoring import installed, option_parse_failed
KITROOT = Path('/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3')


class Tokenizer:
    """Synthetic only: </think> is one token; other characters map reversibly."""
    def encode(self, text, add_special_tokens=False):
        ids = []
        while text:
            if text.startswith('</think>'):
                ids.append(1); text=text[8:]
            else:
                ids.append(ord(text[0])+100); text=text[1:]
        return ids
    def decode(self, ids, skip_special_tokens=True):
        return ''.join('</think>' if i==1 else chr(i-100) for i in ids)


def refuse(fn, text=None):
    try:fn()
    except (ValueError, RuntimeError) as exc:
        if text and text not in str(exc):raise AssertionError((text,str(exc))) from exc
        return
    raise AssertionError('Expected refusal')


def inventory(kit):
    return {str(p.relative_to(kit/'evaluator')):A.sha(p)
            for sub in ('','evalpath','trainer') for p in sorted((kit/'evaluator'/sub).iterdir())
            if p.is_file() and p.suffix in ('.py','.json')}


def make_row(task, cell, cfg, media, tokenizer, mode):
    gt = str(task['ground_truth'])
    # Every type includes correct, incorrect, empty, unclosed, invalid and capped cases.
    texts = ['thought</think>\n'+gt, 'thought</think>\nZ', 'unclosed thinking',
             'thought</think>\n???', 'x'*4100+'</think>\n'+gt, '',
             'thought</think>\n'+'word '*80+'\n'+gt, 'x'*16384]
    raw = texts[mode % len(texts)]
    ids = tokenizer.encode(raw)
    finish = 'length' if mode % len(texts) in (6,7) else 'stop'
    score = importlib.import_module('scoring').score_item
    row = dict(task,key='devrows:'+task['example_id'],status='complete',
               binding=A.digest(dict(request=cfg['binding'],cell=0)),
               frames=32,layout=cell['layout'],model=cell['model'],thinking=True,decoding='greedy',
               media=media,anchor_indices=media['anchor_indices'],raw_generation=raw,token_ids=ids,token_ids_sha256=A.digest(ids),
               finish_reason=finish, **score(dict(task,thinking=True),raw,len(ids),finish=finish))
    short = tokenizer.decode(ids[:4096])
    row['at_4096'] = dict(raw_generation=short, **score(dict(task,thinking=True),short,min(len(ids),4096),
                         cap=4096,finish='length' if len(ids)>=4096 else finish))
    return row


def budgets(cfg, rows, tokenizer):
    budget = importlib.import_module('budget')
    score = importlib.import_module('scoring').score_item
    for b in budget.BUDGETS:
        binding = A.digest(dict(request=cfg['binding'],cell=0,budget=b))
        records, receipts = [], []
        for i, source in enumerate(rows):
            classification = budget.classify(tokenizer,source['token_ids'],b)
            meta = dict(classification,arm=f'B{b}',budget=b,derivation_error=False,
                        retokenize_equal=True,retokenized_source=False,answer_tokens=0)
            if not classification['forced_close'] and not classification['stopped_unclosed']:
                row = source
                meta.update(answer_tokens=len(source['token_ids'])-classification['think_tokens']-1,
                            answer_cap_policy='reuse_full_on_answer')
            elif i % 9 == 0:
                meta['derivation_error']=True
                row = budget.zero_record(source,cfg['cells'][0],binding,meta,ValueError('Synthetic failure'),'test')
            else:
                answer = str(source['ground_truth']) if i % 3 else '???'
                answer_ids = tokenizer.encode(answer)
                text = tokenizer.decode(source['token_ids'][:b],False)+budget.CLOSE+answer
                finish = 'length' if i%5==0 else 'stop'
                scored = score(source,text,len(answer_ids),cap=64,finish=finish)
                meta.update(answer_tokens=len(answer_ids),answer_cap_policy='continuation_64')
                row = {k:v for k,v in source.items() if k not in ('at_4096','token_ids_sha256','token_text')}
                row.update(meta,binding=binding,source_key=source['key'],raw_generation=answer,raw_answer=answer,
                           scoring_text=text,token_ids=answer_ids,finish_reason=finish,
                           continuation_suffix_ids=tokenizer.encode(budget.CLOSE),**scored)
                row['at_4096']=dict(raw_generation=text,**scored)
            raw = json.dumps(row,allow_nan=False)
            receipt = dict(meta,key=source['key']+':'+A.digest(raw),source_key=source['key'],binding=binding,
                           source_sha256=A.digest(source),record_sha256=A.digest(raw),status='complete',
                           score=row['score'],parse_failed=row['parse_failed'],frames=32,layout='duplicate',
                           raw_answer=row.get('raw_answer',row['response_text']))
            records.append(raw); receipts.append(receipt)
        d = Path(cfg['output'])/'0'
        (d/f'budget_{b}.g0.jsonl').write_text('\n'.join(records)+'\n')
        A.dump(d/f'budget_{b}.g0.meta.jsonl',receipts,lines=True)


def run_case(args):
    kit = KITROOT/args.kit; before = inventory(kit)
    origin = A.R3 if args.family=='main' else A.R4
    payload = HERE.parent/'r3' if args.family=='main' else HERE.parent/'r4'/args.family
    root,pins,tasks,captures = origin.payload(payload)
    dest = Path(args.dest); dest.mkdir(parents=True,exist_ok=False)
    source_sha = origin.copy_kit(kit,dest/'kit')
    data,media,official = origin.kit_import(dest/'kit')
    scoring = importlib.import_module('scoring'); merger = importlib.import_module('merge')
    model = 'cp1m200' if args.kit=='aws_vl64rt' and args.layout=='duplicate' else 'f17'
    cell = json.loads((root/f'cells_{model}.json').read_text())[0]
    cell['layout'] = args.layout
    cfg = dict(cells=[cell],datasets=[dict(benchmark='devrows',rows=dict(path=str(root/'TASKS.jsonl'),sha256=pins['TASKS.jsonl']))],
               roots={'video_root':'/synthetic/identity_only'},models=json.loads((HERE.parent/'r3/MODELS.reference.json').read_text()),
               source_sha256=source_sha,gpus=1,smoke_items=0,build_only=False,
               devs1=dict(payload=str(root),pins=pins,adapter_sha256=A.PINS['r3' if origin is A.R3 else 'r4'],
                          code_pins_sha256=A.sha(dest/'kit/CODE_PINS.json'),timing_version=origin.TIMING_VERSION))
    cfg['binding']=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
    cfg['output']=str(dest/'results'); A.dump(dest/'request.json',cfg)
    tasks=data.tasks_for(cfg['datasets'][0],cfg['roots'])
    tokenizer=Tokenizer(); rows=[]; counters={}
    for task in tasks:
        typ=task['question_type']; mode=counters.get(typ,0); counters[typ]=mode+1
        receipt=origin.receipt_template(task,cell,captures[task['native']],media)
        # Limit long fixtures to one per kind; all later rows answer correctly.
        row=make_row(task,cell,cfg,receipt['audit'],tokenizer,mode if mode<8 else 0)
        rows.append(row)
    d=Path(cfg['output'])/'0'; d.mkdir(parents=True)
    A.dump(d/'g0.jsonl',rows,lines=True)
    checks=[dict(example_id=t['example_id'],benchmark='devrows',prompt_equal=True,
                 **({'pixels':{'pass':True}} if i<2 else {})) for t,i in importlib.import_module('parity').probe_tasks(cfg,tasks)]
    A.dump(d/'p0_synthetic.json',dict(checks=checks,layout=cell['layout'],synthetic=True))
    if args.family=='main':
        assert set(counters)==set(A.SCORERS)
        refuse(lambda:scoring.benchmark_summary(rows,tasks,True),'Unknown VSI-Bench')
    if model=='cp1m200':budgets(cfg,rows,tokenizer)
    # Scope proof: every non-dev branch dispatches to the identical original callable.
    orig_summary=scoring.benchmark_summary; orig_score=scoring.score_item
    official_rows=[dict(r,benchmark='official5130') for r in rows if r['question_type'] not in ('relative_count','relative_size_object')]
    official_tasks=[dict(t,benchmark='official5130') for t in tasks if t['question_type'] not in ('relative_count','relative_size_object')]
    for benchmark in ('official5130','vsi500','vsi500_slice'):
        rr=[dict(r,benchmark=benchmark) for r in official_rows]
        tt=[dict(t,benchmark=benchmark) for t in official_tasks]
        expected=orig_summary(rr,tt,True)
        with installed():assert scoring.benchmark_summary(rr,tt,True)==expected
    # Exhaustive dispatch for other benchmarks without changing their implementations.
    from dev_scoring import dev_summary
    for benchmark in ('revsi','pointing','pointing_video','vsti','future_benchmark'):
        sentinel=object(); called=[]
        def unchanged(*values):called.append(values);return sentinel
        tt=[dict(benchmark=benchmark)]
        assert dev_summary([],tt,False,unchanged,official) is sentinel and called==[([],tt,False)]
    result=A.checked_merges(cfg,'synthetic',tokenizer)
    assert scoring.benchmark_summary is orig_summary and scoring.score_item is orig_score
    dev=result['benchmarks']['devrows']
    assert result['parity_pass'] and dev['completed']==len(tasks) and dev['expected']==len(tasks)
    assert dev['per_type'].keys()==counters.keys()
    assert abs(dev['overall_score']-sum(r['score'] for r in rows)/len(rows))<1e-12
    for typ in counters:
        subset=[r for r in rows if r['question_type']==typ]
        assert dev['per_type'][typ]['count']==len(subset)
        assert dev['per_type'][typ]['score']==sum(r['score'] for r in subset)/len(subset)
        assert any(r['hit_token_cap'] and r['score']==1 for r in subset)
        assert any(r['extract_branch']=='unclosed_thinking' and r['score']==0 for r in subset)
    for typ in ('relative_count','relative_size_object'):
        subset=[r for r in rows if r['question_type']==typ]
        if subset:
            assert sum(option_parse_failed(r,official) for r in subset)==5
            assert all(r['score']==0 for r in subset if option_parse_failed(r,official))
    # Check that the unchanged admission still rejects protocol/score/token tampering.
    row,task=rows[0],tasks[0]
    checked_cell=cell if args.kit=='aws_vl64rt' else cell['layout']
    fields=[('layout','wrong'),('score',999),('ground_truth','wrong')]
    if args.kit=='aws_vl64rt':fields += [('model','wrong'),('thinking',False)]
    for field,value in fields:
        refuse(lambda f=field,v=value:merger.check_row(dict(row,**{f:v}),task,32,checked_cell))
    if args.kit=='aws_vl64rt':
        token_audit=importlib.import_module('token_audit')
        bad=deepcopy(row); bad['token_ids'][0]+=1
        refuse(lambda:token_audit.prefix_score(bad,task,cell,tokenizer))
        bad=deepcopy(row);bad['at_4096']['score']=999
        refuse(lambda:token_audit.prefix_score(bad,task,cell,tokenizer))
    bad=deepcopy(row);bad['media']['timestamps'][0]+=1
    refuse(lambda:R.check_frames(bad,task,cell,origin.timing_authority()))
    # Missing parity must keep numbers ineligible, including at_4096.
    with installed():bad_summary=A.kit_merge(cfg,'missing_parity',tokenizer)
    assert not bad_summary['parity_pass']
    assert bad_summary['benchmarks']['devrows']['numbers_status']=='do not count'
    refuse(lambda:R.export_merged(cfg,'missing_parity',dest/'bad_report'),'parity')
    exports=R.export_merged(cfg,'synthetic',dest/'report')
    if model=='cp1m200':
        from budget_admission import BudgetContext
        for b in (2048,4096):
            rr=A.jsonl(d/f'budget_{b}.g0.jsonl');mm=A.jsonl(d/f'budget_{b}.g0.meta.jsonl')
            raw=(d/f'budget_{b}.g0.jsonl').read_text().splitlines()[0]
            bad=dict(mm[0],source_sha256='bad')
            refuse(lambda:BudgetContext(cfg,0,b,tokenizer).add(rows[0],rr[0],raw,bad,tasks[0]),'hash')
            summary=json.loads((Path(cfg['output'])/f'budget_{b}/0/summary_synthetic.json').read_text())
            assert summary['benchmarks']['devrows']['completed']==len(tasks)
            assert set(summary['derivation']['per_type'])==set(counters)
            for flag in ('forced_close','stopped_unclosed','derivation_error'):
                assert sum(v[flag] for v in summary['derivation']['per_type'].values())>0
            assert any(m.get('answer_cap_policy')=='reuse_full_on_answer' and m['answer_tokens']>64 for m in mm)
    A.dump(dest/'MERGE_INPUTS.json',dict(synthetic=True,request_binding=cfg['binding']))
    A.dump(dest/'MERGE_COMPLETE.json',dict(receipt_sha256=A.sha(dest/'MERGE_INPUTS.json'),exports=exports,
           export_sha256={arm:A.sha(dest/'report'/name) for arm,name in exports.items()}))
    assert inventory(kit)==before
    assert inventory(dest/'kit')==before
    bad_cfg=deepcopy(cfg);bad_cfg['binding']='wrong'
    refuse(lambda:A.validate_request(bad_cfg),'binding')
    if (args.kit,args.layout) in (('aws_vl64rt','duplicate'),('aws_eval_gaps','spread')):
        A.validate_request(cfg)
    A.dump(dest/'TEST_RESULT.json',dict(pass_=True,synthetic=True,kit=args.kit,layout=args.layout,
        family=args.family,tasks=len(tasks),per_type=counters,arms=list(exports),
        kit_bytes_before=before,kit_bytes_after=inventory(kit),
        no_gpu=True,original_failure_reproduced=args.family=='main'))
    print(json.dumps(dict(case=str(dest),tasks=len(tasks),types=len(counters),arms=list(exports),result='PASS')))


def suite(args):
    root=Path(args.dest);root.mkdir(parents=True,exist_ok=False)
    cases=[]
    for kit in ('aws_vl64rt','aws_eval_gaps'):
        for layout in ('duplicate','spread'):cases.append((kit,layout,'main'))
    for family in ('DEV_BACKDIR','DEV_FORWARD_TWINS'):
        cases.extend([('aws_vl64rt','duplicate',family),('aws_eval_gaps','spread',family)])
    paths={}
    for kit,layout,family in cases:
        path=root/(family+'_'+kit+'_'+layout)
        command=[sys.executable,'-I','-s',__file__,'case','--dest',str(path),'--kit',kit,'--layout',layout,'--family',family]
        result=subprocess.run(command,text=True,capture_output=True)
        (root/(path.name+'.log')).write_text(result.stdout+result.stderr)
        print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
        if result.returncode:raise RuntimeError('Case failed: '+path.name)
        paths[(kit,family)]=path if (kit=='aws_vl64rt' and layout=='duplicate') or kit=='aws_eval_gaps' else paths.get((kit,family))
    for family in ('main','DEV_BACKDIR','DEV_FORWARD_TWINS'):
        target=root/(family+'_PAIRED.json')
        result=R.compare(paths[('aws_vl64rt',family)],paths[('aws_eval_gaps',family)],target,replicates=200)
        assert set(result['comparisons'])=={'ON16k','B2048','B4096'}
        assert result['comparisons']['ON16k']
    # Use the same production CLI for an f17 merge from an existing synthetic run.
    path=paths[('aws_eval_gaps','main')]
    command=[sys.executable,'-I','-s',str(HERE/'adapter.py'),'merge','--source',str(path),
             '--kit',str(KITROOT/'aws_eval_gaps'),'--dest',str(root/'f17_cli'), '--attempt','synthetic']
    result=subprocess.run(command,text=True,capture_output=True)
    (root/'f17_cli.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(result.stderr)
    # A changed report cannot silently enter a paired comparison.
    tampered=root/'tampered_export';(tampered/'report').mkdir(parents=True)
    for name in ('MERGE_COMPLETE.json','MERGE_INPUTS.json'):
        (tampered/name).write_bytes((path/name).read_bytes())
    export=json.loads((path/'report/ON16k.json').read_text());export['rows'][0]['scores']['answer']=999
    A.dump(tampered/'report/ON16k.json',export)
    refuse(lambda:R.load_exports(tampered),'digest')
    # Room-bootstrap hand oracle and mismatched membership rejection.
    a=[dict(key=str(i),room='r'+str(i//2),stratum='primary',question_type='relative_count',scores={'answer':1.0}) for i in range(4)]
    b=[dict(r,scores={'answer':0.0}) for r in a]
    result=R.paired(a,b,'answer',replicates=100)
    assert result['delta_pp']==100 and result['ci95_pp']==[100,100]
    refuse(lambda:R.paired(a,b[:-1],'answer',replicates=100),'keys')
    A.dump(root/'SUITE.json',dict(pass_=True,cases=8,paired_reports=3,bootstrap_oracle=True,f17_cli=True,
                                fixture_parity='Synthetic receipts; no inference or actual pixel-parity claim'))
    print('PASS: 8 full-journal cases; 3 paired reports; bootstrap oracle and admission negatives')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['suite','case']);p.add_argument('--dest',required=True)
    p.add_argument('--kit');p.add_argument('--layout');p.add_argument('--family');a=p.parse_args()
    (suite if a.command=='suite' else run_case)(a)
if __name__=='__main__':main()
