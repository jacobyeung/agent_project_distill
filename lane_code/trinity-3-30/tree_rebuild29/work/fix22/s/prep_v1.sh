#!/bin/bash
# Build the mode-r delta for a new tree on trinity-3-30 (CPU only, no Orchard call).
# Usage: bash prep.sh NEW_TREE_DIR NEW_SEAL NEW_TAR_SHA256 OUT_LABEL
#   NEW_TREE_DIR: extracted sealed tree (fix21); NEW_SEAL: its source seal; NEW_TAR_SHA256: sha256 of fix21's sealed tar.
# Writes $F/pkg/<label>/{s29r.tar,s29r.tar.sha256,o_go.sh,PREP.json}. o_go.sh is the Orchard stage+submit script.
set -euo pipefail
F=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix22; P=/scratch/jjyeung/envs/p1cpu/bin/python
OLDT=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix21/tb/t2/old
OLD=9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b
TREE=$1; NEW=$2; TARSHA=$3; L=$4
O=$F/pkg/$L; test ! -e $O; mkdir -p $O
KIT=$F/in/qdk/kit_qd; RCJ=$F/in/w24y2/out/rcj
[ "$(sha256sum $KIT/SHA256SUMS.txt | cut -c1-64)" = 8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784 ]
# 1. identity: the procedure applied with the old tree reproduces reviewed qd 8ae781f4 and rcj byte for byte
$P -I $F/s/swap_qd.py $KIT $OLDT $O/id $OLD > $O/id.out
$P -I -c "import json,sys;r=json.load(open('$O/id/RESULT.json'));sys.exit(0 if r['identity'] and not r['changed'] else 1)"
$P -I $F/s/swap_rcj.py $RCJ $O/id_rcj $OLD $OLD > /dev/null; diff -r $RCJ $O/id_rcj
# 2. the swap onto the new tree
$P -I $F/s/swap_qd.py $KIT $TREE $O/new $NEW > $O/new.out
$P -I $F/s/swap_rcj.py $RCJ $O/rcj $OLD $NEW > $O/rcj.json
$P -I $F/s/kdiff.py $KIT $O/new/kit > $O/kdiff.txt
NQ=$($P -I -c "import json;print(json.load(open('$O/new/RESULT.json'))['kit'])")
NT=$($P -I -c "import json;print(json.load(open('$O/new/RESULT.json'))['tree_tar_sha256'])")
[ "$NT" = "$TARSHA" ] || { echo "TAR DIFFERS: kit $NT vs sealed $TARSHA"; exit 1; }
# 3. package: changed qd members, the two rcj helpers, the new code capsule
S=$O/s29r; mkdir -p $S/qd $S/rcj $S/u
(cd $O/new/kit && for f in $($P -I -c "import json;print(' '.join(json.load(open('$O/new/RESULT.json'))['changed']))"); do mkdir -p $S/qd/$(dirname $f); cp -p $f $S/qd/$f; done)
cp -p $O/rcj/nd.py $O/rcj/ch.py $S/rcj/; cp -p $O/new/u/* $S/u/
C=c_${NQ:0:8}r
sed "s#@C@#$C#g" $F/s/rcj_c.tmpl > $S/rcj_c.sh; RCS=$(sha256sum $S/rcj_c.sh | cut -c1-64)
tar cf $O/s29r.tar -C $S qd rcj u rcj_c.sh; TS=$(sha256sum $O/s29r.tar | cut -c1-64); echo "$TS  s29r.tar" > $O/s29r.tar.sha256
RH=$(cd $O/rcj && sha256sum x.py pc.py nd.py ch.py f.json ps.py P_SAMPLE_I.json | awk '{printf "%s:%s ", $2, substr($1,1,16)}')
sed -e "s#@TS@#$TS#; s#@C@#$C#g; s#@NQ@#$NQ#g; s#@RH@#$RH#; s#@TARSHA@#$TARSHA#; s#@NEW@#$NEW#; s#@RCS@#$RCS#" $F/s/o_go.tmpl > $O/o_go.sh
$P -I -c "import json;print(json.dumps(dict(tree=('$NEW'),tree_tar=('$TARSHA'),qd=('$NQ'),folder=('$C'),package=('$TS'),package_bytes=$(stat -c %s $O/s29r.tar),rcj_sh=('$RCS'),rcj=dict(x.split(':') for x in '$RH'.split())),indent=1))" > $O/PREP.json
cat $O/PREP.json; cat $O/kdiff.txt | cut -c1-200
