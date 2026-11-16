source /scratch/jjyeung/geo_bakeoff_kit/work/kit_env.sh; set +e
mkdir -p /scratch/jjyeung/orch_n30/geo_k1/tmp/kitout2/tmp
export GEO_BAKEOFF_OUTPUT_ROOT=/scratch/jjyeung/orch_n30/geo_k1/tmp/kitout2 TMPDIR=/scratch/jjyeung/orch_n30/geo_k1/tmp/kitout2/tmp XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/cache HF_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/hf TORCH_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/torch CUDA_VISIBLE_DEVICES=
cd /scratch/jjyeung/orch_n30/geo_k1/tmp
/scratch/jjyeung/geo_bakeoff_kit/runtime/base/bin/python3 -m pytest -q -p no:cacheprovider --basetemp=/scratch/jjyeung/orch_n30/geo_k1/tmp/kitout2/pytest /scratch/jjyeung/geo_bakeoff_kit/work/tests /scratch/jjyeung/geo_bakeoff_kit/work/geo_bakeoff > /scratch/jjyeung/orch_n30/geo_k1/logs/kit_tests2.log 2>&1
echo EXIT $? >> /scratch/jjyeung/orch_n30/geo_k1/logs/kit_tests2.log
