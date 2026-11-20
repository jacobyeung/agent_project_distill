W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; O=$W/work/tgcs_900001; test -e $O && { echo EXISTS; exit 1; }
timeout 400 bash $W/w24z7/out/tgcs/run_tgcs.sh 900001 /scratch/jjyeung/orch_n30/n_ops8_x/sess_900001.json $W/w24z4/out/kit_n $O; echo rc=$?
M='s#https?://[^ "]*#[URL]#g'
cd $O; ls -la logs; echo ==RESULT; sed -E "$M" RESULT.json | head -40; echo ==HTTP; sed -E "$M" logs/http.jsonl 2>/dev/null | head -20; for f in gc.stderr gc.stdout copier.stderr copier.stdout; do echo "== $f"; sed -E "$M" logs/$f 2>/dev/null | tail -30; done
find $O/n -maxdepth 3 -name "*.json*" -newer $O/logs -printf '%s %p\n' | head -20
