"""Stop before any payload IO, then write one tar stream of the listed files (relative to ROOT) to stdout.
Logs name<TAB>size of every member to SIZES. No exec, no children, no retry. usage: reader.py ROOT LIST SIZES"""
import os, signal, sys, tarfile
root, lst, sizes = sys.argv[1:4]
names = [l.strip() for l in open(lst) if l.strip()]
log = open(sizes, 'w')
os.kill(os.getpid(), signal.SIGSTOP)
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.PAX_FORMAT) as t:
    for n in names:
        ti = t.gettarinfo(os.path.join(root, n), arcname=n)
        with open(os.path.join(root, n), 'rb') as f:
            t.addfile(ti, f)
        log.write('%s\t%d\n' % (n, ti.size)); log.flush()
