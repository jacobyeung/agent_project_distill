"""Exact answers/traces; measured timing and audit/cache telemetry are separate."""
import argparse
from collections import Counter
import hashlib
import json
import math
import re
from pathlib import Path
import statistics

DROP=('seconds','timings','audit','perception_memo','read_cache','read_profile')
CACHES={'processor':('processor',),'vision':('vision',),'sam':('sam_features','sam_detections')}


def validate_trace(out):
    for key in ('text','tokens','finish','calls','heads','scale','scores','audit','entries',
                'prompt_tokens','timings','id','seconds','frames','decode_budget','key',
                'room','question_type','stratum','arm'):
        if key not in out:raise ValueError('Missing required trace field: '+key)
    if not isinstance(out['text'],str) or not out['text'].strip():raise ValueError('Empty generated text')
    if not isinstance(out['tokens'],list) or not out['tokens'] or any(type(t) is not int for t in out['tokens']):
        raise ValueError('Invalid token trace')
    if not isinstance(out['finish'],str) or not out['finish'] or out['finish']=='item_error':
        raise ValueError('Invalid finish')
    if not isinstance(out['audit'],dict) or out['audit'].get('violations')!=[]:raise ValueError('Missing/failed audit')
    if (not isinstance(out['entries'],dict) or any(type(out['entries'].get(k)) is not int or out['entries'][k]<0
                                                for k in ('prefill','steps'))):raise ValueError('Invalid model entry trace')
    if type(out['prompt_tokens']) is not int or out['prompt_tokens']<=0:raise ValueError('Invalid prompt token count')
    if (not isinstance(out['frames'],dict) or out['frames'].get('count')!=32
            or out['frames'].get('matches_training') is not True):raise ValueError('Invalid frame-layout trace')
    if not isinstance(out['decode_budget'],dict) or out['decode_budget'].get('total_tokens')!=len(out['tokens']):
        raise ValueError('Missing/inconsistent decode budget')
    def numeric_tree(value):
        return (bool(value) and all(numeric_tree(x) for x in value) if isinstance(value,list)
                else type(value) in (int,float) and math.isfinite(value))
    if (not isinstance(out['heads'],dict) or any(k not in out['heads'] or not numeric_tree(out['heads'][k])
                                               for k in ('pose9','gravity'))):
        raise ValueError('Invalid head trace')
    if out['scale'] is not None and (type(out['scale']) not in (int,float) or not math.isfinite(out['scale']) or out['scale']<=0):
        raise ValueError('Invalid scale')
    if not isinstance(out['scores'],dict) or 'answer' not in out['scores'] or any(
            v is not None and (type(v) not in (int,float) or not math.isfinite(v)) for v in out['scores'].values()):
        raise ValueError('Invalid scores')
    calls=out['calls']
    if not isinstance(calls,dict) or any(k not in calls for k in ('calls','unserved','records')):
        raise ValueError('Invalid calls schema')
    if not isinstance(calls['records'],list):raise ValueError('Invalid call records')
    counts=Counter();unserved=Counter()
    for call in calls['records']:
        if not isinstance(call,dict) or any(k not in call for k in ('call','family','served','at_token')):
            raise ValueError('Incomplete call trace')
        if (not isinstance(call['call'],str) or not call['call'] or not isinstance(call['family'],str)
                or not call['family'] or type(call['served']) is not bool or type(call['at_token']) is not int
                or not 0<=call['at_token']<=len(out['tokens'])):
            raise ValueError('Invalid call trace')
        counts[call['family']]+=1
        if call['served']:
            if (not isinstance(call.get('response'),str) or not call['response']
                    or type(call.get('forced_tokens')) is not int or call['forced_tokens']<=0):
                raise ValueError('Served call lacks response/forced-token trace')
        else:unserved[call['family']]+=1
    if dict(counts)!=calls['calls'] or dict(unserved)!=calls['unserved']:
        raise ValueError('Call counters differ from trace')


