R=/scratch/jjyeung/orch_n30
date -u +%TZ; free -g | sed -n 2p; cat /proc/loadavg; tmux ls -F "#{session_name}" | grep "^sb_" | tr "\n" " "; echo
tail -3 $R/sb_queue/codexq.log; echo Q: $(cat $R/sb_queue/queue.txt | tr "\n" " ")
for t in sb_mdrev sb_ktfix sb_mask_phrase sb_mask_carry sb_rlfix3 sb_f64fix2; do echo "== $t log=$(wc -c < $R/$t/cursor.log 2>/dev/null)"; ls $R/$t/out 2>/dev/null | tr "\n" " " | cut -c1-300; echo; head -c 350 $R/$t/STATUS.md 2>/dev/null; echo; done
python3 -c "
import json;d=json.load(open('$R/sb_rkdocs/out/GPU_NEED.json'));print(json.dumps(d.get('cpu_fallback'))[:800])"
