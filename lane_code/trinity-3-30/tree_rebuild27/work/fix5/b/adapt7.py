# Adapts the jn6 harness (build26: jn5 vs jn6) to compare jn6 with jn7. Usage: python3 adapt7.py <test_jn6.py> <test_extra6.py> <out dir>
# jn7 cases pre-create X/o/<job>/RELEASE, so a held case ends at its first poll; the harness then asserts
# exactly which cases held (failure, no TERM/USR1 to the work, helper written) and that each published tb.txt.
import sys
from pathlib import Path
s=Path(sys.argv[1]).read_text();e=Path(sys.argv[2]).read_text();out=Path(sys.argv[3])
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(a,s.count(a));s=s.replace(a,b)
rep("W=J/'work/build26'","W=J/'work/build27'")
rep("    if version in ('5','6'):\n","    if version in ('6','7'):\n")
rep("        mirror=[a for a in timeouts if any(str(v).endswith('j6.py') for v in a)]\n",
    "        mirror=[a for a in timeouts if any(str(v).endswith('j6.py') for v in a)]\n"
    "        # jn7: the traceback copy and the hold's own bounded calls are not publication attempts either.\n"
    "        held=[a for a in timeouts if any(str(v).endswith('j7.py') for v in a)]\n"
    "        timeouts=[a for a in timeouts if a not in mirror and a not in held]\n"
    "        hold=version=='7' and expected!=0 and not sig and not setup\n"
    "        hx=x/'o'/job\n"
    "        assert (hx/'HOLD.txt').is_file()==hold,(label,version,'hold',hold)\n"
    "        if hold:\n"
    "            end=(hx/'HOLD_END.txt').read_text()\n"
    "            assert 'reason=release status=%d '%expected in end,(label,end)\n"
    "            assert ('status=%d '%expected) in (hx/'HOLD.txt').read_text().splitlines()[0]\n"
    "        assert (hx/'tb.txt').is_file()==(version=='7' and not setup),(label,version,'tb')\n"
    "        if version=='7' and not setup: assert (hx/'tb.txt').stat().st_size<=204800\n"
    "        if version=='6': assert not held\n")
rep("        timeouts=[a for a in timeouts if a not in mirror]\n","")
rep("        if version=='6' and not setup:\n","        if version in ('6','7') and not setup:\n")
rep("    if pfail=='hang' and version=='6': assert 119<elapsed<124+31,elapsed",
    "    if pfail=='hang' and version=='6': assert 119<elapsed<124+31,elapsed\n"
    "    # jn7 adds the bounded tb copy and a hold released at its first poll.\n"
    "    if pfail=='hang' and version=='7': assert 119<elapsed<124+31+10,elapsed")
rep("            try: rc=p.wait(timeout=(124 if version=='5' else 160) if pfail=='hang' else 20)",
    "            try: rc=p.wait(timeout=(160 if version=='6' else 170) if pfail=='hang' else 20)")
rep("    job='8'+str(len(RESULTS)+1).zfill(4);node=local/('q_22c714e1_'+job)\n",
    "    job='8'+str(len(RESULTS)+1).zfill(4);node=local/('q_22c714e1_'+job)\n"
    "    if version=='7':(x/'o'/job).mkdir(parents=True,exist_ok=True);(x/'o'/job/'RELEASE').write_text('')\n")
rep("for v in ('5','6')","for v in ('6','7')",3)
(out/'test_jn7.py').write_text(s)
e2=e.replace("with_name('test_jn6.py')","with_name('test_jn7.py')").replace("for v in ('5','6')","for v in ('6','7')")
assert e2.count("('6','7')")==1 and 'test_jn7.py' in e2
(out/'test_extra7.py').write_text(e2);print('adapted')
