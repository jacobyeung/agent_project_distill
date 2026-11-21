export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; D=$X/t_e7c1a94b3d20; date -u +%TZ
ls -la $X/n_s/sess_174113.json | cut -c1-80; [ "$(sha256sum $X/n/SHA256SUMS.txt | cut -c1-16)" = 4e29bdfb8754e85f ] && scontrol release 174113 && echo RELEASED $(date -u +%TZ)
sleep 5; squeue -u $USER -h -o "%i %P %j %T %M %R"; squeue -j 174113 --start -h -o "%i %S %R"
sacct -j 174114 -n -X -o State,ExitCode,Elapsed | head -1; cat $D/r.txt 2>/dev/null | cut -c1-400; tail -3 $D/e.txt 2>/dev/null | cut -c1-300
