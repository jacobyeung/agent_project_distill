"""Fixed first-50 A4 OFF comparison: >=49 identical answers and 50 identical call placements."""
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
    # Exact A4 answer_text extraction; no numeric tolerance or punctuation normalization.
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
    for record in value['records']:
        if any(k not in record for k in ('call','family','served','at_token')):
            raise Refusal('Incomplete call placement trace')
        result.append({k:v for k,v in record.items() if k not in ('response','forced_tokens','seconds','timings')})
    return result

def trace(row):
    return {**{k:v for k,v in row.items() if k not in ('seconds','output')},
            'output':{k:v for k,v in row['output'].items() if k not in TRACE_EXCLUDE}}

def rows(root):
    root=Path(root);journal=root/'metadata/reads/0/metadata/journals'
    if not journal.is_dir():raise Refusal('Missing A4 metadata/reads/0/metadata/journals')
    result=[];bindings={};seen=set()
    for kind in SCHEDULE:
        directory=journal/str(kind)/'0';path=directory/'items.jsonl'
        if not path.exists():continue
        env=read(directory/'environment.json');binding=env['binding']
        if binding.get('fixture') is not False:raise Refusal('Fixture or missing production binding')
        if binding.get('shard')!='0/1':raise Refusal('Require the original one-card shard')
        if any(k not in binding for k in BINDINGS):raise Refusal('Missing immutable environment binding')
        bindings[kind]=binding
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
    if isinstance(a,list):
        if len(a)!=len(b):return [dict(path=path,left=a,right=b)]
        result=[]
        for i,(x,y) in enumerate(zip(a,b)):result.extend(differences(x,y,path+'/'+str(i)))
        return result
    return [] if a==b else [dict(path=path,left=a,right=b)]

def compare(left,right,first50=None):
    fixed=first50 or read(HERE/'FIRST50.json');expected=[r['id'] for r in fixed['items']]
    if len(expected)!=50 or len(set(expected))!=50:raise Refusal('Require the sealed 50-item prefix')
    reasons=[];data=[];envs=[]
    for label,root in (('orchard',Path(left)),('trinity',Path(right))):
        loaded,env=rows(root);data.append(loaded);envs.append(env)
        if [r['id'] for r in loaded[:50]]!=expected:reasons.append(label+': first 50 IDs/order differ or are incomplete')
        if [r['id'] for r in loaded]!=fixed['full_order'][:len(loaded)] or len(loaded)>636:
            reasons.append(label+': return is not a prefix of the sealed A4 schedule')
        if read(root/'metadata/EXPORT_PIN.json')!=fixed['export']:reasons.append(label+': export differs from Orchard m200')
        identity=read(root/'metadata/IDENTITY.json')
        if identity.get('plan')!=fixed['plan_sha256'] or identity.get('cards')!=1:reasons.append(label+': plan/cards differ')
        if identity.get('operator_sha256')!=read(HERE/'A4_PINS.json')['operator_sha256']:reasons.append(label+': operator differs')
        info=root/'metadata/LOCAL_RUN.json'
        if info.exists() and read(info).get('mode')!='OFF':reasons.append(label+': comparison requires OFF')
        if info.exists() and read(info).get('backend')!='trinity-local':reasons.append(label+': unrecognized execution backend')
    for kind in set(envs[0])&set(envs[1]):
        for key in BINDINGS:
            if envs[0][kind][key]!=envs[1][kind][key]:reasons.append('binding differs: '+str(kind)+'.'+key)
        for env in envs:
            if any(k.startswith('read_') and v not in ('off',False,0,None,[]) for k,v in env[kind].items()):
                reasons.append('Extension-enabled environment; OFF required')
    if canonical(data[0][:50])!=fixed['orchard_prefix_sha256']:
        reasons.append('Orchard baseline bytes differ from the authenticated job 172744 prefix')
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
        rule='49 or 50 identical extracted answers AND identical call placement on all 50; same A4 items/export and OFF required. Trace equality is reported, not an extra acceptance gate.',
        identical={k:count[k] for k in ('answer','call_placement','trace','text','tokens')},
        identical_output_fields={k:field_counts[k] for k in sorted(fields)},
        trace_excluded_output_fields=list(TRACE_EXCLUDE),per_item=per_item,
        baseline=str(left),candidate=str(right),baseline_rows=len(data[0]),candidate_rows=len(data[1]))

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('trinity_return')
    ap.add_argument('--orchard',default=str(HERE/'reference'));ap.add_argument('--out',required=True)
    a=ap.parse_args(argv);print(utc(),file=sys.stderr)
    result=compare(a.orchard,a.trinity_return);write(a.out,result)
    print(json.dumps({k:v for k,v in result.items() if k!='per_item'},sort_keys=True))
    return 0 if result['verdict']=='SAME_INSTRUMENT' else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError,KeyError) as e:
        print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
