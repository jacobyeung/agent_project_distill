<!-- recovered by seal_plan: transcript=71f94277 line=28827 utc=2026-11-14T05:14:45.054Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/step200_bffa0d6ef; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$R/DECISION.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
t = d.get("tables", {})
def row(v):
    ci = v.get("ci95_pp"); dl = v.get("delta_pp")
    return "%+.1f [%+.1f, %+.1f]" % (dl, ci[0], ci[1]) if ci and dl is not None else str(dl)
for name in ("leg_minus_parent", "leg_minus_f17"):
    tb = t.get(name, {})
    for part in ("primary", "route_own_labels"):
        c = tb.get(part)
        if not c: continue
        print("==", name, part, "overall", row(c["overall"]), "items", c["overall"].get("items"))
        for typ, v in c["per_type"].items():
            print("   %-28s %s  a=%s b=%s" % (typ, row(v), v.get("a_score", v.get("leg", "")), v.get("b_score", v.get("other", ""))))
print(d.get("m100_reversal"), "|", d.get("R3"))
print({k: d["producer_error_counts"][k]["errors"] for k in d.get("producer_error_counts", {})})
EOF