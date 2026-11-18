<!-- recovered by seal_plan: transcript=71f94277 line=29433 utc=2026-11-14T07:19:56.297Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; P=$C/if_p0/out/P0_CONTROL_0fa68201; K=$C/if_p0/out/inventory_v6/kit_ifp0_orchard_job_0fa68201bddadd5b; mkdir -p $P && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$C" "$P" "$K" <<'EOF'
import sys, json, hashlib
C, P, K = sys.argv[1], sys.argv[2], sys.argv[3]
seal = json.load(open(K + "/SEAL.json")).get("kit_sha256") if False else None
import os
seal = "0fa68201bddadd5bfeb0c747f8bcc8fa5b72dd3b2bbc4af2568a5370401b20ea"
vpath = C + "/leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_0fa68201.md"
verdict = open(vpath, encoding="utf-8").read().replace("\r\n", "\n")
vsha = hashlib.sha256(open(vpath, "rb").read()).hexdigest()
prior = C + "/if_p0/out/P0_CONTROL/review.md"
psha = hashlib.sha256(open(prior, "rb").read()).hexdigest()
text = (
"# Cross-family confirmation of the IF-P0 job kit, seal " + seal + "\n\n"
"The author is a GPT-family lane; the reviewers are Claude models (Anthropic). This text has two parts.\n\n"
"## A. Confirmations up to the predecessor seal 8d5bdd73\n\n"
"The independent review of seal 8df5fb58 and the orchestrator's readings of the two diffs up to seal 8d5bdd73 are the text `" + prior + "` (sha256 " + psha + "). That seal's first real job (Orchard job 169413) passed its preflight, the namespace smoke test and the interpreter and NumPy staging, and failed after 64 seconds because the kit asked a staged archive for a member it does not contain.\n\n"
"## B. Independent review of the cumulative change from 8d5bdd73 to " + seal[:8] + " (verbatim; file " + vpath + ", sha256 " + vsha + ")\n\n"
+ verdict.rstrip("\n") + "\n\n"
"## Verdict\n\n"
"PASS for launching arm P0 under seal " + seal + ". The reviewer's three minor findings do not block it. The next real job is the first to execute every stage after the interpreter and NumPy staging, and must show what part B lists. Later arms need the orchestrator's separate launch notes.\n")
open(P + "/review.md", "w", encoding="utf-8", newline="\n").write(text)
rsha = hashlib.sha256(text.encode("utf-8")).hexdigest()
conf = {"schema": "ifp0-cross-family-review-v1", "verdict": "PASS", "kit_sha256": seal,
        "source_identity": {"kind": "sealed_tree", "kit_sha256": seal},
        "reviewer_family": "anthropic",
        "reviewer": "Claude Opus (independent reviews: REVIEW_VERDICT_IF_P0_JOB_KIT.md on seal 8df5fb58 and REVIEW_VERDICT_IF_P0_SEAL_0fa68201.md on the cumulative change) and orchestrator orch-home-distill-79 (diff readings up to 8d5bdd73)",
        "report_sha256": rsha, "synthetic": False}
open(P + "/confirmation.json", "w", encoding="utf-8", newline="\n").write(json.dumps(conf, indent=2) + "\n")
open(P + "/launch_note.md", "w", encoding="utf-8", newline="\n").write("LAUNCH IF-P0 P0 " + seal + "\n")
sys.path.insert(0, K)
import orchard_job_contract as J
from inputs import digest
note = open(P + "/launch_note.md").read()
control = dict(schema="ifp0-job-admission-v1", kit_sha256=seal, arm="P0", synthetic=False,
  confirmation=dict(kit_sha256=seal, record=conf, record_sha256=digest(conf), text=text, sha256=rsha),
  launch_note=note, launch_note_sha256=hashlib.sha256(note.encode()).hexdigest())
J.admit(control, seal, "P0", False); print("admit() accepts P0 for seal", seal[:8])
try:
    J.admit(dict(control, arm="IF8"), seal, "IF8", False); print("UNEXPECTED: IF8 admitted")
except ValueError as e: print("IF8 refused:", e)
print("review.md", rsha[:16])
EOF
sha256sum $P/confirmation.json $P/launch_note.md | cut -c1-16,65-; grep -c "" $C/leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_0fa68201.md