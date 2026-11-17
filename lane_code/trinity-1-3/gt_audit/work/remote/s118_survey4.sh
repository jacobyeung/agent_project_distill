set -u
cd /scratch/jjyeung || exit 1
H=orch_n30/e3_geom/work/harness
echo "== MANIFEST const"; grep -n -E "^(MANIFEST|TOWERS|OUT|GD|ROOT)[A-Z_]* *=" $H/harness.py | cut -c1-250
echo "== e3gd out"; ls -la orch_n30/k1_ops3/work/e3gd/out 2>&1 | head -30
echo "== k1_split"; ls -la orch_n30/k1_ops3/work/k1_split 2>&1 | head
echo "== sens"; ls -la orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/ 2>&1; du -sh orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/render
echo "== kit work refit tables"; ls -la orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/refit | head
echo "== b14"; ls -la orch_n30/b14_k1towers 2>&1 | head -30; ls -la orch_n30/b14_k1towers/k1towers 2>&1 | head -40; ls -d orch_n30/b14_k1towers/*/ 2>/dev/null
for d in orch_n30/b14_k1towers/k1towers/out orch_n30/b14_k1towers/out orch_n30/b14_k1towers/work; do [ -d $d ] && { echo "-- $d"; ls -la $d | head -40; }; done
echo "== b04/e2e K1 lifting outputs?"; ls -d orch_n30/b04_e2ehook* orch_n30/b04* 2>/dev/null
echo "== k1 root"; ls -la /scratch/jjyeung/k1 2>&1 | head -30
echo "== sizes"; du -sh orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json $H/out/PER_ITEM.jsonl $H/out_devs1 $H/out_ho $H/out_tr 2>&1
