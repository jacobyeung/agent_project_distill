"""Compare the analysis against the locally pinned reader, CPU and stdlib only."""
import ast
import gzip
import hashlib
import json
import re
from pathlib import Path
from analyze import ROOT, names, mra, factor

SOURCE=Path('/scratch/jjyeung/orch_n30/reads228/kit/A10b/src')


def function(path, name, namespace):
    source=path.read_text()
    tree=ast.parse(source)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    # Preserve only the authoritative function, avoiding package initialization.
    code='\n'.join(source.splitlines()[fn.lineno-1:fn.end_lineno])
    exec(compile(code,str(path),'exec'),namespace)
    return namespace[name]


def main():
    import math
    from typing import Optional
    official_path=SOURCE/'tree/evalpath/official.py'
    parser_path=SOURCE/'rows/expected_calls.py'
    official=function(official_path,'official_mra',dict(math=math,Optional=Optional))
    parser=function(parser_path,'expected_calls',dict(re=re,CAMERA_TYPES=()))
    checks=dict(score_pairs=0,operand_pairs=0,logged_selectors=0)
    for step in (544,400):
        with gzip.open(ROOT/('work/step%d.jsonl.gz'%step),'rt') as f:
            for r in map(json.loads,f):
                if r['question_type']!='object_abs_distance':continue
                expected=parser(r['question'],r['question_type'])[:2]
                expected=[re.search('obj="([^"]+)"',x).group(1).strip().lower() for x in expected]
                assert names(r['question'])==expected
                checks['operand_pairs']+=1
                for c in r['arms']['tower']['tool_calls']:
                    d=c.get('stage1') or {}
                    if c['family']=='ground' and d.get('linked_candidates',0) and d['chosen_index']<len(d['candidates']):
                        cs=d['candidates']
                        assert d['chosen_index']==max(range(len(cs)),key=lambda i:cs[i]['logit'])
                        checks['logged_selectors']+=1
                    if c['family']=='gap':
                        m=re.search(r'\bdistance\s+([\d.]+)\s+m',c.get('response',''))
                        if m:
                            pred=float(m.group(1))*factor(r['question']);truth=float(r['truth']['scored'])
                            assert abs(mra(pred,truth)-100*official(pred,truth))<1e-12
                            checks['score_pairs']+=1
    for pred in (0.,.05,.1,.15,.2,.25,.5,1.,1.05,1.5,2.):
        for truth in (0.,.1,1.,2.):
            assert abs(mra(pred,truth)-100*official(pred,truth))<1e-12
            checks['score_pairs']+=1
    checks['source_pins']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (official_path,parser_path)}
    checks['corpus_pins']={str(ROOT/('work/step%d.jsonl.gz'%s)):hashlib.sha256((ROOT/('work/step%d.jsonl.gz'%s)).read_bytes()).hexdigest() for s in (544,400)}
    assert list(checks['corpus_pins'].values())==[
        'e88ee503404755810a4a5d60296261c0594445562b71fed9e185d6c33b1e5c9e',
        'b64e382559bbfbd79afa5c3a8c05050bd4fcd277665ce492b78fc374047bbc6a']
    checks['status']='PASS'
    (ROOT/'work/verification.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks,indent=2))


if __name__=='__main__':main()
