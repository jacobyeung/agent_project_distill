import sqlite3,json,re,collections
from itertools import chain
S='/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite'
con=sqlite3.connect(f'file:{S}?mode=ro&immutable=1',uri=True)
def norm(s): return re.sub(r'\s+',' ',s.strip().lower())
cp=collections.defaultdict(set); ap=collections.defaultdict(set)
for i,row,t in con.execute('select i,row,target from rows'):
    d=json.loads(row); a=d['dataset']+'/'+d['scene']; q=d['student_input']['question']
    if d['question_type']=='object_counting':
        if 'count_kind' in d:
            for c in d['provenance'].get('total_categories',[]): cp[a].add(norm(c['name']))
        else:
            m=re.search(r'(?:How many|number of|Count the) (.+?)\(s\)',q)
            if m: cp[a].add(norm(m.group(1)))
    if d['question_type']=='obj_appearance_order':
        m=re.search(r'(?:categories in the video|first appearances|these categories|order of)[^:]*: (.+?)[?.]$',q) or re.search(r'lists (.+?) in the chronological',q)
        if m: ap[a].add(tuple(sorted(norm(x) for x in m.group(1).split(','))))
json.dump({'count':{a:sorted(v) for a,v in cp.items()},'app':{a:sorted(map(list,v)) for a,v in ap.items()}},open('d0_pairs.json','w'))
print(sum(map(len,cp.values())), sum(map(len,ap.values())))
