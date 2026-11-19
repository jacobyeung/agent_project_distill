R=/scratch/jjyeung/orch_n30
date -u +%TZ; tmux ls -F "#{session_name}" | grep "^sb_" | tr "\n" " "; echo
echo "ktrev2 log=$(wc -c < $R/sb_ktrev2/cursor.log)"; ls $R/sb_ktrev2 $R/sb_ktrev2/out 2>/dev/null | tr "\n" " "; echo
ls $R/sb_ktfix $R/sb_ktfix/code $R/sb_ktfix/scripts | tr "\n" " "; echo
cat $R/sb_ktfix/code/README.md | head -60
python3 -c "
import json;d=json.load(open('$R/sb_ktfix/out/GPU_NEED.json'));print(json.dumps({k:v for k,v in d.items() if k not in ('inputs','input_sha256','files')})[:2500])"
cat $R/sb_ktfix/scripts/run_A.sh
