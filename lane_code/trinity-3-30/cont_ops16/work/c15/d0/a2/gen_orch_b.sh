#!/bin/bash
# Usage: gen_orch_b.sh OUT_DIR > orch_b.sh  (upload the job B bundle to i_bb09a77d/b5, derive READY kit x_f5c353f7 on the Orchard
# login, install sess.json (600) in the kit root, run a.py's inventory gate, pull the changed records back as a tar on stdout).
# The job receipt (VB) is uploaded by the A2 bundle; this script checks it is present with the same sha256.
set -euo pipefail
OUT=$(readlink -f "$1"); VB=$(cat $OUT/VB); T=$(mktemp -d /scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/.tb.XXXX)
mkdir -p $T/b5; cp $OUT/over.json $OUT/4.json $OUT/review.json $OUT/staging.json $OUT/full_weights.json $T/b5/
cp /scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/jb.sh $T/b5/jb.sh
(cd $T && sha256sum b5/*) > $OUT/bundle.SHA256SUMS
cat <<HDR
set -euo pipefail
O=/project/community/jjyeung/okh7; IN=\$O/i_bb09a77d; KH=\$O/x_f5c353f7
[ ! -e \$IN/b5 ] && [ ! -e \$KH ] && [ ! -e \$O/r/63e57182 ] || { echo "target exists" >&2; exit 3; }
[ "\$(sha256sum < \$IN/derive_kit.py | cut -c1-8)" = 4ad1a5ac ] || { echo "derive_kit differs" >&2; exit 3; }
[ "\$(sha256sum < \$IN/$VB | cut -d' ' -f1)" = $(sha256sum < $OUT/receipt.json | cut -d' ' -f1) ] || { echo "job receipt absent or differs" >&2; exit 3; }
[ "\$(sha256sum < \$IN/jb/sess.json | cut -c1-16)" = 4b78ef56c3b2cd93 ] || { echo "sess.json differs" >&2; exit 3; }
mkdir -p \$IN/b5
base64 -d > \$IN/b5/.bundle.tar <<'B64'
HDR
(cd $T && tar cf - b5) | base64
cat <<TAIL
B64
tar xf \$IN/b5/.bundle.tar -C \$IN
(cd \$IN && sha256sum -c --quiet) >&2 <<'SUMS'
$(cat $OUT/bundle.SHA256SUMS)
SUMS
/usr/bin/python3 -I \$IN/derive_kit.py \$O/x_07ca49df \$KH \$IN/b5/over.json > \$IN/b5/derive.result.json 2> \$IN/b5/derive.err || { cat \$IN/b5/derive.err >&2; exit 3; }
chmod 700 \$KH
cp \$IN/jb/sess.json \$KH/sess.json && chmod 600 \$KH/sess.json
K=\$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["0"])' \$KH/k/1.json)
cd \$KH && tar cf - SHA256SUMS.txt ANON_OK.json k/\$K.json k/0.json k/1.json k/launch.json k/4.json k/review.json k/staging.json k/pool_selection_aa128e6f.json -C \$IN/b5 derive.result.json
TAIL
mv $T $OUT/bundle_tree
