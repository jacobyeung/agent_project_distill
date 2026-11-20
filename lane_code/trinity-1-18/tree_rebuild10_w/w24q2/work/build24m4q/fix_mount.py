from pathlib import Path
import time
L=Path.cwd();p=L/'out/rcj/pc.py';s=p.read_text()
s=s.replace("            at=cmd.index('--chdir')\n            for dest,item in sorted(assets.items()):", "            at=cmd.index('--chdir')\n            cmd[at:at]=['--tmpfs',value['root']]; at+=2\n            for dest,item in sorted(assets.items()):")
s=s.replace("                cmd[at:at]=['--ro-bind',item['source'],dest]; at+=3\n            cmd[-3:]", "                cmd[at:at]=['--ro-bind',item['source'],dest]; at+=3\n            cmd[at:at]=['--remount-ro',value['root']]\n            cmd[-3:]")
a=L/'attic/build24m4q/pc_mount1.py';p.rename(a);p.write_text(s)
p=L/'out/rcj/x.py';s=p.read_text().replace("        z.write(root/'ch_cfg.json', cfg)\n        try:","        try:\n            z.write(root/'ch_cfg.json', cfg)\n        except Exception:\n            pass\n        try:")
s=s.replace("                    z.write(root/'chain.json', dict(status='UNAVAILABLE',\n                        reason=type(error).__name__+': '+str(error)))", "                    try:\n                        z.write(root/'chain.json', dict(status='UNAVAILABLE',\n                            reason=type(error).__name__+': '+str(error)))\n                    except Exception:\n                        pass")
a=L/'attic/build24m4q/x_diagnostic1.py';p.rename(a);p.write_text(s)
