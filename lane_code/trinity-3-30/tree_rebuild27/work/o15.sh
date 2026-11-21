export TZ=UTC; D=/project/community/jjyeung/okh7/x_22c714e1/t_fa5d00a8e996; sacct -j 174132 -n -X -o State,ExitCode,Elapsed | head -1
sed -n 1,8p $D/r.txt | cut -c1-200; grep -n "AS_EXPECTED\|^==\|expect" $D/r.txt | cut -c1-250 | head -20
python3 -c "
import json
for l in open('$D/r.txt'):
    l=l.strip()
    if l.startswith('{\"case\"'):
        d=json.loads(l); print(d.get('case'),d.get('role'),'fail=',str(d.get('fail'))[:40],'raised_by=',d.get('raised_by'),'err=',str(d.get('error'))[:90],'ok=',d.get('ok'),'as_expected=',d.get('as_expected'))
"
