<!-- recovered by seal_plan: transcript=71f94277 line=2761 utc=2026-11-11T14:27:46.027Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd && NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ) && T=$(date -u +%Y%m%dT%H%MZ) && m=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory
cat >> $m/gemini-key-main-priority.md <<'EOF'

**Argon and Carbon are distillation's to use (USER 2026-11-11 ~06:30 PT):** "My understanding is that the main agent doesn't really need carbon and argon, so you should be able to use those more." Distillation may raise its use of the Argon and Carbon buckets (labelling, frame-level perception for trace conversion, frontier reads), backing off only on 429s; Gemini 3.1 Pro stays main's.
EOF
cat > label_247/inbox/${T}_ORCH_more_key.md <<EOF
# ORCH ($NOW): you may use more of the Gemini key
- The user: "the main agent doesn't really need carbon and argon, so you should be able to use those more." Raise your concurrency caps (Argon 32 -> 48, Carbon 48 -> 64) with your existing ramp rule (+4 per 15 minutes while 429s stay under 1%), and back off at once on 429s. Two other distillation lanes use the same buckets at 16 to 32 calls each. Gemini 3.1 Pro stays untouched.
EOF
cat > frontier_read/inbox/${T}_ORCH_more_key.md <<EOF
# ORCH ($NOW): you may use more of the Gemini key
- The user: "the main agent doesn't really need carbon and argon, so you should be able to use those more." You may ramp to 32 concurrent calls per model while 429s stay under 1%, backing off at once otherwise. Only the Argon and Carbon buckets.
EOF
cat > dose_pool/inbox/${T}_ORCH_more_key.md <<EOF
# ORCH ($NOW): the Gemini-route pilot may start as soon as its plan is in your RESULT
- The user: "the main agent doesn't really need carbon and argon, so you should be able to use those more." So the key is not a constraint: once your scoping RESULT with the route-B pilot plan is posted, start the pilot yourself at 16 concurrent calls per model (ramp to 32 while 429s stay under 1%), and post its RESULT. Everything else in my earlier notes stands: perception only from the models, the program computes, the keep rule, zero invented references, sample rows quoted in the RESULT so I can read them.
EOF
echo "$NOW orch-home-distill-79: USER ~14:30Z: main does not need Argon and Carbon, distillation may use them more (memory gemini-key-main-priority updated). label_247 caps raised to Argon 48 / Carbon 64 with its ramp rule; frontier_read may ramp to 32; dose_pool's route-B pilot may start once its plan is posted (16 per model)." >> ORCH_HANDOFF.md