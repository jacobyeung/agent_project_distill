"""Create a NEW frozen payload after the operator supplies missing, sourced labels."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
from adapter import payload,jsonl,dump,sha,strata,excluded_strata,SCORERS
from collections import Counter


def resolve(source,labels,dest):
    root,pins,rows,captures=payload(source)
    additions=jsonl(labels);by_id={r['qid']:r for r in additions}
    if len(by_id)!=len(additions):raise ValueError('Duplicate label update')
    missing={r['id'] for r in rows if r['answer'] is None or r['released_answer'] is None}
    if set(by_id)!=missing:raise ValueError('Supply exactly all missing-label items; existing labels cannot be changed')
    for r in rows:
        if r['id'] not in by_id:continue
        new=by_id[r['id']]
        for field in ('answer','released_answer'):
            if r[field] is not None:
                if field in new and str(new[field])!=str(r[field]):raise ValueError('Cannot replace existing label')
                continue
            if new.get(field) is None:raise ValueError('Both labels required by current ruling')
            evidence=new[field+'_source'];p=Path(evidence['path'])
            if not p.is_absolute() or not str(p).startswith('/scratch/'):raise ValueError('Use a staged scratch label source')
            if sha(p)!=evidence['sha256']:raise ValueError('Label source hash differs')
            if not evidence.get('locator'):raise ValueError('Give a row/field locator for human source review')
            r[field]=new[field]
            r['label_provenance'][field+'_supplement']=evidence
        r['ground_truth']=r['released_answer'];r['stratum']=strata(r)['stratum']
    dest=Path(dest).resolve();dest.mkdir(parents=True,exist_ok=False)
    for p in root.iterdir():
        if p.is_file() and p.suffix in ('.py','.json','.jsonl','.sha256','.md'):
            (dest/p.name).write_bytes(p.read_bytes())
    exc=jsonl(root/'EXCLUDED.jsonl')
    dump(dest/'TASKS.jsonl',rows,lines=True);dump(dest/'STRATA.jsonl',[strata(r) for r in rows]+excluded_strata(exc),lines=True)
    dump(dest/'LABEL_BLOCKERS.jsonl',[],lines=True)
    counts=json.loads((root/'COUNTS.json').read_text());counts.update(label_blockers=0,strata=dict(Counter(r['stratum'] for r in rows)),
         per_type={t:dict(Counter(r['stratum'] for r in rows if r['question_type']==t)) for t in SCORERS})
    dump(dest/'COUNTS.json',counts)
    for n in pins:pins[n]=sha(dest/n)
    dump(dest/'PINS.json',pins)
    for n in ('TASKS.jsonl','STRATA.jsonl','LABEL_BLOCKERS.jsonl'):(dest/(n+'.sha256')).write_text(pins[n]+'  '+n+'\n')
    dump(dest/'LABEL_RESOLUTION.json',dict(parent_strata_sha256=sha(root/'STRATA.jsonl'),supplement_sha256=sha(labels),items=len(additions),
         limitation='Hashes and locators bind supplied evidence; operator must verify each label is independent and in the question units.'))
    payload(dest)
    print(str(dest/'STRATA.jsonl.sha256'))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','labels','dest'):p.add_argument('--'+n,required=True)
    a=p.parse_args();resolve(a.source,a.labels,a.dest)
