#!/bin/bash
# Dry launcher checks (no GPU, no vnice): head node refused; busy cards refused; a free card is picked; t-only arms pass through.
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; ROOT="$(dirname "$KIT")"; T="$ROOT/work/dry_launch_test"; mkdir -p "$T"
printf '#!/bin/bash\necho "0, 49140, 35000, 8.9"\necho "1, 49140, 3, 8.9"\n' > "$T/smi_free"; chmod +x "$T/smi_free"
printf '#!/bin/bash\necho "0, 49140, 35000, 8.9"\n' > "$T/smi_busy"; chmod +x "$T/smi_busy"
run() { GTC_DRY_LAUNCH=1 GTC_WAIT_SECONDS=0 GTC_NVIDIA_SMI="$T/$1" GTC_HOST="$2" bash "$KIT/launch_gpu.sh" $3 2>&1; }
o=$(run smi_free trinity ""); echo "$o" | grep -q 'LAUNCH_REFUSED head_node' || { echo FAIL head; exit 1; }; echo PASS head_node_refused
o=$(run smi_busy trinity-2-28 ""); echo "$o" | grep -q 'no_card_free' || { echo FAIL busy; exit 1; }; echo PASS busy_cards_refused
o=$(run smi_free trinity-2-28 ""); echo "$o" | grep -q 'gpu=1 arms=t,s' && echo "$o" | grep -q "would run bash /data3/shared/scripts/vnice/vnice.sh" || { echo FAIL pick; echo "$o"; exit 1; }; echo PASS free_card_picked_under_vnice
o=$(run smi_free trinity-2-28 t); echo "$o" | grep -q 'arms=t ' || { echo FAIL tonly; exit 1; }; echo PASS t_only
o=$(run smi_free trinity-0-13 ""); echo "$o" | grep -q "would run bash $ROOT/work/gpu_inner" || { echo FAIL 013; exit 1; }; echo PASS 0-13_without_vnice
echo '{"status": "PASS"}'
