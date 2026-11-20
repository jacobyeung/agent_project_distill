export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=173725; O=$X/o/$J; cd $O; ls -la | grep -v " k_" ; ls -la rd0; du -sh .; tar czf - . | wc -c
python3 - <<'PY'
import json,os
t=json.load(open('timings.json'))
def short(x,n=1500): s=json.dumps(x); return s[:n]
for k in ('returncode','aggregate_limit_status','aggregate_publication_bytes','helper_publication_bytes','proc_status','rdiff_status','mode_r_seconds','publication_errors','log_tail_errors'): print(k, short(t.get(k),400))
print('chain', short(t.get('chain'),2500))
print('files', {k:v.get('size') for k,v in t.get('files',{}).items()})
for f in ('proc_check.json','routing_types.json','nd.json','cand_cmp.json','rd0/rdiff_summary.json'):
    if os.path.exists(f): print('==',f, short(json.load(open(f)),1800))
PY
grep -n "Error\|REFUS\|FAIL" $X/j/$J.log | grep -v '^.*{"source' | tail -15 | cut -c1-300
