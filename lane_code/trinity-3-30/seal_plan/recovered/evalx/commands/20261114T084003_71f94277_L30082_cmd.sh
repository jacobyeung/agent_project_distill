<!-- recovered by seal_plan: transcript=71f94277 line=30082 utc=2026-11-14T08:40:03.008Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; P=$C/if_p0/out/P0_CONTROL_799a21dd; K=$C/if_p0/out/modes_v7/kit_ifp0_orchard_job_799a21dd2eef37af; mkdir -p $P && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$C" "$P" "$K" <<'EOF'
import sys, json, hashlib
C, P, K = sys.argv[1], sys.argv[2], sys.argv[3]
seal = "799a21dd2eef37afefe675d655536edd46d48af9a56c2b5fc86d4b2a5a101b4c"
vpath = C + "/leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_799a21dd.md"
verdict = open(vpath, encoding="utf-8").read().replace("\r\n", "\n")
vsha = hashlib.sha256(open(vpath, "rb").read()).hexdigest()
prior = C + "/if_p0/out/P0_CONTROL_0fa68201/review.md"
psha = hashlib.sha256(open(prior, "rb").read()).hexdigest()
text = (
"# Cross-family confirmation of the IF-P0 job kit, seal " + seal + "\n\n"
"The author is a GPT-family lane; the reviewers are Claude models (Anthropic). This text has two parts.\n\n"
"## A. Confirmations up to the predecessor seal 0fa68201\n\n"
"The earlier reviews and readings are the text `" + prior + "` (sha256 " + psha + "). That seal's real job (Orchard job 169474) passed every archive inventory and the namespace smoke test and failed after 45 seconds at a runtime check that demanded a composite fast-path flag the production runtime never has; the extractor was also found to drop file modes.\n\n"
"## B. Independent review of the change from 0fa68201 to " + seal[:8] + " (verbatim; file " + vpath + ", sha256 " + vsha + ")\n\n"
+ verdict.rstrip("\n") + "\n\n"
"## Verdict\n\n"
"PASS for launching arm P0 under seal " + seal + ". The next real job is the first to execute the Triton compile probe on a GPU, the model, checkpoint and frame staging, prepare and training; it must show what part B lists. Later arms need the orchestrator's separate launch notes.\n")
open(P + "/review.md", "w", encoding="utf-8", newline="\n").write(text)
rsha = hashlib.sha256(text.encode("utf-8")).hexdigest()
conf = {"schema": "ifp0-cross-family-review-v1", "verdict": "PASS", "kit_sha256": seal,
        "source_identity": {"kind": "sealed_tree", "kit_sha256": seal},
        "reviewer_family": "anthropic",
        "reviewer": "Claude Opus (independent reviews of seals 8df5fb58, 0fa68201 and 799a21dd) and orchestrator orch-home-distill-79 (diff readings up to 8d5bdd73)",
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
N=$(date -u +%Y%m%dT%H%MZ); cat > $C/if_p0/inbox/${N}_ORCH_GO_build_P0_packet_seal_799a21dd_general.md <<'EOF'
# ORCH: seal 799a21dd is confirmed READY; control files written; build the P0 packet for `general` now

Independent verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_799a21dd.md` (READY, no blocker; 207 science files identical; the kernel path is production's; 116 tests from a private copy; a tiny real native model passes the per-layer rule on all 32 layers). Its minor m1 (the per-layer rule runs only after all staging; a two-layer check inside `check-runtime` would catch a false refusal 15 to 30 minutes earlier) goes into the next seal, not this one.

Control files: `/scratch/jjyeung/orch_cd/if_p0/out/P0_CONTROL_799a21dd/` (`review.md`, `confirmation.json`, `launch_note.md`). Your gate's `admit()` accepts P0 and refuses IF8 with them.

Now: fresh token (never a35f2d78fe7c5ee8d or a1bf5cb5a7bad53bf), P0 packet with `--partition general`, verify `BATCH.sh` against its pin, hand-off note into `/scratch/jjyeung/orch_cd/evalx/inbox/` with `IF_P0_P0_PACKET_READY_799a21dd` in its name (token, path, size, sha256, the two `sbatch` argument lists with `/usr/local/bin/sbatch`, the result path, how to tell a refusal from a training failure). evalx has my word to submit it on arrival. One RESULT from you.
EOF
cat > $C/evalx/inbox/${N}_ORCH_WORD_submit_P0_seal_799a21dd.md <<'EOF'
# ORCH word: submit IF-P0 P0 under seal 799a21dd when its packet arrives

Lane if_p0 is building the packet (seal 799a21dd2eef37afefe675d655536edd46d48af9a56c2b5fc86d4b2a5a101b4c, partition `general`, fresh token); the hand-off note will have `IF_P0_P0_PACKET_READY_799a21dd` in its name. This word covers that one packet: verify the batch hash; queue and main-notice check; `/usr/local/bin/sbatch --test-only`, then one real submission; RESULT with the job id; observe its start (inventories, the Triton compile probe in `check-runtime`, model and checkpoint staging, `prepare` with selection hash 4d53d9b8..., the frame plan, step-0 equality, peak memory, the first step times) and report those as they appear; fetch the bounded return when it ends.

**Queue order from now on.** The one-GPU slot is free at this moment, so P0 goes in as soon as its packet arrives. The step-400 read and the next native pilot are submitted when each is ready, through the bounded controller with `ALLOW <the P0 job id you submit under this word>`; they queue behind P0. Tell me when both are queued and P0 has reported its first measured step times: I then decide whether P0 runs to its end or yields the slot to the two reads.
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: REVIEW of IF-P0 seal 799a21dd: READY (leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_799a21dd.md; Opus high): science identical; kernel path is production's; compile probe early; per-layer rule after staging (minor m1); modes correct; 116 tests. WROTE if_p0/out/P0_CONTROL_799a21dd/{review.md, confirmation.json, launch_note.md}; the kit's admit() accepts P0, refuses IF8. ORDERS ($N): if_p0 builds the P0 packet for general with a fresh token; evalx submits it on arrival; the step-400 read and the next native pilot queue behind it via the bounded controller; I decide whether P0 runs to its end once it has measured step times and both reads are queued." >> $C/ORCH_HANDOFF.md