<!-- recovered by seal_plan: transcript=71f94277 line=31246 utc=2026-11-14T11:41:01.994Z kind=commands original_path=(bash command)  -->
O=/scratch/jjyeung/orch_cd/if_p0/out; C=$O/P0_CONTROL_eef3ba96; SEAL=eef3ba96a639d634be9ec9e976ce16aadec648f4eeb07e2bc6fee196d94516bb; test -e $C && { echo "control dir exists"; exit 1; }; mkdir $C; PREV=$(sha256sum $O/P0_CONTROL_799a21dd/review.md | cut -c1-64); DIFF=$(sha256sum $O/guards_v8/IF_P0_RUNTIME_VS_799a21dd.diff | cut -c1-64); cat > $C/review.md <<EOF
# Cross-family confirmation of the IF-P0 job kit, seal $SEAL

The author is a GPT-family lane; the reviewers are Claude models (Anthropic). This text has two parts.

## A. Confirmations up to the predecessor seal 799a21dd

The earlier independent reviews and readings are the text \`/scratch/jjyeung/orch_cd/if_p0/out/P0_CONTROL_799a21dd/review.md\` (sha256 $PREV). That seal's real job (Orchard job 169491) passed the archive inventories, the staging of runtime, model, checkpoint and databases, and the runtime check (staged NumPy, FLA and Triton, 806 FLA files, executable ptxas, a compiled Triton read-back). It failed in \`prepare\` because a CPU node-load guard written for shared Trinity nodes refused a load of 8.83 on a node that also runs our own four-GPU training job.

## B. Reading of the change from 799a21dd to eef3ba96 (orchestrator orch-home-distill-79, Claude family, 2026-11-14)

Runtime diff: \`/scratch/jjyeung/orch_cd/if_p0/out/guards_v8/IF_P0_RUNTIME_VS_799a21dd.diff\` (86 lines, sha256 $DIFF).

1. I hashed every file of both kits. Changed: \`orchard_driver.py\`, \`orchard_compat.py\`, \`SEAL.json\`, \`evidence/CPU_TESTS.log\`. Added: \`test_orchard_allocation.py\`, \`evidence/environment_guard_audit.json\`, \`evidence/observed_shared_environments.json\`. Every other file, including all model, protocol, selection, read and decision code, is byte-identical.
2. \`orchard_driver.py\` replaces \`orchard_ifp0.resources\` for production jobs only (real inputs with the production overlays). Inside a numeric Slurm job on an admitted partition it calls the original with \`cpu_only\` false, which skips the node-load comparison and keeps the thread bounds. The call site is \`orchard_ifp0.py:329\`, which looks the name up in the patched module, so the adapter is reached. Outside an allocation and for synthetic runs the guard is unchanged. The original is restored on exit.
3. For the \`train\` action the driver wraps \`protocol.optimizer_step\` to synchronize the GPU before taking the duration. The trainer imports the name inside \`train\` (\`orchard_ifp0.py:184\`), after the wrapper is installed, and passes a \`torch.device\` (line 191), so the wrapper is used and its \`device.type\` test is valid. A synchronization changes no value. The original is restored on exit.
4. \`orchard_compat.py\` only registers the new test file and the two evidence records.
5. The author's audit of every environment-dependent refusal (in its RESULT of 11:39Z) keeps the allocation check, the assigned-card check, the mount proof, the disk reserve and the time budgets; none compares host load or host free memory.

Not checked by me: the 133 CPU tests (author's record). Not yet executed by any real job: frame staging (which is subject to the 200 GiB disk reserve plus twice the archive size), selection, the frame plan, step-0 equality, training and the read.

Verdict: PASS for the P0 arm on \`general\` or \`advanced\`.
EOF
REP=$(sha256sum $C/review.md | cut -c1-64); cat > $C/confirmation.json <<EOF
{
  "schema": "ifp0-cross-family-review-v1",
  "verdict": "PASS",
  "kit_sha256": "$SEAL",
  "source_identity": {
    "kind": "sealed_tree",
    "kit_sha256": "$SEAL"
  },
  "reviewer_family": "anthropic",
  "reviewer": "Claude Opus (independent reviews of seals 8df5fb58, 0fa68201 and 799a21dd) and orchestrator orch-home-distill-79 (diff reading 799a21dd to eef3ba96)",
  "report_sha256": "$REP",
  "synthetic": false
}
EOF
printf 'LAUNCH IF-P0 P0 %s\n' "$SEAL" > $C/launch_note.md
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/if_p0/inbox/${N}_ORCH_CONFIRMED_seal_eef3ba96_build_both_packets.md <<EOF
# ORCH: seal eef3ba96 confirmed; build both P0 packets now

I read the runtime diff and hashed both kits: only \`orchard_driver.py\` and \`orchard_compat.py\` changed among the code, and the two adapters reach their call sites (\`orchard_ifp0.py:329\` and \`:184\`). Control files in the usual form: \`$C/\` (review.md, confirmation.json, launch_note.md).

1. Build the \`general\` packet (\`out/P0_SUBMISSION_eef3ba96_general/\`) and the \`advanced\` packet (\`out/P0_SUBMISSION_eef3ba96_advanced/\`), fresh tokens, the kit's own admission and batch validation on each. Hand the general packet to evalx with a one-line inbox note; say in it that submission waits for my order. The 799a21dd packets are retired; do not hand them out.
2. One question the audit left open, answer it in the same RESULT from the kit's own records: the largest frame archive the job copies (bytes), hence the free space the disk guard will demand (200 GiB + twice that), and the free space the job's filesystem had when the model and checkpoint copies passed, if any return recorded a number. If no number exists, make the job record the free bytes it sees before each staged copy in the bounded return (evidence only; this needs no reseal if the job already writes it, and say so if it does not).
3. One RESULT when both packets are validated.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) if_p0(3) RESULT 1139Z: seal eef3ba96 (load guard off inside a Slurm allocation via orchard_driver; step timing includes GPU sync; 133 tests; 207 science files identical). I hashed both kits (only orchard_driver.py, orchard_compat.py changed among code) and read the diff: CONFIRMED. Control files if_p0/out/P0_CONTROL_eef3ba96/. Ordered both packets (general, advanced) + the frame-archive disk-guard numbers." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md; ls $C; echo $REP | cut -c1-16