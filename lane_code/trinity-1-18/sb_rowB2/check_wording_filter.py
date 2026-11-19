"""Check bounded Levenshtein against an unbanded dynamic program."""
import ctypes
import hashlib
import itertools
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    f=ctypes.CDLL(str(ROOT/'inputs/wording_filter.so')).within
    f.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];f.restype=ctypes.c_int
    strings=[''.join(s) for n in range(5) for s in itertools.product('ab',repeat=n)]
    def distance(a,b):
        previous=list(range(len(b)+1))
        for i,x in enumerate(a,1):
            current=[i]
            for j,y in enumerate(b,1):
                current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
            previous=current
        return previous[-1]
    count=0
    for a in strings:
        for b in strings:
            want=distance(a,b)
            for k in range(4):
                assert f(a.encode(),b.encode(),k)==min(want,k+1),(a,b,k,want)
                count+=1
    result=dict(status='PASS',comparisons=count,input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__),ROOT/'wording_filter.cpp',ROOT/'inputs/wording_filter.so']})
    (ROOT/'out/WORDING_FILTER_CHECK.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('PASS',count)
if __name__=='__main__':main()
