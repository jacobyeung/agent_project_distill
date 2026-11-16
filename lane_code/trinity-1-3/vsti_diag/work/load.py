import json,re,collections
X='/scratch/jjyeung/orch_n30/vsti_diag/work/x'
C='/scratch/jjyeung/orch_n30/native_r4/in/comparators'
T={t['id']:t for t in map(json.loads,open(X+'/i/TASKS.jsonl'))}
S=json.load(open(X+'/i/SCORES.json'))
nat={r['key']:r for r in map(json.loads,open(X+'/j0/items.jsonl')) if r['arm']=='native'}
cmp={}
for n in ('f17','p1m200'):
    cmp[n]={'q'+str(r['example_id']):r for r in map(json.loads,open(f'{C}/{n}.per_question_scores.jsonl'))}
REL=['camera_obj_rel_dist_v1','camera_obj_rel_dist_v2','camera_obj_rel_dist_v3','obj_obj_relative_pos_lr','obj_obj_relative_pos_nf','obj_obj_relative_pos_ud']
def opt(k,letter):
    for o in S[k]['options']:
        if o.split('.')[0].strip()==str(letter).strip(): return o.split('.',1)[1].strip()
    return None
def thinktext(r):
    t=r['decode']['text']; return t.split('</think>')[0]
