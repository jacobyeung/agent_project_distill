#!/bin/bash
# Dry launcher checks (no GPU, no vnice): head node and the five barred hosts refused; busy cards (> 100 MiB) refused; a free
# card is picked; arm b only; 0-13 runs without vnice, other hosts under vnice; a t or s argument is refused.
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; ROOT="$(dirname "$KIT")"; T="$ROOT/work/dry_launch_test"; mkdir -p "$T"
printf '#!/bin/bash\necho "0, 49140, 35000, 8.9"\necho "1, 49140, 3, 8.9"\n' > "$T/smi_free"; chmod +x "$T/smi_free"
printf '#!/bin/bash\necho "0, 49140, 35000, 8.9"\n' > "$T/smi_busy"; chmod +x "$T/smi_busy"
printf '#!/bin/bash\necho "0, 49140, 101, 8.9"\n' > "$T/smi_101"; chmod +x "$T/smi_101"
printf '#!/bin/bash\necho "0, 49140, 100, 8.9"\n' > "$T/smi_100"; chmod +x "$T/smi_100"
run() { GTC_DRY_LAUNCH=1 GTC_WAIT_SECONDS=0 GTC_NVIDIA_SMI="$T/$1" GTC_HOST="$2" bash "$KIT/launch_gpu.sh" $3 2>&1; }
o=$(run smi_free trinity ""); echo "$o" | grep -q 'LAUNCH_REFUSED head_node' || { echo FAIL head; exit 1; }; echo PASS head_node_refused
for h in trinity-1-13 trinity-0-23 trinity-0-8 trinity-3-23 trinity-0-18; do
  o=$(run smi_free $h ""); echo "$o" | grep -q "LAUNCH_REFUSED host_not_allowed_$h" || { echo FAIL $h; exit 1; }; done; echo PASS five_barred_hosts_refused
o=$(run smi_busy trinity-2-28 ""); echo "$o" | grep -q 'no_card_free' || { echo FAIL busy; exit 1; }; echo PASS busy_cards_refused
o=$(run smi_101 trinity-0-13 ""); echo "$o" | grep -q 'no_card_free' || { echo FAIL 101; exit 1; }; echo PASS 101_MiB_refused
o=$(run smi_100 trinity-0-13 ""); echo "$o" | grep -q 'gpu=0 arms=b ' || { echo FAIL 100; echo "$o"; exit 1; }; echo PASS 100_MiB_accepted
o=$(run smi_free trinity-2-28 ""); echo "$o" | grep -q 'gpu=1 arms=b ' && echo "$o" | grep -q "would run bash /data3/shared/scripts/vnice/vnice.sh" || { echo FAIL pick; echo "$o"; exit 1; }; echo PASS free_card_picked_under_vnice_off_0-13
o=$(run smi_free trinity-0-13 b); echo "$o" | grep -q "would run bash $ROOT/work/gpu_inner" && echo "$o" | grep -q 'arms=b ' || { echo FAIL 013; exit 1; }; echo PASS 0-13_without_vnice_arm_b
grep -q -- '--arms b ' "$(ls -t "$ROOT"/work/gpu_inner_*.sh | head -1)" || { echo FAIL inner_arms; exit 1; }; echo PASS inner_runs_arm_b
for a in t s t,s; do o=$(run smi_free trinity-0-13 $a); echo "$o" | grep -q 'usage' || { echo FAIL arg_$a; exit 1; }; done; echo PASS t_s_arguments_refused
echo '{"status": "PASS"}'
