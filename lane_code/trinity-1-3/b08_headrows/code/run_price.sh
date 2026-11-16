#!/bin/bash
# Price all dev-S1 captures with the frozen predicted-mask programs (CPU), one process per scene, 8 at a time.
L=/scratch/jjyeung/orch_n30/b08_headrows; W=$L/work; S=$W/src118/devs1_mask_run/kit
cd $W
python3 -c "import json;[print(c['scene']) for c in json.load(open('$S/out/MANIFEST.json'))['captures']]" > $W/price_scenes.txt
cat $W/price_scenes.txt | xargs -P 8 -I{} bash -c 'sid=$(echo {} | tr / _); /scratch/jjyeung/envs/p1cpu/bin/python -I -s '$L'/code/pricekit/price_masks.py --manifest '$S'/out/MANIFEST.json --items '$S'/out/ITEMS.jsonl --cache '$W'/src118/devs1_mask_run/candidates --exports '$W'/src118/devs1_r2 --head-pins '$S'/out/HEADS.json --out '$W'/price_r1/$sid --scene {} > '$W'/logs/price_$sid.log 2>&1; echo "{} rc=$?" >> '$W'/logs/price_done.txt'
echo ALLDONE >> $W/logs/price_done.txt
