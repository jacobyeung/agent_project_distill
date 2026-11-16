L=/dev/shm/jjyeung/b04/host/b04_e2ehook; R=$L/parity_kit/host_results/cpu_first_c
grep -v "Warning\|warn" $L/work/first_c.log | tail -c 1200; echo; tmux ls 2>/dev/null | grep b04
ps -o pid,etime,rss,pcpu,cmd -u jjyeung | grep -E "parity_kit" | grep -v grep | cut -c1-140; ls $R; wc -l $R/items.jsonl
/scratch/jjyeung/envs/vllm/bin/python -c "
import json
for l in open('$R/items.jsonl'):
    r=json.loads(l); print(r.get('key'), r.get('question_type'), r.get('scores'), r.get('finish'), round(r.get('seconds',0)), [c.get('call') for c in (r.get('calls') or {}).get('records',[])][:6])
" 2>&1 | tail -8
SP=/dev/shm/jjyeung/b05/stage/sam3_capretry_native_v1/lib; ls $SP; ls $SP/python3*/site-packages | grep -i -E "^(iopath|portalocker|hydra|omegaconf|timm|ftfy|regex|huggingface_hub|einops|pycocotools|decord)" | head -20
