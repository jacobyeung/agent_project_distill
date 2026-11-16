"""Admission contract for externally merged dev-858 and official result bundles."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

F17='47308d99246bdf253a5d55ce9ec04a38a4fcc355092603a51e8de34604749eae'

def admit(pinfile,checkpoint,count):
    value=load(checked(load(pinfile)))
    if value.get('schema')!='legs1-auxiliary-comparison-v1':raise ValueError('Auxiliary comparison schema missing')
    if value.get('leg_artifact_sha256')!=checkpoint or value.get('f17_artifact_sha256')!=F17:
        raise ValueError('Auxiliary comparison checkpoint mismatch')
    if value.get('items')!=count or len(value['leg'])!=count or len(value['f17'])!=count:
        raise ValueError('Auxiliary comparison membership size differs')
    if value.get('parity_pass') is not True or value.get('synthetic') is not False:
        raise ValueError('Auxiliary comparison must be empirical with passing parity')
    for side in ('leg','f17'):
        if not value.get('sources',{}).get(side):raise ValueError('Auxiliary comparison needs source receipts')
        for p in value['sources'][side]:checked(p)
    return value
