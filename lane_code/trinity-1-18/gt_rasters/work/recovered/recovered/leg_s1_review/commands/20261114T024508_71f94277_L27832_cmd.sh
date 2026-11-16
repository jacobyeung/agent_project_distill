<!-- recovered by seal_plan: transcript=71f94277 line=27832 utc=2026-11-14T02:45:08.588Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; P=$C/if_p0/out/P0_CONTROL; mkdir -p $P && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$C" "$P" <<'EOF'
import sys, json, hashlib, datetime
C, P = sys.argv[1], sys.argv[2]
seal = "8d5bdd730bebb9b317f7d4aa715cfe06981f698eceed13af81f3232d07cd3a90"
verdict_path = C + "/leg_s1_review/REVIEW_VERDICT_IF_P0_JOB_KIT.md"
verdict = open(verdict_path, encoding="utf-8").read().replace("\r\n", "\n")
vsha = hashlib.sha256(open(verdict_path, "rb").read()).hexdigest()
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
d1 = C + "/if_p0/out/refinement_v2/IF_P0_JOB_RUNTIME.diff"
d2 = C + "/if_p0/out/tree_provenance_v3/IF_P0_JOB_RUNTIME.diff"
text = (
"# Cross-family confirmation of the IF-P0 job kit, seal " + seal + "\n\n"
"This text has three parts: (A) the independent review of seal 8df5fb58 by a reviewer of another model family than the author; (B) the orchestrator's reading of the runtime diff from 8df5fb58 to 0ae42c6e; (C) the orchestrator's reading of the runtime diff from 0ae42c6e to the final seal. The author is a GPT-family lane; the reviewer and the orchestrator are Claude models (Anthropic).\n\n"
"## A. Independent review of seal 8df5fb584417e0e5 (verbatim; file " + verdict_path + ", sha256 " + vsha + ")\n\n"
+ verdict.rstrip("\n") + "\n\n"
"## B. Diff 8df5fb58 -> 0ae42c6e (file " + d1 + ", sha256 " + sha(d1) + ", 362 lines; read in full by orchestrator orch-home-distill-79)\n\n"
"- The prior-arm gate (P0 headroom, IF8 pass, twelve-hour projection) is factored into one function and also runs as the new action check-prior, after the interpreter is staged and before the model, the donor, the database and the frames are read (review finding m2). The trainer repeats it.\n"
"- The job now runs, before any large read: the mount proof of its private /tmp, the card query with name and UUID, an allocation check (general, one node, one task, eight CPUs, at least 200 GiB), the staging of the pinned bwrap binary and a namespace smoke test with the system Python (finding m5). Then the interpreter and overlays, check-runtime, and only then the large inputs.\n"
"- The IF8 projection uses the logged data seconds and a compute multiplier of 4.3 as its upper bound, rejects missing or impossible data times, and refuses instead of shortening (finding m1).\n"
"- The fixture root can be redirected by an environment variable restricted to /scratch (finding m6).\n"
"- Noted, not a defect: the early namespace call creates its bind-source folders before staging; every extractor creates folders with exist_ok, but the fixture rehearsal skips the namespace, so the first real job is the first execution of this order.\n"
"- Model, optimizer, protocol, selection, exclusion gate, read and decision rules are not touched by this diff.\n\n"
"## C. Diff 0ae42c6e -> " + seal[:8] + " (file " + d2 + ", sha256 " + sha(d2) + "; read in full by the orchestrator)\n\n"
"- The admission no longer asks for a git commit or a source_clean flag; it requires source_identity = {kind: sealed_tree, kit_sha256: the kit's own seal}. A code_commit is optional and, if present, must be 40 hex characters. The run record carries the source identity and the words 'not in git'. Reason: no lane holds a git worktree for this kit, the production leg is itself identified by a sealed tree, and the kit carries a data file that does not belong in git.\n"
"- Nothing else changes.\n\n"
"## What was not checked and what the first real job (P0) must show\n\n"
"As in part A: check-runtime passing on the node; selection.json sha256 4d53d9b893d5c34dce32357b6e1c80ba93a2a39fde75df92dac78890be49669f with 2,667 excluded-scene and 17,478 outside-k7pd skips; a frame plan of 86,396 k7pd and 1,664 k6tk entries; bitwise step-0 equality in gpu_step0.json; peak reserved memory; data seconds against wall seconds per step; budget.json with the IF8 projection. The tests (67) and the three-arm fixture rehearsal are the author's records for the final seal; the orchestrator did not rerun them. The independent reviewer ran the 52 tests of seal 8df5fb58.\n\n"
"Verdict for seal " + seal + ": PASS for launching arm P0. Later arms need the orchestrator's separate launch notes.\n")
open(P + "/review.md", "w", encoding="utf-8", newline="\n").write(text)
rsha = hashlib.sha256(text.encode("utf-8")).hexdigest()
conf = {"schema": "ifp0-cross-family-review-v1", "verdict": "PASS", "kit_sha256": seal,
        "source_identity": {"kind": "sealed_tree", "kit_sha256": seal},
        "reviewer_family": "anthropic",
        "reviewer": "Claude Opus (independent review of seal 8df5fb58, REVIEW_VERDICT_IF_P0_JOB_KIT.md) and orchestrator orch-home-distill-79 (Claude; diff readings to the final seal)",
        "report_sha256": rsha, "synthetic": False}
open(P + "/confirmation.json", "w", encoding="utf-8", newline="\n").write(json.dumps(conf, indent=2) + "\n")
open(P + "/launch_note.md", "w", encoding="utf-8", newline="\n").write("LAUNCH IF-P0 P0 " + seal + "\n")
print(rsha, len(text))
EOF
sha256sum $P/review.md $P/confirmation.json $P/launch_note.md | cut -c1-16,65-; K=$C/if_p0/out/tree_provenance_v3/kit_ifp0_orchard_job_8d5bdd730bebb9b3; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import sys, json, hashlib
sys.path.insert(0, '$K')
import orchard_job_contract as J
conf=json.load(open('$P/confirmation.json')); text=open('$P/review.md', encoding='utf-8').read(); note=open('$P/launch_note.md').read()
from inputs import digest
control=dict(schema='ifp0-job-admission-v1', kit_sha256=conf['kit_sha256'], arm='P0', synthetic=False,
  confirmation=dict(kit_sha256=conf['kit_sha256'], record=conf, record_sha256=digest(conf), text=text, sha256=hashlib.sha256(text.encode()).hexdigest()),
  launch_note=note, launch_note_sha256=hashlib.sha256(note.encode()).hexdigest())
J.admit(control, conf['kit_sha256'], 'P0', False); print('admit() accepts the three control files for arm P0')
try:
    J.admit(dict(control, arm='IF8'), conf['kit_sha256'], 'IF8', False); print('UNEXPECTED: IF8 admitted')
except ValueError as e: print('IF8 refused as expected:', e)
"