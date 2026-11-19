"""Print the content and evidence of the complete rows in READ30.md."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent;out=root/'out'
audit={a['qid']:a for a in json.loads((out/'AUDIT.json').read_text())['rows']}
sections=(out/'READ30.md').read_text().split('```json\n')[1:]
reviews=[]
for n,part in enumerate(sections,1):
    row=json.loads(part.split('\n```',1)[0]);p=row['provenance']['relative_count_counts'];a=audit[row['qid']]
    reviews.append(f"{n}. {row['qid']} | {row['dataset']}/{row['scene']} | template {p['template_id']} | {p['form']}\n{row['student_input']['question']}\n"+'; '.join(row['student_input']['options'])+'\n'+row['target']+'\nGT IDs/first frames: '+str(a['ids_and_first_frames']))
assert len(reviews)==30
(out/'READ30_REVIEW.txt').write_text('\n\n'.join(reviews)+'\n')
print('\n\n'.join(reviews))
