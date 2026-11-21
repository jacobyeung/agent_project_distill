import re
from .carrier_c1_routing import ALIAS
class SceneCoverageError(ValueError): pass
def dev_names(pin): return ['d1/scene0001_00','d1/v0af0925a20fb']
def benchmark_names(pin): return ['d3/42897607']
class Exclusions:
    def __init__(self,a,b): self.aliases={**ALIAS,'d1':'d1','d2':'d2','d3':'d3'}
    def dataset(self,v):
        if not isinstance(v,str) or v.casefold() not in self.aliases: raise SceneCoverageError('Unknown')
        return self.aliases[v.casefold()]
    def key(self,v):
        d,s=v.split('/',1); return self.dataset(d)+'/'+s
    def identifiers(self,row):
        ds,sc=row.get('dataset'),row.get('scene')
        if ds is None or not isinstance(sc,str): raise SceneCoverageError('lacks')
        return {self.dataset(ds)+'/'+sc}
