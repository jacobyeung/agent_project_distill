cd /
SLURM_JOB_ID=dry0 PYTHONPATH=/scratch/opt_t/q.zip timeout 1200 nice -n 19 /scratch/jjyeung/envs/p1cpu/bin/python -s -B -m launch_r1.p_handover_receipt --run-pins /scratch/opt_t/RP.json --artifact /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/673bc60f/m200/artifact.json --output /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/673bc60f/m200/h.json --trainer-commit sha256:b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b
echo rc=$?
