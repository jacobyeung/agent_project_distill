#!/bin/bash
# Usage: gen_orch_a2.sh OUT_DIR VB_NAME > orch_a2.sh   (upload the a2 bundle, derive x_8417c021 on the Orchard login, pull records back as a tar on stdout)
set -euo pipefail
OUT=$(readlink -f "$1"); VB=$2; T=$(mktemp -d /scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/.tb.XXXX)
mkdir -p $T/a2; cp $OUT/receipt.json $T/$VB; cp $OUT/over.json $OUT/4.json $OUT/full_weights.json $OUT/ja2.sh $OUT/fam.py $OUT/s2.py $OUT/s2.sh $OUT/s2sum.py $T/a2/
(cd $T && sha256sum $VB a2/*) > $OUT/bundle.SHA256SUMS
cat <<HDR
set -euo pipefail
O=/project/community/jjyeung/okh7; IN=\$O/i_bb09a77d; KH=\$O/x_8417c021
[ ! -e \$IN/a2 ] && [ ! -e \$IN/$VB ] && [ ! -e \$KH ] && [ ! -e \$O/r/4d3cd40e ] || { echo "target exists" >&2; exit 3; }
[ "\$(sha256sum < \$IN/derive_kit.py | cut -c1-8)" = 4ad1a5ac ] || { echo "derive_kit differs" >&2; exit 3; }
mkdir -p \$IN/a2
base64 -d > \$IN/a2/.bundle.tar <<'B64'
HDR
(cd $T && tar cf - $VB a2) | base64
cat <<TAIL
B64
tar xf \$IN/a2/.bundle.tar -C \$IN
(cd \$IN && sha256sum -c --quiet) >&2 <<'SUMS'
$(cat $OUT/bundle.SHA256SUMS)
SUMS
/usr/bin/python3 -I \$IN/derive_kit.py \$O/x_07ca49df \$KH \$IN/a2/over.json > \$IN/a2/derive.result.json 2> \$IN/a2/derive.err || { cat \$IN/a2/derive.err >&2; exit 3; }
chmod 700 \$KH
K=\$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["0"])' \$KH/k/1.json)
cd \$KH && tar cf - SHA256SUMS.txt ANON_OK.json k/\$K.json k/0.json k/1.json k/launch.json k/4.json k/pool_selection_aa128e6f.json -C \$IN/a2 derive.result.json
TAIL
mv $T $OUT/bundle_tree
