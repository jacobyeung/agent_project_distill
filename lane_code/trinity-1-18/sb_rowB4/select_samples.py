"""Select five distinct sources per family for full trace review."""
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rows=[json.loads(s) for s in (OUT/'rows.jsonl').read_text().splitlines()]
    prior=json.loads(Path('/scratch/jjyeung/orch_n30/sb_rowB3/out/READ30_REVIEW.json').read_text())
    old_rows={r['qid']:r for r in [json.loads(s) for s in Path('/scratch/jjyeung/orch_n30/sb_rowB3/out/rows.jsonl').read_text().splitlines()]}
    excluded={old_rows[q]['provenance']['sb_rowB3']['source_qid'] for q in prior['reviewed_qids']}
    rows=[r for r in rows if r['provenance']['sb_rowB4']['source_qid'] not in excluded]
    rows.sort(key=lambda r:hashlib.sha256(('sb_rowB4|READ30|'+r['qid']).encode()).hexdigest())
    chosen=[];selection={}
    for fam in sorted({r['question_type'] for r in rows}):
        rr=[r for r in rows if r['question_type']==fam];used=set();family=[]
        def flags(r):return [o['in_view'] for o in r['provenance']['sb_rowB4']['visibility'].values()]
        selectors=[('all_in_view',lambda r:all(flags(r))),('all_out_of_view',lambda r:not any(flags(r))),
                   ('mixed',lambda r:any(flags(r)) and not all(flags(r))),
                   ('future_reference',lambda r:any(o.get('recorded_frame',0)>r['provenance']['camera_frame'] for o in r['provenance']['sb_rowB4']['visibility'].values()))]
        for kind,pred in selectors:
            r=next(r for r in rr if r['provenance']['sb_rowB4']['source_qid'] not in used and pred(r))
            used.add(r['provenance']['sb_rowB4']['source_qid']);family.append(r)
        if fam.startswith('camera_'):
            def other(r):return r['provenance']['sb_rowB4']['first_seen_cell']==['untied',str(len(r['provenance']['instances']))]
        else:
            first=family[0]['provenance']['sb_rowB4']['semantic_answer']
            def other(r):return r['provenance']['sb_rowB4']['semantic_answer']!=first
        r=next(r for r in rr if r['provenance']['sb_rowB4']['source_qid'] not in used and other(r));family.append(r)
        assert len({r['provenance']['sb_rowB4']['source_qid'] for r in family})==5
        chosen.extend(family);selection[fam]=[r['qid'] for r in family]
    with (OUT/'READ30.md').open('w') as f:
        for i,r in enumerate(chosen,1):
            f.write(f'## {i}. {r["question_type"]}: {r["qid"]}\n\n'+r['student_input']['question']+'\n\n'+'\n'.join(r['student_input']['options'])+'\n\n'+r['target']+'\n\nFull row:\n```json\n'+json.dumps(r,sort_keys=True)+'\n```\n\n')
    result=dict(input_sha256={str(p):sha(p) for p in [Path(__file__),OUT/'rows.jsonl',Path('/scratch/jjyeung/orch_n30/sb_rowB3/out/READ30_REVIEW.json'),Path('/scratch/jjyeung/orch_n30/sb_rowB3/out/rows.jsonl')]},selection=selection,
        criteria=['all in view','all out of view','mixed visibility','future sighting reference','opposite semantic answer or latest first-seen camera winner'],
        distinct_sources_per_family=5,output_sha256=sha(OUT/'READ30.md'))
    (OUT/'SAMPLE_SELECTION.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
