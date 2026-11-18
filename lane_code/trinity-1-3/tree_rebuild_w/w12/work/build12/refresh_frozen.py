from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build12'
old=B/'proofs/n1/package/frozen';retained=B/'proofs/prior_frozen'
assert old.exists() and not retained.exists()
old.rename(retained)
print('Prior extraction retained; the next package extraction starts empty.')
