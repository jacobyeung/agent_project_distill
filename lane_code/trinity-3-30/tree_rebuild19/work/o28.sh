export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173673; O=$X/o/$J
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; sacct -j $J -X -n -o State,Start,End,ExitCode,MaxRSS
tail -5 $X/j/$J.log | cut -c1-300; tail -5 $X/j/$J.err | cut -c1-400
ls -la $O 2>/dev/null | grep -v "^total" | cut -c30-; for f in timings db_bytes import_probe; do test -f $O/$f.json && { echo "== $f"; head -c 1500 $O/$f.json; echo; }; done
ls $O/rd0 2>/dev/null; grep -v KITX_OK $X/j/$J.log | tail -8 | cut -c1-300
