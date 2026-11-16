G=/scratch/jjyeung/orch_n30/geo_k1; K=/scratch/jjyeung/geo_bakeoff_kit; cd $G; date -u
cat pred_cpu/pi3x/*/FAILED_*.json | cut -c1-1500; echo
grep -n "Error\|Traceback" logs/cpu_pi3x.log | tail -8
cat > logs/kit2.sh <<EOS
source $K/work/kit_env.sh; set +e
mkdir -p $G/tmp/kitout2/tmp
export GEO_BAKEOFF_OUTPUT_ROOT=$G/tmp/kitout2 TMPDIR=$G/tmp/kitout2/tmp XDG_CACHE_HOME=$G/tmp/cache HF_HOME=$G/tmp/hf TORCH_HOME=$G/tmp/torch CUDA_VISIBLE_DEVICES=
cd $G/tmp
$K/runtime/base/bin/python3 -m pytest -q -p no:cacheprovider --basetemp=$G/tmp/kitout2/pytest $K/work/tests $K/work/geo_bakeoff > $G/logs/kit_tests2.log 2>&1
echo EXIT \$? >> $G/logs/kit_tests2.log
EOS
tmux new-window -t b14 -n kit2 "bash $G/logs/kit2.sh"
