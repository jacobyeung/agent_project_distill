#!/bin/bash
export TZ=UTC; KH=/project/community/jjyeung/okh7/x_ee227714; R=$KH/runs/6ed2c7aa
echo "== steps"; cat -n $KH/o/172660.steps | cut -c1-200
echo "== w.steps"; cat -n $KH/o/172660.w.steps | cut -c1-200
echo "== vt.json"; sha256sum $KH/o/172660.vt.json; grep -n -o -E "210b2534[0-9a-f]*|rows.sqlite[^,]{0,120}" $KH/o/172660.vt.json | head
echo "== d"; cat $R/d/0.json; echo; sha256sum $R/d/binding.json $R/d/inputs/data_receipt.json
grep -c "" $KH/o/172660.err
