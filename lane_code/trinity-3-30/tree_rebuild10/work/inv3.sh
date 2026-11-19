set -u; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=/scratch/jjyeung/n30_mirror/tree_rebuild
[ -e /scratch/jjyeung/orch_n30/tree_rebuild_w ] && echo "EXISTS tree_rebuild_w" || ln -s $W /scratch/jjyeung/orch_n30/tree_rebuild_w
cd $W && for p in w9f:b9f_64a2ea92 w12:b12_de231562 w13:b13_35d4b18b w14:b14_094933b3; do d=${p%%:*}; t=${p#*:}; mkdir -p $d && (cd $d && tar xf $M/tree_rebuild_$t.tar) && echo "untar $d ok"; done
cp -rn clone/tree_rebuild_w/work/. work/ ; cp -rn clone/tree_rebuild_w/prompts/. prompts/; cp -n clone/tree_rebuild_w/STATUS.md work/STATUS_tree_rebuild9.md; ls work | tr '\n' ' '; echo
du -sh $W; df -BG --output=avail /scratch | tail -1
cd $W/w15; echo "== run.sh"; cat work/build14/run.sh; echo "== real14 paths"; grep -nE "/scratch|/data|snap_|config.json" work/build14/real14.py | head -30; echo "== opener14 paths"; grep -nE "/scratch|/data" work/build14/opener14.py | head; echo "== INPUTS.json keys"; head -c 3000 work/build14/INPUTS.json
echo; echo "== proofs/real"; ls work/build14/proofs/real; head -c 2500 work/build14/proofs/real/RESULT.json
