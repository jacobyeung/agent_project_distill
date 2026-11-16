import sys,json,gzip,re,collections
from pathlib import Path
T=sys.argv[1]; sys.path.insert(0,T)
from student_pilot.training_contract import call_responses
X=Path('/scratch/jjyeung/orch_n30/contracts_rebuild/work/real/x')
man=json.loads((X/'66caacf5c9191457.json').read_text())
c=collections.Counter(); forms=collections.Counter(); ex=[]
for ds in man['sets']:
    for role,pin in ds['files'].items():
        p=X/(pin['sha256'][:16]+'.jsonl.gz')
        with gzip.open(p,'rt') as s:
            for line,t in enumerate(s,1):
                row=json.loads(t); c['rows']+=1
                c['ver:'+str(row.get('spec_version',row.get('trace_revision',row.get('routing',{}).get('trace_revision') if isinstance(row.get('routing'),dict) else None)))]+=1
                try: pairs=call_responses(row)
                except Exception as e: c['call_responses_error']+=1; continue
                hit=False
                for call,text in pairs:
                    if isinstance(call,str) and call.startswith('<gap'):
                        body=text if isinstance(text,str) else ''
                        body=body.strip().removeprefix('<tool_response>').removesuffix('</tool_response>').strip()
                        first=body.splitlines()[0] if body else ''
                        forms[re.sub(r'[0-9]+\.[0-9]+','N',re.sub(r'^[^:]+: ','NAME: ',first))[:60]]+=1
                        if re.fullmatch(r'-?[0-9]+(?:\.[0-9]+)? ?m',body): hit=True; ex.append((str(p.name),line,row.get('qid'),call,body)) if len(ex)<5 else None
                if hit: c['bare_rows']+=1
print(dict(c)); print('gap first-line forms:'); [print(' ',n,f) for f,n in forms.most_common(25)]; print('examples',ex)
