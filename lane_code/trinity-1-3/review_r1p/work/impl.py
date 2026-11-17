import sys,json
tree,sel=sys.argv[1],sys.argv[2]
sys.path[:0]=[tree,tree+'/generator/derivgen_v7']
from student_pilot import s1_pool
impl=s1_pool.implementation();s=json.load(open(sel))['implementation']
print(tree.split('/')[-1], 'EQUAL' if impl==s else 'DIFF', sorted(k for k in set(impl)|set(s) if impl.get(k)!=s.get(k)))
