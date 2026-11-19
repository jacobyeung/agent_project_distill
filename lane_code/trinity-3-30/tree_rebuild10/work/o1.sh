TZ=UTC squeue -u $USER -o '%i %j %T %M %S' 2>&1 | head
K=/project/community/jjyeung/okh7
f=$K/x_69d2930d/runs/673bc60f/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/receipt.json; ls -la $f; sha256sum $f; echo B64BEGIN; base64 -w0 $f; echo; echo B64END
ls $K/x_ee227714/runs 2>&1 | head; ls -la $K/x_ee227714/runs/6ed2c7aa $K/x_ee227714/runs/6ed2c7aa/inputs 2>&1 | head -30
