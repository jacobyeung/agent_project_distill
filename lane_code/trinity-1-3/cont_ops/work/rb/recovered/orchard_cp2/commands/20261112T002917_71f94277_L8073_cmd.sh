<!-- recovered by seal_plan: transcript=71f94277 line=8073 utc=2026-11-12T00:29:17.575Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; python3 - <<'EOF'
p='ORCH_STATE_20261111T0935Z.md'
L=open(p).read().split('\n')
i=52
assert L[i].startswith('- HARD DEADLINE on Orchard')
L[i]=("- Orchard (2026-11-12T00:35Z): LEG-S1's first launch is WORLD 4 on partition `advanced` (4 GPUs per user, shared cap with main; start estimate immediate; legs of at most 24 h chained by exact resume; admission folded into the job's first phase). A fresh 8-GPU preempt job waits about 7 days; `scontrol top` is off; changing pending job 168042's files for LEG-S1 is not safe. 168042 (CP1-Rv on v3.13, estimate 2026-11-13T04:19Z) and 168043 stay pending and untouched. HARD DEADLINE: 168042's kit authorization expires 2026-11-14T20:50:43Z; the in-place date extension (route C, orchard_cp2 work/legs1_swap; review swap_review/REVIEW_VERDICT_ROUTE_C.md = SAFE AFTER FIXES; fixes done, re-check owed) runs only on my written confirm `*_ORCH_CONFIRM_route_c.md`. Launch gate for LEG-S1: frozen tree + cross-family review + inputs on Orchard (first tar 162 MB; MDG inputs 14.3 GB from 2-18 mdg_build/work, list mdg_assets_inv/MDG_ASSET_SOURCES.md) + pre-launch card to the user + my `*_ORCH_GO_legs1_launch.md`. Main approved Orchard use (nothing of its own running there); asked about the shared 4-GPU advanced cap in its notices log (line 48). orchard_cp2 runs under ACP: its brief must say never end the turn.")
open(p,'w').write('\n'.join(L))
EOF
grep -c "" ORCH_STATE_20261111T0935Z.md