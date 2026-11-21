export TZ=UTC; date -u +%TZ
timeout 50 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; echo "== postc"; cat log/postc.log | cut -c1-300; echo "== rv2 log tail"; tail -n 2 log/rv2.log | cut -c1-300; for f in d5.json WAITING_REVIEW.json REVIEW_REFUSED.json; do [ -e live2/$f ] && echo "$f: $(cut -c1-400 live2/$f)"; done; echo "== evidence summaries"; python3 -I -B -c "
import json, os
tot=0
for n in (\"e0\",\"e1\",\"e2\",\"e3\"):
    d=json.load(open(\"live2/\"+n+\".json\")); tot+=os.path.getsize(\"live2/\"+n+\".json\")
    print(n, d.get(\"stream\"), \"admitted\", d.get(\"admitted_rows\"), \"answer_only\", d.get(\"answer_only\"), \"protected_rooms\", {k:v.get(\"rows\") for k,v in d.get(\"protected_rooms\",{}).items()}, \"sample\", len(d.get(\"sample\",[])), \"types\", len(d.get(\"question_types\",{})), \"forms\", len(d.get(\"trace_forms\",[])))
    print(\"    question_types\", json.dumps(d.get(\"question_types\"))[:700])
print(\"e5\", open(\"live2/e5.json\").read()[:200]); print(\"bytes of e0..e7\", sum(os.path.getsize(\"live2/e%d.json\"%i) for i in range(8)))
"; echo "== eva"; tail -n 1 n2/eva.jsonl | cut -c1-600; ls n2/p/q/p/ | tr "\n" " "; echo; ls -la n2/p/q/p/frames_4608*/r | tail -2 | cut -c1-100'
squeue -j 174134 -h -o "%i %T %M %N"
