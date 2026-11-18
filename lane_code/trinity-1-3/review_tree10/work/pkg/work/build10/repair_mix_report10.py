from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
(L/'out/MIX_R1.json').write_bytes((B/'inputs/mix.json').read_bytes())
old=B/'proofs/kits/metadata_pass'
assert not old.exists()
(B/'kits').rename(old)
(B/'KIT_METADATA_REPAIR.json').write_text(json.dumps(dict(reason='Local path relocation changes the mix metadata bytes. The report copy must equal the bound mix, preserving all quota values.',
    source='work/build10/inputs/mix.json',report='out/MIX_R1.json',retained='work/build10/proofs/kits/metadata_pass'),indent=2)+'\n')
