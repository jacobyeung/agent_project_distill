<!-- recovered by seal_plan: transcript=71f94277 line=3306 utc=2026-11-11T14:58:54.802Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > vla_nav/inbox/${T}_ANSWER_prompt_parity.md <<'EOF'
# ANSWER (orchestrator, prompt parity): use the student's native thinking template; one encoder for training and evaluation
Ruling: nav and click rows use the template the student and base Qwen3.5 were trained on, not enable_thinking=False.
- Prompt: apply_chat_template(..., add_generation_prompt=True) with the default thinking template, so it ends "<think>\n". No ANSWER_FORMAT_INSTRUCTION on nav or click rows.
- Target: sentence + "\n</think>\n\n" + answer (+ eos). One think block per sequence.
- Decoding: forced prefix sentence + "\n</think>\n\n", then the constrained greedy decode as now.
Reason: a second think block after an empty one is off-distribution for both arms, and the student writes its routed programs inside the native block; the arm comparison must not carry that confound.
Do:
1. Switch chat_prompt and think_block in navrun.encode (the one place), rerun your tests with the real tokenizer, and keep the prompt+suffix tokenisation check.
2. navrun.encode.encode_row is the single source for N1 and NU: any trainer that runs them imports it (a nav mode), and your kit has a test that the trainer-side ids equal the evaluator-side ids for the same row. If the trainer is the student trainer, write the exact nav-mode patch to batches.py as a file under out/ (do not edit another lane's tree).
3. Edit section 4.2 of /scratch/jjyeung/orch_cd/vla_design_review/VLA_SCHEMA.md (the three lines on row target, encoding and decoding) and the matching checks in schema_examples.py; keep .pre_template copies; run the examples script; add one line to SCHEMA_CHANGES.md. Section 6's provider prompts (single-image, enable_thinking=False) stay as they are.
4. Post one RESULT with the test counts. GPU hold still stands: after your render ends, start nothing on a GPU.
EOF
cat > vla_heads/inbox/${T}_NOTE_schema_4_2_template.md <<'EOF'
# NOTE (orchestrator): schema 4.2 changes for nav and click rows
Nav and click rows now use the default thinking template (prompt ends "<think>\n"; target = sentence + "\n</think>\n\n" + answer; no ANSWER_FORMAT_INSTRUCTION). vla_nav's navrun.encode.encode_row is the single encoder for N1 and NU; a token trainer for those arms imports it. Read section 4.2 of VLA_SCHEMA.md and SCHEMA_CHANGES.md before the next build on token arms.
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) vla_nav QUESTION trainer_prompt_parity: ruled native thinking template (prompt ends <think>\\n, one think block, no ANSWER_FORMAT_INSTRUCTION for nav/click), navrun.encode.encode_row single source for train+eval; vla_nav edits schema 4.2 + examples; note left in vla_heads/inbox." >> ORCH_HANDOFF.md
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | head -4; cat vla_nav/STATUS.md | head -12