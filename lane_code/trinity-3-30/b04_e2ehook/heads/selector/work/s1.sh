hostname -s; date -u
mkdir -p /scratch/jjyeung/orch_n30/b04_e2ehook_sl
O=/scratch/jjyeung/orch_cd
T=$O/leg_s1_tree/work/tree_s1_admissionfix_168872
du -sh $T/student_pilot $O/grd_selector/work/setsel 2>&1
ls $O/grd_selector/work/setsel $O/devs1_masks/out/kit/work/vendor
ls /scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing | head -30
ls $O/k1_build/work/kit_k1a/work/refit; ls /scratch/jjyeung/k1/run_tower_sam_2 | head -3; ls /scratch/jjyeung/k1/run_tower_sam_2 | wc -l
ls /scratch/jjyeung/orch_n30/ ; pgrep -u jjyeung -fa python | cut -c1-200 | head; uptime; nproc; free -g | head -2; df -h /scratch | tail -1
cd / && tar cf - --exclude='*.pyc' scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot scratch/jjyeung/orch_cd/grd_selector/work/setsel/build.py scratch/jjyeung/orch_cd/grd_selector/work/setsel/fit.py scratch/jjyeung/orch_cd/grd_selector/work/setsel/fit_pairs.py scratch/jjyeung/orch_cd/grd_selector/work/setsel/setlib.py scratch/jjyeung/orch_cd/devs1_masks/out/kit/work/vendor/MODELS.json scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets/GT_SET_PRIMARY_296.json scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/work/gt_set.py scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/work/gate.py scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/native_kit/bindings.py scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/work/refit 2>/dev/null | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "cd /scratch/jjyeung/orch_n30/b04_e2ehook/heads/selector/src118 && tar xf -"; echo tar_rc=$?
