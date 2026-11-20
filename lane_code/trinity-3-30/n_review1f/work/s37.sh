R=/scratch/jjyeung/orch_n30/n_review/r1f; mkdir -p $R/chk; cat > $R/chk/taska.py <<'PYEOF'
# usage: taska.py <job dir with nd.json chain.json routing_types.json cand_cmp.json na.json.gz rd0/rdiff_summary.json>
import json,sys,gzip,os,hashlib,collections
D=sys.argv[1]; J=lambda n: json.load(open(os.path.join(D,n)))
sha=lambda n: hashlib.sha256(open(os.path.join(D,n),'rb').read()).hexdigest()
COPIED=['/row/'+k for k in 'source_qid candidate_id question question_type answer gt_answer ground_record provenance tool_output_spans'.split()]
PATHS=['/row/s1_source/source/path','/row/s1_source/frame_binding/authority/map/path','/row/s1_source/frame_binding/authority/plan/path','/row/s1_source/frame_binding/authority/fps_authority/path']
FPS=['/row/s1_source/frame_binding/fps_source']
inp=lambda p,par: p==par or p.startswith(par+'/')
out={}
for n in ('nd.json','chain.json','routing_types.json','cand_cmp.json','na.json.gz','n_sample.json','p_sample.json','routing_selection.json','proc_check.json'):
    if os.path.isfile(os.path.join(D,n)): out['sha_'+n]=sha(n)
nd=J('nd.json')
allowed=set(['/i','/row','/row/s1_source']+COPIED)
cfc=nd['content_field_counts']
out['a_content_paths_outside_allowed']={k:v for k,v in cfc.items() if k not in allowed}
out['a_target_or_encode_diff']={k:v for k,v in cfc.items() if k in ('/target','/row/student_input','/row/routing','/row/qid','/row/dataset','/row/scene','/row/category','/row/r1_source','/row/target','/row/suffix','/row/response','/row/trace')}
cls=collections.Counter(); bad={}
for p,c in nd['paths'].items():
    lab=[n for n,ps in (('copied',COPIED),('paths',PATHS),('fps',FPS),('ordinal',['/i'])) if any(inp(p,x) for x in ps)]
    if lab: cls[lab[0]]+=c
    else: bad[p]=c
out['b_paths_outside_four_classes']=bad; out['b_class_leaf_counts']=dict(cls)
out['b_metadata_classes']=nd['metadata_classes']; out['b_unclassified']=nd['unclassified_paths']
s1=[p for p in nd['paths'] if p.startswith('/row/s1_source')]; out['b_s1_source_leaves_not_paths_or_fps']=[p for p in s1 if p not in PATHS+FPS]
for k in ('P_database_sha256','database_sha256','P_rows','N_rows','matched_rows','N_without_P','identical_sql_rows','content_differing_rows','absent_count','absent_unattributed','retained_excluded','U_Faithful','task_i','task_ii','task_iii','status','request_sha256','content_fields_sha256'):
    out['nd_'+k]=nd.get(k)
ch=J('chain.json')
out['c_chain']={s:{k:r.get(k) for k in ('status','rows_checked','refused_rows','database_rows','complete','unique_rows_checked','counts','database_key_set_sha256','checked_key_set_sha256')} for s,r in ch['streams'].items()}
out['c_population']=ch.get('population'); out['c_extent_receipt']=ch.get('extent_receipt'); out['c_first']=ch.get('first_ten_refusals'); out['c_config_sha256']=ch.get('config_sha256')
out['c_other']={k:ch[k] for k in ch if k not in ('streams','population','first_ten_refusals','candidate','extent_receipt')}
if os.path.isfile(os.path.join(D,'routing_types.json')): out['rt']=J('routing_types.json')
na=json.load(gzip.open(os.path.join(D,'na.json.gz')))
out['na']={k:na.get(k) for k in ('schema','status','count','unattributed','counts_by_source_attribution','U_Faithful')}
out['na_attr']=dict(collections.Counter(r['attribution'] for r in na['rows']))
out['na_lists']=dict(collections.Counter(h for r in na['rows'] for h in r['removal_list_sha256s']))
rs=os.path.join(D,'rd0/rdiff_summary.json')
if os.path.isfile(rs): v=json.load(open(rs)); out['rd_summary']={k:v.get(k) for k in v if k not in ('examples',)}
print(json.dumps(out,indent=1,sort_keys=True,default=str))
PYEOF
sha256sum $R/chk/taska.py; date -u +%TZ
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $R/chk/taska.py /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173754/173754 > $R/taska_d173754.json 2>&1; sha256sum $R/taska_d173754.json; head -c 9000 $R/taska_d173754.json
