#!/bin/bash
# cont_ops17: step-600 reads in order (one general slot): direct, then facing, then VSTI; each autosub waits for the export and a free general
W=/scratch/jjyeung/orch_n30/cont_ops17/work
K=h1read7 TOK=a136f924ab1 STEP=600 LABEL=direct POLL=180 bash $W/autosub400.sh || exit $?
sleep 120
K=h1face7 TOK=a0359570077 STEP=600 LABEL=facing POLL=120 bash $W/autosub400.sh || exit $?
sleep 120
K=h1vsti7 TOK=a4dab97810e STEP=600 LABEL=vsti POLL=120 bash $W/autosub400.sh
