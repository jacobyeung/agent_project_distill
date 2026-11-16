cd /scratch/jjyeung/orch_n30/geo_k1/tmp
python3 /scratch/jjyeung/orch_n30/geo_k1/k1towers/kitcheck.py /scratch/jjyeung/geo_bakeoff_kit /scratch/jjyeung/orch_n30/geo_k1/out/kit_check.json > /scratch/jjyeung/orch_n30/geo_k1/logs/kitcheck.log 2>&1
source /scratch/jjyeung/geo_bakeoff_kit/work/kit_env.sh; set +e
export TMPDIR=/scratch/jjyeung/orch_n30/geo_k1/tmp XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/cache HF_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/hf TORCH_HOME=/scratch/jjyeung/orch_n30/geo_k1/tmp/torch GEO_BAKEOFF_OUTPUT_ROOT=/scratch/jjyeung/orch_n30/geo_k1/tmp/kitout CUDA_VISIBLE_DEVICES=
mkdir -p /scratch/jjyeung/orch_n30/geo_k1/tmp/kitout
/scratch/jjyeung/geo_bakeoff_kit/runtime/base/bin/python3 -m pytest -q -p no:cacheprovider /scratch/jjyeung/geo_bakeoff_kit/work/tests /scratch/jjyeung/geo_bakeoff_kit/work/geo_bakeoff > /scratch/jjyeung/orch_n30/geo_k1/logs/kit_tests.log 2>&1
echo EXIT $? >> /scratch/jjyeung/orch_n30/geo_k1/logs/kit_tests.log
