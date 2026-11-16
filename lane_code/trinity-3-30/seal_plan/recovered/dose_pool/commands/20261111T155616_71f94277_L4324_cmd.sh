<!-- recovered by seal_plan: transcript=71f94277 line=4324 utc=2026-11-11T15:56:16.655Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; mkdir -p render_gaps/events render_gaps/work render_gaps/out; T=$(date -u +%Y%m%dT%H%MZ)
cat > render_gaps/BRIEF.md <<'EOF'
# render_gaps (Codex Astra): add the missing question types to the v3.14 scene renderer, with validators and rows for a human to read
Host trinity-2-18. Your folder: /scratch/jjyeung/orch_cd/render_gaps (write only here). Everything else is read-only: copy what you change into work/.

## Why
The student learns to answer spatial questions by writing a short program that calls its own heads (ground, angle, gap, count) and copies the printed values into its answer; training rows show that form with ground-truth values in the tool responses ("head-backed traces"). Lane dose_pool renders such rows from scenes for a pool of 233,799 questions, but its scene renderer knows only four types (absolute distance, relative distance, direction medium, direction hard). Its spec of what is missing: /scratch/jjyeung/orch_cd/dose_pool/out/RENDERER_GAPS.md and events/20261111T1544Z_RESULT_renderer_gaps.md. The user (2026-11-11): "we should preemptively develop all this code and test it!" and "it's often a very wise choice to actually read the traces".

## Inputs (read-only)
- The fixed v3.14 generator and runtime from lane integ_v314 pass 2: /scratch/jjyeung/orch_cd/integ_v314/work/gen_r2, work/tree_v314_r2, out/GEN_V314_R2.patch, out/INTEG_V314_R2.patch, out/RECORD.md, events/20261111T1554Z_RESULT_integ_v314_pass2.md. Its round trip already covers 12 program types through the production trace generator; find out which of the missing types that generator can already write and reuse its forms exactly (the runtime must parse what you render, byte for byte).
- The scene renderer dose_pool uses: its driver /scratch/jjyeung/orch_cd/dose_pool/work/v314/dose_t0.py and the trees copied under dose_pool/work/v314 (ground_rows' render_full.render_scan); the validator it runs (exact replay, benchmark template, shuffle, label equality, dev exclusion, token and gate positions, pack round trip).
- Reference programs and label rules: /scratch/jjyeung/orch_cd/gt_ceiling/work/tp/prog_v2.py; rows already rendered and read: /scratch/jjyeung/orch_cd/dose_pool/out/ROWS_READ_T0.md.
- Scenes with ground truth on this node: those dose_pool's T0 run used (its STATUS.md names the roots).

## Build, in this order
1. Direction easy (34,411 pool questions): the benchmark's easy template and the medium angle call without the back branch.
2. Counting (8,816): `<ground mode="instances">` with ground-truth identity, every counted instance visible in the sampled frames, the count copied from the printed instance list; rows whose label counts instances not visible in the frames are refused, and the refusal is counted.
3. Relative count (4,199): two counting traces and one comparison line.
4. Absolute direction (23,436; a VSI-590K-only type): the angle call plus one rotation-sense calculator line.
For each: the renderer, the validator checks the four existing types have, a unit test, parity with prog_v2's answer on the same inputs (state n and the mismatch count), the answer and option histograms against the benchmark's for that type, and the refusal table.
Wording rule for every sentence the model is trained to write: state the rule or the computation; never mention a benchmark, a dataset, a label or a release. (The existing distance sentence ends "which is how this benchmark defines the answer"; remove that clause in your copy too.)

## Deliver
- out/RENDER_GAPS.patch against integ_v314's gen_r2 state (and say which files of dose_pool's copied trees it replaces), with tests.
- out/ROWS_READ_GAPS.md: 8 rendered rows per new type from at least 5 scenes, in the layout of ROWS_READ_T0.md (question, options, answer, ground truth, the full trace), chosen by a fixed seed, not cherry-picked; plus 3 refused examples per type with the reason.
- out/COUNTS.md: per type, questions tried, admitted, refused by reason, on the scenes you rendered.
- events/<UTC stamp from date -u +%Y%m%dT%H%MZ>_RESULT_render_gaps.md and a final message, each at most 15 lines.

