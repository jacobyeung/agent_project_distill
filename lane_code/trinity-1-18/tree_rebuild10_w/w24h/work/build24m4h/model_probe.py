import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
r=J.load(input_file('0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a'))
print('BASE MODEL',r['base_model'])
try:
 p=input_file(r['base_model']['sha256']);v=J.load(p);print('MODEL ROOT',v.get('root'));print('FILES',list(v.get('files',{})))
except ValueError as e:print(e)
