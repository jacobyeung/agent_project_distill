#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 || $# -gt 2 || ( $# -eq 2 && $2 != --dry-run ) ]]; then
    echo 'Usage: apply_contract_patches_r6.sh TARGET_TREE [--dry-run]' >&2
    exit 2
fi
packet=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
target=$(realpath -e -- "$1")
[[ -d $target && ! -L $1 && $target != / ]] || exit 2
parent=$(dirname -- "$target")
py=/scratch/jjyeung/envs/p1cpu/bin/python
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/contracts_rebuild/work/.cache
# Check permissions before any validation inventory or staging copy.
"$py" -I -s -B "$packet/contract_hash_checks_r6.py" writable "$target"
# All validation precedes installation. Retain the original tree for rollback.
plan=$("$py" -I -s -B "$packet/contract_hash_checks_r6.py" pre "$target")
transaction=$(mktemp -d "$parent/.contracts-XXXXXXXX")
printf '%s\n' "$plan" > "$transaction/plan"
"$py" -I -s -B "$packet/contract_hash_checks_r6.py" inventory "$target" > "$transaction/before"
if [[ ${2:-} == --dry-run ]]; then
    "$py" -I -s -B "$packet/contract_hash_checks_r6.py" stage-changed "$target" "$transaction/staged"
else
    cp -a -- "$target" "$transaction/staged"
fi
chmod -R u+w -- "$transaction/staged"
while IFS= read -r patch_file; do
    if ! patch --batch --forward -p1 -F0 --no-backup-if-mismatch -d "$transaction/staged" -i "$packet/$patch_file" > "$transaction/$patch_file.log" 2>&1; then
        cat "$transaction/$patch_file.log" >&2
        exit 1
    fi
    if grep -Ei 'reject|fuzz|offset|FAILED|Reversed|Skipping' "$transaction/$patch_file.log"; then exit 1; fi
done < "$transaction/plan"
"$py" -I -s -B "$packet/contract_hash_checks_r6.py" post "$transaction/staged" "$transaction/plan"
"$py" -I -s -B "$packet/contract_hash_checks_r6.py" inventory "$target" > "$transaction/recheck"
cmp -- "$transaction/before" "$transaction/recheck"
if [[ ${2:-} == --dry-run ]]; then
    printf 'Validated dry run; target unchanged. Retained staging: %s\n' "$transaction"
    exit 0
fi
restore() {
    if [[ ! -e $target && -d $transaction/original ]]; then mv -T -- "$transaction/original" "$target"; fi
}
trap restore EXIT
trap 'exit 130' INT TERM HUP
mv -T -- "$target" "$transaction/original"
mv -T -- "$transaction/staged" "$target"
printf 'Applied and verified; retained original: %s/original\n' "$transaction"