## Limits
CPU only; no GPU, no ssh, no git commands, no network, no deletion commands of any kind (a hook blocks them). Run under `ulimit -f 204800`; folder under 2 GB; temporary files under work/tmp, not /tmp; at most 8 CPU threads. /home and /data* are overloaded network storage: do not read or write them. You cannot ask questions: decide, and write the choice down.
EOF
tmux new -d -s cx_render_gaps "bash /scratch/jjyeung/orch_cd/orch_tools/codex_local.sh implement /scratch/jjyeung/orch_cd/render_gaps /scratch/jjyeung/orch_cd/render_gaps/BRIEF.md --model gpt-6-astra --effort high --skip-git-check --label render_gaps > /scratch/jjyeung/orch_cd/render_gaps/dispatch.out 2>&1"
cat > leg_s1_tree/inbox/${T}_ORCH_v314_pass2_landed.md <<'EOF'
# ORCH: integ_v314 pass 2 has landed; rebase on it now
/scratch/jjyeung/orch_cd/integ_v314/events/20261111T1554Z_RESULT_integ_v314_pass2.md: runtime work/tree_v314_r2, generator work/gen_r2, patches out/INTEG_V314_R2.patch and out/GEN_V314_R2.patch. It binds the program version through preparation, training, checkpoint, export and loaders (so reconcile it with the rehearsal patch's version field: keep ONE mechanism), sets min_mask_px=154 scaled by mask area, adopts the largest-mask camera rule (priced: tie on 2,345 items), and its round trip covers 12 program types with 575 rows. Codex lane render_gaps is adding direction easy, counting, relative count and absolute direction to the scene renderer (patch will be /scratch/jjyeung/orch_cd/render_gaps/out/RENDER_GAPS.patch); merge it when its RESULT lands.
EOF
cat > dose_pool/inbox/${T}_ORCH_v314_pass2_landed.md <<'EOF'
# ORCH: integ_v314 pass 2 has landed: rerender with its generator, with the wording fix
/scratch/jjyeung/orch_cd/integ_v314/events/20261111T1554Z_RESULT_integ_v314_pass2.md: generator work/gen_r2 (patch out/GEN_V314_R2.patch), runtime work/tree_v314_r2. It changes what a valid instance is (min_mask_px=154 scaled by mask area) and binds the program version into rows, so T0 must be rerendered with it for training and inference to agree. Do: copy gen_r2, apply the wording fix from my 1537Z note, rerender T0, then render ARKit and T1 with the same state; report rows per type against the first T0 run and encode 12 rows through tree_v314_r2's routing encoder (the 7 distance rows that tree 31b57cf refused must now pass). The missing types (direction easy, counting, relative count, absolute direction) come from Codex lane render_gaps (/scratch/jjyeung/orch_cd/render_gaps/out/RENDER_GAPS.patch when its RESULT lands): add them then, as a second, additive render.
EOF
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; sed -i '/^integ_v314|/d' $S/LANES; printf 'render_gaps|tmux:cx_render_gaps||\n' >> $S/LANES
echo "$(date -u +%Y-%m-%dT%H:%MZ) integ_v314 pass 2 (Codex Astra) RESULT 1554Z: all rulings in (version bound through prepare/train/checkpoint/export/loaders with typed refusals; min_mask_px=154 scaled; exact odd-frame depth on the production class; camera rule priced on 2,345 items: tie, largest mask adopted; round trip 575 rows, 12 types nonzero incl. 25 camera-gap rows; perception-defect round trip; unmocked verifier + real tokenizer; 6/6 CPU acceptance, 64/64 continuations byte-equal). GPU canary unrun. leg_s1_tree told to rebase; dose_pool told to rerender T0/ARKit/T1 with gen_r2 + wording fix; render_gaps (Codex Astra, tmux cx_render_gaps) adds direction easy, counting, relative count, absolute direction to the scene renderer with ROWS_READ_GAPS.md for me to read." >> ORCH_HANDOFF.md; sleep 2; tmux ls | grep cx_ | cut -c1-28