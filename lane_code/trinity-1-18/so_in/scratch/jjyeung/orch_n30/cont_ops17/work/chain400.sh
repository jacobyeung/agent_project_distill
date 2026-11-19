#!/bin/bash
# cont_ops17: step-400 reads in order (one general slot): direct, then facing, then VSTI; each autosub waits for the export and a free general
W=/scratch/jjyeung/orch_n30/cont_ops17/work
K=h1read7 TOK=a59a7bff4c4 STEP=400 LABEL=direct POLL=180 bash $W/autosub400.sh || exit $?
sleep 120
K=h1face7 TOK=afdfd5caac6 STEP=400 LABEL=facing POLL=120 bash $W/autosub400.sh || exit $?
sleep 120
K=h1vsti7 TOK=a4525db2f6a STEP=400 LABEL=vsti POLL=120 bash $W/autosub400.sh
