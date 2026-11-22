#!/bin/bash
# Dry launcher checks (no GPU, nothing runs): the head node and the five barred hosts refused; a GPU launch off trinity-0-13
# refused; busy cards (> 100 MiB in either reading) refused; a free card picked on 0-13 at normal priority; both nvidia-smi
# readings written to EVENTS.jsonl; the CPU rehearsal writes the same inner command line with only the device, --captures and
# --anchor-limit changed; every child's exit code is logged; wrong arguments are refused.
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; ROOT="$(dirname "$KIT")"; T="$ROOT/work/dry_launch_test"; mkdir -p "$T"
printf '#!/bin/bash\necho "0, 49140, 35000, 8.9"\necho "1, 49140, 3, 8.9"\n' > "$T/smi_free"; chmod +x "$T/smi_free"
printf '#!/bin/bash\necho "0, 49140, 35000, 8.9"\n' > "$T/smi_busy"; chmod +x "$T/smi_busy"
printf '#!/bin/bash\necho "0, 49140, 101, 8.9"\n' > "$T/smi_101"; chmod +x "$T/smi_101"
printf '#!/bin/bash\necho "0, 49140, 100, 8.9"\n' > "$T/smi_100"; chmod +x "$T/smi_100"
# a card that is free in reading 1 and busy in reading 2 (the counter file flips between calls)
printf '#!/bin/bash\nf=%s/flip.n; n=$(cat $f 2>/dev/null || echo 0); echo $((n+1)) > $f\nif [ "$n" = 0 ]; then echo "0, 49140, 3, 8.9"; else echo "0, 49140, 9000, 8.9"; fi\n' "$T" > "$T/smi_flip"; chmod +x "$T/smi_flip"
run() { J1_DRY_LAUNCH=1 J1_WAIT_SECONDS=0 J1_NVIDIA_SMI="$T/$1" J1_HOST="$2" bash "$KIT/launch_gpu.sh" $3 2>&1; }
o=$(run smi_free trinity ""); echo "$o" | grep -q 'LAUNCH_REFUSED head_node' || { echo FAIL head; exit 1; }; echo PASS head_node_refused
for h in trinity-1-13 trinity-0-23 trinity-0-8 trinity-3-23 trinity-0-18; do
  o=$(run smi_free $h ""); echo "$o" | grep -q "LAUNCH_REFUSED host_not_allowed_$h" || { echo FAIL $h; exit 1; }; done; echo PASS five_barred_hosts_refused
o=$(run smi_free trinity-2-28 ""); echo "$o" | grep -q 'LAUNCH_REFUSED gpu_launch_only_on_trinity-0-13_not_trinity-2-28' || { echo FAIL off013; echo "$o"; exit 1; }; echo PASS gpu_off_0-13_refused
o=$(run smi_busy trinity-0-13 ""); echo "$o" | grep -q 'no_card_free' || { echo FAIL busy; exit 1; }; echo PASS busy_cards_refused
o=$(run smi_101 trinity-0-13 ""); echo "$o" | grep -q 'no_card_free' || { echo FAIL 101; exit 1; }; echo PASS 101_MiB_refused
echo 0 > "$T/flip.n"; o=$(run smi_flip trinity-0-13 ""); echo "$o" | grep -q 'no_card_free' || { echo FAIL flip; echo "$o"; exit 1; }; echo PASS card_busy_in_second_reading_refused
o=$(run smi_100 trinity-0-13 ""); echo "$o" | grep -q 'LAUNCH gpu=0 priority=normal' || { echo FAIL 100; echo "$o"; exit 1; }; echo PASS 100_MiB_accepted
o=$(run smi_free trinity-0-13 ""); echo "$o" | grep -q 'LAUNCH gpu=1 priority=normal' && echo "$o" | grep -q "would run bash $ROOT/work/gpu_inner" || { echo FAIL pick; echo "$o"; exit 1; }; echo PASS free_card_picked_on_0-13
E="$ROOT/work/dry_launch/EVENTS.jsonl"
grep -q '"NVIDIA_SMI_1", "host": "trinity-0-13", "detail": "0,49140,35000,8.9;1,49140,3,8.9"' "$E" && grep -q '"NVIDIA_SMI_2".*seconds_after_1=0' "$E" || { echo FAIL readings; exit 1; }; echo PASS both_readings_in_EVENTS
GI="$(ls -t "$ROOT"/work/gpu_inner_*.sh | head -1)"
grep -q -- '--device cuda --out '"$ROOT"'/work/dry_launch --hard-stop 3300 --captures all --anchor-limit 32' "$GI" && grep -q 'timeout -k 30 3600 ' "$GI" || { echo FAIL inner; cat "$GI"; exit 1; }; echo PASS inner_line_one_card_timeout
grep -q 'CUDA_VISIBLE_DEVICES=1 ' "$GI" || { echo FAIL one_card; exit 1; }; echo PASS one_card_visible
grep -q '"CHILD".*name=sha256sum exit=0' "$E" && grep -q '"CHILD".*name=nvidia_smi_2 exit=0' "$E" || { echo FAIL child_log; exit 1; }; echo PASS child_exit_codes_logged
sleep 1; o=$(run smi_free trinity-2-28 "rehearse-cpu scannet/scene0642_01"); echo "$o" | grep -q 'LAUNCH rehearsal device=cpu captures=scannet/scene0642_01 anchors=32' || { echo FAIL reh; echo "$o"; exit 1; }
CI="$(ls -t "$ROOT"/work/cpu_inner_*.sh | head -1)"
diff <(sed -e 's/CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=[0-9]*/DEV/' -e 's/--device cuda/--device X/' -e 's/--captures all/--captures C/' "$GI") \
     <(sed -e 's/CUDA_VISIBLE_DEVICES= /DEV /' -e 's/--device cpu/--device X/' -e 's#--captures scannet/scene0642_01#--captures C#' "$CI") > /dev/null \
  || { echo FAIL rehearsal_inner_differs; diff "$GI" "$CI"; exit 1; }; echo PASS rehearsal_runs_the_same_inner_line
sleep 1; o=$(run smi_free trinity-2-28 "rehearse-cpu scannet/scene0642_01 4"); CI4="$(ls -t "$ROOT"/work/cpu_inner_*.sh | head -1)"
grep -q -- '--anchor-limit 4$' "$CI4" || { echo FAIL anchors4; exit 1; }; echo PASS rehearsal_anchor_limit_only_changes_that_flag
o=$(run smi_busy trinity "rehearse-cpu scannet/scene0642_01"); echo "$o" | grep -q 'LAUNCH_REFUSED head_node' || { echo FAIL reh_head; exit 1; }; echo PASS rehearsal_refuses_head_node
for a in d gpu "rehearse-cpu" "rehearse-cpu x 4 5" "rehearse-cpu x four"; do o=$(run smi_free trinity-0-13 "$a"); echo "$o" | grep -q 'usage' || { echo FAIL arg_$a; exit 1; }; done; echo PASS wrong_arguments_refused
cp "$ROOT/SHA256SUMS_J1" "$T/sums.bak"; c1="$(head -c1 "$ROOT/SHA256SUMS_J1")"; n1=0; [ "$c1" = 0 ] && n1=1; sed -i "1s/^./$n1/" "$ROOT/SHA256SUMS_J1"; o=$(run smi_free trinity-0-13 ""); cp "$T/sums.bak" "$ROOT/SHA256SUMS_J1"
echo "$o" | grep -q 'kit_bytes_differ_from_SHA256SUMS_J1' || { echo FAIL seal; exit 1; }; echo PASS changed_seal_refused
echo '{"status": "PASS"}'
