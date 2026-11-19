W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w14/work/build14/kits/r1
date -u +%TZ; tmux ls | grep tr10; tail -c 600 $W/w15/work/build15/STATUS.md
cat $K/BUILD.json | head -c 2500; echo; echo "== job.sh"; head -c 4000 $K/job.sh; echo; ls $K/b $K/k | head -80 | tr '\n' ' '; echo; du -sh $K
echo "== b13 host steps"; awk '/[Hh]ost steps/,/^## /' $W/w14/out/BUILD13_REPORT.md | head -40
echo "== b14 report head"; head -c 3000 $W/w14/out/BUILD14_REPORT.md
