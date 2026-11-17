#!/bin/bash
set -uo pipefail
export TZ=UTC
O=/project/community/jjyeung/okh7; BUN=$O/i_1be16f28
echo "$(date -u +%TZ) patch start"
printf '%s  %s\n' c642f2343237413bba08aa2ac62212d4373d97d19f3185e27e069f3c7f481975 "$O/t_c8b460a1.sh" | sha256sum -c - || exit 11
bash "$O/t_c8b460a1.sh"; rc=$?; echo "$(date -u +%TZ) patch rc=$rc"; [ $rc -eq 0 ] || exit 12
cd "$BUN" || exit 13
bash o.sh; rc=$?; echo "$(date -u +%TZ) o.sh rc=$rc"; [ $rc -eq 0 ] || exit 14
PY_GATE=/project/community/jjyeung/latency/envs/fit/bin/python3 BW_GATE=/project/community/jjyeung/cp4tk_rt/kit/bwrap bash g.sh; rc=$?; echo "$(date -u +%TZ) g.sh rc=$rc"
exit $rc
