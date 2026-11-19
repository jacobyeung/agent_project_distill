export TZ=UTC; date -u +%FT%TZ
P=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820
python3 -c "
import json;d=json.load(open('$P/prepared/receipt.json'));print(json.dumps(d['h1_r0']['per_source'])[:600])"
sha256sum $P/config.json $P/vqa/receipt.json $P/prepared/receipt.json | cut -c1-16
tail -4 /project/community/jjyeung/okh7/x_ee227714/o/172660.steps | cut -c1-200
