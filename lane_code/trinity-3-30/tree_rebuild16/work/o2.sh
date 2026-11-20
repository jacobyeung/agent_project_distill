export TZ=UTC; date -u +%TZ; O=/project/community/jjyeung/okh7; P=$O/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820
ls -la $P/routing/pool | head -40; ls -la $P/prepared $P/vqa $P/pointing | head -30
grep -o '"catalog"[^}]*' $P/routing/receipt.json | head -3 | cut -c1-400
grep -o 'eac5f9f0[^"]*' -r $P/routing/receipt.json $P/routing/materialization.json $P/config.json | head -5
grep -o '"[^"]*"[^"]*"4e8e6c04[0-9a-f]*"' $P/routing/receipt.json $P/routing/materialization.json | head -5 | cut -c1-300
