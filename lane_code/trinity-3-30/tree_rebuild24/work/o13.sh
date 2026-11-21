export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; for J in 173964 173966; do echo "== $J"; sacct -j $J -X -n -o State,End,ExitCode; ls $X/o/$J 2>/dev/null | head -20; done
test -f $X/o/173966/E3.json && python3 -c "
import json;r=json.load(open('$X/o/173966/E3.json'));print(r.get('status'),json.dumps(r.get('checks')));print(json.dumps({k:v for k,v in (r.get('rate') or {}).items() if k!='parts'}));print(json.dumps(r.get('resume_real'))[:600])"
tail -3 $X/o/173964/j2.log 2>/dev/null | cut -c1-250; df -BG /project/community | tail -1
