"""Fixed first-50 A10b OFF comparison: >=49 identical answers and 50 identical call placements."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *

TRACE_EXCLUDE=('seconds','timings','audit','perception_memo','read_cache','read_profile')
BINDINGS=('export_sha256','item_set_sha256','items_sha256','reader_sha256','maker_sha256',
          'evaluator_code_sha256','expected_calls_sha256','r0_code_sha256','parity_code_sha256',
          'mapping_sha256','lineage','step','stage1_select_rule','perception_memo',
          'perception_memo_modules','perception_memo_verify_ids','save_own_depth')

def answer(row):
    # Exact A10b answer_text extraction; no numeric tolerance or punctuation normalization.
    output=row['output']
    if output.get('finish')=='max_calls':return ''
    text=output['text'];matches=re.findall(r'<answer>\s*(.*?)\s*</answer>',text,re.S)
    if matches:return matches[-1].strip()
    if '</think>' in text:return text.rsplit('</think>',1)[1].split('<|',1)[0].strip()
    return text.split('<|',1)[0].strip()

def calls(row):
    # Preserve record order, literal tool arguments, token position, and service placement.
    value=row['output']['calls']
    result=[]
    for index,record in enumerate(value['records']):
        if any(k not in record for k in ('call','family','served','at_token')):
            raise Refusal('Incomplete call placement trace')
        result.append((index,record['family'],record['call'],record['served'],record['at_token']))
    return result

def trace(row):
    return {**{k:v for k,v in row.items() if k not in ('seconds','output')},
            'output':{k:v for k,v in row['output'].items() if k not in TRACE_EXCLUDE}}

def rows(root):
    root=Path(root);journal=root/'metadata/reads/0/metadata/journals'
    if not journal.is_dir():raise Refusal('Missing A10b metadata/reads/0/metadata/journals')
    result=[];bindings={};seen=set()
    for kind in SCHEDULE:
        directory=journal/str(kind)/'0';path=directory/'items.jsonl'
        if not path.exists():continue
        env=read(directory/'environment.json');binding=env['binding']
        if binding.get('fixture') is not False:raise Refusal('Fixture or missing production binding')
        if binding.get('shard')!='0/1':raise Refusal('Require the original one-card shard')
        if any(k not in binding for k in BINDINGS):raise Refusal('Missing immutable environment binding')
        bindings[kind]=env
        with path.open() as stream:
            for line in stream:
                if not line.endswith('\n'):raise Refusal('Torn journal')
                row=json.loads(line)
                if row.get('complete') is not True or row.get('arm')!='tower' or row.get('mode')!='none':
                    raise Refusal('Incomplete or perturbed item')
                if row['id'] in seen:raise Refusal('Duplicate item')
                seen.add(row['id'])
                if row['type']!=ORDER[kind]:raise Refusal('Wrong type journal')
                output=row['output']
                if output.get('audit',{}).get('violations')!=[]:raise Refusal('Missing audit or audit violation')
                if not isinstance(output.get('text'),str) or not isinstance(output.get('tokens'),list):raise Refusal('Missing text/token trace')
                if output.get('finish') in (None,'','item_error'):raise Refusal('Failed item trace')
                if not isinstance(output.get('calls',{}).get('records'),list):raise Refusal('Missing calls')
                calls(row)
                result.append(row)
    if not result:raise Refusal('No complete journal rows')
    return result,bindings

def differences(a,b,path=''):
    if type(a)!=type(b):return [dict(path=path,left=a,right=b)]
    if isinstance(a,dict):
        result=[]
        for key in sorted(a.keys()|b.keys()):
            sub=path+'/'+str(key)
            if key not in a:result.append(dict(path=sub,missing='left',right=b[key]))
            elif key not in b:result.append(dict(path=sub,missing='right',left=a[key]))
            else:result.extend(differences(a[key],b[key],sub))
        return result
    if isinstance(a,(list,tuple)):
        if len(a)!=len(b):return [dict(path=path,left=a,right=b)]
        result=[]
        for i,(x,y) in enumerate(zip(a,b)):result.extend(differences(x,y,path+'/'+str(i)))
        return result
    return [] if a==b else [dict(path=path,left=a,right=b)]

def compare(left,right,first50=None):
    fixed=first50 or read(HERE/'FIRST50.json');expected=[r['id'] for r in fixed['items']]
    if len(expected)!=50 or len(set(expected))!=50:raise Refusal('Require the sealed 50-item prefix')
    reasons=[];data=[];envs=[]
    # Reference metadata is immutable even when a candidate copies the same edit.
    reference_pins=fixed.get('reference_sha256',{})
    required={'metadata/IDENTITY.json'}|{str(p.relative_to(Path(left))) for p in
        Path(left).glob('metadata/reads/*/metadata/journals/*/*/environment.json')}
    if set(reference_pins)!=required:reasons.append('orchard: reference pin inventory differs')
    for name,digest in reference_pins.items():
        path=Path(left)/name
        if Path(name).is_absolute() or '..' in Path(name).parts:raise Refusal('Unsafe reference pin path')
        if not path.is_file() or sha(path)!=digest:reasons.append('orchard: reference pin differs: '+name)
    for label,root in (('orchard',Path(left)),('trinity',Path(right))):
        loaded,env=rows(root);data.append(loaded);envs.append(env)
        if [r['id'] for r in loaded[:50]]!=expected:reasons.append(label+': first 50 IDs/order differ or are incomplete')
        if [r['id'] for r in loaded]!=fixed['full_order'][:len(loaded)] or len(loaded)>636:
            reasons.append(label+': return is not a prefix of the sealed A10b schedule')
        if read(root/'metadata/EXPORT_PIN.json')!=fixed['export']:reasons.append(label+': export differs from Orchard m400')
        identity=read(root/'metadata/IDENTITY.json')
        if identity.get('plan')!=fixed['plan_sha256'] or identity.get('cards')!=1:reasons.append(label+': plan/cards differ')
        if identity.get('operator_sha256')!=read(HERE/'A10b_PINS.json')['operator_sha256']:reasons.append(label+': operator differs')
        for value in env.values():
            settings=value.get('settings')
            if not isinstance(settings,dict):reasons.append(label+': missing settings; OFF required')
            elif any(k.startswith('read_') and v not in ('off',False,0,None,[]) for k,v in settings.items()):
                reasons.append(label+': Extension-enabled settings; OFF required')
        if label=='trinity':
            summary_path=root/'SUMMARY.json'
            summary=read(summary_path) if summary_path.is_file() else {}
            if 'failure' not in summary or summary['failure'] is not None:
                reasons.append('trinity: SUMMARY failure must be explicitly None')
            if type(summary.get('completed')) is not int or summary['completed']<50:
                reasons.append('trinity: SUMMARY completed must be >=50')
            if (root/'FAILED.json').exists():reasons.append('trinity: FAILED.json exists')
            info=root/'metadata/LOCAL_RUN.json'
            if not info.is_file():reasons.append('trinity: missing LOCAL_RUN.json')
            else:
                local_run=read(info)
                if local_run.get('deviation'):
                    reasons.append('trinity: recorded deviation: '+str(local_run['deviation']))
                if (root/'metadata/RUNTIME_RELOCATION.json').exists():
                    reasons.append('trinity: recorded deviation: runtime_relocation')
                for key,wanted in (('backend','trinity-local'),('host','trinity-2-28'),('mode','OFF')):
                    if local_run.get(key)!=wanted:reasons.append('trinity: LOCAL_RUN '+key+' must be '+wanted)
            cards=root/'metadata/CARDS.json'
            if not cards.is_file() or 'RTX 6000 Ada' not in str(read(cards).get('snapshot',{}).get('name','')):
                reasons.append('trinity: CARDS snapshot must identify RTX 6000 Ada')
            # Check every journal environment, including empty/unselected journal directories.
            for path in sorted((root/'metadata/reads').glob('*/metadata/journals/*/*/environment.json')):
                if not str(read(path).get('host','')).startswith('trinity-2-28'):
                    reasons.append('trinity: journal host differs: '+str(path.relative_to(root)))
            receipt=root/'metadata/RETURN_ID.json'
            job=read(receipt).get('job') if receipt.is_file() else None
            if job is None or str(job)==str(fixed.get('reference_job','173060')):
                reasons.append('trinity: missing RETURN_ID or Orchard reference job reused')
    for kind in set(envs[0])&set(envs[1]):
        for section in ('binding','settings'):
            x,y=envs[0][kind].get(section),envs[1][kind].get(section)
            if not isinstance(x,dict) or not isinstance(y,dict):
                reasons.append(section+' missing or not a dict: '+str(kind));continue
            for key in sorted(set(x)|set(y)):
                if key not in x or key not in y or x[key]!=y[key]:
                    reasons.append(section+' differs: '+str(kind)+'.'+key)
    if canonical(data[0][:50])!=fixed['orchard_prefix_sha256']:
        reasons.append('Orchard baseline bytes differ from the authenticated job 173060 prefix')
    # Return diagnostics for every expected ID even if the run is incomplete.
    indexed=[{r['id']:r for r in side} for side in data]
    count=Counter();per_item=[];field_counts=Counter();fields=set()
    for identifier in expected:
        x,y=[side.get(identifier) for side in indexed]
        if x is None or y is None:
            per_item.append(dict(id=identifier,missing='orchard' if x is None else 'trinity'));continue
        values=dict(answer=(answer(x),answer(y)),call_placement=(calls(x),calls(y)),
                    trace=(trace(x),trace(y)),text=(x['output']['text'],y['output']['text']),
                    tokens=(x['output']['tokens'],y['output']['tokens']))
        equal={key:a==b for key,(a,b) in values.items()}
        for key,same in equal.items():count[key]+=int(same)
        for key in x['output'].keys()|y['output'].keys():
            fields.add(key);field_counts[key]+=int(key in x['output'] and key in y['output'] and x['output'][key]==y['output'][key])
        per_item.append(dict(id=identifier,identical=equal,
            answer_diff=[] if equal['answer'] else list(values['answer']),
            call_placement_diff=differences(*values['call_placement']),
            trace_diff=differences(*values['trace'])))
    eligible=not reasons
    same=eligible and count['answer']>=49 and count['call_placement']==50
    return dict(schema='read228-comparison-v1',verdict='SAME_INSTRUMENT' if same else 'DIAGNOSTIC_ONLY',
        items=50,eligible=eligible,ineligibility_reasons=sorted(set(reasons)),
        rule='49 or 50 identical extracted answers AND identical call placement on all 50; same A10b items/export and OFF required. Trace equality is reported, not an extra acceptance gate.',
        identical={k:count[k] for k in ('answer','call_placement','trace','text','tokens')},
        identical_output_fields={k:field_counts[k] for k in sorted(fields)},
        trace_excluded_output_fields=list(TRACE_EXCLUDE),per_item=per_item,
        baseline=str(left),candidate=str(right),baseline_rows=len(data[0]),candidate_rows=len(data[1]))

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('trinity_return')
    ap.add_argument('--orchard',default=str(HERE/'reference'));ap.add_argument('--out',required=True)
    a=ap.parse_args(argv);print(utc(),file=sys.stderr)
    destination=local(a.out)
    result=compare(a.orchard,a.trinity_return);write(destination,result)
    print(json.dumps({k:v for k,v in result.items() if k!='per_item'},sort_keys=True))
    return 0 if result['verdict']=='SAME_INSTRUMENT' else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError,KeyError) as e:
        print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
