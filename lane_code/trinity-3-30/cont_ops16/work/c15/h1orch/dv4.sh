P=/project/community/jjyeung/okh7/x_f5c353f7/runs/359fcc3c/inputs/prepare_35e47f02fbf74107ae910d52e99157e8/routing/pool
ls -la $P; test -f $P/receipt.json && { sha256sum $P/receipt.json; head -c 6000 $P/receipt.json; }
