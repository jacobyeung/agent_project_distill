"""Resolve the shipped adapter and the explicitly supplied trainer tree."""
import os
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
CORE=BASE/'sj/orch_cd/evalx/work/milestone'

def install(tree):
    os.environ['LEGS1_TREE']=str(Path(tree).resolve())
    sys.path.extend([str(CORE/'native/out2'),str(CORE/'orchard_native'),str(CORE),str(Path(tree).resolve())])
    import common
    common.TREE=Path(tree).resolve()
    import geometry,routed
    geometry.TREE=routed.TREE=common.TREE
    return common
