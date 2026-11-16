set -u
cd /scratch/jjyeung/geo_bakeoff_kit || exit 1
du -sh data/fixture data/frame_contract 2>/dev/null; ls data/fixture/* | head; 
T=/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872
M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
C=/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py
d=$(ls -d /scratch/jjyeung/k1/run_tower_sam_2/*/ | head -1)
du -sh $T /scratch/jjyeung/k1_frames 2>/dev/null
tar cf - --exclude='*.pyc' PAYLOAD.json KIT_SEAL.json work launch out/CANDIDATES.md out/RUNCARD.md out/REVIEW_PACKET.md out/receipts -C / ${T#/}/student_pilot ${T#/}/trace_format ${T#/}/rk ${M#/} ${C#/} ${d#/}tower.npz ${d#/}PHASE_COMPLETE.json | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "mkdir -p /scratch/jjyeung/orch_n30/b14_k1towers/work/ref && cd /scratch/jjyeung/orch_n30/b14_k1towers/work/ref && tar xf -" && echo SENT
