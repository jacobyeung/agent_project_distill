<!-- recovered by seal_plan: transcript=71f94277 line=34808 utc=2026-11-15T02:49:26.092Z kind=commands original_path=(bash command)  -->
D=/data2/jjyeung/agent_project_data/distill_design; cat >> $D/INFUSION_VISION_CAPACITY_20261113.md <<'EOF'

## Result (2026-11-15): IF8 does not pass the registered gate

Kit seal eef3ba96, Orchard, one H100 per arm, 300 updates over 9,600 rows, read on 52 held-out clips (1,552 frame pairs; 37 physical scenes). P0 (branches frozen at zero; job 169530): primary direction error 18.1069 degrees, 90% clip-bootstrap interval [16.77, 19.62]; 35.6 s per step; peak 24.7 GiB. IF8 (branches trained in language-model layers 1 to 8; job 169652): 15.5006 degrees, interval [14.32, 16.68]; about 50 s per step; peak 31.9 GiB. Improvement 2.6062 degrees, registered paired physical-scene interval [1.66, 3.80] (paired clip bootstrap [1.76, 3.50]). The registered pass needed 5 degrees (13.107 or lower); the result is also below the 3-to-7-degree band that called for the frozen-branch comparator. AT8 was not run. What it rules out: a pass for this eight-layer implementation at 300 updates on this read. What it does not: vision-only capacity more broadly (new cross-token parameters sit only in layers 4 and 8; the other six augmented layers add tokenwise feed-forward branches; one seed; one probe). Close-out file: /scratch/jjyeung/orch_cd/if_p0/out/IF_P0_FINAL_20261115.md. Earlier jobs 169413, 169474, 169491 failed in staging, the runtime check and a CPU load guard; canary 169512 was cancelled at step 24 for a slot. Status: closed; no extension ordered.
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
M='/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory'
i=M+'/MEMORY.md'; t=open(i).read()
import re
line=[l for l in t.split('\n') if 'unbundling-infusion-vision-capacity-20261113.md' in l]
assert len(line)==1, line
new="- **Result 11-15 (USER link 11-13):** [Unbundling: vision capacity inside the LM](unbundling-infusion-vision-capacity-20261113.md) IF-P0 ran: branches in LM layers 1-8 cut pose error 18.1 -> 15.5 deg (+2.6 [1.7, 3.8]); gate was 5; no pass, closed"
t=t.replace(line[0],new,1); open(i,'w').write(t); print(len(line[0]),len(new),len(t.encode()))
p=M+'/unbundling-infusion-vision-capacity-20261113.md'; s=open(p).read()
s=s.rstrip('\n')+"\n\n**Result (2026-11-15).** IF-P0 ran on Orchard at kit seal eef3ba96 (300 updates, 52 held-out clips). P0 (branches frozen at zero) reads 18.107 degrees of pose direction error (90% interval 16.77 to 19.62); IF8 (vision-only branches trained in LM layers 1 to 8) reads 15.501 (14.32 to 16.68). Improvement 2.61 degrees, paired interval [1.66, 3.80]: real but below the registered 5-degree pass mark and below the 3-to-7 marginal band, so AT8 was not run and the experiment is closed. It does not rule out the idea more broadly: new cross-token parameters sat only in layers 4 and 8, 300 updates, one seed, one probe. Record: distill_design/INFUSION_VISION_CAPACITY_20261113.md (Result section); close-out /scratch/jjyeung/orch_cd/if_p0/out/IF_P0_FINAL_20261115.md. Cost lesson: three P0 jobs failed before training on staging and environment guards before one ran.\n"
open(p,'w').write(s)
EOF