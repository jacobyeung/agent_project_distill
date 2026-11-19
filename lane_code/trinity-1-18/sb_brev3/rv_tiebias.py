"""Expected accuracy of the visible heuristic 'pick uniformly among objects with the earliest first_seen' (camera families)."""
import json, collections as C, sqlite3
B3='/scratch/jjyeung/orch_n30/sb_rowB3/'
S='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/'
rows=[json.loads(l) for l in open(B3+'out/rows.jsonl')]
ranges=json.load(open(S+'FAMILY_INDEX_RANGES.json'))['families']
con=sqlite3.connect('file:'+S+'vqa/rows.sqlite?mode=ro',uri=True)
src=[]
for f in ['camera_obj_rel_dist_v1','camera_obj_rel_dist_v2','camera_obj_rel_dist_v3']:
    for a,b in ranges[f]: src+=[json.loads(s) for s, in con.execute('select row from rows where i between ? and ?',(a,b))]
def acc(rr):
    out={}
    for f in ['camera_obj_rel_dist_v1','camera_obj_rel_dist_v2','camera_obj_rel_dist_v3']:
        xs=[r for r in rr if r['question_type']==f]; tot=0.; tt=0.; nt=0
        for r in xs:
            fs=r['provenance']['first_seen']; win=r['student_input']['options'][ord(r['answer'])-65][3:]
            m=min(fs.values()); e=[l for l,v in fs.items() if v==m]; v=(win in e)/len(e); tot+=v
            if len(set(fs.values()))<len(fs): tt+=v; nt+=1
        out[f]=dict(rows=len(xs),heuristic_acc=round(tot/len(xs),4),uniform=round(1/len(xs[0]['student_input']['options']),4),tied_rows=nt,tied_heuristic_acc=round(tt/max(nt,1),4))
    return out
res=dict(before_all_sources=acc(src),after_delivered=acc(rows))
json.dump(res,open('/scratch/jjyeung/orch_n30/sb_brev3/out/RV_TIEBIAS.json','w'),indent=1)
print(json.dumps(res,indent=1))
