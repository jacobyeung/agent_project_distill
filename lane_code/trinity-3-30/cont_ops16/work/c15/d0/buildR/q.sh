B=/scratch/jjyeung/orch_n30/b07_offread/builds/R
ls -la $B $B/out
echo "#### REBIND_READY"; cat $B/out/REBIND_READY.md
echo "#### RUN"; cat $B/RUN.md 2>/dev/null || cat $B/out/RUN.md
