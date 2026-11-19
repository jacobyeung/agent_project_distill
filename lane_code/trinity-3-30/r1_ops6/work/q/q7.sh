export TZ=UTC; date -u +%FT%TZ
K=/project/community/jjyeung/okh7/x_ee227714; I=$K/runs/6ed2c7aa/inputs
cat $I/phase_prepare.complete.json; echo
find $I/prepare_da5580b7d92f490bb3cfe8df447e7820 -maxdepth 3 | head -40
tail -6 $K/o/172660.steps | cut -c1-220
ls -la --time-style=+%H:%M:%S $K/runs/6ed2c7aa | awk '{print $5,$6,$7}'
