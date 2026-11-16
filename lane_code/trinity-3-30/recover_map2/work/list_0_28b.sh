date -u +%FT%TZ; R=/scratch/jjyeung/evalx_native_step200_20261114
cd $R && cat base_STATE.json; echo; cat export_STATE.json; echo; cat runtime_STATE.json; echo; head -c 2300 base_INVENTORY.json; echo
du -s base runtime transport export_BAD 2>/dev/null
find . -maxdepth 3 -not -path './runtime/*/*' -printf '%y %s %p\n' | head -80
