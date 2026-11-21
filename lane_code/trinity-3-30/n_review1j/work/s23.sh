T=/scratch/jjyeung/orch_n30/n_review/r1j/t; F=$T/launch_r1/entry.py
grep -n "def check_host_selection\|R1_ROUTING_SELECTION_DIFFERS\|def _selection\|def selection" $F < /dev/null
n=$(grep -n "def check_host_selection" $F < /dev/null | cut -d: -f1); sed -n "${n},$((n+70))p" $F < /dev/null