def blob(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def rows(root,codec=None):
    found={}
    paths=sorted(Path(root).glob('journals/*/*/items.jsonl'))
    paths+=sorted(Path(root).glob('shard-*/journals/*/*/items.jsonl'))
    paths+=sorted(Path(root).glob('u*/journals/*/*/items.jsonl'))
    for path in paths:
        receipt=path.parent/'WEIGHTS.json'
        if receipt.exists():
            from a9 import read_wire
            if read_wire(json.loads(receipt.read_bytes())).get('verified') is not True:
                raise ValueError('Unchecked cache weights; cannot compare journal')
        for line in path.read_bytes().splitlines(keepends=True):
            if not line.endswith(b'\n'):raise ValueError('Torn JSONL: '+str(path))
            row=json.loads(line)
            if codec is not None:
                from a9 import read_wire
                row=codec.decode(read_wire(row))
            identifier=row['id']
            if row.get('complete') is not True or row['arm']!='tower' or row['mode']!='none':
                raise ValueError('Unexpected incomplete/perturbed record')
            if identifier in found:raise ValueError('Duplicate ID: '+identifier)
            if row['output'].get('audit',{}).get('violations'):raise ValueError('Audit violation')
            validate_trace(row['output'])
            found[identifier]=row
    return found


def semantic(row):
    out={k:v for k,v in row['output'].items() if k not in DROP}
    return {**{k:v for k,v in row.items() if k not in ('output','seconds')},'output':out}


def compare_source_hashes(left,right,codec=None):
    fields=('reader_sha256','maker_sha256','evaluator_code_sha256',
            'expected_calls_sha256','r0_code_sha256','parity_code_sha256')
    def collect(root):
        result={}
        for path in sorted(Path(root).glob('journals/*/*/environment.json')):
            environment=json.loads(path.read_bytes())
            if codec is not None:
                from a9 import read_wire
                environment=codec.decode(read_wire(environment))
            binding=environment['binding']
            if any(not isinstance(binding.get(field),str) or not re.fullmatch('[0-9a-f]{64}',binding[field]) for field in fields):
                raise ValueError('Missing/invalid production source hash')
            result[str(path.relative_to(root))]={field:binding[field] for field in fields}
        if not result:raise ValueError('Missing production environment bindings')
        return result
    a,b=collect(left),collect(right)
    return dict(passed=a==b,left=a,right=b)


def compare(left,right,sample,*,enabled_caches=('processor','vision','sam'),cache_sides=('right',),codec=None):
    a,b=rows(left,codec),rows(right,codec);expected={r['id'] for r in sample['items']}
    if sample['count']!=50 or len(expected)!=50:raise ValueError('Expected the fixed 50 unique items')
    if set(a)!=expected or set(b)!=expected:raise ValueError('Missing/extra items in parity run')
    by_id={item['id']:item for item in sample['items']}
    for data in (a,b):
        for identifier,row in data.items():
            if row['type']!=by_id[identifier]['question_type'] or row['output']['question_type']!=row['type']:
                raise ValueError('Trace type differs from fixed sample')
            if row['output']['id']!='devrows:'+identifier or row['output']['key']!=row['output']['id']:
                raise ValueError('Inner reader identity differs from journal')
    differences=[]
    for identifier in sorted(expected):
        x,y=semantic(a[identifier]),semantic(b[identifier])
        if blob(x)!=blob(y):
            keys=sorted(set(x['output'])|set(y['output']))
            changed=[k for k in keys if blob(x['output'].get(k))!=blob(y['output'].get(k))]
            differences.append(dict(id=identifier,output_fields=changed,
                                    same_score=blob(x['output']['scores'])==blob(y['output']['scores'])))
    def timing(data):
        result={}
        for kind in sorted({r['type'] for r in data.values()}):
            values=[r['seconds'] for r in data.values() if r['type']==kind]
            result[kind]=dict(items=len(values),mean_seconds_per_item=statistics.mean(values),
                              median_seconds_per_item=statistics.median(values),total_seconds=sum(values))
        return result
    def caches(data):
        result={}
        for row in data.values():
            for name,stats in row['output'].get('read_cache',{}).get('stats',{}).items():
                current=result.setdefault(name,{})
                for key,value in stats.items():current[key]=max(current.get(key,0),value)
        return result
    if set(enabled_caches)-CACHES.keys():raise ValueError('Unknown enabled cache')
    if set(cache_sides)-{'left','right'}:raise ValueError('Unknown cache side')
    counters={'left':caches(a),'right':caches(b)}
    cache_failures=[]
    for side in cache_sides:
        if enabled_caches:
            for row in (a if side=='left' else b).values():
                telemetry=row['output'].get('read_cache',{})
                if set(telemetry.get('enabled',[]))!={'read_'+k+'_cache' for k in enabled_caches}:
                    raise ValueError('Enabled cache declaration is missing or differs')
                cap,held,peak=(telemetry.get(k) for k in ('max_bytes','held_bytes','peak_bytes'))
                if any(type(v) is not int for v in (cap,held,peak)) or not 0<=held<=peak<=cap or cap<262144:
                    raise ValueError('Missing/invalid cache memory bound receipt')
        for enabled in enabled_caches:
            for name in CACHES[enabled]:
                hits=counters[side].get(name,{}).get('hits')
                if type(hits) is not int or hits<=0:cache_failures.append(side+':'+name+':no_hits')
    return dict(schema='read-parity50-v2',passed=not differences and not cache_failures,items=50,
                tolerance='Zero bytes for text, tokens, calls, responses, heads, scale, finish, scores and all other semantic fields.',
                excluded_output_fields=list(DROP),differences=differences,
                left=timing(a),right=timing(b),enabled_caches=list(enabled_caches),cache_failures=cache_failures,
                left_cache_counters=counters['left'],right_cache_counters=counters['right'],
                left_sha256=hashlib.sha256(blob([semantic(a[k]) for k in sorted(expected)])).hexdigest(),
                right_sha256=hashlib.sha256(blob([semantic(b[k]) for k in sorted(expected)])).hexdigest())


def main():
    p=argparse.ArgumentParser();p.add_argument('left');p.add_argument('right')
    p.add_argument('--sample',default=str(Path(__file__).with_name('sample50.json')))
    p.add_argument('--out',required=True);a=p.parse_args()
    result=compare(a.left,a.right,json.loads(Path(a.sample).read_text()))
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
