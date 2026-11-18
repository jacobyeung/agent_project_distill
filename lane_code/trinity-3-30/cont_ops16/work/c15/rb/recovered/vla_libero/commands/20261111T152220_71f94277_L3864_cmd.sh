<!-- recovered by seal_plan: transcript=71f94277 line=3864 utc=2026-11-11T15:22:20.687Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > vla_libero/inbox/${T}_ORCH_integration_breaks.md <<'EOF'
# ORCH: the cross-lane integration test found five breaks, all in your heads hook; apply the patches
Codex lane vla_integ ran the four VLA packages in one process (/scratch/jjyeung/orch_cd/vla_integ/out/BREAKS.md, INTEG.md; patches out/01..09; tests work/integration.py; rerun with work/run_integ.sh). Every break is your hook departing from the schema:
1. vl_heads_hook.py:200 never applies the where-dropout (schema 5.5): a whole U1 run would train without it. Patches 05-07.
2. vl_heads_hook.py:65 hardcodes the regression head and ignores the canonical vla config: an arm would run under the wrong label. Patch 01 (reads the config, refuses a wrong schema tag and an unsupported flow head).
3. vl_heads_hook.py:96 zeros any proprio span <= 1e-6; the heads zero only exactly constant spans (schema 7). Patch 03.
4. vl_heads_hook.py:120 casts proprio to bf16; the interface requires fp32. Patch 02.
5. vl_data_patch.py:28 emits a [K,7] bool action mask; the schema's mask is [B,K]. Patches 04, 08, 09.
Do:
- Read each patch, apply it to your kit (Trinity copy and the Orchard copy), rerun your own tests, then rerun /scratch/jjyeung/orch_cd/vla_integ/work/run_integ.sh against your live folder and report its table.
- Patches 05-07 need raw where_output and a stable episode_id and t from the caller: wire your production dataset and cache to that helper (the test used a fixture) and add a test that the dropout rate observed over 1,000 rows matches the schema's.
- The flow-matching expert has no native path through your hook: either add it (the heads package dispatches it in config.py:177 and flow.py:106) or keep the fail-fast guard and say so in the pre-launch card. Default: add it, since the user asked for a diffusion-style head to be ready.
- No GPU job and no Orchard submission; CPU only. One RESULT with the test counts.
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) vla_integ (Codex Astra) RESULT 1521Z: six arms run in one process on CPU (17 s); five break classes, all in vla_libero's heads hook (where-dropout never applied, hook hardcodes the regression head and ignores the vla config, proprio span threshold, proprio cast to bf16, action-mask shape), nine patches under vla_integ/out; nav grammar, mirrored geometry, occlusion masks and train/eval tokenizer prefixes pass. Patches handed to vla_libero (inbox). trace_save BLOCKER 1520Z: its governed read of 14 Claude transcripts (160 MB) still queued in the governor; no action (it waits, no retry)." >> ORCH_HANDOFF.md
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; sed -i '/^vla_integ|/d' $S/LANES