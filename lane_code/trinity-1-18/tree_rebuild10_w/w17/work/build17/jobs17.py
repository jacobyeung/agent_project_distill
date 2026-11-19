from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build17';T=L/'work/tree_r1';O=B/'proofs/operator';O.mkdir(parents=True,exist_ok=True)
p=T/'launch_r1/build.py';s=p.read_text()
start=s.index("    (output/'b/q.sh').write_text(")
end=s.index('    manifest=',start)
script='''#!/bin/bash
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem={memory}G
#SBATCH --time={time}
{gpu}set -eu
umask 077
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
{visible}ulimit -v {cap}
exec python3 -I -s -B b/a.py q "$1" "$2"
'''
cpu=script.format(memory=256,time='48:00:00',gpu='',visible='export CUDA_VISIBLE_DEVICES=""\n',cap=240*1024**2)
gpu=script.format(memory=192,time='12:00:00',gpu='#SBATCH --gres=gpu:1\n',visible='',cap=180*1024**2)
s=s[:start]+"    (output/'b/q.sh').write_text("+repr(cpu)+")\n    (output/'b/q1.sh').write_text("+repr(gpu)+")\n"+s[end:]
p.write_text(s)
(O/'j.sh').write_text(cpu);(O/'j1.sh').write_text(gpu)
record=dict(cpu=dict(memory_gib=256,cpus=8,hours=48,address_space_gib=240,device='cpu'),
            gpu=dict(memory_gib=192,cpus=8,hours=12,address_space_gib=180,device='cuda:0',gpus=1,minimum_gpu_memory_gib=80),
            recommended='gpu',estimate='GUESS; no full-size weights or frozen towers were loaded here.',
            arithmetic=dict(bf16_9b_bytes=9_000_000_000*2,cpu_weight_copies=3,cpu_weight_peak_gib=54_000_000_000/2**30,
                cpu_frozen_towers_and_heads_gib=24,cpu_activations_workspace_gib=96,cpu_readers_runtime_margin_gib=48,
                gpu_weights_towers_heads_gib=28,gpu_activations_workspace_gib=40,gpu_allocator_margin_gib=12),
            basis=['work/tree_r1/student_pilot/carrier_c1_run.py:load_model',
                   'work/tree_r1/student_pilot/carrier_c1_run.py:first_batch_check',
                   'work/tree_r1/student_pilot/carrier_c1_run.py:check_plan_rows'],
            semantics='One process loads once; all four logical ranks run sequentially, with the native full forward and loss for every first-step draw. No optimizer or backward pass. The operator supplies the submission name. CPU memory fit is plausible at this request; GPU is recommended for latency, not because of Trinity limits. GPU memory and time remain GUESS.')
(O/'SIZING.json').write_text(json.dumps(record,indent=2)+'\n')
(B/'STATUS.md').write_text((B/'STATUS.md').read_text()+'\nStep 2 complete. General-partition CPU and one-GPU scripts carry request-sized caps and no embedded submission name. Full-size memory and duration are GUESS. Evidence: proofs/operator/SIZING.json.\n')
