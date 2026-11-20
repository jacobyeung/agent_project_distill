X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173796; ls -la $O/live; sha256sum $O/live/*
python3 -I -s -B - <<'PY'
import json,os
O='/project/community/jjyeung/okh7/x_22c714e1/o/173796/live'
for n in sorted(os.listdir(O)):
    v=json.load(open(O+'/'+n)); print('@@',n,list(v)[:30] if isinstance(v,dict) else type(v).__name__)
    def find(x,p=''):
        if isinstance(x,dict):
            for k,y in x.items():
                if k in ('sources','source_deferrals') or 'DEFERRED' in json.dumps(y)[:20000] and k in ('selection','receipt'): print('  ',p+'/'+k, json.dumps(y)[:1200])
                elif isinstance(y,(dict,list)): find(y,p+'/'+k)
    find(v)
    s=json.dumps(v); print('  moved_to_vqa_store',s.count('moved_to_vqa_store'),'source_not_final',s.count('source_not_final'),'655b953d',s.count('655b953d'))
PY
