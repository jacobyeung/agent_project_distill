X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173680; cd $O; date -u +%TZ
python3 -I -s -B -c "
import json,collections;d=json.load(open('proc_check.json'));print({k:v for k,v in d.items() if k!='rows'});print(collections.Counter((r['key'][0],r['status'],r['reason']) for r in d['rows']))"
ls -la $X/j | grep 173680; for f in $X/j/*173680*; do echo "@@@ $f"; tail -c 2500 $f; echo; done
