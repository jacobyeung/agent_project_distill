W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/w15
echo "== path roots referenced (inputs/kits/proofs json + py under work/build14, work/build13)"
grep -rhoE "/scratch/jjyeung/[A-Za-z0-9_./-]+" work/build14 work/build13 work/n1fix2 out/BUILD14_REPORT.md 2>/dev/null | awk -F/ '{print "/"$2"/"$3"/"$4"/"$5"/"$6}' | sort | uniq -c | sort -rn | head -40
echo "== exist?"; for p in $(grep -rhoE "/scratch/jjyeung/[A-Za-z0-9_./-]+" work/build14 work/build13 work/n1fix2 2>/dev/null | awk -F/ '{print "/"$2"/"$3"/"$4"/"$5"/"$6}' | sort -u); do [ -e "$p" ] && echo "OK $p" || echo "MISSING $p"; done | head -60
echo "== confirmation section"; awk '/For the confirmation/,0' out/BUILD14_REPORT.md | head -60
echo "== w15 size"; du -sh $W/w15; ls work/build14/kits work/build14/inputs | head -40
