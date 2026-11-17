import math
TO_CM={'cm':1.0,'m':100.0,'in':2.54,'ft':30.48}
def slip(pred,gt,u, lo=math.log(1.6), hi=math.log(1.35)):
    gcm=gt*TO_CM[u]
    e_own=abs(math.log(pred/gt))
    cands=[(abs(math.log(pred*TO_CM[v]/gcm)),v) for v in TO_CM if v!=u]
    e,v=min(cands)
    if e_own>lo and e<hi and e<e_own: return v, pred*TO_CM[v]/TO_CM[u]
    return None, pred
