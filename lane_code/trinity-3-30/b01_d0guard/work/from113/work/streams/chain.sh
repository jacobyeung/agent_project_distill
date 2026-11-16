#!/bin/bash
D=/scratch/jjyeung/orch_n30/native_r2/work/streams; OB=/scratch/jjyeung/orch_n30/native_r2/work/obj
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
S=/data3/jjyeung/orch_n13_20261026/io_governor/streams
finish() { while [ ! -f $D/$1.done ]; do sleep 30; done; mv $S/native_r2_$1.json $S/native_r2_$1.done.$(date +%s) 2>/dev/null; echo "$(date -u +%FT%TZ) $1 $(cat $D/$1.done)" >> $D/chain.log; }
finish masks
$D/start_stream.sh geometry 679895040 $OB/geometry_8c58df1547371bdb.tar -- timeout 7200 /home/jjyeung/google-cloud-sdk/bin/gsutil -q cat gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/geometry_8c58df1547371bdb.tar > $D/geometry.log 2>&1 &
finish geometry
$D/start_stream.sh numpy 202598400 $OB/np226_5204b3a0.tar -- timeout 7200 bash $O 'cat /project/community/jjyeung/okh7/x_07ca49df/k/np226_5204b3a0.tar' > $D/numpy.log 2>&1 &
finish numpy
$D/start_stream.sh frames 1340000000 $OB/frames.tar -- timeout 10800 bash $O 'cd /project/community/jjyeung/okh7/nr2tmp && python3 fp.py frame_request.txt /project/community/jjyeung/cp4tk_fr/k6tk' > $D/frames.log 2>&1 &
finish frames
cd $OB && sha256sum masks_4984fac22d84e8c5.tar geometry_8c58df1547371bdb.tar np226_5204b3a0.tar frames.tar >> $D/chain.log
echo "$(date -u +%FT%TZ) ALL DONE" >> $D/chain.log
