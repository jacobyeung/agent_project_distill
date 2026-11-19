from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';sys.path.insert(0,str(B))
from joblib import load
spec=load(B/'kits/q/k/p.json');uploads=load(B/'UPLOADS.json')
text='''The kit remains GO=false. Nothing was submitted. Run the commands below only after reviewing the delivery and supplying the missing pinned inputs.

Before submission, the operator creates these opaque links. The job authenticates the linked metadata archive and model archive against `k/p.json` before staging.

```bash
ln -s /project/community/jjyeung/distill/okit /project/community/jjyeung/okh7/l_94a76bda
ln -s /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar /project/community/jjyeung/okh7/l_3d48eea0
```

If a link already exists, check its target and pinned content. The delivery does not replace it.

The upload inventory is `UPLOADS.json`. Its entries specify every local file, opaque destination, SHA-256 and byte count. From the extracted delivery, the supplied `upload.py` checks every file before writing to N's new pool folder. It never writes into P's kit or run.

```bash
python3 work/build21/upload.py "$PWD" /project/community/jjyeung/okh7/x_22c714e1
```

The resolver requires the verified four-part export listing and pinned external tokenizer metadata. It checks P's export-only receipt, small-file archive, part lengths, individual hashes and combined hash. Native export files are staged together under their original manifest sibling names.

Mode q also requires authenticated host envelopes for all bound routing slices, with exact row membership, RGB joins, scene coverage and extent receipt. A missing input must remain a refusal. `proofs/receipts/RESULT.json` lists absent dependencies by SHA-256 and original path. The local capacity proof does not supply production RGB, model shards or host envelopes.

The decoded executable scanner covers shell arguments, environment names and values, staged paths and the decoded operational input map. Source code and authenticated provenance records retain their identifiers. Actual scheduler execution, bwrap isolation and the full model archive are not exercised locally.

The result archive contains the proof result and a separate room census. The census cannot admit a failed proof.
'''
text+=f"\nUpload total: {uploads['total_bytes']} bytes (source: `UPLOADS.json`). N pool: `{spec['n_root']}` (source: decoded `kits/q/k/p.json`).\n"
(B/'OPERATOR.md').write_text(text)
