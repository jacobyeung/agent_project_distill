L=/scratch/jjyeung/orch_n30/b04_e2ehook_sl; tail -2 $L/full_raw.log | cut -c1-200 >&2; ls $L/full_raw/caps | wc -l >&2; grep -c error $L/full_raw/progress.jsonl >&2
tar cf - -C $L/full_raw caps progress.jsonl
