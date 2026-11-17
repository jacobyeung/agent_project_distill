export TZ=UTC; date -u +%TZ
K=/project/community/jjyeung/okh7/x_4b3114cf
sacct -j 170527 -n -o JobID%16,State,ExitCode,Start,End,Elapsed 2>&1
ls -la --time-style=+%H:%M:%S $K/o
echo ==err; tail -n 60 $K/o/170527.err | cut -c1-400
echo ==w; cat $K/o/170527.w.steps | cut -c1-300
echo ==steps; tail -n 25 $K/o/170527.steps | cut -c1-300
for f in $K/o/170527.SLOT* $K/o/170527.*fail* ; do test -f "$f" && { echo "== $f"; head -c 2000 "$f"; echo; }; done
ls $K/runs 2>&1 | head; ls -la $K/runs/17c4ffa4 2>&1 | head -20
