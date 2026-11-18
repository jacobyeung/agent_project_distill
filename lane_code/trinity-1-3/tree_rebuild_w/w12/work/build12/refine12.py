"""Retain prior kits and prepare empty kit destinations for the tightened check."""
from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build12'
target=B/'proofs/prior_kits'
assert not target.exists()
(B/'kits').rename(target)
(B/'kits').mkdir()
decisions=B/'DECISIONS.md'
text=decisions.read_text()
text+='\nUnknown null-valued keys are differences too: key presence must match outside the allow-list. Only recipe.mix can vary inside recipe. The focused producer/reader test covers the null-valued extension as well as the reviewer topology cases.\n'
decisions.write_text(text)
(B/'STATUS.md').write_text('# Build 12 status\n\nGO=false. The config comparison now distinguishes absent keys from explicit null values. Source qualification is being refreshed; prior kits remain retained under proofs/prior_kits.\n')
print(json.dumps(dict(kits_retained=str(target.relative_to(L)),new_kits_empty=True)))
