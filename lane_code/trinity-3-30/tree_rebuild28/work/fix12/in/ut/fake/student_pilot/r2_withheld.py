SHA256='w'
def room(x): return x
class Withheld:
    def __init__(self): self.aliases={'scannet/scene0003'}
    def touches(self,row,cov): return bool(set(cov.get('names',[]))&{'d1/scene0003'})
