from common import *
p=L/'out/rcj/x.py';s=p.read_text().replace('"PATH":str(binary.parent)+os.pathsep+os.environ.get("PATH", "")','"PATH":"/project/community/jjyeung/cp4tk_rt/kit:/usr/local/bin:/usr/bin:/bin"')
s=s.replace("    binary = z.checked(pin['file'], pin['sha256'])","    binary = z.checked(pin['file'], pin['sha256'])\n    if str(binary) != '/project/community/jjyeung/cp4tk_rt/kit/bwrap':\n        raise ValueError('R1_BINARY_LOCATION_DIFFERS')")
replace(p,s);(D/'rcj_scan.log').rename(L/'attic/build24m4j/rcj_scan_third.log')
