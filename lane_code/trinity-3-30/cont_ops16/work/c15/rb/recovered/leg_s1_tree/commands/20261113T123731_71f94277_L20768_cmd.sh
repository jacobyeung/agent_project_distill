<!-- recovered by seal_plan: transcript=71f94277 line=20768 utc=2026-11-13T12:37:31.698Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/leg_s1_fourstream_kit/final_a; sha256sum SHA256SUMS.txt | cut -c1-64; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c '
import json
l=json.load(open("launch.json"))
for k in ("status","production_authorized","in_job_admission","run","world_size","partition"):
    print(k, "=", str(l.get(k))[:120])
print("keys:", sorted(l)[:40])
a=json.load(open("k/4.json"))
for k in ("modes","allow_until_utc","gpu_cap","wall_seconds","max_parallel_jobs","written_authorization","written_authorizations","production_go","scope"):
    if k in a: print("4.json", k, "=", str(a[k])[:300])
print("4.json keys:", sorted(a))
'; ls k | head -n 40; ls /scratch/jjyeung/orch_cd/leg_s1_tree/inbox | grep -i "AUTHORIZ" | tail -n 3