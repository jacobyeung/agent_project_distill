import os, sys, tarfile
names = [l.strip() for l in open(sys.argv[1]) if l.strip()]
t = tarfile.TarFile(fileobj=open(os.devnull, 'wb'), mode='w', format=tarfile.PAX_FORMAT)
total = 0
for n in names:
    ti = t.gettarinfo('/' + n, arcname=n)
    total += len(ti.tobuf(tarfile.PAX_FORMAT, tarfile.ENCODING, 'surrogateescape'))
    total += (ti.size + 511) // 512 * 512
total += 1024
total = (total + tarfile.RECORDSIZE - 1) // tarfile.RECORDSIZE * tarfile.RECORDSIZE
print(total)
