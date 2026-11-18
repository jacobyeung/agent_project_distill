<!-- recovered by seal_plan: transcript=71f94277 line=4475 utc=2026-11-11T16:05:35.704Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; sed -n 1,9p gt_ceiling/STATUS.md | cut -c1-900; python3 - <<'EOF'
p='/scratch/jjyeung/orch_cd/READY_QUEUE.md'
s=open(p).read()
s+='''- GRD-1 (denser SAM 3 re-cache) DEMOTED to the end of the Trinity list (grd_selector RESULT 1605Z): the kit is ready (1.7-2.3 GPU-h, card out/RUN_CARD_DENSE.md), but a CPU sensitivity run predicts no routing decision changes: proposal recall moves abs and size by about 0.2 points per recall point with GT geometry and about 0 with tower geometry; with tower geometry even GT masks with the depth cut stay below direct (abs 38.5 vs 57.3, size 52.3 vs 68.1); counting is bound by accepts and identity (oracle accepts 62.2, accepts plus identity 75.9, direct 71.1). Geometry (GEO-1, gt_ceiling task 5) and counting identity rank above it.
'''
open(p,'w').write(s)
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) grd_selector RESULT 1605Z: dense SAM 3 re-cache kit ready (work/dense, out/RUN_CARD_DENSE.md, guards, 1.7-2.3 GPU-h, CPU chain reproduces price2_vsi exactly) and out/RUN_CARD_PRES32_V3.md; CPU sensitivity predicts NO routing flip from denser proposals (0.2 pt per recall point on abs/size with GT geometry, ~0 with tower; GT masks + cut on tower geometry abs 38.5 / size 52.3 vs direct 57.3 / 68.1; counting oracle accepts 62.2, accepts+identity 75.9 vs direct 71.1). GRD-1 demoted in READY_QUEUE.md; geometry and counting identity rank above." >> ORCH_HANDOFF.md