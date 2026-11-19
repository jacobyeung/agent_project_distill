from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];D=L/'work/build21e';A=L/'attic/build21e'
delivery=json.loads((D/'DELIVERY.json').read_text());path=L/delivery['package']
path.rename(A/path.name)
(D/'DELIVERY.json').rename(A/'DRAFT_DELIVERY.json')
print('Draft retained in',A/path.name)
