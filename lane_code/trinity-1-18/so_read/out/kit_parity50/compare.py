"""Exact answers/traces; measured timing and audit/cache telemetry are separate."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

DROP=('seconds','timings','audit','perception_memo','read_cache','read_profile')


def blob(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def rows(root):
    found={}
    paths=sorted(Path(root).glob('journals/*/*/items.jsonl'))
    paths+=sorted(Path(root).glob('shard-*/journals/*/*/items.jsonl'))
    for path in paths:
        for line in path.read_bytes().splitlines(keepends=True):
            if not line.endswith(b'\n'):raise ValueError('Torn JSONL: '+str(path))
            row=json.loads(line);identifier=row['id']
            if row.get('complete') is not True or row['arm']!='tower' or row['mode']!='none':
                raise ValueError('Unexpected incomplete/perturbed record')
            if identifier in found:raise ValueError('Duplicate ID: '+identifier)
            if row['output'].get('audit',{}).get('violations'):raise ValueError('Audit violation')
            for key in ('text','tokens','finish','calls','heads','scores'):
                if key not in row['output']:raise ValueError('Missing required trace field: '+key)
            found[identifier]=row
    return found


def semantic(row):
    out={k:v for k,v in row['output'].items() if k not in DROP}
    return {**{k:v for k,v in row.items() if k not in ('output','seconds')},'output':out}


def compare(left,right,sample):
    a,b=rows(left),rows(right);expected={r['id'] for r in sample['items']}
    if sample['count']!=50 or len(expected)!=50:raise ValueError('Expected the fixed 50 unique items')
    if set(a)!=expected or set(b)!=expected:raise ValueError('Missing/extra items in parity run')
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
    return dict(schema='read-parity50-v1',passed=not differences,items=50,
                tolerance='Zero bytes for text, tokens, calls, responses, heads, scale, finish, scores and all other semantic fields.',
                excluded_output_fields=list(DROP),differences=differences,
                left=timing(a),right=timing(b),
                left_cache_counters=caches(a),right_cache_counters=caches(b),
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
