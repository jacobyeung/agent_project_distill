set -euo pipefail
umask 077
trap 'r=$?; if [ "$r" -ne 0 ]; then printf "phase failed: exit %s line %s\n" "$r" "$LINENO" >&2; fi' EXIT
export P=/scratch/jjyeung/orch_n30/so_pack/work/review1_dev01/a4242ba297742/p T=04:00:00
test "${P##*a15_cot_ap}" = a0123456789ab
J=$(cat "$P/a/4.txt"); [[ "$J" =~ ^[0-9]+$ ]]
if ! V=$(sacct -n -X -j "$J" --format=State 2>"$P/a/0.err"); then
  cat "$P/a/0.err" >&2; echo PACK_CPU_RETRY; exit 0
fi
S=$(printf '%s\n' "$V" | awk 'NF{print $1;exit}'); S=${S%%+*}
case "$S" in
 COMPLETED) test -s "$P/a/c/CPU.json"; echo PACK_CPU_READY;;
 PENDING|RUNNING|CONFIGURING|COMPLETING) echo "PACK_CPU_WAIT $J $S"; exit 0;;
 "") echo "CPU accounting has no state for $J" >&2; echo PACK_CPU_RETRY; exit 0;;
 *) echo "CPU job $J state $S" >&2; tail -n 60 "$P/a/4.err" >&2 || true; exit 1;;
esac
