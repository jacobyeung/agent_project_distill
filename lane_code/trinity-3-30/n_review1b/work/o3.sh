cd /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/routing || exit 1
sha256sum receipt.json materialization.json pool/*; echo ====; base64 -w0 materialization.json
