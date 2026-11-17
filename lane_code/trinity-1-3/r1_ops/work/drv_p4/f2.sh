export TZ=UTC
K=/project/community/jjyeung/okh7/x_69d2930d/o
sacct -j 170956 -X -o JobID,State,ExitCode,Elapsed,End -P 2>/dev/null | tail -1
ls -la $K | grep 170956
echo ==== PROOFJSON; head -c 300000 $K/170956.proof.json
echo; echo ==== PROOFLOG; head -c 600000 $K/170956.proof.log
echo; echo ==== ERR; tail -30 $K/170956.err | cut -c1-400
