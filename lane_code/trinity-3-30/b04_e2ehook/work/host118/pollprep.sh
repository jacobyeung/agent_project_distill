L=/dev/shm/jjyeung/b04/host2/b04_e2ehook
tail -c 1500 $L/work/prep.log | grep -v -i warn; echo; ls $L/parity_kit/restore_bw 2>&1 | head; ls $L/parity_kit/settings_bw.json; tmux ls | grep b04
wc -l /dev/shm/jjyeung/b04/host/b04_e2ehook/parity_kit/host_results/cpu_first_c/items.jsonl
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
