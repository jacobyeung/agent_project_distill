import re,sys
def dec(b,depth=0):
    out=[]
    for line in b.split(b'\n'):
        m=re.search(rb"bytes\.fromhex\(['\"]([0-9a-f]+)['\"]\)",line)
        if m and depth<6:
            out.append(b'<<HEX '+str(depth).encode()+b'>>');out.append(dec(bytes.fromhex(m.group(1).decode()),depth+1));out.append(b'<</HEX>>')
        else: out.append(line)
    return b'\n'.join(out)
d=dec(open(sys.argv[1],'rb').read())
d=d.replace(b'a4282fee306d6',b'TOKEN').replace(b'a89e8fdab55d4',b'TOKEN')
d=d.replace(b'a4282fee306d6'.hex().encode(),b'TOKENHEX').replace(b'a89e8fdab55d4'.hex().encode(),b'TOKENHEX')
sys.stdout.buffer.write(d)
