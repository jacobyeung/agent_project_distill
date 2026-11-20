from common import *
import re
for name in NAMES:
 p=D/('naming24m1_'+name+'.py');s=p.read_text()
 maps=J.load(D/'DEPENDENT_PINS.json')[name]['source_maps']
 values={(rel,field):h for rel,fields in maps.items() for field,h in fields.items()}
 replace(p,re.sub(r'^SOURCE_SEALS=.*$','SOURCE_SEALS='+repr(values),s,flags=re.M))
p=L/'out/arm_routing.py';replace(p,p.read_text().replace('build24m4l','build24m4n').replace('24M4L','24M4N'))
print('Scanner pins and arming helper updated')
