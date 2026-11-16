<!-- recovered by seal_plan: transcript=71f94277 line=20777 utc=2026-11-13T12:37:37.739Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/leg_s1_fourstream_kit/final_a; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c '
import json
l=json.load(open("k/launch.json"))
for k in sorted(l):
    print(k, "=", str(l[k])[:160])
a=json.load(open("k/4.json"))
print("---- 4.json")
for k in sorted(a):
    print(k, "=", str(a[k])[:260])
'