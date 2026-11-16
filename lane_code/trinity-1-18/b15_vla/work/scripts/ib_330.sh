set -o pipefail
cd /scratch/jjyeung && tar cf - envs/nav_habitat024 | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "cd /scratch/jjyeung && tar xf -"; echo "env rc=$?"
cd /scratch/jjyeung/orch_cd/nav_survey && tar cf - refs | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "cd /scratch/jjyeung/orch_n30/b15_vla/navrun_inputs && tar xf -"; echo "refs rc=$?"
cd /scratch/jjyeung/orch_cd/nav_survey/refs && find . -type f -exec sha256sum {} + | sort -k2
