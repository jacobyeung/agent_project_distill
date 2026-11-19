R=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b
for p in u/7c9f2d84/receipt.json k/8957d119.json runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/routing/receipt.json f/469ddece/receipt.json; do ls -la $R/$p 2>&1 | cut -c1-250; done
ls $R/f/469ddece 2>&1 | head; ls $R/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820 2>&1 | head -20; ls $R/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/routing 2>&1 | head
