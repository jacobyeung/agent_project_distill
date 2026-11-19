R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ
sed -n 1,30p sb_ktfix2/code/runner.py | cut -c1-250
echo ====; sed -n 1,30p sb_cachk/kit_v2/launch_gpu.sh | cut -c1-200
echo ====; grep -n -E "add_argument|CUDA_VISIBLE" sb_ph2fix/sb_mask_phrase/part2/launch_gpu.py | head -10 | cut -c1-200
cat sb_stage228/*.done 2>/dev/null; cat sb_stage228/union.tar.err | head -3
timeout 40 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'df -h /scratch | tail -1; du -sh /scratch/jjyeung 2>/dev/null'
