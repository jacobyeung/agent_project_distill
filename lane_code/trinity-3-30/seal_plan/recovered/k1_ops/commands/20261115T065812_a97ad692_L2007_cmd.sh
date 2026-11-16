<!-- recovered by seal_plan: transcript=a97ad692 line=2007 utc=2026-11-15T06:58:12.658Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/a97ad692-7041-4f72-8b75-8f8e29df8950/scratchpad; T=$(date -u +%Y%m%dT%H%MZ); cat > $R/k1_ops/inbox/${T}_ORCH_RULING_buffer_on_218_then_infiniband.md <<'EOF'
# ORCH RULING on your 0656Z question: option (c), with a bounded buffer on trinity-2-18

Not (a): the governor's owner has answered nothing tonight, and K1 should not wait on a configuration change of its tool. Not (b): a queued stream would hold an ssh session open and idle for as long as the governor makes it wait.

Do (c), bounded:
1. **Buffer root** `/scratch/jjyeung/k1_buf` on trinity-2-18, at most 7 GB in total. I am relaxing my own staging floor for this buffer only: this node has about 135 GB free and must stay above 125 GB; check free space before each stream and stop if it would fall below.
2. **T2**: register the read of the 138 mp4s from /data2 on trinity-2-18 with the governor (honest expected bytes 2,897,231,394; one stream; the governor sets the rate) into the buffer. It waits its turn; no ssh is open while it waits. Verify sizes with your `verify_mp4.py` on the buffer.
3. **T3**: run the rate-capped fetch on trinity-2-18, registered with the governor likewise, writing into the buffer. Run the d3 byte-parity gate on what it wrote before pushing anything; if parity fails, stop and report (the Orchard-archive fallback needs the Orchard owner and my order).
4. **Push** each finished buffer part to trinity-1-18 over InfiniBand as one tar pipe inside one limiter call (under 120 s each: 2.9 GB at InfiniBand speed is seconds; split by part if needed), then verify hashes on 1-18. Node-to-node InfiniBand copies do not pass the governor.
5. Build the remaining frames on trinity-1-18 from the pushed mp4s as your packet says, then the parity gate, B4, and the RESULT event with two card readings.
6. Leave the buffer in place after the push (no agent deletes); write its path, size and the sha256-verified destination into `out/REMOVAL_CANDIDATES_K1_BUFFER.md` for the user.
If a registered stream is not admitted within 45 minutes, send one QUESTION event with the governor's view and keep it queued. T4 and T5 as you are doing.
EOF
grep -v '^next_queue|' "$S/LANES" > "$S/LANES.new"; cp "$S/LANES.new" "$S/LANES"; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import re
p='$S/lanewatch.sh'; s=open(p).read(); s=re.sub(r'\n  \[next_queue\]=\"[^\"]*\"','',s); open(p,'w').write(s)"; cp "$S/LANES" "$S/lanewatch.sh" $R/orch_tools/session_scripts_20261115/
echo "- $(date -u +%Y-%m-%dT%H:%MZ) k1_ops QUESTION 0656Z: the governor refuses to register streams on trinity-1-18 (not in allowed_hosts; meter does not sample it). Ruled (c): bounded buffer /scratch/jjyeung/k1_buf on 2-18 (<= 7 GB; node stays above 125 GB free), T2 and T3 registered on 2-18, parity gate before any push, InfiniBand tar push to 1-18 inside limiter calls, buffer listed for the user's removal. next_queue finished its inbox watch and ended; removed from LANES." >> $R/ORCH_HANDOFF.md