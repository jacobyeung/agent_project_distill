from common import *
s=(L/'work/build24m2b/scene_tests.py').read_text()
s=s.replace("F=D/'scene_tests'","F=D/'scene_tests'")
# Use production native functions, with retained synthetic population pins.
(D/'scene_tests.py').write_text(s)
