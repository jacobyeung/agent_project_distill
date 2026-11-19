K=/project/community/jjyeung/okh7; cd $K
F="x_69d2930d/runs/673bc60f/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/receipt.json"
ls -la $F; sha256sum $F | cut -c1-16,65-; ls x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared | head
echo B64BEGIN; tar czf - $F | base64 -w0; echo; echo B64END
