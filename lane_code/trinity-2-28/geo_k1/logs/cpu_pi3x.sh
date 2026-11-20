source /scratch/jjyeung/geo_bakeoff_kit/work/kit_env.sh; set +e
export TMPDIR=/scratch/jjyeung/orch_n30/geo_k1/tmp XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/cache HF_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/hf TORCH_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/torch CUDA_VISIBLE_DEVICES=
cd /scratch/jjyeung/orch_n30/geo_k1/tmp
/usr/bin/time -v /scratch/jjyeung/geo_bakeoff_kit/runtime/base/bin/python3 /scratch/jjyeung/orch_n30/geo_k1/k1towers/k1_infer.py --model pi3x --manifest /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json --towers /scratch/jjyeung/k1/run_tower_sam_2 --out /scratch/jjyeung/orch_n30/geo_k1/pred_cpu/pi3x --device cpu --threads 8 --captures scannet/scene0201_02 > /scratch/jjyeung/orch_n30/geo_k1/logs/cpu_pi3x.log 2>&1
echo EXIT $? >> /scratch/jjyeung/orch_n30/geo_k1/logs/cpu_pi3x.log
