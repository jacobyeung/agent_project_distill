<!-- recovered by seal_plan: transcript=71f94277 line=21854 utc=2026-11-13T14:24:22.744Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/orchard_cp2/out/canary3_169009; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c '
import json
d=json.load(open("resume_live_20261113T141805Z.json"))
r=d["phases"]["phase_7_resume"][0]
s=r["steps"][0]
print("step",s["step"],"lr",s.get("learning_rates"),"grad",s.get("gradient_norms"))
print("loss",s.get("loss_per_stream"))
sv=r["saves"][0]
print("save",{k:(str(v)[:200]) for k,v in sv.items() if k!="disk_guard"})
'; ls | grep -i "phase4" | head -n 3; f=$(ls | grep -i "phase4_result" | head -n 1); /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c '
import json,sys
d=json.load(open(sys.argv[1]))
s=json.dumps(d)
import re
for m in re.finditer(r"\"learning_rates\": \{[^}]*\}", s): print(m.group(0)[:160])
' "$f" | head -n 4