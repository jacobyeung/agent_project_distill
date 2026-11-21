W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
date -u +%TZ
timeout 120 nice -n 10 find $W -maxdepth 9 \( -name population.json -o -name reader_filters.json -o -name 'f.json' -o -name c4.json -o -name s2.json -o -name WAITING_REVIEW.json -o -name ADMIT.json -o -name 'e2.json' \) -printf '%TY%Tm%Td %s %p\n' < /dev/null 2>/dev/null | grep -v '/attic/' | sort | tail -60
date -u +%TZ
