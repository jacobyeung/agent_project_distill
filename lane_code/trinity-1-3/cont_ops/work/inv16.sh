set -euo pipefail
O=/project/community/jjyeung/okh7; IN=$O/i_bb09a77d; KH=$O/x_7cb63d1e
cd /tmp
[ ! -e $KH ] && [ ! -e $O/r/1b235d89 ] || { echo "target exists" >&2; exit 3; }
/usr/bin/python3 -I $IN/derive_kit.py $O/x_07ca49df $KH $IN/over.json > $IN/derive.result.json 2> $IN/derive.err || { cat $IN/derive.err >&2; exit 3; }
chmod 700 $KH
K=$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["0"])' $KH/k/1.json)
cd $KH && tar cf - SHA256SUMS.txt ANON_OK.json k/$K.json k/0.json k/1.json k/launch.json k/4.json k/pool_selection_13b52fee.json -C $IN derive.result.json
