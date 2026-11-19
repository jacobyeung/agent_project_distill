export TZ=UTC; date -u +%FT%TZ
R=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa; P=$R/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820
ls -la --time-style=+%H:%M:%S $R $R/inputs | awk '{print $5,$6,$7}'
sha256sum $P/config.json $P/prepared/s1_receipt.json $P/prepared/receipt.json $R/inputs/data_receipt.json 2>&1
python3 -c "
import json;c=json.load(open('$P/config.json'));print('config preparation pin:',json.dumps(c.get('preparation') or c.get('admission'))[:300])" 2>&1
tail -3 /project/community/jjyeung/okh7/x_ee227714/o/172660.steps | cut -c1-200
