export TZ=UTC; P=/project/community/jjyeung
ls -d $P/*/venv/lib/python3*/site-packages/torch $P/*/env/lib/python3*/site-packages/torch $P/*/*/venv/lib/python3*/site-packages/torch $P/*/*/env/lib/python3*/site-packages/torch $P/*/*/lib/python3*/site-packages/torch $P/*/lib/python3*/site-packages/torch 2>/dev/null | head
ls $P/cp4tk_rt/kit $P/cp4tk_rt/bin 2>/dev/null | head -20
ls /project/community/jjyeung/okh7 | head -30
squeue -j 174085 -h -o '%T %r %S'
