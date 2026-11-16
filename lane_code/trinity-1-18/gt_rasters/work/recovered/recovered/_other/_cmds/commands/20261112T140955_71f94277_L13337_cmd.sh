<!-- recovered by seal_plan: transcript=71f94277 line=13337 utc=2026-11-12T14:09:55.695Z kind=commands original_path=(bash command)  -->
mkdir -p /scratch/jjyeung/orch_cd/arch_jobs && cd /scratch/jjyeung/orch_cd/arch_jobs && SRC=/scratch/jjyeung/orch_cd/leg_s1_tree/work/kit_s1_frozen_no_flag_complete/k/t_38917ea542d7becf.tar && SHA=$(sha256sum $SRC | cut -d' ' -f1) && SZ=$(stat -c %s $SRC) && echo "$SHA $SZ" && JOB=$(/scratch/jjyeung/envs/p1cpu/bin/python -I -s -c "
import json,base64,sys
j=dict(id='distill_legs1_src_38917ea5', transport='archive', expected_bytes=int(sys.argv[2]), tier=3, priority=60,
       source=dict(host='trinity-2-18', archive=sys.argv[1], sha256=sys.argv[3]),
       destination=dict(host='trinity-2-18', path='/data3/jjyeung/distill_src_archive/t_38917ea542d7becf.tar'))
print(base64.b64encode(json.dumps(j).encode()).decode())" $SRC $SZ $SHA) && setsid /scratch/jjyeung/envs/p1cpu/bin/python -s /scratch/jjyeung/io_governor/copy_archive.py --job "$JOB" --receipt /scratch/jjyeung/orch_cd/arch_jobs/distill_legs1_src_38917ea5.receipt.json