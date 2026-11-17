import importlib.util,json,glob,collections,sys
def mod(p,n):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b8=mod('/scratch/jjyeung/orch_n30/review_tree9/b8/work/tree_r1/student_pilot/row_text_audit.py','b8')
b9=mod('/scratch/jjyeung/orch_n30/review_tree9/pkg/work/tree_r1/student_pilot/row_text_audit.py','b9')
L='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/'
c=collections.Counter();ex=[]
for p in sorted(glob.glob(L+'slices_final/*.jsonl')+glob.glob(L+'slices_v3/*.jsonl')):
    for line in open(p):
        r=json.loads(line);a=set(b8.reasons(r));b=set(b9.reasons(r))
        c['rows']+=1
        if a!=b:
            k=(tuple(sorted(a-b)),tuple(sorted(b-a)),p.split('/')[-1]);c[k]+=1
            if len(ex)<3:ex.append((r['qid'],sorted(a),sorted(b)))
        if (a-{'runtime_box_status'})!=(b-{'runtime_box_status'}):c['other_pattern_diff']+=1
for k,v in c.items():print(k,v)
print(ex)
