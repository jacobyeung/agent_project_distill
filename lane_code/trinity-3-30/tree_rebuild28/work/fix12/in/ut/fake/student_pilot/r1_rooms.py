import re
class Rooms:
    def __init__(self,pins):
        self.aliases={'d3/vaaaaaaaaaaaa':'arkitscenes/42897607'}
        self.visits={'111':'NA'}; self.r0={'scannetpp/r0room'}; self.k1={'scannet/scene0002'}
    def canonical(self,row):
        c=self.aliases.get(row.get('dataset','')+'/'+row.get('scene',''))
        return (c,'alias') if c else (None,'unresolved')
    def room(self,c):
        ds,cap=c.split('/',1)
        if ds=='scannet':
            m=re.match(r'(scene\d+)',cap)
            if m: return 'scannet/'+m.group(1)
        if ds in ('scannetpp','scannetppv2'): return 'scannetpp/'+cap
        if ds=='arkitscenes' and cap.isdigit(): return 'arkitscenes/capture'+cap
        raise ValueError('R1_ROOM_CANONICAL_UNRESOLVED')
    def status(self,row):
        c,h=self.canonical(row)
        if not c: return 'unresolved',None,h
        return 'ok',c,h
