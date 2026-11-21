set -euo pipefail
squeue(){ printf "%s" "$Q_ROWS"; }
squeue -u jjyeung -p debug -h -o '%j|%b' > a/9.txt
if grep -Eiq '^a15_cot_ap[^|]*[|].*gpu' a/9.txt; then exit 1; fi
echo admitted
