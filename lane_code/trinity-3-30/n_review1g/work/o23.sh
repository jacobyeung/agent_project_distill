X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173912; TZ=UTC date +%TZ
ls $X/u | grep -c '^655b953d'; cat $O/q.log | cut -c1-300; cat $O/r0.json; echo; cat $O/RESULT.json; echo
nice -n 10 python3 -I -s -B - <<'PY'
import json,hashlib
X='/project/community/jjyeung/okh7/x_22c714e1'; O=X+'/o/173912'
rs=json.load(open(O+'/routing_selection.json')); s1=rs['inputs_pinned'].get('s1_routing',{})
print('pinned s1_routing keys',list(s1)); print(' selection pin',s1.get('selection')); print(' rows',rs['rows'],'regen',rs['regenerated_sha256'],'receipt',rs['regenerated_receipt'])
P=json.load(open(X+'/u/5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'))['sources']
for n in ('k_dr_p_q_sc_p_p_receipt.json','k_dr_p_q_selection_pool_receipt.json'):
    v=json.load(open(O+'/'+n)); s=v['sources']; print('==',n,hashlib.sha256(open(O+'/'+n,'rb').read()).hexdigest()[:8],'scope',json.dumps(v.get('scope'))[:200],'rows_withheld_by_source',json.dumps(v.get('rows_withheld_by_source'))[:300])
    for k in sorted(set(P)|set(s)):
        a=P.get(k,{}); b=s.get(k,{})
        print('  %-16s P %-9s %-24s %6s %6s | N %-9s %-24s %6s %6s'%(k,a.get('status'),a.get('reason'),a.get('declared_rows'),a.get('retained'),b.get('status'),b.get('reason'),b.get('declared_rows'),b.get('retained')))
PY
