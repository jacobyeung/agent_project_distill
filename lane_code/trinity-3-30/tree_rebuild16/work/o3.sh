export TZ=UTC; O=/project/community/jjyeung/okh7; P=$O/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820
grep -o '.\{300\}eac5f9f0.json.\{200\}' $P/config.json | head -2
grep -o '.\{200\}eac5f9f0.json.\{100\}' $P/routing/materialization.json | head -2
grep -o '.\{250\}4e8e6c04e697.\{120\}' $P/routing/receipt.json | head -2
