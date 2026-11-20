W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; P=/scratch/jjyeung/envs/p1cpu/bin/python; R=/scratch/jjyeung/orch_n30/n_review/r1g; mkdir -p $R
D=$W/work/d173881/173881; date -u +%TZ; ls $D | tr '\n' ' '; echo
cd $R && nice -n 10 $P -I -s -B /scratch/jjyeung/orch_n30/n_review/r1f/chk/taska.py $D 2>&1 | sed 's/PASS/STATUS_OK/g' > $R/taska_d173881.json; sha256sum $R/taska_d173881.json
F=$(ls $W/w24y2/out/rcj/f.json $W/w24y2/work/*/rcj/f.json 2>/dev/null | head -1); echo "F=$F"; sha256sum $F
nice -n 10 $P -I -s -B - "$D" "$F" "$R/taska_d173881.json" <<'PY' 2>&1 | sed 's/PASS/STATUS_OK/g'
import json,sys,os,hashlib
D,F,T=sys.argv[1:4]; t=json.load(open(T))
print('TASKA non-chain keys:')
for k in sorted(t):
    if k.startswith(('c_chain','b_class','b_metadata','c_other','c_extent')): continue
    print(' ',k,json.dumps(t[k],default=str)[:600])
print('c_other extent fields:',{k:v for k,v in t['c_other'].items() if k!='extent_scope'})
es=t['c_other'].get('extent_scope',{}); print('extent card',json.dumps(es.get('card'))[:900])
tc=es.get('tests',{}); print('tests status',tc.get('status'),'no_real_other',tc.get('no_real_other'))
for n,c in tc.get('cases',{}).items(): print('  case',n,{k:c.get(k) for k in ('qid','expected','observed','exempted','origin','status','row_sha256')}, 'store', json.dumps(c.get('source_store'))[:200])
for s in tc.get('stores',[])[:2]: print('  store',s)
r=t['c_chain']['routing']; print('routing chain',{k:r[k] for k in r if k!='counts'}, r['counts'])
for s in ('vqa','pointing','pose'): print(' ',s,t['c_chain'][s]['status'],t['c_chain'][s]['refused_rows'],t['c_chain'][s]['rows_checked'])
nd=json.load(open(D+'/nd.json'))
print('nd field_derivation',json.dumps(nd.get('field_derivation'))[:2500])
print('nd content_field_paths',json.dumps(nd.get('content_field_paths'))[:1500])
print('nd criteria',json.dumps(nd.get('criteria'))[:1500])
print('nd absent_counts',json.dumps(nd.get('absent_counts'))[:800], 'P_absent_source', json.dumps(nd.get('P_absent_source'))[:300])
f=json.load(open(F)); print('f.json keys',sorted(f) if isinstance(f,dict) else type(f))
print('f.json',json.dumps(f)[:2500])
for n in ('routing_types.json','proc_check.json','rdiff_summary.json','cand_cmp.json'):
    p=os.path.join(D,n)
    if not os.path.isfile(p): p=os.path.join(D,'rd0',n)
    if os.path.isfile(p): print('==',n,hashlib.sha256(open(p,'rb').read()).hexdigest()[:16],json.dumps(json.load(open(p)))[:1800])
    else: print('==',n,'ABSENT')
PY
ls $D/rd0 2>&1 | head; ls $D/live 2>&1 | head -30
