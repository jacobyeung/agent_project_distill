#!/usr/bin/env bash
# PDG v3 (gated connector) S1->S2 gate (PDG_V3_DESIGN.md section 5). Run on a Trinity compute node that reaches code-aws, after the gate
# cells 098e5e92_s1g_vsi (shards 0-4 of 25, thinking pinned) and 098e5e92_s1g_nothink_vsi (shard 0 of 5) and the norm
# job (eval/v3d/8b2dc6a7_out.json) have finished. Three ssh calls. Writes GATE_S1S2.json locally and to the S1 run root
# on code-aws, where s/f90df9d5_legs.sh reads it before S2 leg 1. Exit 0 = PASS, 3 = FAIL.
# usage: pdg_v3_gate_run.sh GATE_SCRIPT_DIR   (the directory holding pdg_v3_gate.py)
set -euo pipefail
tools="${1:?directory of pdg_v3_gate.py}"
work="/scratch/$USER/pdg_v3_gate_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$work"
ssh_aws() { timeout 180 ssh -o ConnectTimeout=10 code-aws "$@"; }
R=/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9/d/orch/runs/aws128p_20261025
C=$R/eval/cells
ssh_aws "cd $C && tar cf - 098e5e92_s1g_vsi/run/questions 098e5e92_s1g_vsi/run/sharding.json 098e5e92_s1g_nothink_vsi/run/questions b359b000_arm_vsi/score/per_question_scores.jsonl b359b000_nothink_vsi/score/per_question_scores.jsonl -C $R/eval/v3d 8b2dc6a7_out.json" | tar xf - -C "$work"
qids=$(python3 -c "
import json, sys
a = json.load(open(sys.argv[1]))['assignments']
print(' '.join(x['qid'] for x in a if x['shard_index'] < 5))" "$work/098e5e92_s1g_vsi/run/sharding.json")
ssh_aws "cd $C/b359b000_arm_vsi/run/questions && tar cf - \$(for q in $qids; do ls \${q}_*.json; done)" | { mkdir -p "$work/base_think"; tar xf - -C "$work/base_think"; }
set +e
python3 "$tools/pdg_v3_gate.py" "$work/098e5e92_s1g_vsi/run/questions" --base "$work/b359b000_arm_vsi/score/per_question_scores.jsonl" \
    --base-questions "$work/base_think" --min-items 95 --out "$work/gate_think.json" > /dev/null; think=$?
python3 "$tools/pdg_v3_gate.py" "$work/098e5e92_s1g_nothink_vsi/run/questions" \
    --base "$work/b359b000_nothink_vsi/score/per_question_scores.jsonl" --min-items 95 --out "$work/gate_nothink.json" > /dev/null; nothink=$?
set -e
python3 - "$work" "$think" "$nothink" <<'PY'
import json, sys, datetime
work, think, nothink = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
t = json.load(open(f"{work}/gate_think.json")); n = json.load(open(f"{work}/gate_nothink.json"))
norm = json.load(open(f"{work}/8b2dc6a7_out.json"))["summary"]["connectors"]["v3_s1_final"]
checks = {"thinking_vsi": t["gate"], "nothink_vsi": n["gate"],
          "norm_ratio": "PASS" if norm["ratio_median_of_items"] <= 0.5 and norm["ratio_items_p90"] <= 1.0 else "FAIL",
          "thinking_items": t["items"], "nothink_items": n["items"]}
ok = checks["thinking_vsi"] == checks["nothink_vsi"] == checks["norm_ratio"] == "PASS"
out = {"gate": "PASS" if ok else "FAIL", "checks": checks, "written_utc": datetime.datetime.utcnow().isoformat() + "Z",
       "thinking": {k: t.get(k) for k in ("items", "candidate", "base", "diff_vs_base", "diff_ci95", "length_check", "parse_failures", "cap_hits", "gate_reasons")},
       "nothink": {k: n.get(k) for k in ("items", "candidate", "base", "diff_vs_base", "diff_ci95", "parse_failures", "gate_reasons")},
       "norm": {k: norm[k] for k in ("ratio_median_of_items", "ratio_items_p90", "delta_token_norm_median", "cosine_injected_vs_rgb_median")}}
open(f"{work}/GATE_S1S2.json", "w").write(json.dumps(out, indent=1, sort_keys=True) + "\n")
print(json.dumps(out, indent=1, sort_keys=True))
PY
ssh_aws "cat > $R/r1pdgs1v3g_098e5e92/GATE_S1S2.json" < "$work/GATE_S1S2.json"
grep -q '"gate": "PASS"' "$work/GATE_S1S2.json" && exit 0 || exit 3
